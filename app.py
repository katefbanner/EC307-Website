# app.py (refactored layout with left-hand menu)
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime
from bson import ObjectId
import streamlit as st

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    st.error("Set MONGO_URI in your .env")
    st.stop()

# MONGO_URI = st.secrets.get("MONGO_URI", os.getenv("MONGO_URI"))
# if not MONGO_URI:
    # st.error("Set MONGO_URI in .env (for local) or in Streamlit Secrets (for deployment)")
    # st.stop()

# --- Database setup ---
client = MongoClient(MONGO_URI)
db = client["examdb"]
exam_col = db["exam_questions"]
student_col = db["student_questions"]
contrib_col = db["contributed_questions"]

st.set_page_config(page_title="EC307", page_icon="📘", layout="wide")
st.title("EC307")
st.caption("Browse past questions, ask about them, and vote for what Oriana should discuss next week.")

# --- Left-hand menu ---
menu_options = ["Exam Questions", "Vote for Next Lecture Exam Question"]
with st.sidebar:
    st.header("Navigation")
    page = st.radio("Go to", menu_options)

    # Instructor login (same as before)
    st.markdown("---")
    st.subheader("Instructor Login")
    if "instructor_logged_in" not in st.session_state:
        st.session_state.instructor_logged_in = False

    if not st.session_state.instructor_logged_in:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                if (username == st.secrets["instructor"]["username"] 
                    and password == st.secrets["instructor"]["password"]):
                    st.session_state.instructor_logged_in = True
                    st.success("✅ Logged in as instructor")
                else:
                    st.error("❌ Invalid credentials")
    else:
        st.success("Logged in as instructor")
        if st.button("Logout"):
            st.session_state.instructor_logged_in = False

## --- Helper: filters for exam questions ---
def render_filters():
    # Create three columns for the filters
    col1, col2, col3 = st.columns(3)

    # Topic filter
    topics = sorted({t for doc in exam_col.find() for t in doc.get("topics", [])})
    topic_options = ["All"] + topics
    topic = col1.selectbox("Topic", topic_options)

    # Year filter
    years = sorted({doc.get("year") for doc in exam_col.find() if doc.get("year") is not None})
    year_options = ["All"] + years
    year = col2.selectbox("Year", year_options)

    # Question type filter
    types = sorted({doc.get("type", "Other") for doc in exam_col.find()})
    type_options = ["All"] + types
    q_type = col3.selectbox("Question Type", type_options)

    # Build query dict
    query = {}
    if topic != "All":
        query["topics"] = topic
    if year != "All":
        query["year"] = int(year)
    if q_type != "All":
        query["type"] = q_type
    return query


# --- Helper: render one exam question ---
def question_card(exam):
    qid = exam["_id"]
    qid_str = str(qid)

    # Card for exam question
    st.markdown(
        f"""
        <div style="
            background-color: #ffffff;
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            margin-bottom: 4px;
        ">
            <h4 style="margin-bottom:6px">{exam['text']}</h4>
            <div style="font-size:0.9em;color:#333;margin-bottom:10px;">
                <b>Topic:</b> {', '.join(exam.get('topics', []))} &nbsp; | &nbsp;
                <b>Year:</b> {exam.get('year', 'N/A')} &nbsp; | &nbsp;
                <b>Question Type:</b> {exam.get('type', 'N/A')} &nbsp; | &nbsp;
                <b>Votes:</b> {exam.get('votes', 0)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Verified student questions (responses)
    verified_qs = student_col.find({"question_id": qid, "verified": True})
    for v in verified_qs:
        with st.expander(f"💬 {v.get('question')[:80]}"):
            st.markdown(f"**Student:** {v.get('question')}")
            st.markdown(f"**Response:** {v.get('response')}")

    # Ask question box
    ask_key = f"ask_{qid_str}"
    comment = st.text_area("💬 Ask a question about this exam question", key=ask_key)
    if st.button("Submit question", key=f"submit_{qid_str}"):
        if comment and comment.strip():
            student_col.insert_one({
                "question_id": qid,
                "student": "anonymous",
                "question": comment.strip(),
                "response": None,
                "verified": False,
                "created_at": datetime.utcnow()
            })
            st.success("✅ Your question has been submitted. It will appear once answered and verified.")

    # Light separator bar
    st.markdown(
        '<div style="height:12px; background-color:#f0f2f6; margin:12px 0; border-radius:6px;"></div>',
        unsafe_allow_html=True
    )

# --- Main content depending on menu ---
if page == "Exam Questions":
    st.header("Browse Questions from Past Exams")
    st.caption("Below is all the questions from previous EC307 exams for AT. You can ask about any question below, we will respond to your anonymous question and post the question with our response so everyone can view it and learn.")
    query = render_filters()
    for exam in exam_col.find(query).sort("year", -1).limit(200):
        question_card(exam)

elif page == "Vote for Next Lecture Exam Question":
    st.header("Vote for Next Week's Lecture Exam Question")
    st.caption("Choose which exam question you want Oriana to cover next week.")
    # Add your existing voting interface here
    st.info("Voting interface placeholder — add your code here")


# --- Instructor panel ---
if st.session_state.get("instructor_logged_in", False):

    if page == "Exam Questions":
        # Instructor view for student questions on existing exams
        st.markdown("---")
        st.header("Instructor: Review Student Questions on Exams")
        unverified_student = list(student_col.find({"verified": False}).sort("created_at", 1).limit(200))
        st.write(f"Unverified student questions: {len(unverified_student)}")
        for doc in unverified_student:
            parent = exam_col.find_one({"_id": doc["question_id"]})
            if parent:
                st.markdown(f"**For exam:** {parent['text'][:180]}")
            else:
                st.markdown("**For exam:** [Deleted or missing exam]")
            st.markdown(f"**Student asked:** {doc['question']}")
            resp_key = f"resp_{str(doc['_id'])}"
            response_text = st.text_area("Write your response here", key=resp_key)
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Verify & Publish", key=f"verify_{str(doc['_id'])}"):
                    if response_text.strip():
                        student_col.update_one(
                            {"_id": doc["_id"]},
                            {"$set": {"response": response_text.strip(), "verified": True, "answered_at": datetime.utcnow()}}
                        )
                        st.success("Answer saved & verified — it will now appear for students.")
            with col2:
                if st.button("🗑 Delete Question", key=f"delete_{str(doc['_id'])}"):
                    student_col.delete_one({"_id": doc["_id"]})
                    st.success("Student question deleted")

