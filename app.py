import os
import html
import json
import time
import uuid
from datetime import datetime
from typing import Optional, List, Tuple

import streamlit as st
import streamlit.components.v1 as components

from chatbot_engine import initialize_chatbot
from vector_store import add_new_pdf_to_vector_db
from langchain_community.chat_message_histories import UpstashRedisChatMessageHistory

# ══════════════════════════════════════════════════════════════════════════
# 1. PAGE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Air India Assistant - Maharaja AI",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════
# 2. THEME SYSTEM (light / dark) — palette stays on-brand in both modes
# ══════════════════════════════════════════════════════════════════════════
if "theme" not in st.session_state:
    st.session_state.theme = "light"

LIGHT = {
    "bg": "#FBF7F0",
    "surface": "#FFFFFF",
    "surface_alt": "#F3ECE0",
    "border": "#EAE0D2",
    "text": "#2A1E22",
    "text_muted": "#8A7A72",
    "text_soft": "#A6968E",
    "input_track": "#3D1428",
}
DARK = {
    "bg": "#150C12",
    "surface": "#241722",
    "surface_alt": "#2C1B27",
    "border": "#3B2531",
    "text": "#F5EDE7",
    "text_muted": "#C9B7B0",
    "text_soft": "#9A8A83",
    "input_track": "#1C0E17",
}
T = DARK if st.session_state.theme == "dark" else LIGHT

# Fixed brand accents — identical in both themes
MAROON = "#3D1428"
MAROON_DEEP = "#2A0E1C"
RED = "#D2262E"
RED_DEEP = "#8E1015"
GOLD = "#C9A15A"

# ══════════════════════════════════════════════════════════════════════════
# 3. SESSION + PERSISTENT CHAT MEMORY (Upstash Redis, bound to URL state)
# ══════════════════════════════════════════════════════════════════════════
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
    ttl=86400,
)

# Timestamps live in session_state, index-aligned with history_store.messages.
if "msg_times" not in st.session_state:
    st.session_state.msg_times = [None] * len(history_store.messages)
else:
    while len(st.session_state.msg_times) < len(history_store.messages):
        st.session_state.msg_times.append(None)


@st.cache_resource
def load_bot():
    return initialize_chatbot()


bot_chain = load_bot()

