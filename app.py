
import os
import streamlit as st
from chatbot_engine import initialize_chatbot
from vector_store import add_new_pdf_to_vector_db

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

        /* ---------- App background ---------- */
        .stApp {
            background: radial-gradient(circle at top left, #1B1D24 0%, #101114 55%, #0A0A0C 100%);
            color: #E8E6E3;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {background: transparent !important;}

        /* ---------- Hero header ---------- */
        .hero-container {
            text-align: center;
            padding: 30px 20px 24px 20px;
            border-radius: 20px;
            background: linear-gradient(135deg, #7A1418 0%, #D22630 55%, #A01C22 100%);
            box-shadow: 0 12px 34px rgba(210, 38, 48, 0.35);
            margin-bottom: 14px;
            border: 1px solid rgba(255,255,255,0.06);
        }

        .hero-icon { font-size: 46px; margin-bottom: 4px; }

        .brand-title {
            color: #FFFFFF;
            font-size: 40px;
            font-weight: 700;
            letter-spacing: 3px;
            margin: 0;
            text-shadow: 0 2px 10px rgba(0,0,0,0.35);
        }

        .brand-subtitle {
            color: #F3D9A0;
            font-size: 16px;
            font-weight: 500;
            letter-spacing: 1px;
            margin-top: 4px;
        }

        .hero-divider {
            width: 70px;
            height: 3px;
            background: #E8C978;
            margin: 12px auto 0 auto;
            border-radius: 3px;
        }

        .tagline-box {
            text-align: center;
            color: #A9A6A1;
            font-size: 15px;
            padding: 14px 10px 6px 10px;
            line-height: 1.5;
        }

        /* ---------- Chat bubbles ---------- */
        div[data-testid="stChatMessage"] {
            border-radius: 16px;
            padding: 6px 8px;
            margin-bottom: 10px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.35);
            border: 1px solid rgba(255,255,255,0.06);
        }

        div[data-testid="stChatMessageContent"] {
            font-size: 15.5px;
            line-height: 1.55;
            color: #EDEBE8;
        }

        /* User bubble */
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
            background: linear-gradient(135deg, #2A1416 0%, #34181A 100%);
            border-left: 4px solid #D22630;
        }

        /* Assistant bubble */
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
            background: linear-gradient(135deg, #1C1B16 0%, #211E17 100%);
            border-left: 4px solid #BBA156;
        }

        /* ---------- Chat input ---------- */
        [data-testid="stChatInput"] {
            background-color: #17181C !important;
            border-radius: 14px;
            border: 1.5px solid #3A2C2C;
        }

        [data-testid="stChatInput"] textarea {
            color: #EDEBE8 !important;
        }

        [data-testid="stChatInput"]:focus-within {
            border: 1.5px solid #D22630;
            box-shadow: 0 0 0 3px rgba(210,38,48,0.20);
        }

        /* ---------- Buttons ---------- */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #D22630 0%, #A01C22 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 8px 18px;
            font-weight: 600;
            letter-spacing: 0.4px;
            box-shadow: 0 4px 14px rgba(210,38,48,0.35);
            transition: all 0.2s ease-in-out;
        }

        div.stButton > button:first-child:hover {
            background: linear-gradient(135deg, #A01C22 0%, #7A1418 100%);
            color: white;
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(210,38,48,0.45);
        }

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #121317 0%, #0D0E11 100%);
            border-right: 1px solid #26221D;
        }

        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h2 {
            color: #E8C978;
            font-weight: 700;
        }

        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] span {
            color: #B7B4AF !important;
        }

        .sidebar-caption {
            color: #7C7975;
            font-size: 13px;
            margin-top: -8px;
            margin-bottom: 14px;
        }

        /* File uploader */
        [data-testid="stFileUploaderDropzone"] {
            border: 1.5px dashed #BBA156;
            border-radius: 12px;
            background: #17161233;
        }

        [data-testid="stFileUploaderDropzone"] * {
            color: #C9C6C1 !important;
        }

        /* Success / info / error boxes */
        div[data-testid="stAlert"] {
            border-radius: 12px;
            background-color: #17181C;
            border: 1px solid #2A2B2F;
            color: #E8E6E3;
        }

        /* Divider styling */
        hr { border-color: #26262A !important; }

        /* Spinner text */
        .stSpinner > div { color: #E8C978 !important; }

        /* Empty state */
        .empty-state {
            text-align: center;
            color: #6D6A66;
            padding: 30px 10px;
            font-size: 14.5px;
        }

    </style>
""", unsafe_allow_html=True)

# 3. Dynamic Knowledge Base Pipeline: Admin Sidebar
with st.sidebar:
    st.markdown("### 🛠️ Admin Control Panel")
    st.markdown(
        "<p class='sidebar-caption'>Manage the Maharaja AI knowledge base</p>",
        unsafe_allow_html=True
    )
    st.write("Upload new Air India PDFs dynamically to update the knowledge base.")

    uploaded_file = st.file_uploader("Choose an Air India PDF document", type=["pdf"])

    if uploaded_file is not None:
        st.markdown(f"📄 **{uploaded_file.name}** ready to upload")

        if st.button("🚀 Process & Ingest Document", use_container_width=True):
            with st.spinner("Parsing layout, extracting tables, and generating embeddings..."):
                # Ensure data directory exists
                os.makedirs("./data", exist_ok=True)
                save_path = os.path.join("./data", uploaded_file.name)

                # Save the uploaded file temporarily to disk
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Process the file dynamically
                status_msg = add_new_pdf_to_vector_db(save_path)
                st.success(status_msg)

                # Clear the cache so the chatbot reloads the newly updated vector store
                st.cache_resource.clear()
                st.info("🔄 Vector database re-indexed. The chatbot is ready with fresh context!")

    st.markdown("---")
    st.markdown(
        "<p class='sidebar-caption'>✈️ Maharaja AI · Powered by RAG</p>",
        unsafe_allow_html=True
    )

# 4. Air India Header Section
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-icon">✈️</div>
        <h1 class="brand-title">AIR INDIA</h1>
        <p class="brand-subtitle">MAHARAJA CORPORATE SUPPORT AI AGENT</p>
        <div class="hero-divider"></div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="tagline-box">
        Ask anything about booking policies, schedules, refunds, baggage, or airline procedures.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# 5. Initialize and Cache the RAG Engine
@st.cache_resource
def load_bot():
    return initialize_chatbot()

try:
    bot_chain = load_bot()
except Exception as e:
    st.error(f"Failed to initialize chatbot. Error: {e}")
    st.stop()

# 6. Handle Session States
if "messages" not in st.session_state:
    st.session_state.messages = []
if "langchain_history" not in st.session_state:
    st.session_state.langchain_history = []

# 7. Render Historic Messages
if not st.session_state.messages:
    st.markdown(
        """
        <div class="empty-state">
            💬 Start the conversation — ask about baggage allowance, refunds, flight schedules, and more.
        </div>
        """,
        unsafe_allow_html=True
    )

for message in st.session_state.messages:
    avatar = "🧑‍💼" if message["role"] == "user" else "✈️"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 8. Operational Loop for Chat Input
if user_query := st.chat_input("How can I assist you with Air India policies today?"):

    # Render user prompt
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    # Render Assistant generation
    with st.chat_message("assistant", avatar="✈️"):
        with st.spinner("Retrieving verified Air India directives..."):
            try:
                response = bot_chain.invoke({
                    "input": user_query,
                    "chat_history": st.session_state.langchain_history
                })

                output_text = response["answer"]
                st.markdown(output_text)

                # Commit to persistence histories
                st.session_state.messages.append({"role": "assistant", "content": output_text})
                st.session_state.langchain_history.extend([
                    ("human", user_query),
                    ("ai", output_text)
                ])
            except Exception as e:
                st.error(f"Execution Error: {e}")