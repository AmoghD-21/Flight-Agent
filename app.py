# import os
# import uuid
# import streamlit as st

# from chatbot_engine import initialize_chatbot
# from vector_store import add_new_pdf_to_vector_db
# from langchain_community.chat_message_histories import UpstashRedisChatMessageHistory


# # 1. Page Configuration
# st.set_page_config(
#     page_title="Air India Assistant - Maharaja AI",
#     page_icon="✈️",
#     layout="centered",
#     initial_sidebar_state="expanded"
# )


# # 2. Air India Dark Theme CSS Injection
# st.markdown("""
#     <style>
#         @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

#         html, body, [class*="css"] {
#             font-family: 'Poppins', sans-serif;
#         }

#         .stApp {
#             background: radial-gradient(circle at top left, #1B1D24 0%, #101114 55%, #0A0A0C 100%);
#             color: #E8E6E3;
#         }

#         #MainMenu {visibility: hidden;}
#         footer {visibility: hidden;}
#         header {background: transparent !important;}

#         .hero-container {
#             text-align: center;
#             padding: 30px 20px 24px 20px;
#             border-radius: 20px;
#             background: linear-gradient(135deg, #7A1418 0%, #D22630 55%, #A01C22 100%);
#             box-shadow: 0 12px 34px rgba(210, 38, 48, 0.35);
#             margin-bottom: 14px;
#         }

#         .hero-icon { font-size: 46px; margin-bottom: 4px; }

#         .brand-title {
#             color: #FFFFFF;
#             font-size: 40px;
#             font-weight: 700;
#             letter-spacing: 3px;
#         }

#         .brand-subtitle {
#             color: #F3D9A0;
#             font-size: 16px;
#             font-weight: 500;
#         }

#         div[data-testid="stChatMessage"] {
#             border-radius: 16px;
#             margin-bottom: 10px;
#         }

#         section[data-testid="stSidebar"] {
#             background: linear-gradient(180deg, #121317 0%, #0D0E11 100%);
#         }

#     </style>
# """, unsafe_allow_html=True)


# # 3. Sidebar - PDF Upload (RAG Knowledge Base)
# with st.sidebar:
#     st.markdown("### 🛠️ Admin Control Panel")

#     uploaded_file = st.file_uploader(
#         "Upload Air India PDF",
#         type=["pdf"]
#     )

#     if uploaded_file is not None:
#         st.markdown(f"📄 **{uploaded_file.name}** ready")

#         if st.button("🚀 Process & Ingest Document"):
#             with st.spinner("Processing document..."):

#                 os.makedirs("./data", exist_ok=True)
#                 save_path = os.path.join("./data", uploaded_file.name)

#                 with open(save_path, "wb") as f:
#                     f.write(uploaded_file.getbuffer())

#                 status = add_new_pdf_to_vector_db(save_path)

#                 st.success(status)

#                 st.cache_resource.clear()
#                 st.info("Vector DB updated!")


# # 4. Hero Header
# st.markdown("""
# <div class="hero-container">
#     <div class="hero-icon">✈️</div>
#     <h1 class="brand-title">AIR INDIA</h1>
#     <p class="brand-subtitle">MAHARAJA CORPORATE SUPPORT AI AGENT</p>
# </div>
# """, unsafe_allow_html=True)

# st.markdown(
#     "Ask about booking, refunds, baggage, schedules, and airline policies."
# )

# st.markdown("---")


# # 5. Initialize chatbot (cached)
# @st.cache_resource
# def load_bot():
#     return initialize_chatbot()

# bot_chain = load_bot()


# # 6. Persistent Chat Memory (UPSTASH REDIS + URL PERSISTENCE)
# # Check if a session ID already exists in the browser URL query params
# query_params = st.query_params

# if "session" in query_params:
#     session_id = query_params["session"]
#     st.session_state.user_session_id = session_id
# elif "user_session_id" in st.session_state:
#     session_id = st.session_state.user_session_id
# else:
#     # If it's a completely fresh visit, generate a brand new session ID
#     session_id = str(uuid.uuid4())
#     st.session_state.user_session_id = session_id
#     # Lock this session ID into the browser's URL query string parameters
#     st.query_params["session"] = session_id

# # Connect to Upstash Redis using the persistent session_id
# history_store = UpstashRedisChatMessageHistory(
#     url=os.getenv("UPSTASH_REDIS_REST_URL"),
#     token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
#     session_id=session_id,
#     ttl=86400  # 24 hours
# )


# # 7. Render chat history from Upstash
# for msg in history_store.messages:
#     role = "user" if msg.type == "human" else "assistant"
#     avatar = "🧑‍💼" if role == "user" else "✈️"

