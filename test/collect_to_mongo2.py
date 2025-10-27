from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://veripix:veripix@localhost:27017/veripix?authSource=veripix")
raw = client.veripix.images_raw
raw.create_index("path_local", unique=True)

def stage_image(path_local, nom_image, type_image, source, page_url, download_url, mime=None):
    doc = {
        "path_local": path_local,
        "nom_image": nom_image,
        "type_image": type_image,     # "artificielle" ici
        "source": source,             # "artbreeder"
        "page_url": page_url,         # page de navigation
        "download_url": download_url, # URL directe utilisée
        "mime": mime,
        "status": "new",
        "collected_at": datetime.utcnow()
    }
    raw.update_one({"path_local": path_local}, {"$setOnInsert": doc}, upsert=True)
