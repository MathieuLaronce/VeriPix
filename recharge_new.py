from pymongo import MongoClient

client = MongoClient("mongodb://isen:isen@localhost:27017/admin?authSource=admin")
db = client["veripix"]
raw = db["images_raw"]

# remet tout en "new"
result = raw.update_many({}, {"$set": {"status": "new"}})
print("Documents remis à new :", result.modified_count)
