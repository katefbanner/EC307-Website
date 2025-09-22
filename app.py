import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# load .env file
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["examdb"]
questions = db["questions"]

# Force light theme
st.set_page_config(
    page_title="Exam Question Databank",
    page_icon="📘",
    layout="wide",         # gives you more room
    initial_sidebar_state="expanded"
)

st.title("📘 Exam Question Databank")
st.caption("Find previous exam questions by year and topic, contribute your own, and vote for the exam question you want Oriana to discuss next week.")

with st.container():
    st.subheader("✨ Browse Questions")
    st.markdown("Filter by topic and year below.")

# Fetch questions
def question_card(q):
    st.markdown(
        f"""
        <div style="
            background-color: #ffffff;
            padding: 1rem;
            border-radius: 0.75rem;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        ">
            <h4>{q['text']}</h4>
            <p><b>Topic:</b> {', '.join(q.get('topics', []))} | <b>Year:</b> {q.get('year', 'N/A')}</p>
            <p><b>Votes:</b> {q.get('votes', 0)}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

for q in questions.find().limit(5):
    question_card(q)

# sidebarw
with st.sidebar:
    st.header("🔍 Filters")
    topic = st.selectbox("Select Topic", ["All", "Math", "Physics"])
    year = st.selectbox("Select Year", ["All", 2021, 2022, 2023])