# ══════════════════════════════════════════════════════════════════════════
# 4. GLOBAL CSS — organized into clearly commented sections
# ══════════════════════════════════════════════════════════════════════════
st.markdown(
    f"""
    <style>
        /* ---------- Font import ---------- */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,300;0,400;0,500;0,600;0,700;1,700;1,800&display=swap');

        :root {{
            --bg: {T['bg']};
            --surface: {T['surface']};
            --surface-alt: {T['surface_alt']};
            --border: {T['border']};
            --text: {T['text']};
            --text-muted: {T['text_muted']};
            --text-soft: {T['text_soft']};
            --input-track: {T['input_track']};
            --maroon: {MAROON};
            --maroon-deep: {MAROON_DEEP};
            --red: {RED};
            --red-deep: {RED_DEEP};
            --gold: {GOLD};
        }}

        /* ---------- Base / reset ---------- */
        html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}

        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        .stApp {{ background: var(--bg) !important; transition: background 0.3s ease; }}
        [data-testid="stHeader"] {{ background: transparent !important; }}

        .block-container,
        [data-testid="stMainBlockContainer"] {{
            max-width: 780px !important;
            margin: 0 auto !important;
            padding-top: 1.25rem !important;
            padding-bottom: 1rem !important;
        }}

        ::selection {{ background: var(--gold); color: var(--maroon-deep); }}

        /* smooth page scrolling */
        html {{ scroll-behavior: smooth; }}

        /* ---------- Animations ---------- */
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        @keyframes slideUp {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        @keyframes scaleIn {{ from {{ opacity: 0; transform: scale(0.94); }} to {{ opacity: 1; transform: scale(1); }} }}
        @keyframes typingBounce {{
            0%, 60%, 100% {{ transform: translateY(0); opacity: 0.4; }}
            30% {{ transform: translateY(-4px); opacity: 1; }}
        }}
        @keyframes blink {{ 50% {{ opacity: 0; }} }}
        @keyframes ripple {{
            from {{ transform: scale(0); opacity: 0.45; }}
            to {{ transform: scale(2.2); opacity: 0; }}
        }}
        @keyframes glowPulse {{
            0%, 100% {{ box-shadow: 0 0 0 0 rgba(201, 161, 90, 0.35); }}
            50% {{ box-shadow: 0 0 0 6px rgba(201, 161, 90, 0); }}
        }}

        .msg-row {{ animation: slideUp 0.35s ease both; }}

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, var(--maroon) 0%, var(--maroon-deep) 100%) !important;
        }}
        section[data-testid="stSidebar"] * {{ color: #FBF7F0 !important; }}

        .side-heading {{
            font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
            color: var(--gold) !important; margin: 18px 0 8px 2px;
        }}
        .side-card {{
            background: rgba(251, 247, 240, 0.06);
            border: 1px solid rgba(201, 161, 90, 0.25);
            border-radius: 14px;
            padding: 14px 14px 12px;
            margin-bottom: 10px;
            animation: fadeIn 0.4s ease both;
        }}
        .side-status-dot {{
            display: inline-block; width: 8px; height: 8px; border-radius: 50%;
            background: #5FD675; margin-right: 6px; box-shadow: 0 0 6px #5FD675;
        }}

        [data-testid="stFileUploaderDropzone"] {{
            background: rgba(251, 247, 240, 0.06) !important;
            border: 1.5px dashed var(--gold) !important;
            border-radius: 12px !important;
            transition: all 0.2s ease !important;
        }}
        [data-testid="stFileUploaderDropzone"]:hover {{
            background: rgba(201, 161, 90, 0.12) !important;
            transform: translateY(-1px);
        }}

        section[data-testid="stSidebar"] button {{
            background: linear-gradient(120deg, var(--red) 0%, var(--red-deep) 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 20px !important;
            font-weight: 600 !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease !important;
            position: relative;
            overflow: hidden;
        }}
        section[data-testid="stSidebar"] button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(0,0,0,0.28) !important;
        }}
        section[data-testid="stSidebar"] button:active {{ transform: translateY(0) scale(0.97); }}

        section[data-testid="stSidebar"] .stAlert {{
            background: rgba(251, 247, 240, 0.1) !important;
            border-radius: 10px !important;
        }}

        .theme-row {{ display: flex; align-items: center; justify-content: space-between; }}

        /* ---------- Header / hero ---------- */
        .hero-container {{
            position: sticky; top: 0; z-index: 999;
            position: relative;
            text-align: center;
            padding: 30px 20px 26px;
            border-radius: 20px;
            background: linear-gradient(120deg, var(--maroon) 0%, var(--red-deep) 55%, var(--red) 100%);
            box-shadow: 0 12px 34px rgba(61, 20, 40, 0.30);
            margin: 4px 0 18px 0;
            overflow: hidden;
            animation: scaleIn 0.4s ease both;
        }}
        .hero-container::before {{
            content: ""; position: absolute; top: -60px; right: -40px;
            width: 170px; height: 170px; border-radius: 50%;
            border: 3px solid rgba(201, 161, 90, 0.35);
        }}
        .hero-container::after {{
            content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 4px;
            background: linear-gradient(90deg, transparent, var(--gold), transparent);
        }}
        .brand-mark {{ display: flex; align-items: center; justify-content: center; gap: 10px; }}
        .brand-title {{
            color: #FFFFFF; font-size: 29px; font-weight: 800; font-style: italic;
            margin: 0; letter-spacing: 1px; line-height: 1;
        }}
        .brand-subtitle {{
            color: var(--gold); font-size: 12px; font-weight: 600; letter-spacing: 3px;
            text-transform: uppercase; margin: 11px 0 0 0; text-align: center;
        }}
        .brand-tagline {{
            color: rgba(251,247,240,0.75); font-size: 11.5px; margin-top: 6px; font-weight: 400;
        }}

        /* ---------- Chat scroll panel ---------- */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div.chat-scroll-marker) {{
            background: transparent !important;
            border: none !important;
        }}

        /* ---------- Message bubbles ---------- */
        .msg-row {{ display: flex; align-items: flex-end; gap: 8px; margin-bottom: 16px; }}
        .msg-row.user {{ justify-content: flex-end; }}
        .msg-row.assistant {{ justify-content: flex-start; }}

        .avatar {{
            flex: 0 0 auto; width: 30px; height: 30px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: 700; color: #FFFFFF;
            box-shadow: 0 2px 6px rgba(0,0,0,0.18);
        }}
        .avatar.user {{ background: var(--maroon); order: 2; }}
        .avatar.assistant {{ background: linear-gradient(135deg, var(--red), var(--red-deep)); }}

        .bubble-col {{ display: flex; flex-direction: column; max-width: 72%; }}
        .msg-row.user .bubble-col {{ align-items: flex-end; order: 1; }}
        .msg-row.assistant .bubble-col {{ align-items: flex-start; }}

        .sender-label {{
            font-size: 10px; font-weight: 700; letter-spacing: 1px;
            text-transform: uppercase; margin-bottom: 4px; opacity: 0.65; color: var(--text-muted);
        }}

        .message-bubble {{
            padding: 12px 16px; border-radius: 14px; line-height: 1.55;
            font-size: 0.94rem; word-wrap: break-word;
            box-shadow: 0 2px 10px rgba(61, 20, 40, 0.10);
        }}
        .user-bubble {{ background: var(--maroon); color: #FBF7F0; border-bottom-right-radius: 4px; }}
        .msg-row.user .sender-label {{ color: #B76E45; }}
        .assistant-bubble {{
            background: var(--surface); color: var(--text); border: 1px solid var(--border);
            border-left: 3px solid var(--red); border-bottom-left-radius: 4px;
        }}
        .msg-row.assistant .sender-label {{ color: var(--red); }}

        .msg-footer {{ display: flex; align-items: center; gap: 8px; margin-top: 4px; }}
        .msg-time {{ font-size: 9px; color: var(--text-soft); }}
        .msg-row.user .msg-footer {{ justify-content: flex-end; }}

        .copy-btn {{
            font-size: 9px; color: var(--text-soft); cursor: pointer; border: none; background: none;
            padding: 0; font-family: 'Poppins', sans-serif; font-weight: 600;
            transition: color 0.15s ease; letter-spacing: 0.3px;
        }}
        .copy-btn:hover {{ color: var(--red); }}

        /* ---------- Typing indicator ---------- */
        .typing-bubble {{ display: flex; gap: 4px; align-items: center; padding: 14px 16px; }}
        .typing-bubble .dot {{
            width: 6px; height: 6px; border-radius: 50%; background: var(--red);
            opacity: 0.4; animation: typingBounce 1.2s infinite ease-in-out;
        }}
        .typing-bubble .dot:nth-child(2) {{ animation-delay: 0.2s; }}
        .typing-bubble .dot:nth-child(3) {{ animation-delay: 0.4s; }}
        .stream-cursor {{
            display: inline-block; color: var(--red); animation: blink 0.8s steps(1) infinite;
        }}

        /* ---------- Empty state ---------- */
        .empty-state-wrap {{ text-align: center; padding: 24px 10px 6px; animation: fadeIn 0.5s ease both; }}
        .empty-icon-badge {{
            width: 58px; height: 58px; border-radius: 50%; margin: 0 auto 14px;
            background: linear-gradient(135deg, var(--maroon), var(--red));
            display: flex; align-items: center; justify-content: center;
            font-size: 24px; box-shadow: 0 8px 20px rgba(61, 20, 40, 0.28);
            animation: glowPulse 2.4s infinite ease-in-out;
        }}
        .empty-title {{ font-weight: 700; font-size: 16px; color: var(--text); margin-bottom: 5px; }}
        .empty-subtitle {{ font-size: 12.5px; color: var(--text-muted); margin-bottom: 6px; line-height: 1.6; }}

        /* Quick-start chip buttons */
        [data-testid="stMainBlockContainer"] .stButton button,
        .block-container .stButton button {{
            background: var(--surface) !important;
            border: 1px solid var(--gold) !important;
            color: var(--maroon) !important;
            border-radius: 20px !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
            transition: all 0.2s ease !important;
            position: relative;
            overflow: hidden;
        }}
        [data-testid="stMainBlockContainer"] .stButton button:hover,
        .block-container .stButton button:hover {{
            background: var(--maroon) !important;
            color: #FBF7F0 !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(61, 20, 40, 0.22);
        }}
        [data-testid="stMainBlockContainer"] .stButton button:active {{ transform: translateY(0) scale(0.97); }}

        /* Toolbar buttons (clear / new / regenerate) */
        .toolbar-row .stButton button {{
            font-size: 0.78rem !important;
            border-radius: 18px !important;
            background: var(--surface-alt) !important;
            border: 1px solid var(--border) !important;
            color: var(--text) !important;
        }}
        .toolbar-row .stButton button:hover {{
            border-color: var(--red) !important;
            color: var(--red) !important;
            background: var(--surface) !important;
        }}

        /* ---------- Chat input ---------- */
        [data-testid="stBottom"],
        [data-testid="stBottomBlockContainer"] {{ background: var(--bg) !important; }}
        [data-testid="stBottomBlockContainer"] {{
            max-width: 780px !important; margin: 0 auto !important;
            padding: 0.75rem 1rem 1.25rem !important;
        }}
        [data-testid="stChatInput"] {{
            background: var(--input-track) !important;
            border: 1px solid rgba(201, 161, 90, 0.45) !important;
            border-radius: 30px !important;
            box-shadow: 0 2px 12px rgba(61, 20, 40, 0.18) !important;
            transition: box-shadow 0.2s ease, border-color 0.2s ease !important;
        }}
        [data-testid="stChatInput"]:focus-within {{
            border-color: var(--gold) !important;
            box-shadow: 0 0 0 4px rgba(201, 161, 90, 0.22) !important;
        }}
        [data-testid="stChatInput"] textarea {{
            font-family: 'Poppins', sans-serif !important;
            color: #FFFFFF !important;
            background: transparent !important;
            caret-color: #FFFFFF !important;
        }}
        [data-testid="stChatInput"] textarea::placeholder {{ color: rgba(255, 255, 255, 0.55) !important; }}
        [data-testid="stChatInput"] button {{
            background: linear-gradient(120deg, var(--red) 0%, var(--red-deep) 100%) !important;
            border-radius: 50% !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        }}
        [data-testid="stChatInput"] button:hover {{
            transform: scale(1.12) rotate(8deg) !important;
            box-shadow: 0 0 0 4px rgba(201, 161, 90, 0.3) !important;
        }}
        [data-testid="stChatInput"] button:active {{ transform: scale(0.9) !important; }}
        [data-testid="stChatInput"] button svg {{ fill: #FFFFFF !important; }}

        /* ---------- Floating scroll-to-bottom button ---------- */
        .scroll-fab {{
            position: fixed; right: 24px; bottom: 96px; z-index: 9999;
            width: 38px; height: 38px; border-radius: 50%;
            background: var(--maroon); color: #FBF7F0; border: 1px solid var(--gold);
            display: flex; align-items: center; justify-content: center;
            font-size: 15px; cursor: pointer; box-shadow: 0 4px 14px rgba(0,0,0,0.25);
            transition: transform 0.15s ease;
        }}
        .scroll-fab:hover {{ transform: translateY(-2px); }}

        /* ---------- Mobile responsiveness ---------- */
        @media (max-width: 640px) {{
            .block-container, [data-testid="stMainBlockContainer"] {{ padding-left: 0.6rem !important; padding-right: 0.6rem !important; }}
            .bubble-col {{ max-width: 84%; }}
            .brand-title {{ font-size: 22px; }}
            .hero-container {{ padding: 22px 14px 20px; }}
            .scroll-fab {{ right: 14px; bottom: 88px; }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════
# 5. RENDER HELPERS
# ══════════════════════════════════════════════════════════════════════════
def render_message_row(role: str, content: str, msg_id: str, timestamp: Optional[str] = None,
                        streaming: bool = False) -> str:
    label = "Passenger" if role == "user" else "Maharaja AI"
    initials = "P" if role == "user" else "AI"
    bubble_class = "user-bubble" if role == "user" else "assistant-bubble"
    safe_content = html.escape(content).replace("\n", "<br>")
    cursor = '<span class="stream-cursor">▍</span>' if streaming else ""
    copy_html = (
        f'<button class="copy-btn" onclick="copyMsg(\'{msg_id}\', this)">Copy</button>'
        if content and not streaming else ""
    )
    time_html = f'<span class="msg-time">{timestamp}</span>' if timestamp else ""
    footer = f'<div class="msg-footer">{time_html}{copy_html}</div>' if (timestamp or copy_html) else ""
    return f"""
    <div class="msg-row {role}">
        <div class="avatar {role}">{initials}</div>
        <div class="bubble-col">
            <div class="sender-label">{label}</div>
            <div class="message-bubble {bubble_class}">{safe_content}{cursor}</div>
            {footer}
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


def build_copy_store_script(messages) -> str:
    """Embeds every message's raw text in a JS lookup table so the inline
    copy buttons can read it without triggering a Streamlit rerun."""
    store = {f"m{i}": msg.content for i, msg in enumerate(messages)}
    return f"""
    <script>
        window.__maharajaCopyStore = {json.dumps(store)};
        function copyMsg(id, btn) {{
            const text = window.__maharajaCopyStore[id];
            if (!text) return;
            navigator.clipboard.writeText(text).then(() => {{
                const original = btn.innerText;
                btn.innerText = "Copied ✓";
                setTimeout(() => {{ btn.innerText = original; }}, 1500);
            }});
        }}
    </script>
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


def stream_answer(placeholder, output_text: str) -> str:
    """Renders the answer word-by-word into `placeholder`, returns the timestamp used."""
    words = output_text.split(" ")
    streamed = ""
    chunk: List[str] = []
    for word in words:
        chunk.append(word)
        if len(chunk) >= 3:
            streamed += " ".join(chunk) + " "
            placeholder.markdown(
                render_message_row("assistant", streamed.strip(), "m_stream", streaming=True),
                unsafe_allow_html=True,
            )
            chunk = []
            time.sleep(0.04)
    if chunk:
        streamed += " ".join(chunk)
        placeholder.markdown(
            render_message_row("assistant", streamed.strip(), "m_stream", streaming=True),
            unsafe_allow_html=True,
        )
        time.sleep(0.04)
    reply_time = datetime.now().strftime("%I:%M %p")
    return reply_time


def run_query(user_query: str, history_snapshot: List) -> Optional[str]:
    """Calls the RAG chain with a typing indicator, then streams the answer.
    Returns the final answer text (or None on error)."""
    typing_placeholder = st.empty()
    typing_placeholder.markdown(render_typing_indicator(), unsafe_allow_html=True)
    trigger_autoscroll()

    try:
        formatted_history: List[Tuple[str, str]] = []
        for msg in history_snapshot:
            role_type = "human" if msg.type == "human" else "ai"
            formatted_history.append((role_type, msg.content))

        response = bot_chain.invoke({"input": user_query, "chat_history": formatted_history})
        output_text = response["answer"]
    except Exception as e:
        typing_placeholder.empty()
        st.error(f"Execution Error: {e}")
        return None

    if output_text:
        reply_time = stream_answer(typing_placeholder, output_text)
        typing_placeholder.markdown(
            render_message_row("assistant", output_text, "m_last", timestamp=reply_time),
            unsafe_allow_html=True,
        )
        history_store.add_ai_message(output_text)
        st.session_state.msg_times.append(reply_time)
    return output_text


# ══════════════════════════════════════════════════════════════════════════
# 6. SIDEBAR — theme toggle, admin upload, conversation tools
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="brand-mark" style="justify-content:flex-start;gap:8px;">'
                '<span style="font-size:20px;">✈️</span>'
                '<span style="font-weight:800;font-style:italic;font-size:18px;">MAHARAJA AI</span>'
                '</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:10px;letter-spacing:2px;color:var(--gold);'
                'text-transform:uppercase;margin-top:2px;">Corporate Control Panel</div>',
                unsafe_allow_html=True)

    # ---- Theme toggle ----
    st.markdown('<div class="side-heading">Appearance</div>', unsafe_allow_html=True)
    is_dark = st.toggle("🌙 Dark mode", value=(st.session_state.theme == "dark"), key="theme_toggle")
    new_theme = "dark" if is_dark else "light"
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

    # ---- Knowledge base status ----
    st.markdown('<div class="side-heading">Knowledge Base</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="side-card"><span class="side-status-dot"></span>'
        f'<b>{len(history_store.messages)}</b> messages in this session</div>',
        unsafe_allow_html=True,
    )

    # ---- PDF ingestion ----
    st.markdown('<div class="side-heading">Ingest Source Document</div>', unsafe_allow_html=True)
    st.caption("Upload an Air India PDF to expand the RAG knowledge base.")
    uploaded_file = st.file_uploader("Upload Air India PDF", type=["pdf"], label_visibility="collapsed")
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

    # ---- Conversation tools ----
    st.markdown('<div class="side-heading">Conversation</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🆕 New chat", use_container_width=True):
            new_id = str(uuid.uuid4())
            st.session_state.user_session_id = new_id
            st.query_params["session"] = new_id
            st.session_state.msg_times = []
            st.rerun()
    with col_b:
        if st.button("🗑️ Clear", use_container_width=True):
            try:
                history_store.clear()
            except Exception:
                pass
            st.session_state.msg_times = []
            st.rerun()

    if history_store.messages:
        transcript_lines = [f"Air India · Maharaja AI — Conversation Transcript",
                             f"Session: {session_id}",
                             f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                             "-" * 40]
        for i, msg in enumerate(history_store.messages):
            who = "Passenger" if msg.type == "human" else "Maharaja AI"
            ts = st.session_state.msg_times[i] if i < len(st.session_state.msg_times) else ""
            transcript_lines.append(f"[{ts}] {who}: {msg.content}")
        transcript_text = "\n".join(transcript_lines)
        st.download_button(
            "⬇️ Download conversation",
            data=transcript_text,
            file_name=f"maharaja_ai_chat_{session_id[:8]}.txt",
            mime="text/plain",
            use_container_width=True,
        )

# ══════════════════════════════════════════════════════════════════════════
# 7. HEADER / HERO
# ══════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <div class="hero-container">
        <div class="brand-mark">
            <svg width="26" height="26" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M50 8 L86 78 L14 78 Z" stroke="#C9A15A" stroke-width="6" stroke-linejoin="round"/>
            </svg>
            <h1 class="brand-title">AIR INDIA</h1>
        </div>
        <p class="brand-subtitle">Maharaja AI &middot; Corporate Travel Assistant</p>
        <p class="brand-tagline">Bookings &middot; Baggage &middot; Refunds &middot; Policies — answered instantly</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════
# 8. CAPTURE INPUT FIRST
# ══════════════════════════════════════════════════════════════════════════
quick_query = st.session_state.pop("trigger_query", None)
regenerate_flag = st.session_state.pop("do_regenerate", False)
typed_query = st.chat_input("Type an Air India policy query...")
user_query = quick_query or typed_query

# Stable history snapshot captured before mutating the store below.
stable_history_snapshot = list(history_store.messages)

if user_query:
    history_store.add_user_message(user_query)
    st.session_state.msg_times.append(datetime.now().strftime("%I:%M %p"))

# ══════════════════════════════════════════════════════════════════════════
# 9. CHAT PANEL
# ══════════════════════════════════════════════════════════════════════════
panel_height = 460 if stable_history_snapshot or user_query else 280
chat_panel = st.container(height=panel_height, border=False)
with chat_panel:
    st.markdown('<div class="chat-scroll-marker"></div>', unsafe_allow_html=True)

    if history_store.messages:
        rows_html = []
        for i, msg in enumerate(history_store.messages):
            role = "user" if msg.type == "human" else "assistant"
            ts = st.session_state.msg_times[i] if i < len(st.session_state.msg_times) else None
            rows_html.append(render_message_row(role, msg.content, msg_id=f"m{i}", timestamp=ts))
        st.markdown("".join(rows_html), unsafe_allow_html=True)
        st.markdown(build_copy_store_script(history_store.messages), unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <div class="empty-state-wrap">
                <div class="empty-icon-badge">✈️</div>
                <div class="empty-title">Welcome aboard, Maharaja AI</div>
                <div class="empty-subtitle">I can help you with bookings, baggage, refunds,<br>
                flight schedules, travel policies, and more.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        suggestions = [
            "🧳 Baggage Allowance", "✈️ Book Flight", "💺 Seat Selection",
            "🛂 Check-in", "📅 Flight Schedule", "💳 Refund Policy",
        ]
        cols = st.columns(3)
        for idx, suggestion in enumerate(suggestions):
            with cols[idx % 3]:
                if st.button(suggestion, key=f"chip_{idx}", use_container_width=True):
                    st.session_state.trigger_query = suggestion.split(" ", 1)[1]
                    st.rerun()

    # ---- Answer a freshly submitted query ----
    if user_query:
        run_query(user_query, stable_history_snapshot)

    trigger_autoscroll()

# ══════════════════════════════════════════════════════════════════════════
# 10. TOOLBAR — regenerate last response (only when relevant)
# ══════════════════════════════════════════════════════════════════════════
last_is_ai = bool(history_store.messages) and history_store.messages[-1].type == "ai"
if last_is_ai and not user_query:
    st.markdown('<div class="toolbar-row">', unsafe_allow_html=True)
    tcol1, tcol2 = st.columns([1, 3])
    with tcol1:
        if st.button("🔄 Regenerate", use_container_width=True):
            # Locate the last human message and the history strictly before it,
            # then ask the chain again. (The store only supports append/clear,
            # so the previous answer stays in history and a fresh one is added.)
            last_human = None
            preceding: List = []
            msgs = history_store.messages
            for j in range(len(msgs) - 1, -1, -1):
                if msgs[j].type == "human":
                    last_human = msgs[j].content
                    preceding = msgs[:j]
                    break
            st.markdown('</div>', unsafe_allow_html=True)
            if last_human:
                answer_placeholder = st.empty()
                answer_placeholder.markdown(render_typing_indicator(), unsafe_allow_html=True)
                try:
                    formatted_history = [
                        ("human" if m.type == "human" else "ai", m.content) for m in preceding
                    ]
                    response = bot_chain.invoke({"input": last_human, "chat_history": formatted_history})
                    output_text = response["answer"]
                    reply_time = stream_answer(answer_placeholder, output_text)
                    history_store.add_ai_message(output_text)
                    st.session_state.msg_times.append(reply_time)
                except Exception as e:
                    st.error(f"Execution Error: {e}")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# 11. FLOATING SCROLL-TO-BOTTOM BUTTON
# ══════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <div class="scroll-fab" onclick="
        (function() {
            const markers = document.querySelectorAll('.chat-scroll-marker');
            if (markers.length === 0) return;
            const marker = markers[markers.length - 1];
            const node = marker.closest('[data-testid=\\'stVerticalBlockBorderWrapper\\']');
            if (node) { node.scrollTo({top: node.scrollHeight, behavior: 'smooth'}); }
        })();
    ">↓</div>
    """,
    unsafe_allow_html=True,
)