import sys
import os
from dotenv import load_dotenv

# Load env vars explicitly
load_dotenv()

# Add current directory to sys.path so we can import src
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from src.agent.core import Agent

def main():
    # Initialize agent
    try:
        agent = Agent()
    except Exception as e:
        print(f"Error initializing agent: {e}")
        print("Please check your .env file and API keys.")
        return

    print("\n🎮 Nintendo Store Agent (Type 'quit' to exit)")
    print("=" * 50)
    print("Exemplos de perguntas:")
    print(" - 'I want a game for a 5 year old'")
    print(" - 'Do you have Mario Kart?'")
    print(" - 'Recommend a game similar to Zelda'")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\nUser: ")
            if user_input.strip().lower() in ["quit", "exit", "q"]:
                print("Goodbye! 👋")
                break
            
            if not user_input.strip():
                continue

            response = agent.run(user_input)
            print(f"\nAgent: {response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
