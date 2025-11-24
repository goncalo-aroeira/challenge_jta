"""
Mock test for Agent - demonstrates functionality without OpenAI API key.
"""
import os
import sys
import json
from unittest.mock import Mock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.core import Agent


def create_mock_response(content=None, tool_calls=None):
    """Create a mock OpenAI response."""
    mock_message = Mock()
    mock_message.content = content
    mock_message.tool_calls = tool_calls
    
    mock_choice = Mock()
    mock_choice.message = mock_message
    
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.usage = Mock()
    mock_response.usage.total_tokens = 100
    
    return mock_response


def create_tool_call(function_name, arguments):
    """Create a mock tool call."""
    mock_tool_call = Mock()
    mock_tool_call.id = f"call_{function_name}_123"
    mock_tool_call.function = Mock()
    mock_tool_call.function.name = function_name
    mock_tool_call.function.arguments = json.dumps(arguments)
    return mock_tool_call


def test_mock_agent():
    print("\n" + "="*80)
    print("MOCK TEST - AGENT WITH FUNCTION CALLING (No API Key Required)")
    print("="*80)
    
    # Test 1: Unrelated Query
    print("\n\n" + "="*80)
    print("TEST 1: Unrelated Query (pizza)")
    print("="*80)
    
    with patch('openai.OpenAI') as mock_openai:
        # Mock the OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # First call: LLM responds directly (no tools)
        mock_client.chat.completions.create.return_value = create_mock_response(
            content="I apologize, but I can only help you with Nintendo Switch products. I cannot assist with ordering pizza. However, I'd be happy to recommend some great Nintendo Switch games! Would you like some suggestions?"
        )
        
        agent = Agent(session_id="mock-test")
        response = agent.run("I want a pepperoni pizza with extra cheese please.")
        
        print(f"\n✓ Agent Response:\n{response}\n")
        assert "Nintendo Switch" in response
        assert "pizza" in response.lower()
    
    # Test 2: Simple Search with Tool Call
    print("\n\n" + "="*80)
    print("TEST 2: Simple Search Query (requires tools)")
    print("="*80)
    
    with patch('openai.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # First call: LLM wants to use search_products
        tool_call = create_tool_call("search_products", {
            "store": "Store A",
            "max_age": 5,
            "segment": "Games",
            "limit": 5
        })
        
        mock_client.chat.completions.create.side_effect = [
            create_mock_response(tool_calls=[tool_call]),
            create_mock_response(content="""Great! I found several perfect games for a 5-year-old at Store A:

1. **Animal Crossing: New Horizons** (Age 3+)
   - A relaxing and creative game where you build your own island paradise
   - Perfect for young children with its peaceful gameplay

2. **Kirby Star Allies** (Age 3+)
   - Colorful and fun platformer adventure
   - Easy controls, great for beginners

3. **Mario Kart 8 Deluxe** (Age 6+)
   - Fun racing game that the whole family can enjoy
   - Has assisted steering mode for younger players

All of these are available at Store A and are age-appropriate for a 5-year-old!""")
        ]
        
        agent = Agent(session_id="mock-test")
        response = agent.run("I want games for a 5 year old child at Store A")
        
        print(f"\n✓ Agent Response:\n{response}\n")
        assert "Animal Crossing" in response or "games" in response.lower()
    
    # Test 3: Complex Query with Multiple Tools
    print("\n\n" + "="*80)
    print("TEST 3: Complex Query (multiple tools, excluding franchise)")
    print("="*80)
    
    with patch('openai.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # First call: Search for "Super Mario Odyssey"
        tool_call_1 = create_tool_call("get_product_by_name_fuzzy", {
            "name": "Super Mario Odyssey"
        })
        
        # Second call: Get similar products
        tool_call_2 = create_tool_call("get_cooccurrence_neighbors", {
            "product_id": 2,
            "limit": 5
        })
        
        # Third call: Search with filters
        tool_call_3 = create_tool_call("search_products", {
            "store": "Store A",
            "max_age": 5,
            "exclude_franchise": "Super Mario",
            "segment": "Games",
            "limit": 10
        })
        
        mock_client.chat.completions.create.side_effect = [
            create_mock_response(tool_calls=[tool_call_1]),
            create_mock_response(tool_calls=[tool_call_2, tool_call_3]),
            create_mock_response(content="""Perfect! Since your nephew loved Super Mario Odyssey but already has all Super Mario games, here are excellent alternatives at Store A for a 5-year-old:

**Top Recommendations:**

1. **Animal Crossing: New Horizons** (Age 3+)
   - Customers who loved Mario Odyssey also enjoyed this
   - Creative, relaxing gameplay perfect for young children
   - Available at Store A

2. **Kirby Star Allies** (Age 3+)
   - Similar platforming fun but in the Kirby universe
   - Colorful and accessible for younger players
   - Great alternative to Mario games

3. **Yoshi's Crafted World** (Age 3+)
   - Charming platformer with a unique art style
   - Easy difficulty, perfect for 5-year-olds
   - Available at Store A

These games share the fun, accessible platforming that made Mario Odyssey great, but offer fresh experiences in different franchises!""")
        ]
        
        agent = Agent(session_id="mock-test")
        query = """I want to buy a game for my nephew, at Store A, who is 5 years old.
We loved Super Mario Odyssey, but I cannot buy a game from this family as he already has all Super Mario games."""
        response = agent.run(query)
        
        print(f"\n✓ Agent Response:\n{response}\n")
        assert ("Animal Crossing" in response or "Kirby" in response or 
                "recommendations" in response.lower())
    
    print("\n" + "="*80)
    print("ALL MOCK TESTS PASSED ✓")
    print("="*80)
    print("\nNote: These are mock tests demonstrating the agent's behavior.")
    print("To test with real OpenAI API, set OPENAI_API_KEY and run test_agent.py")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_mock_agent()