#     with st.chat_message(role, avatar=avatar):
#         st.markdown(msg.content)


# # 8. Chat input + RAG pipeline
# # if user_query := st.chat_input("How can I assist you with Air India policies today?"):

# #     with st.chat_message("user", avatar="🧑‍💼"):
# #         st.markdown(user_query)

# #     with st.chat_message("assistant", avatar="✈️"):
# #         with st.spinner("Retrieving verified Air India directives..."):
# #             try:

# #                 # Convert Redis history into RAG format
# #                 formatted_history = []
# #                 for msg in history_store.messages:
# #                     role_type = "human" if msg.type == "human" else "ai"
# #                     formatted_history.append((role_type, msg.content))

# #                 # Call RAG chain
# #                 response = bot_chain.invoke({
# #                     "input": user_query,
# #                     "chat_history": formatted_history
# #                 })

# #                 output_text = response["answer"]
# #                 st.markdown(output_text)

# #                 # Store in Upstash Redis
# #                 history_store.add_user_message(user_query)
# #                 history_store.add_ai_message(output_text)

# #             except Exception as e:
# #                 st.error(f"Execution Error: {e}")


# # 8. Chat input + RAG pipeline (Optimized for Real-Time Streaming)
# if user_query := st.chat_input("How can I assist you with Air India policies today?"):

#     with st.chat_message("user", avatar="🧑‍💼"):
#         st.markdown(user_query)

#     with st.chat_message("assistant", avatar="✈️"):
#         # 1. Create an empty container that we will fill word-by-word
#         response_placeholder = st.empty()
#         full_response = ""
        
#         try:
#             # Reconstruct history format from Upstash Redis
#             formatted_history = []
#             for msg in history_store.messages:
#                 role_type = "human" if msg.type == "human" else "ai"
#                 formatted_history.append((role_type, msg.content))

#             # 2. Swap out .invoke() for .stream()
#             stream_chunks = bot_chain.stream({
#                 "input": user_query,
#                 "chat_history": formatted_history
#             })

#             # 3. Iterate over the stream as chunks arrive live
#             for chunk in stream_chunks:
#                 # Filter out document tokens, grab only the text 'answer' tokens
#                 if "answer" in chunk:
#                     full_response += chunk["answer"]
#                     # Render the text string on the screen progressively
#                     response_placeholder.markdown(full_response + "▌")
            
#             # Remove the cursor block character once streaming finishes completely
#             response_placeholder.markdown(full_response)

#             # 4. Commit the complete built answers back to your Upstash cloud memory
#             history_store.add_user_message(user_query)
#             history_store.add_ai_message(full_response)

#         except Exception as e:
#             st.error(f"Streaming Execution Error: {e}")













import os
import html
import time
import uuid
from datetime import datetime
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

from chatbot_engine import initialize_chatbot
from vector_store import add_new_pdf_to_vector_db
from langchain_community.chat_message_histories import UpstashRedisChatMessageHistory

