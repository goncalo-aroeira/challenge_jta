"""
Query logging and tracking system.
Tracks all interactions with the agent for analytics and continuous improvement.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
from sqlalchemy import text

from src.config.database import engine


@dataclass
class QueryLog:
    """
    Structured log of a single query interaction.
    """
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: str = ""
    
    # Query
    query: str = ""
    intent_type: Optional[str] = None
    
    # Execution
    tools_called: List[str] = field(default_factory=list)
    tool_arguments: Dict[str, Any] = field(default_factory=dict)
    used_fallback: bool = False
    
    # Results
    products_returned: int = 0
    response_time_ms: float = 0.0
    llm_tokens_used: int = 0
    success: bool = False
    
    # Feedback (optional)
    user_feedback: Optional[int] = None  # 1-5 stars
    user_clicked_product: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['tools_called'] = json.dumps(self.tools_called)
        data['tool_arguments'] = json.dumps(self.tool_arguments)
        return data


class QueryTracker:
    """
    Manages query logging and persistence.
    """
    
    def __init__(self):
        self.current_log: Optional[QueryLog] = None
        self.logs: List[QueryLog] = []
    
    def start_query(self, query: str, session_id: str = "default"):
        """Start tracking a new query."""
        self.current_log = QueryLog(
            timestamp=datetime.now(),
            session_id=session_id,
            query=query
        )
    
    def set_intent(self, intent_type: str):
        """Set the detected intent type."""
        if self.current_log:
            self.current_log.intent_type = intent_type
    
    def log_tool_call(self, tool_name: str, arguments: Dict[str, Any]):
        """Log a tool call."""
        if self.current_log:
            self.current_log.tools_called.append(tool_name)
            self.current_log.tool_arguments[tool_name] = arguments
    
    def set_fallback(self, used: bool = True):
        """Mark if fallback mechanism was used."""
        if self.current_log:
            self.current_log.used_fallback = used
    
    def finish_query(
        self, 
        success: bool, 
        products_count: int, 
        elapsed_ms: float,
        tokens_used: int = 0
    ):
        """Finish tracking and save to database."""
        if self.current_log:
            self.current_log.success = success
            self.current_log.products_returned = products_count
            self.current_log.response_time_ms = elapsed_ms
            self.current_log.llm_tokens_used = tokens_used
            
            # Save to memory
            self.logs.append(self.current_log)
            
            # Save to database (if table exists)
            try:
                self._save_to_db(self.current_log)
            except Exception as e:
                print(f"Warning: Could not save log to database: {e}")
            
            # Reset
            self.current_log = None
    
    def add_feedback(self, rating: int, product_id: Optional[int] = None):
        """Add user feedback to the last query."""
        if self.logs:
            last_log = self.logs[-1]
            last_log.user_feedback = rating
            last_log.user_clicked_product = product_id
            
            # Update in database
            try:
                self._update_feedback(last_log)
            except Exception as e:
                print(f"Warning: Could not update feedback: {e}")
    
    def _save_to_db(self, log: QueryLog):
        """Save log to PostgreSQL."""
        sql = """
            INSERT INTO query_logs 
            (timestamp, session_id, query, intent_type, tools_called, 
             tool_arguments, used_fallback, products_returned, 
             response_time_ms, llm_tokens_used, success)
            VALUES 
            (:timestamp, :session_id, :query, :intent, :tools, 
             :args, :fallback, :count, :time, :tokens, :success)
        """
        
        with engine.begin() as conn:
            conn.execute(text(sql), {
                "timestamp": log.timestamp,
                "session_id": log.session_id,
                "query": log.query,
                "intent": log.intent_type,
                "tools": json.dumps(log.tools_called),
                "args": json.dumps(log.tool_arguments),
                "fallback": log.used_fallback,
                "count": log.products_returned,
                "time": log.response_time_ms,
                "tokens": log.llm_tokens_used,
                "success": log.success
            })
    
    def _update_feedback(self, log: QueryLog):
        """Update feedback in database."""
        sql = """
            UPDATE query_logs
            SET user_feedback = :feedback,
                user_clicked_product = :product_id
            WHERE timestamp = :timestamp AND session_id = :session_id
        """
        
        with engine.begin() as conn:
            conn.execute(text(sql), {
                "feedback": log.user_feedback,
                "product_id": log.user_clicked_product,
                "timestamp": log.timestamp,
                "session_id": log.session_id
            })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from logged queries."""
        if not self.logs:
            return {"total_queries": 0}
        
        total = len(self.logs)
        successful = sum(1 for log in self.logs if log.success)
        avg_time = sum(log.response_time_ms for log in self.logs) / total
        avg_products = sum(log.products_returned for log in self.logs) / total
        
        # Tool usage distribution
        tool_counts: Dict[str, int] = {}
        for log in self.logs:
            for tool in log.tools_called:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        return {
            "total_queries": total,
            "success_rate": successful / total if total > 0 else 0,
            "avg_response_time_ms": avg_time,
            "avg_products_returned": avg_products,
            "tool_usage": tool_counts,
            "fallback_rate": sum(1 for log in self.logs if log.used_fallback) / total
        }
    
    def print_stats(self):
        """Print statistics to console."""
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("QUERY TRACKER STATISTICS")
        print("="*60)
        print(f"Total Queries: {stats['total_queries']}")
        print(f"Success Rate: {stats.get('success_rate', 0):.1%}")
        print(f"Avg Response Time: {stats.get('avg_response_time_ms', 0):.0f}ms")
        print(f"Avg Products Returned: {stats.get('avg_products_returned', 0):.1f}")
        print(f"Fallback Usage: {stats.get('fallback_rate', 0):.1%}")
        
        if stats.get('tool_usage'):
            print("\nTool Usage:")
            for tool, count in sorted(stats['tool_usage'].items(), key=lambda x: x[1], reverse=True):
                print(f"  - {tool}: {count} calls")
        
        print("="*60 + "\n")


