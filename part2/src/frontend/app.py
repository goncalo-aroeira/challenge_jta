import sys
import os
import streamlit as st
from dotenv import load_dotenv

# --- Setup Path ---
# Add part2 root to path so we can import src
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up 2 levels: src/frontend -> src -> part2
part2_root = os.path.abspath(os.path.join(current_dir, "../.."))
if part2_root not in sys.path:
    sys.path.append(part2_root)

from src.agent.core import Agent

# --- Config ---
st.set_page_config(
    page_title="Nintendo Store Agent",
    page_icon="🎮",
    layout="centered"
)

load_dotenv()

# --- Initialize Agent ---
@st.cache_resource
def get_agent():
    return Agent()

try:
    agent = get_agent()
except Exception as e:
    st.error(f"Error initializing agent: {e}")
    st.stop()

# --- UI ---
st.title("🎮 Nintendo Store Assistant")
st.markdown("Welcome! I can help you find games, consoles, and accessories for Nintendo Switch.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! How can I help you today?"}
    ]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about games..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = agent.run(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"An error occurred: {e}")
