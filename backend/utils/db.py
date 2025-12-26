import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get MongoDB connection string from environment variables
# REQUIRED - no fallback to ensure explicit configuration
mongo_uri = os.getenv('MONGODB_URI')
mongo_db = os.getenv('MONGODB_DB')

if not mongo_uri or not mongo_db:
    raise ValueError("MONGODB_URI and MONGODB_DB environment variables must be set in .env file")

# Connect to MongoDB
client = MongoClient(mongo_uri)

# Select database
db = client[mongo_db]

# Collections
session_states_collection = db["session_states"]
