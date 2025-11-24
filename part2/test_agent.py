"""
Test script for the Agent with Function Calling.
"""
import os
import sys
from pathlib import Path

# Add part2 to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

print(f"🔑 API Key loaded: {os.getenv('OPENAI_API_KEY')[:20]}..." if os.getenv('OPENAI_API_KEY') else "❌ API Key NOT loaded")

from src.agent.core import Agent


def test_agent():
    print("\n" + "="*80)
    print("TESTING AGENT WITH FUNCTION CALLING")
    print("="*80)
    
    agent = Agent(session_id="test-session")
    
    # Test 1: Unrelated Query (from README)
    print("\n\n" + "="*80)
    print("TEST 1: Unrelated Query (should detect and decline politely)")
    print("="*80)
    query1 = "I want a pepperoni pizza with extra cheese please."
    response1 = agent.run(query1)
    print(f"\nFinal Response:\n{response1}\n")
    
    # Test 2: Simple Search
    print("\n\n" + "="*80)
    print("TEST 2: Simple Search Query")
    print("="*80)
    query2 = "I want games for a 5 year old child at Store A"
    response2 = agent.run(query2)
    print(f"\nFinal Response:\n{response2}\n")
    
    # Test 3: Complex Query (from README)
    print("\n\n" + "="*80)
    print("TEST 3: Complex Query with Multiple Constraints")
    print("="*80)
    query3 = """I want to buy a game for my nephew, at Store A, who is 5 years old.
We loved Super Mario Odyssey, but I cannot buy a game from this family as he already has all Super Mario games."""
    response3 = agent.run(query3)
    print(f"\nFinal Response:\n{response3}\n")
    
    # Test 4: Similar Products Query
    print("\n\n" + "="*80)
    print("TEST 4: Finding Similar Products")
    print("="*80)
    query4 = "What games are similar to Animal Crossing?"
    response4 = agent.run(query4)
    print(f"\nFinal Response:\n{response4}\n")
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80 + "\n")
    
    # Print statistics
    agent.tracker.print_stats()


if __name__ == "__main__":
    test_agent()
