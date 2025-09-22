from pymongo import MongoClient

# Connect to local MongoDB instance
client = MongoClient('mongodb://localhost:27017/')

db = client['mongodb_test']  # Use (or create) this database 