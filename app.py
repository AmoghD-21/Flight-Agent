import os
import uuid
import streamlit as st

from chatbot_engine import initialize_chatbot
from vector_store import add_new_pdf_to_vector_db
from langchain_community.chat_message_histories import UpstashRedisChatMessageHistory


# 1. Page Configuration
st.set_page_config(
    page_title="Air India Assistant - Maharaja AI",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="expanded"
)


# 2. Air India Dark Theme CSS Injection
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
        }

        .stApp {
            background: radial-gradient(circle at top left, #1B1D24 0%, #101114 55%, #0A0A0C 100%);
            color: #E8E6E3;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {background: transparent !important;}

        .hero-container {
            text-align: center;
            padding: 30px 20px 24px 20px;
            border-radius: 20px;
            background: linear-gradient(135deg, #7A1418 0%, #D22630 55%, #A01C22 100%);
            box-shadow: 0 12px 34px rgba(210, 38, 48, 0.35);
            margin-bottom: 14px;
        }

        .hero-icon { font-size: 46px; margin-bottom: 4px; }

        .brand-title {
            color: #FFFFFF;
            font-size: 40px;
            font-weight: 700;
            letter-spacing: 3px;
        }

        .brand-subtitle {
            color: #F3D9A0;
            font-size: 16px;
            font-weight: 500;
        }

        div[data-testid="stChatMessage"] {
            border-radius: 16px;
            margin-bottom: 10px;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #121317 0%, #0D0E11 100%);
        }

    </style>
""", unsafe_allow_html=True)


# 3. Sidebar - PDF Upload (RAG Knowledge Base)
with st.sidebar:
    st.markdown("### 🛠️ Admin Control Panel")

    uploaded_file = st.file_uploader(
        "Upload Air India PDF",
        type=["pdf"]
    )

    if uploaded_file is not None:
        st.markdown(f"📄 **{uploaded_file.name}** ready")

        if st.button("🚀 Process & Ingest Document"):
            with st.spinner("Processing document..."):

                os.makedirs("./data", exist_ok=True)
                save_path = os.path.join("./data", uploaded_file.name)

                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                status = add_new_pdf_to_vector_db(save_path)

                st.success(status)

                st.cache_resource.clear()
                st.info("Vector DB updated!")


# 4. Hero Header
st.markdown("""
<div class="hero-container">
    <div class="hero-icon">✈️</div>
    <h1 class="brand-title">AIR INDIA</h1>
    <p class="brand-subtitle">MAHARAJA CORPORATE SUPPORT AI AGENT</p>
</div>
""", unsafe_allow_html=True)

st.markdown(
    "Ask about booking, refunds, baggage, schedules, and airline policies."
)

st.markdown("---")


# 5. Initialize chatbot (cached)
@st.cache_resource
def load_bot():
    return initialize_chatbot()

bot_chain = load_bot()


# 6. Persistent Chat Memory (UPSTASH REDIS + URL PERSISTENCE)
# Check if a session ID already exists in the browser URL query params
query_params = st.query_params

if "session" in query_params:
    session_id = query_params["session"]
    st.session_state.user_session_id = session_id
elif "user_session_id" in st.session_state:
    session_id = st.session_state.user_session_id
else:
    # If it's a completely fresh visit, generate a brand new session ID
    session_id = str(uuid.uuid4())
    st.session_state.user_session_id = session_id
    # Lock this session ID into the browser's URL query string parameters
    st.query_params["session"] = session_id

# Connect to Upstash Redis using the persistent session_id
history_store = UpstashRedisChatMessageHistory(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
    session_id=session_id,
    ttl=86400  # 24 hours
)


# 7. Render chat history from Upstash
for msg in history_store.messages:
    role = "user" if msg.type == "human" else "assistant"
    avatar = "🧑‍💼" if role == "user" else "✈️"

    with st.chat_message(role, avatar=avatar):
        st.markdown(msg.content)


# 8. Chat input + RAG pipeline
if user_query := st.chat_input("How can I assist you with Air India policies today?"):

    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(user_query)

    with st.chat_message("assistant", avatar="✈️"):
        with st.spinner("Retrieving verified Air India directives..."):
            try:

                # Convert Redis history into RAG format
                formatted_history = []
                for msg in history_store.messages:
                    role_type = "human" if msg.type == "human" else "ai"
                    formatted_history.append((role_type, msg.content))

                # Call RAG chain
                response = bot_chain.invoke({
                    "input": user_query,
                    "chat_history": formatted_history
                })

                output_text = response["answer"]
                st.markdown(output_text)

                # Store in Upstash Redis
                history_store.add_user_message(user_query)
                history_store.add_ai_message(output_text)

            except Exception as e:
                st.error(f"Execution Error: {e}")