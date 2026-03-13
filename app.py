import time
import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from chatbot import Chatbot


# -----------------------------
# Configuration
# -----------------------------
APP_TITLE = "UDST Student Support Chatbot"
APP_ICON = "🎓"
ASSISTANT_AVATAR = "🤖"
CHAT_PLACEHOLDER = "Ask a question about UDST..."
CHAT_HEIGHT = 520
LOGO_CANDIDATES = ("udst-logo.png", "udst_logo.png")
EXAMPLE_QUESTIONS = [
    "How many colleges are there in UDST?",
    "What programs are offered at UDST?",
    "What IT programs does UDST have?",
    "What is UDST?",
    "Where is UDST located?",
    "Does UDST have a library?",
]
SUGGESTED_QUESTIONS = [
    "Who is the president of UDST?",
    "What business programs are available at UDST?",
    "What is the official UDST website?",
]

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------
# Cached resources
# -----------------------------
@st.cache_resource
def load_bot():
    return Chatbot("udst_faq.csv")


# -----------------------------
# Helper functions
# -----------------------------
def resolve_logo_path() -> str | None:
    base_dir = Path(__file__).resolve().parent
    for filename in LOGO_CANDIDATES:
        candidate = base_dir / filename
        if candidate.exists():
            return str(candidate)
    return None


def logo_data_uri(path: str | None) -> str | None:
    if not path:
        return None
    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def format_answer(answer: str) -> str:
    lines = [line.strip() for line in answer.split("\n") if line.strip()]

    if len(lines) <= 1:
        return answer

    title = lines[0]
    bullets = lines[1:]

    formatted = f"**{title}**\n\n"
    for item in bullets:
        formatted += f"- {item}\n"
    return formatted


def confidence_label(score: float | None) -> str:
    if score is None:
        return "Direct match"
    if score >= 0.85:
        return "High confidence"
    if score >= 0.65:
        return "Medium confidence"
    return "Low confidence"


def default_messages() -> list[dict]:
    return [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm the UDST Student Support Assistant. Ask me about colleges, "
                "programs, admissions-related information, and general university details."
            ),
            "time": time.strftime("%H:%M"),
            "category": None,
            "score": None,
        }
    ]


def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = default_messages()
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None


def reset_chat():
    st.session_state.messages = default_messages()
    st.session_state.pending_question = None


def add_message(role: str, content: str, category=None, score=None):
    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
            "category": category,
            "score": score,
            "time": time.strftime("%H:%M"),
        }
    )


def queue_question(question: str):
    cleaned_question = question.strip()
    if not cleaned_question:
        return

    add_message("user", cleaned_question)
    st.session_state.pending_question = cleaned_question


def process_pending_question():
    pending_question = st.session_state.pending_question
    if not pending_question:
        return

    time.sleep(0.45)
    answer, category, score = bot.get_response(pending_question)
    add_message(
        "assistant",
        format_answer(answer),
        category=category,
        score=score,
    )
    st.session_state.pending_question = None
    st.rerun()


def assistant_avatar():
    return ASSISTANT_AVATAR


def render_auto_scroll_script():
    components.html(
        """
        <script>
        const parentDoc = window.parent.document;
        const mainSection = parentDoc.querySelector('[data-testid="stMain"]');
        if (mainSection) {
            mainSection.scrollTo({ top: mainSection.scrollHeight, behavior: "smooth" });
        }

        const scrollables = parentDoc.querySelectorAll('div[style*="overflow: auto"]');
        scrollables.forEach((node) => {
            node.scrollTo({ top: node.scrollHeight, behavior: "smooth" });
        });
        </script>
        """,
        height=0,
    )


