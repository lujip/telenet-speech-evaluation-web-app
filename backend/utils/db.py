from pymongo import MongoClient

# Connect to local MongoDB instance
client = MongoClient('mongodb://admin:Ginabot7232@192.168.77.74:27017/mongodb_test?authSource=admin')

db = client['recruitment']  # Use (or create) this database 
