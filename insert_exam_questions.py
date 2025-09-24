# insert_exam_questions.py
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise SystemExit("Set MONGO_URI in your .env")

client = MongoClient(MONGO_URI)
db = client["examdb"]
exam_col = db["exam_questions"]

# Replace or extend this list with all your real exam questions
exam_docs = [
    {
        "text": "The elasticity of official GDP figures to nighttime lights is systematically larger in more authoritarian regimes because autocrats overstate exports.",
        "topics": ["W2: GDP"],
        "year": 2024,
        "votes": 0,
        "created_at": datetime.utcnow(),
        "type": "Section A",
    },
    {
        "text": "Exposure to innovation during childhood through one’s family or neighbourhood has a significant causal effect on a child’s propensity to become an inventor.",
        "topics": ["W8: Innovation"],
        "year": 2024,
        "votes": 0,
        "created_at": datetime.utcnow(),
        "type": "Section A",
    },
    {
        "text": "As firms and wage jobs appear over the course of economic development, it is men from wealthy households that get them first, followed by men of poorer households and finally women.",
        "topics": ["W3: Labour Supply"],
        "year": 2024,
        "votes": 0,
        "created_at": datetime.utcnow(),
        "type": "Section A",
    },
    {
        "text": "Jobs training programmes inside and outside of firms work equally well in both the short run and long run.",
        "topics": ["W6: Job Training"],
        "year": 2024,
        "votes": 0,
        "created_at": datetime.utcnow(),
        "type": "Section A",
    },
]

# Insert docs
res = exam_col.insert_many(exam_docs)
print(f"Inserted {len(res.inserted_ids)} exam_questions. IDs (first 3): {res.inserted_ids[:3]}")
