
import json, os
from datetime import datetime
from pymongo import MongoClient

JSON_PATH = "data/inaturalist_meta.json"
IMG_DIR   = "dataset/reelle"

client = MongoClient("mongodb://isen:isen@localhost:27017/admin?authSource=admin")
db  = client["veripix"]
raw = db["images_raw"]
raw.create_index("path_local", unique=True)

# 1) Charge le JSON complet
with open(JSON_PATH, "r", encoding="utf-8") as f:
    hits = json.load(f)

# 2) Liste les fichiers réellement téléchargés (inaturalist_1.jpg, _2.jpg, ...)
files = sorted(
    [f for f in os.listdir(IMG_DIR) if f.startswith("inaturalist_") and f.lower().endswith(".jpg")],
    key=lambda x: int(x.split("_")[1].split(".")[0])
)

added = 0
for idx, filename in enumerate(files, start=1):
    path_local = os.path.abspath(os.path.join(IMG_DIR, filename))
    # Sécurités : borne sur la taille de hits et présence de photos
    if idx-1 >= len(hits):
        break
    obs = hits[idx-1]
    photos = obs.get("photos") or []
    if not photos:
        continue

    photo0 = photos[0]
    download_url = (photo0.get("url") or "").replace("square", "large")

    doc = {
        "path_local": path_local,
        "nom_image": filename,
        "type_image": "reelle",
        "source": "inaturalist",
        "page_url": obs.get("uri"),
        "download_url": download_url,
        "license": photo0.get("license_code") or obs.get("license_code"),
        "taxon_name": (obs.get("taxon") or {}).get("name"),
        "common_name": (obs.get("taxon") or {}).get("preferred_common_name"),
        "location": obs.get("location"),
        "collected_at": datetime.utcnow(),
        "status": "new",
        "extra": {"observation_id": obs.get("id")},
    }

    try:
        raw.update_one({"path_local": path_local}, {"$setOnInsert": doc}, upsert=True)
        added += 1
        print("Mongo", filename)
    except Exception as e:
        print(filename, e)

print("Terminé")