# Global tracker instance
_global_tracker: Optional[QueryTracker] = None


def get_tracker() -> QueryTracker:
    """Get or create the global query tracker."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = QueryTracker()
    return _global_tracker


# SQL to create the query_logs table
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS query_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    session_id VARCHAR(100),
    
    -- Query
    query TEXT NOT NULL,
    intent_type VARCHAR(50),
    
    -- Execution
    tools_called JSONB,
    tool_arguments JSONB,
    used_fallback BOOLEAN DEFAULT FALSE,
    
    -- Results
    products_returned INT,
    response_time_ms INT,
    llm_tokens_used INT,
    success BOOLEAN,
    
    -- Feedback
    user_feedback INT CHECK (user_feedback BETWEEN 1 AND 5),
    user_clicked_product INT
);

CREATE INDEX IF NOT EXISTS idx_query_logs_timestamp ON query_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_query_logs_intent ON query_logs(intent_type);
CREATE INDEX IF NOT EXISTS idx_query_logs_success ON query_logs(success);
"""


def init_logging_table():
    """Initialize the query_logs table in the database."""
    try:
        with engine.begin() as conn:
            conn.execute(text(CREATE_TABLE_SQL))
        print("✓ Query logging table initialized")
    except Exception as e:
        print(f"Warning: Could not initialize query_logs table: {e}")


if __name__ == "__main__":
    # Test the tracker
    print("Testing QueryTracker...")
    
    tracker = QueryTracker()
    
    # Simulate a query
    tracker.start_query("Test query: games for kids", session_id="test-123")
    tracker.set_intent("search_product")
    tracker.log_tool_call("search_products", {"store": "Store A", "max_age": 7})
    tracker.finish_query(success=True, products_count=5, elapsed_ms=245.5, tokens_used=150)
    
    # Simulate another query
    tracker.start_query("I want pizza", session_id="test-123")
    tracker.set_intent("unrelated")
    tracker.finish_query(success=True, products_count=0, elapsed_ms=120.0, tokens_used=50)
    
    # Print stats
    tracker.print_stats()
    
    print("\n✓ QueryTracker test completed")
