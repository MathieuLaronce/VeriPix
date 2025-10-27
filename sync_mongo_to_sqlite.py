# sync_mongo_to_sqlite.py
import os, time, json, sqlite3
from pymongo import MongoClient

SQLITE_DB = "./data/veripix.db"
MONGO_URI = "mongodb://isen:isen@localhost:27017/admin?authSource=admin"
MONGO_DB  = "veripix"
MONGO_COL = "images_raw"

def _get_source_id(cur: sqlite3.Cursor, source_name: str | None) -> int | None:
    if not source_name:
        return None
    cur.execute("SELECT id_source FROM sources WHERE name = ?", (source_name,))
    row = cur.fetchone()
    return row[0] if row else None

def sync_mongo_to_sqlite(
    mongo_uri: str = MONGO_URI,
    db_name: str = MONGO_DB,
    col_name: str = MONGO_COL,
    sqlite_path: str = SQLITE_DB
):
    client = MongoClient(mongo_uri)
    raw = client[db_name][col_name]

    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()

    # ne prendre que les nouveaux (ou sans status)
    docs = list(raw.find({"status": {"$in": ["new", None]}}))
    print(f"synchroniser depuis Mongo: {len(docs)}")

    inserted = 0
    skipped  = 0
    missing  = 0
    errors   = 0
    prov_ins = 0

    for d in docs:
        path_local = d.get("path_local")
        if not path_local:
            skipped += 1
            raw.update_one({"_id": d["_id"]}, {"$set": {"status": "error", "reason": "no_path_local"}})
            continue

        if not os.path.isfile(path_local):
            missing += 1
            raw.update_one({"_id": d["_id"]}, {"$set": {"status": "missing_file"}})
            continue

        nom_image   = d.get("nom_image") or os.path.basename(path_local)
        type_image  = d.get("type_image") or "reelle"
        source_name = d.get("source") or "unknown"
        source_id   = _get_source_id(cur, source_name)
        fmt         = os.path.splitext(path_local)[1].lstrip(".").upper() or None

        try:
            # 1) IMAGES (upsert par path_local unique)
            cur.execute("""
                INSERT INTO images (nom_image, type_image, source, source_id, path_local, format, date_import)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                nom_image, type_image, source_name, source_id, path_local, fmt,
                time.strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            inserted += 1
            print(f"images: {nom_image}")

            # récupérer id_image
            id_image = cur.lastrowid
            if not id_image:
                cur.execute("SELECT id_image FROM images WHERE path_local = ?", (path_local,))
                row = cur.fetchone()
                id_image = row[0] if row else None

            # 2) PROVENANCE (si id_image trouvé)
            if id_image:
                page_url     = d.get("page_url")
                download_url = d.get("download_url")
                license_code = d.get("license") or d.get("license_code")
                taxon_name   = d.get("taxon_name")
                common_name  = d.get("common_name")
                location     = d.get("location")

                # convertir ObjectId et datetime → str avant json.dumps
                d2 = dict(d)
                if "_id" in d2:
                    d2["_id"] = str(d2["_id"])
                raw_json = json.dumps(d2, ensure_ascii=False, default=str)

                cur.execute("""
                    INSERT INTO provenance
                    (id_image, provider_id, page_url, download_url, license_code, taxon_name, common_name, location, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    id_image,
                    (d.get("extra") or {}).get("observation_id"),
                    page_url, download_url, license_code,
                    taxon_name, common_name, location, raw_json
                ))
                conn.commit()
                prov_ins += 1
                print(f"   ↳ provenance OK (id_image={id_image})")

            # 3) marquer Mongo en synced
            raw.update_one({"_id": d["_id"]}, {"$set": {"status": "synced"}})

        except sqlite3.IntegrityError:
            # déjà présent (path_local unique) -> marquer synced côté Mongo
            skipped += 1
            raw.update_one({"_id": d["_id"]}, {"$set": {"status": "synced"}})
            print(f"déjà présent (images): {nom_image}")
        except Exception as e:
            errors += 1
            raw.update_one({"_id": d["_id"]}, {"$set": {"status": "error", "reason": str(e)}})
            print(f"erreur pour {nom_image} : {e}")

    conn.close()
    client.close()

    summary = {
        "images_inserted": inserted,
        "images_skipped": skipped,
        "missing_files": missing,
        "errors": errors,
        "provenance_inserted": prov_ins,
        "processed": len(docs)
    }
    print(f"Résumé: {summary}")
    return summary

if __name__ == "__main__":
    sync_mongo_to_sqlite()