# 1. Page Configuration
st.set_page_config(
    page_title="Air India Assistant - Maharaja AI",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. Sidebar - PDF Upload (Keep standard Streamlit for admin utilities)
with st.sidebar:
    st.markdown("### 🛠️ Admin Control Panel")
    st.caption("Ingest new source documents into the RAG knowledge base.")
    uploaded_file = st.file_uploader("Upload Air India PDF", type=["pdf"])
    if uploaded_file is not None:
        st.markdown(f"📄 **{uploaded_file.name}** ready")
        if st.button("🚀 Process & Ingest Document", use_container_width=True):
            with st.spinner("Processing..."):
                os.makedirs("./data", exist_ok=True)
                save_path = os.path.join("./data", uploaded_file.name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                status = add_new_pdf_to_vector_db(save_path)
                st.success(status)
                st.cache_resource.clear()

# 3. Initialize chatbot (cached backend framework logic)
@st.cache_resource
def load_bot():
    return initialize_chatbot()

bot_chain = load_bot()

# 4. Persistent Chat Memory (UPSTASH REDIS + URL STATE BINDING)
query_params = st.query_params
if "session" in query_params:
    session_id = query_params["session"]
    st.session_state.user_session_id = session_id
elif "user_session_id" in st.session_state:
    session_id = st.session_state.user_session_id
else:
    session_id = str(uuid.uuid4())
    st.session_state.user_session_id = session_id
    st.query_params["session"] = session_id

history_store = UpstashRedisChatMessageHistory(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
    session_id=session_id,
    ttl=86400
)

# 4b. Timestamps live in session_state, index-aligned with history_store.messages.
#     Messages loaded from Redis before this session started get None (shown blank);
#     anything sent during this session gets a real clock time.
if "msg_times" not in st.session_state:
    st.session_state.msg_times = [None] * len(history_store.messages)
else:
    while len(st.session_state.msg_times) < len(history_store.messages):
        st.session_state.msg_times.append(None)

# 5. Global styling — Air India "Vista" brand palette.
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,300;0,400;0,500;0,600;0,700;1,700;1,800&display=swap');

        html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        .stApp { background: #FBF7F0 !important; }
        [data-testid="stHeader"] { background: transparent !important; }

        .block-container,
        [data-testid="stMainBlockContainer"] {
            max-width: 760px !important;
            margin: 0 auto !important;
            padding-top: 2rem !important;
            padding-bottom: 1rem !important;
        }

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #3D1428 0%, #2A0E1C 100%) !important;
        }
        section[data-testid="stSidebar"] * { color: #FBF7F0 !important; }
        [data-testid="stFileUploaderDropzone"] {
            background: rgba(251, 247, 240, 0.06) !important;
            border: 1px dashed #C9A15A !important;
            border-radius: 12px !important;
        }
        section[data-testid="stSidebar"] button {
            background: #D2262E !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 20px !important;
        }
        section[data-testid="stSidebar"] button:hover { background: #8E1015 !important; }
        section[data-testid="stSidebar"] .stAlert {
            background: rgba(251, 247, 240, 0.1) !important;
            border-radius: 10px !important;
        }

        /* ---------- Header ---------- */
        .hero-container {
            position: relative;
            text-align: center;
            padding: 28px 20px 24px;
            border-radius: 18px;
            background: linear-gradient(120deg, #3D1428 0%, #8E1015 55%, #D2262E 100%);
            box-shadow: 0 10px 30px rgba(61, 20, 40, 0.28);
            margin: 6px 0 20px 0;
            overflow: hidden;
        }
        .hero-container::before {
            content: ""; position: absolute; top: -60px; right: -40px;
            width: 160px; height: 160px; border-radius: 50%;
            border: 3px solid rgba(201, 161, 90, 0.35);
        }
        .hero-container::after {
            content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 4px;
            background: linear-gradient(90deg, transparent, #C9A15A, transparent);
        }
        .brand-mark { display: flex; align-items: center; justify-content: center; gap: 10px; }
        .brand-title {
            color: #FFFFFF; font-size: 28px; font-weight: 800; font-style: italic;
            margin: 0; letter-spacing: 1px; line-height: 1;
        }
        .brand-subtitle {
            color: #C9A15A; font-size: 12px; font-weight: 600; letter-spacing: 3px;
            text-transform: uppercase; margin: 10px 0 0 0; text-align: center;
        }

        /* ---------- Chat scroll panel ---------- */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div.chat-scroll-marker) {
            background: transparent !important;
            border: none !important;
        }

        /* ---------- Chat bubbles ---------- */
        .msg-row { display: flex; align-items: flex-end; gap: 8px; margin-bottom: 16px; }
        .msg-row.user { justify-content: flex-end; }
        .msg-row.assistant { justify-content: flex-start; }

        .avatar {
            flex: 0 0 auto; width: 30px; height: 30px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: 700; color: #FFFFFF;
        }
        .avatar.user { background: #3D1428; order: 2; }
        .avatar.assistant { background: #D2262E; }

        .bubble-col { display: flex; flex-direction: column; max-width: 74%; }
        .msg-row.user .bubble-col { align-items: flex-end; order: 1; }
        .msg-row.assistant .bubble-col { align-items: flex-start; }

        .sender-label {
            font-size: 10px; font-weight: 700; letter-spacing: 1px;
            text-transform: uppercase; margin-bottom: 4px; opacity: 0.6; color: #7A6A62;
        }

        .message-bubble {
            padding: 12px 16px; border-radius: 14px; line-height: 1.55;
            font-size: 0.94rem; word-wrap: break-word;
            box-shadow: 0 2px 8px rgba(61, 20, 40, 0.08);
        }
        .user-bubble { background: #3D1428; color: #FBF7F0; border-bottom-right-radius: 4px; }
        .msg-row.user .sender-label { color: #B76E45; }
        .assistant-bubble {
            background: #FFFFFF; color: #2A1E22; border: 1px solid #EAE0D2;
            border-left: 3px solid #D2262E; border-bottom-left-radius: 4px;
        }
        .msg-row.assistant .sender-label { color: #D2262E; }

        .msg-time { font-size: 9px; color: #A6968E; margin-top: 3px; }
        .msg-row.user .msg-time { text-align: right; }

        /* ---------- Typing indicator ---------- */
        .typing-bubble { display: flex; gap: 4px; align-items: center; padding: 14px 16px; }
        .typing-bubble .dot {
            width: 6px; height: 6px; border-radius: 50%; background: #D2262E;
            opacity: 0.4; animation: typingBounce 1.2s infinite ease-in-out;
        }
        .typing-bubble .dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-bubble .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typingBounce {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
            30% { transform: translateY(-4px); opacity: 1; }
        }
        .stream-cursor {
            display: inline-block; color: #D2262E; animation: blink 0.8s steps(1) infinite;
        }
        @keyframes blink { 50% { opacity: 0; } }

        /* ---------- Empty state ---------- */
        .empty-state-wrap { text-align: center; padding: 22px 10px 6px; }
        .empty-icon-badge {
            width: 54px; height: 54px; border-radius: 50%; margin: 0 auto 14px;
            background: linear-gradient(135deg, #3D1428, #D2262E);
            display: flex; align-items: center; justify-content: center;
            font-size: 22px; box-shadow: 0 6px 16px rgba(61, 20, 40, 0.25);
        }
        .empty-title { font-weight: 700; font-size: 15px; color: #3D1428; margin-bottom: 4px; }
        .empty-subtitle { font-size: 12.5px; color: #8A7A72; margin-bottom: 4px; }

        /* Quick-start chip buttons inside the main column */
        [data-testid="stMainBlockContainer"] .stButton button,
        .block-container .stButton button {
            background: #FFFFFF !important;
            border: 1px solid #C9A15A !important;
            color: #3D1428 !important;
            border-radius: 20px !important;
            font-weight: 600 !important;
            font-size: 0.85rem !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stMainBlockContainer"] .stButton button:hover,
        .block-container .stButton button:hover {
            background: #3D1428 !important;
            color: #FBF7F0 !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(61, 20, 40, 0.2);
        }

        /* ---------- Chat input: dark pill, white text (fixes contrast bug) ---------- */
        [data-testid="stBottom"],
        [data-testid="stBottomBlockContainer"] { background: #FBF7F0 !important; }
        [data-testid="stBottomBlockContainer"] {
            max-width: 760px !important; margin: 0 auto !important;
            padding: 0.75rem 1rem 1.25rem !important;
        }
        [data-testid="stChatInput"] {
            background: #3D1428 !important;
            border: 1px solid rgba(201, 161, 90, 0.45) !important;
            border-radius: 30px !important;
            box-shadow: 0 2px 10px rgba(61, 20, 40, 0.15) !important;
        }
        [data-testid="stChatInput"] textarea {
            font-family: 'Poppins', sans-serif !important;
            color: #FFFFFF !important;
            background: transparent !important;
            caret-color: #FFFFFF !important;
        }
        [data-testid="stChatInput"] textarea::placeholder { color: rgba(255, 255, 255, 0.55) !important; }
        [data-testid="stChatInput"] button {
            background: linear-gradient(120deg, #D2262E 0%, #8E1015 100%) !important;
            border-radius: 50% !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        }
        [data-testid="stChatInput"] button:hover {
            transform: scale(1.12) rotate(8deg) !important;
            box-shadow: 0 0 0 4px rgba(201, 161, 90, 0.3) !important;
        }
        [data-testid="stChatInput"] button:active { transform: scale(0.9) !important; }
        [data-testid="stChatInput"] button svg { fill: #FFFFFF !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_message_row(role: str, content: str, timestamp: Optional[str] = None, streaming: bool = False) -> str:
    label = "Passenger" if role == "user" else "Maharaja AI"
    initials = "P" if role == "user" else "AI"
    bubble_class = "user-bubble" if role == "user" else "assistant-bubble"
    safe_content = html.escape(content).replace("\n", "<br>")
    cursor = '<span class="stream-cursor">▍</span>' if streaming else ""
    time_html = f'<div class="msg-time">{timestamp}</div>' if timestamp else ""
    return f"""
    <div class="msg-row {role}">
        <div class="avatar {role}">{initials}</div>
        <div class="bubble-col">
            <div class="sender-label">{label}</div>
            <div class="message-bubble {bubble_class}">{safe_content}{cursor}</div>
            {time_html}
        </div>
    </div>
    """


def render_typing_indicator() -> str:
    return """
    <div class="msg-row assistant">
        <div class="avatar assistant">AI</div>
        <div class="bubble-col">
            <div class="sender-label">Maharaja AI</div>
            <div class="message-bubble assistant-bubble typing-bubble">
                <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            </div>
        </div>
    </div>
    """


def trigger_autoscroll():
    components.html(
        """
        <script>
        (function() {
            function scrollToBottom() {
                const doc = window.parent.document;
                const markers = doc.querySelectorAll('.chat-scroll-marker');
                if (markers.length === 0) return;
                const marker = markers[markers.length - 1];
                const node = marker.closest('[data-testid="stVerticalBlockBorderWrapper"]');
                if (node) { node.scrollTop = node.scrollHeight; }
            }
            scrollToBottom();
            setTimeout(scrollToBottom, 60);
            setTimeout(scrollToBottom, 250);
        })();
        </script>
        """,
        height=0,
    )


# 6. Header
st.markdown(
    """
    <div class="hero-container">
        <div class="brand-mark">
            <svg width="26" height="26" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M50 8 L86 78 L14 78 Z" stroke="#C9A15A" stroke-width="6" stroke-linejoin="round"/>
            </svg>
            <h1 class="brand-title">AIR INDIA</h1>
        </div>
        <p class="brand-subtitle">Maharaja AI &middot; Corporate Support</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# 7. Capture input FIRST. st.chat_input always floats at the bottom of the
#    page regardless of where it's called, so we can read its value before
#    laying out the chat panel and use it to update history immediately.
quick_query = st.session_state.pop("trigger_query", None)
typed_query = st.chat_input("Type an Air India policy query...")
user_query = quick_query or typed_query

if user_query:
    history_store.add_user_message(user_query)
    st.session_state.msg_times.append(datetime.now().strftime("%I:%M %p"))

# 8. Chat panel
panel_height = 440 if history_store.messages else 260
chat_panel = st.container(height=panel_height, border=False)
with chat_panel:
    st.markdown('<div class="chat-scroll-marker"></div>', unsafe_allow_html=True)

    if history_store.messages:
        rows_html = []
        for i, msg in enumerate(history_store.messages):
            role = "user" if msg.type == "human" else "assistant"
            ts = st.session_state.msg_times[i] if i < len(st.session_state.msg_times) else None
            rows_html.append(render_message_row(role, msg.content, timestamp=ts))
        st.markdown("".join(rows_html), unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <div class="empty-state-wrap">
                <div class="empty-icon-badge">✈️</div>
                <div class="empty-title">Welcome aboard, Maharaja AI</div>
                <div class="empty-subtitle">Ask about policies, baggage, bookings, or corporate travel —<br>or try one of these:</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        suggestions = ["🧳 Baggage allowance", "🎫 Book a flight", "💺 Seat selection", "↩️ Refund policy"]
        cols = st.columns(2)
        for idx, suggestion in enumerate(suggestions):
            with cols[idx % 2]:
                if st.button(suggestion, key=f"chip_{idx}", use_container_width=True):
                    st.session_state.trigger_query = suggestion.split(" ", 1)[1]
                    st.rerun()

    # 9. If a query just came in, show a typing indicator, call the RAG
    #    chain, then reveal the answer word-by-word for a streaming feel.
    if user_query:
        typing_placeholder = st.empty()
        typing_placeholder.markdown(render_typing_indicator(), unsafe_allow_html=True)
        trigger_autoscroll()

        try:
            formatted_history = []
            for msg in history_store.messages[:-1]:  # exclude the query we just added
                role_type = "human" if msg.type == "human" else "ai"
                formatted_history.append((role_type, msg.content))

            response = bot_chain.invoke({
                "input": user_query,
                "chat_history": formatted_history
            })
            output_text = response["answer"]
        except Exception as e:
            typing_placeholder.empty()
            st.error(f"Execution Error: {e}")
            output_text = None

        if output_text:
            words = output_text.split(" ")
            streamed = ""
            chunk = []
            for word in words:
                chunk.append(word)
                if len(chunk) >= 3:
                    streamed += " ".join(chunk) + " "
                    typing_placeholder.markdown(
                        render_message_row("assistant", streamed.strip(), streaming=True),
                        unsafe_allow_html=True,
                    )
                    chunk = []
                    time.sleep(0.04)
            if chunk:
                streamed += " ".join(chunk)
                typing_placeholder.markdown(
                    render_message_row("assistant", streamed.strip(), streaming=True),
                    unsafe_allow_html=True,
                )
                time.sleep(0.04)

            reply_time = datetime.now().strftime("%I:%M %p")
            typing_placeholder.markdown(
                render_message_row("assistant", output_text, timestamp=reply_time),
                unsafe_allow_html=True,
            )

            history_store.add_ai_message(output_text)
            st.session_state.msg_times.append(reply_time)

    trigger_autoscroll()