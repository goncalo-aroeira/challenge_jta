import os
import json
import time
from typing import Any, Dict, List
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from .prompts import SYSTEM_PROMPT

# Load .env file
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)

# Import tools
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from recsys.tools import (
    search_products,
    get_product_details,
    get_cooccurrence_neighbors,
    find_similar_products,
    get_product_by_name_fuzzy
)
from utils.tracking import QueryTracker


class Agent:
    """
    LLM Agent with Function Calling capabilities.
    
    Uses OpenAI's function calling to let the LLM decide which tools to use
    and execute them in an agentic loop.
    """
    
    def __init__(self, session_id: str = "default"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.tools = self._define_tools()
        self.max_iterations = 5  # Prevent infinite loops
        self.session_id = session_id
        self.tracker = QueryTracker()
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """
        Define available tools for the LLM using OpenAI function calling schema.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_products",
                    "description": "Search for Nintendo Switch products with various filters. Use this when the customer wants products matching specific criteria.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "store": {
                                "type": "string",
                                "enum": ["Store A", "Store B", "Store C"],
                                "description": "Filter by specific store"
                            },
                            "max_age": {
                                "type": "integer",
                                "description": "Maximum age rating (e.g., 7 for games suitable for 7 year olds)"
                            },
                            "exclude_franchise": {
                                "type": "string",
                                "description": "Franchise to exclude from results (e.g., 'Super Mario')"
                            },
                            "segment": {
                                "type": "string",
                                "enum": ["Games", "Console", "Accessories"],
                                "description": "Product segment",
                                "default": "Games"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_product_details",
                    "description": "Get detailed information about a specific product by ID or name. Use when customer mentions a specific game.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "integer",
                                "description": "Product ID"
                            },
                            "product_name": {
                                "type": "string",
                                "description": "Product name (used if product_id not provided)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_cooccurrence_neighbors",
                    "description": "Find products frequently bought together with a given product. Use when customer asks 'what goes well with X' or wants similar products.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "integer",
                                "description": "ID of the product to find neighbors for"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 5
                            }
                        },
                        "required": ["product_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_similar_products",
                    "description": "Find products similar to a given product. Currently uses co-occurrence as proxy. Use when customer asks for 'games like X'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "integer",
                                "description": "ID of the reference product"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of similar products",
                                "default": 5
                            }
                        },
                        "required": ["product_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_product_by_name_fuzzy",
                    "description": "Search for products by partial name (fuzzy matching). Use when customer mentions a game but you need to find the exact product.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Partial product name to search for"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 5
                            }
                        },
                        "required": ["name"]
                    }
                }
            }
        ]
    
    def run(self, query: str) -> str:
        """
        Main agentic loop with function calling.
        
        Process:
        1. Send query to LLM with available tools
        2. LLM decides which tools to call (if any)
        3. Execute tools and return results to LLM
        4. LLM generates final response
        5. Repeat if needed (max iterations limit)
        """
        # Start tracking
        start_time = time.time()
        self.tracker.start_query(query, self.session_id)
        
        print(f"\n{'='*60}")
        print(f"Processing query: {query}")
        print(f"{'='*60}\n")
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ]
        
        total_products = 0
        total_tokens = 0
        
        for iteration in range(self.max_iterations):
            print(f"--- Iteration {iteration + 1} ---")
            
            # Call LLM with tools
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.tools,
                tool_choice="auto"  # Let LLM decide
            )
            
            message = response.choices[0].message
            
            # Track tokens
            if hasattr(response, 'usage'):
                total_tokens += response.usage.total_tokens
            
            # Check if LLM wants to call tools
            if not message.tool_calls:
                # No tool calls - LLM has final answer
                print("✓ LLM generated final response (no tools needed)")
                
                # Finish tracking
                elapsed_ms = (time.time() - start_time) * 1000
                self.tracker.finish_query(
                    success=True,
                    products_count=total_products,
                    elapsed_ms=elapsed_ms,
                    tokens_used=total_tokens
                )
                
                return message.content
            
            # LLM wants to call tools
            print(f"LLM requested {len(message.tool_calls)} tool call(s):")
            
            # Add LLM's message to conversation
            messages.append(message)
            
            # Execute each tool call
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"  → {function_name}({arguments})")
                
                # Track tool call
                self.tracker.log_tool_call(function_name, arguments)
                
                # Execute the tool
                try:
                    result = self._execute_tool(function_name, arguments)
                    result_str = json.dumps(result)
                    
                    # Count products returned
                    if isinstance(result, list):
                        total_products += len(result)
                        print(f"    ✓ Returned {len(result)} result(s)")
                    else:
                        if result and not result.get("error"):
                            total_products += 1
                        print(f"    ✓ Returned 1 result")
                except Exception as e:
                    result_str = json.dumps({"error": str(e)})
                    print(f"    ✗ Error: {e}")
                
                # Add tool result to conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str
                })
        
        # Max iterations reached
        print("\n⚠ Max iterations reached")
        
        # Finish tracking
        elapsed_ms = (time.time() - start_time) * 1000
        self.tracker.finish_query(
            success=False,
            products_count=total_products,
            elapsed_ms=elapsed_ms,
            tokens_used=total_tokens
        )
        
        return "I apologize, but I'm having trouble processing your request. Could you please rephrase or simplify your question?"
    
    def _execute_tool(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute the requested tool function.
        """
        tool_map = {
            "search_products": search_products,
            "get_product_details": get_product_details,
            "get_cooccurrence_neighbors": get_cooccurrence_neighbors,
            "find_similar_products": find_similar_products,
            "get_product_by_name_fuzzy": get_product_by_name_fuzzy
        }
        
        func = tool_map.get(function_name)
        if not func:
            return {"error": f"Tool '{function_name}' not found"}
        
        try:
            return func(**arguments)
        except Exception as e:
            return {"error": str(e)}

