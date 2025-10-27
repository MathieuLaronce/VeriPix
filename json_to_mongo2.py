# json_to_mongo2.py
import json, os
from datetime import datetime
from pymongo import MongoClient

def load_jsons_to_mongo(
    mongo_uri="mongodb://isen:isen@localhost:27017/admin?authSource=admin",
    db_name="veripix",
    col_name="images_raw",
    json_path_inat="data/inaturalist_meta.json",
    img_dir_inat="dataset/reelle",
    json_path_art="data/artbreeder_meta.json",
    img_dir_art="dataset/artificielle",
):
    """Charge les JSON (iNaturalist + Artbreeder) dans Mongo, en ne gardant que les fichiers présents."""
    client = MongoClient(mongo_uri)
    db  = client[db_name]
    raw = db[col_name]
    raw.create_index("path_local", unique=True)

    summary = {"inat_inserted": 0, "art_inserted": 0}

    # ----- iNaturalist (réelles)
    if os.path.exists(json_path_inat):
        with open(json_path_inat, "r", encoding="utf-8") as f:
            hits = json.load(f)

        files = sorted(
            [f for f in os.listdir(img_dir_inat) if f.startswith("inaturalist_") and f.lower().endswith(".jpg")],
            key=lambda x: int(x.split("_")[1].split(".")[0])
        )

        added_inat = 0
        for idx, filename in enumerate(files, start=1):
            path_local = os.path.abspath(os.path.join(img_dir_inat, filename))
            if idx - 1 >= len(hits):
                break
            obs = hits[idx - 1]
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
                added_inat += 1
                print("Mongo (iNat) :", filename)
            except Exception as e:
                print("iNat err", filename, e)
        print(f"➡ iNaturalist : {added_inat} documents insérés.")
        summary["inat_inserted"] = added_inat
    else:
        print("JSON iNaturalist non trouvé, saute:", json_path_inat)

    # ----- Artbreeder (artificielles)
    if os.path.exists(json_path_art):
        with open(json_path_art, "r", encoding="utf-8") as f:
            meta = json.load(f)

        added_art = 0
        for rec in meta:
            filename   = rec.get("nom_image")
            path_local = rec.get("path_local") or os.path.abspath(os.path.join(img_dir_art, filename or ""))
            if not filename:
                continue
            if not os.path.isfile(path_local):
                continue

            doc = {
                "path_local": path_local,
                "nom_image": filename,
                "type_image": "artificielle",
                "source": rec.get("source") or "artbreeder",
                "page_url": rec.get("page_url"),
                "download_url": rec.get("download_url") or rec.get("source_url"),
                "mime": rec.get("mime"),
                "collected_at": datetime.utcnow(),
                "status": "new",
                "extra": {"timestamp": rec.get("timestamp")},
            }

            try:
                raw.update_one({"path_local": path_local}, {"$setOnInsert": doc}, upsert=True)
                added_art += 1
                print("Mongo (Artbreeder) :", filename)
            except Exception as e:
                print("Artbreeder err", filename, e)
        print(f"➡ Artbreeder : {added_art} documents insérés.")
        summary["art_inserted"] = added_art
    else:
        print("JSON Artbreeder non trouvé, saute:", json_path_art)

    print("Terminé.")
    client.close()
    return summary


if __name__ == "__main__":
    load_jsons_to_mongo()
