import streamlit as st
from chatbot_engine import initialize_chatbot

# 1. Set up the browser tab title and layout
st.set_page_config(page_title="Air India Support - Maharaja AI", page_icon="✈️", layout="centered")

st.title("✈️ Air India Corporate Support")
st.subheader("Maharaja AI Agent (RAG Powered)")
st.write("Ask anything about booking policies, name changes, surcharges, or GDS violations.")
st.markdown("---")

# 2. Initialize the RAG chatbot and cache it so it doesn't reload on every single click
@st.cache_resource
def load_bot():
    return initialize_chatbot()

try:
    bot_chain = load_bot()
except Exception as e:
    st.error(f"Failed to initialize chatbot. Is your GITHUB_TOKEN set correctly? Error: {e}")
    st.stop()

# 3. Setup Session State for keeping track of chat history in the UI
if "messages" not in st.session_state:
    st.session_state.messages = []
if "langchain_history" not in st.session_state:
    st.session_state.langchain_history = []

# 4. Display all previous messages on the screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Handle New User Input
if user_query := st.chat_input("Type your policy or scheduling question here..."):
    
    # Display human message immediately
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    # Generate AI response with a neat loading spinner
    with st.chat_message("assistant"):
        with st.spinner("Searching Air India knowledge base..."):
            try:
                # Invoke our RAG chain
                response = bot_chain.invoke({
                    "input": user_query,
                    "chat_history": st.session_state.langchain_history
                })
                
                output_text = response["answer"]
                st.markdown(output_text)
                
                # Append to UI history
                st.session_state.messages.append({"role": "assistant", "content": output_text})
                
                # Append to LangChain conversational memory format
                st.session_state.langchain_history.extend([
                    ("human", user_query),
                    ("ai", output_text)
                ])
            except Exception as e:
                st.error(f"An error occurred while getting response: {e}")