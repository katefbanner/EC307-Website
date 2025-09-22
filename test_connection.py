from pymongo import MongoClient
from dotenv import load_dotenv

# load .env file
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(uri)

db = client["examdb"]
questions = db["questions"]

# find all documents
for q in questions.find():
    print(q)
