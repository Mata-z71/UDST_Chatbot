import streamlit as st
from chatbot import Chatbot

st.set_page_config(
    page_title="UDST Student Support Chatbot",
    page_icon="🎓",
    layout="centered",
)

@st.cache_resource
def load_bot():
    return Chatbot("udst_faq.csv")

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

bot = load_bot()

st.title("🎓 UDST Student Support Chatbot")
st.write("Ask questions about **UDST colleges, programs, and general university information**.")

st.markdown("### Example Questions")
st.markdown("""
- How many colleges are there in UDST?
- What programs are offered at UDST?
- What IT programs does UDST have?
- What is UDST?
- Where is UDST located?
- Does UDST have a library?
- What is the official UDST website?
""")

user_question = st.text_input("Ask your question")

if st.button("Ask"):
    answer, category, score = bot.get_response(user_question)

    st.markdown("### Answer")
    st.markdown(format_answer(answer))

    st.markdown("### Info")
    st.write("Category:", category)
    st.write("Similarity Score:", round(score, 3))