# -----------------------------
# UI components
# -----------------------------
def render_styles():
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

            :root {
                --bg: #eff5fb;
                --surface: rgba(255, 255, 255, 0.84);
                --surface-strong: #ffffff;
                --surface-soft: rgba(255, 255, 255, 0.68);
                --border: rgba(15, 23, 42, 0.08);
                --text: #122033;
                --muted: #5f6f86;
                --primary: #0f766e;
                --primary-deep: #0b5d56;
                --primary-soft: #dff5f2;
                --accent: #f59e0b;
                --shadow-lg: 0 22px 60px rgba(15, 23, 42, 0.10);
                --shadow-md: 0 16px 38px rgba(15, 23, 42, 0.08);
                --radius-xl: 28px;
                --radius-lg: 22px;
                --radius-md: 18px;
            }

            .stApp {
                background:
                    linear-gradient(180deg, #edf4fb 0%, #f8fbfd 45%, #f3f7fb 100%);
                color: var(--text);
                font-family: 'Manrope', sans-serif;
            }

            .block-container {
                max-width: 1120px;
                padding-top: 1.6rem;
                padding-bottom: 1.6rem;
            }

            h1, h2, h3, h4, p, span, label, div {
                font-family: 'Manrope', sans-serif;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0f172a 0%, #10243a 100%);
                border-right: 1px solid rgba(255, 255, 255, 0.06);
            }

            [data-testid="stSidebar"] * {
                color: #ecf3ff !important;
            }

            [data-testid="stSidebar"] .stButton > button {
                width: 100%;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.14);
                color: #ffffff;
                box-shadow: none;
            }

            .hero-shell {
                padding: 1.8rem 2rem;
                border-radius: var(--radius-xl);
                background:
                    linear-gradient(135deg, rgba(15, 118, 110, 0.96), rgba(14, 165, 164, 0.82)),
                    linear-gradient(135deg, #0f766e, #0ea5a4);
                box-shadow: var(--shadow-lg);
                color: #ffffff;
                position: relative;
                overflow: hidden;
                margin-bottom: 1.2rem;
            }

            .hero-header {
                display: flex;
                align-items: center;
                gap: 1rem;
                margin-bottom: 0.7rem;
            }

            .hero-logo {
                background: #ffffff;
                border-radius: 14px;
                padding: 8px;
                box-shadow: 0 8px 20px rgba(15, 23, 42, 0.18);
                border: 1px solid rgba(15, 23, 42, 0.10);
                line-height: 0;
                flex: 0 0 auto;
            }

            .hero-logo img {
                display: block;
            }


            .hero-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.45rem;
                padding: 0.45rem 0.85rem;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.14);
                font-size: 0.84rem;
                font-weight: 800;
                letter-spacing: 0.02em;
            }

            .hero-title {
                font-size: clamp(2rem, 3vw, 3rem);
                line-height: 1.02;
                font-weight: 800;
                margin: 0.35rem 0 0;
            }

            .hero-subtitle {
                margin: 0.85rem 0 0;
                max-width: 760px;
                color: rgba(245, 255, 253, 0.95);
                line-height: 1.7;
                font-weight: 500;
            }

            .section-label {
                margin: 1.1rem 0 0.65rem;
                font-size: 0.94rem;
                font-weight: 800;
                color: var(--text);
                letter-spacing: 0.01em;
            }

            .section-note {
                margin: 0 0 0.8rem;
                color: #34475f;
                font-size: 0.95rem;
                font-weight: 600;
            }

            .welcome-card {
                padding: 1rem 1.1rem;
                border-radius: var(--radius-lg);
                background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(246, 251, 253, 0.96));
                border: 1px solid rgba(15, 118, 110, 0.10);
                box-shadow: var(--shadow-md);
                margin-bottom: 0.9rem;
            }

            .welcome-title {
                font-size: 1rem;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .welcome-copy {
                color: var(--muted);
                font-size: 0.95rem;
                line-height: 1.7;
            }

            .stButton > button {
                border-radius: var(--radius-md);
                border: 1px solid var(--border);
                background: rgba(255, 255, 255, 0.92);
                color: var(--text);
                font-weight: 700;
                box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
                padding: 0.85rem 1rem;
                transition:
                    transform 0.18s ease,
                    box-shadow 0.18s ease,
                    border-color 0.18s ease,
                    background 0.18s ease,
                    color 0.18s ease;
            }

            .stButton > button:hover {
                transform: translateY(-2px);
                border-color: rgba(15, 118, 110, 0.22);
                color: var(--primary);
                background: rgba(255, 255, 255, 0.98);
                box-shadow: 0 16px 32px rgba(15, 23, 42, 0.09);
            }

            .stButton > button:focus {
                border-color: rgba(15, 118, 110, 0.34);
                box-shadow: 0 0 0 0.2rem rgba(15, 118, 110, 0.12);
            }

            .prompt-helper {
                font-size: 0.88rem;
                color: var(--muted);
                margin-top: 0.3rem;
                line-height: 1.55;
            }

            [data-testid="stChatMessage"] {
                padding: 0.95rem 1.1rem !important;
                margin-bottom: 1.15rem !important;
                border-radius: 24px;
            }

            [data-testid="stChatMessage"] > div {
                padding: 0.2rem 0.25rem !important;
            }

            [data-testid="stChatMessage"]:not(:has([data-testid="chatAvatarIcon-user"])) {
                background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(247, 251, 253, 0.98));
                border: 1px solid rgba(15, 118, 110, 0.09);
                box-shadow: 0 14px 30px rgba(15, 23, 42, 0.05);
            }

            [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
                background: linear-gradient(180deg, rgba(15, 118, 110, 0.12), rgba(15, 118, 110, 0.08));
                border: 1px solid rgba(15, 118, 110, 0.14);
                box-shadow: 0 14px 30px rgba(15, 118, 110, 0.08);
            }

            [data-testid="stChatMessageContent"] p,
            [data-testid="stChatMessageContent"] li {
                font-size: 1rem;
                line-height: 1.75;
                color: var(--text);
            }

            [data-testid="stChatMessageContent"] {
                padding: 0.35rem 0.35rem 0.25rem 0.35rem !important;
                margin-top: 0.1rem;
            }

            [data-testid="chatAvatarIcon-assistant"] {
                background: rgba(15, 118, 110, 0.12);
                border-radius: 50%;
                padding: 6px;
                box-shadow: 0 4px 10px rgba(15, 23, 42, 0.10);
                border: 1px solid rgba(15, 118, 110, 0.18);
            }

            [data-testid="stChatInput"] {
                background: rgba(255, 255, 255, 0.94);
                border: 1px solid rgba(15, 23, 42, 0.08);
                border-radius: 22px;
                box-shadow: 0 16px 40px rgba(15, 23, 42, 0.10);
            }

            .metadata-row {
                display: flex;
                gap: 0.5rem;
                flex-wrap: wrap;
                margin-top: 0.7rem;
                margin-bottom: 0.1rem;
                padding-left: 0.35rem;
            }

            .metadata-pill {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                padding: 0.35rem 0.7rem;
                border-radius: 999px;
                background: var(--primary-soft);
                color: var(--primary-deep);
                font-size: 0.78rem;
                font-weight: 800;
            }

            .typing-indicator {
                display: inline-flex;
                align-items: center;
                gap: 0.38rem;
                padding: 0.45rem 0.05rem;
                color: #475a72;
                font-weight: 700;
            }

            .typing-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: rgba(15, 118, 110, 0.7);
                animation: typing-bounce 1.2s infinite ease-in-out;
            }

            .typing-dot:nth-child(2) {
                animation-delay: 0.15s;
            }

            .typing-dot:nth-child(3) {
                animation-delay: 0.3s;
            }

            @keyframes typing-bounce {
                0%, 80%, 100% {
                    opacity: 0.35;
                    transform: translateY(0);
                }
                40% {
                    opacity: 1;
                    transform: translateY(-3px);
                }
            }

            .sidebar-card {
                padding: 1rem;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.08);
                margin-top: 0.9rem;
                transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
            }

            .sidebar-card:hover {
                transform: translateY(-2px);
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.18);
            }

            .sidebar-card a {
                color: #ffffff !important;
                text-decoration: none;
                font-weight: 800;
            }

            .sidebar-card p {
                margin: 0.28rem 0 0;
                color: rgba(236, 243, 255, 0.78) !important;
                font-size: 0.92rem;
                line-height: 1.6;
            }

            .logo-surface {
                background: white;
                padding: 10px;
                border-radius: 14px;
                display: inline-block;
                box-shadow: 0 10px 22px rgba(15, 23, 42, 0.14);
                line-height: 0;
                border: 1px solid rgba(15, 23, 42, 0.08);
            }

            .logo-surface img {
                display: block;
            }

            .sidebar-logo {
                margin-bottom: 12px;
            }

            .footer-card {
                margin-top: 1.1rem;
                padding: 1rem 1.2rem;
                border-radius: 20px;
                background: rgba(255, 255, 255, 0.74);
                border: 1px solid rgba(15, 23, 42, 0.06);
                box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
                text-align: center;
                color: var(--muted);
                font-size: 0.92rem;
                line-height: 1.7;
            }

            @media (max-width: 900px) {
                .block-container {
                    padding-top: 1.3rem;
                    padding-bottom: 1.2rem;
                }

                .hero-shell {
                    padding: 1.3rem;
                }

                .hero-title {
                    font-size: 2rem;
                }
            }

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    with st.sidebar:
        if LOGO_DATA_URI:
            st.markdown(
                f"""
                <div class="sidebar-logo logo-surface">
                    <img src="{LOGO_DATA_URI}" width="120" alt="UDST logo">
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif LOGO_PATH:
            st.image(LOGO_PATH, width=120)

        st.markdown("## UDST Assistant")
        st.write("Quick access to important university resources.")

        if st.button("Clear chat", use_container_width=True):
            reset_chat()
            st.rerun()

        st.markdown(
            """
            <div class="sidebar-card">
                <a href="https://www.udst.edu.qa" target="_blank">Official Website</a>
                <p>Explore the main UDST portal for university-wide information.</p>
            </div>
            <div class="sidebar-card">
                <a href="https://www.udst.edu.qa/admissions" target="_blank">Admissions</a>
                <p>Learn about admission requirements, deadlines, and application details.</p>
            </div>
            <div class="sidebar-card">
                <a href="https://www.udst.edu.qa/academic/our-colleges" target="_blank">Programs</a>
                <p>Browse academic colleges, departments, and available programs.</p>
            </div>
            <div class="sidebar-card">
                <a href="https://www.udst.edu.qa/contact-us" target="_blank">Contact Information</a>
                <p>Find contact channels if you need support beyond the chatbot.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_hero():
    logo_html = ""
    if LOGO_DATA_URI:
        logo_html = (
            f'<div class="hero-logo"><img src="{LOGO_DATA_URI}" width="72" alt="UDST logo"></div>'
        )

    st.markdown(
        f"""
        <section class="hero-shell">
            <div class="hero-header">
                {logo_html}
                <div class="hero-badge">University Knowledge Assistant</div>
            </div>
            <h1 class="hero-title">UDST Student Support Chatbot</h1>
            <p class="hero-subtitle">
                Ask about UDST colleges, programs, admissions-related information, and general
                university details. The assistant uses semantic search to match your question
                with the most relevant answer.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_welcome_card():
    st.markdown(
        """
        <div class="welcome-card">
            <div class="welcome-title">What this assistant can help with</div>
            <div class="welcome-copy">
                Get fast answers about UDST colleges, academic programs, university information,
                and frequently asked student questions. Use a quick prompt below or type your own question.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_prompt_grid(title: str, note: str, questions: list[str], key_prefix: str):
    st.markdown(f'<div class="section-label">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-note">{note}</div>', unsafe_allow_html=True)

    columns = st.columns(3)

    for index, question in enumerate(questions):
        with columns[index % 3]:
            if st.button(question, key=f"{key_prefix}_{index}", use_container_width=True):
                queue_question(question)
                st.rerun()


def render_message(message: dict):
    avatar = assistant_avatar() if message["role"] == "assistant" else "👤"

    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

        metadata = []
        if message.get("time"):
            metadata.append(f'<span class="metadata-pill">Time {message["time"]}</span>')
        if message["role"] == "assistant" and message.get("category"):
            metadata.append(f'<span class="metadata-pill">Category {message["category"]}</span>')
        if message["role"] == "assistant":
            metadata.append(
                f'<span class="metadata-pill">{confidence_label(message.get("score"))}</span>'
            )

        if metadata:
            st.markdown(
                f'<div class="metadata-row">{"".join(metadata)}</div>',
                unsafe_allow_html=True,
            )


def render_typing_indicator():
    with st.chat_message("assistant", avatar=assistant_avatar()):
        st.markdown(
            """
            <div class="typing-indicator">
                <span>UDST Assistant is typing</span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_footer():
    st.markdown(
        """
        <div class="footer-card">
            AI-powered university assistant built with Streamlit and semantic search using Sentence Transformers.
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Layout and chat logic
# -----------------------------
bot = load_bot()
LOGO_PATH = resolve_logo_path()
LOGO_DATA_URI = logo_data_uri(LOGO_PATH)

initialize_session_state()
render_styles()
render_sidebar()
render_hero()
render_welcome_card()

if len(st.session_state.messages) <= 1 and not st.session_state.pending_question:
    render_prompt_grid(
        "Quick prompts",
        "Start with a common student question to explore what the chatbot can do.",
        EXAMPLE_QUESTIONS,
        "quick_prompt",
    )

st.markdown('<div class="section-label">Conversation</div>', unsafe_allow_html=True)
chat_container = st.container(height=CHAT_HEIGHT, border=False)

with chat_container:
    for message in st.session_state.messages:
        render_message(message)

    if st.session_state.pending_question:
        render_typing_indicator()

user_prompt = st.chat_input(CHAT_PLACEHOLDER)
if user_prompt:
    queue_question(user_prompt)
    st.rerun()

if len(st.session_state.messages) > 1:
    render_prompt_grid(
        "Suggested questions",
        "More ideas you can ask next without losing your current conversation.",
        SUGGESTED_QUESTIONS,
        "suggested_prompt",
    )

render_footer()
render_auto_scroll_script()
process_pending_question()
