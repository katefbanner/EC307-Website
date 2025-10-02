# app.py (refactored layout with left-hand menu)
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime
from bson import ObjectId

#  hide the GitHub icon
st.markdown(
    """
    <style>
    .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

            
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

favicon_path = os.path.join(os.path.dirname(__file__), "favicon.png")

st.set_page_config(
    page_title="EC307",
    layout="wide",
    page_icon=favicon_path
)

st.title("EC307") 
st.markdown(
    "<p style='font-size:18px;'>Browse past exam questions, ask your own, and vote on the exam question Professor Bandiera will cover next lecture.</p>", 
    unsafe_allow_html=True
)


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

    # Start card wrapper
    

    # Section A → text-based questions
    if exam.get("type", "").startswith("Section A"):
        st.markdown(
            f"<h4 style='margin-bottom:6px'>{exam.get('text', '')}</h4>",
            unsafe_allow_html=True
        )

    # Section B → image-based questions
    elif exam.get("type", "").startswith("Section B"):
        for img in exam.get("fig_path", []):
            st.image(img, use_container_width=True)

    # Common metadata footer
    st.markdown(
        f"""
        <div style="font-size:0.9em;color:#333;margin-top:10px;">
            <b>Topic:</b> {', '.join(exam.get('topics', []))} &nbsp; | &nbsp;
            <b>Year:</b> {exam.get('year', 'N/A')} &nbsp; | &nbsp;
            <b>Question Type:</b> {exam.get('type', 'N/A')} &nbsp; | &nbsp;
            <b>Votes:</b> {exam.get('votes', 0)}
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

    st.markdown("---")

def vote_page():
    st.header("Vote for Next Week's Lecture Exam Question")
    st.write("##### Choose which exam question you want Professor Bandiera to cover next week.")
    st.markdown("---")

    # Example: filter questions by topic and type
    topic_filter = {"topics": "Methods of Development I: Program Evaluation and RCTs"}
    topic_questions = list(exam_col.find(topic_filter))

    if "has_voted" not in st.session_state:
        st.session_state.has_voted = False

    # Iterate through questions in pairs (for 2 columns)
    for i in range(0, len(topic_questions), 2):
        cols = st.columns(2)

        for j, col in enumerate(cols):
            if i + j < len(topic_questions):
                q = topic_questions[i + j]

                with col:
                    # Show images with consistent width
                    for img in q.get("fig_path", []):
                        st.image(img, use_container_width=True)

                    # Show vote count
                    st.markdown(f"👍 **{q.get('votes', 0)} votes**")

                    # Voting button
                    if not st.session_state.has_voted:
                        if st.button("Place vote", key=str(q["_id"])):
                            exam_col.update_one(
                                {"_id": ObjectId(q["_id"])},
                                {"$inc": {"votes": 1}}
                            )
                            st.session_state.has_voted = True
                            st.success("✅ Thanks for voting!")
                            st.rerun()
                    else:
                        st.button("Place vote", key=str(q["_id"]), disabled=True)


# --- Main content depending on menu ---
if page == "Exam Questions":
    st.header("Browse Questions from Past Exams")
    st.write("##### Below are all the past EC307 exam questions for AT. You can ask about any of them, and we’ll respond to your question and share both the question and our response so everyone can learn.")


    query = render_filters()
    st.markdown("---")
    for exam in exam_col.find(query).sort("year", -1).limit(200):
        question_card(exam)

elif page == "Vote for Next Lecture Exam Question":
    # Add your existing voting interface here
    vote_page()

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
