import os, time, json, sqlite3
from pymongo import MongoClient

SQLITE_DB = "./data/veripix.db"
MONGO_URI = "mongodb://isen:isen@localhost:27017/admin?authSource=admin"
MONGO_DB  = "veripix"
MONGO_COL = "images_raw"

def sync_mongo_to_sqlite(
    mongo_uri=MONGO_URI,
    db_name=MONGO_DB,
    col_name=MONGO_COL,
    sqlite_path=SQLITE_DB
):
    client = MongoClient(mongo_uri)
    col = client[db_name][col_name]

    con = sqlite3.connect(sqlite_path)
    cur = con.cursor()

    # je ne veut que ce qui n'est PAS encore "synced"
    docs = list(col.find({"$or":[{"status":"new"},{"status":{"$exists":False}}]}))
    print("a synchroniser:", len(docs))

    ins = 0
    skip = 0
    prov_ok = 0
    err = 0

    for d in docs:
        path_local = d.get("path_local")
        if not path_local:
            print("pas de path_local -> skip")
            skip += 1
            # ne pas changer le statut
            continue

        if not os.path.isfile(path_local):
            print("fichier manquant -> skip:", path_local)
            skip += 1
            # pareil on laisse "new"
            continue

        nom_image   = d.get("nom_image") or os.path.basename(path_local)
        type_image  = d.get("type_image") or "reelle"
        source_name = d.get("source") or "unknown"

        # source_id 
        try:
            cur.execute("SELECT id_source FROM sources WHERE name = ?", (source_name,))
            row = cur.fetchone()
            source_id = row[0] if row else None
        except:
            source_id = None

        fmt = os.path.splitext(path_local)[1].replace(".","").upper() or None
        
        
        
        try:
              date_import = time.ctime() 
              cur.execute("INSERT INTO images (nom_image, type_image, source, source_id, path_local, format, date_import) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (nom_image, type_image, source_name, source_id, path_local, fmt, date_import))
              con.commit()
              ins += 1
              print("image inseree:", nom_image)
              
              
              id_image = cur.lastrowid
              if not id_image:
                cur.execute("SELECT id_image FROM images WHERE path_local = ?", (path_local,))
                r2 = cur.fetchone()
                id_image = r2[0] if r2 else None

            # PROVENANCE 
              if id_image:
                page_url     = d.get("page_url")
                download_url = d.get("download_url")
                license_code = d.get("license") or d.get("license_code")
                location     = d.get("localisation") or d.get("location")
                provider_id  = (d.get("extra") or {}).get("observation_id")

                cur.execute(
                    "INSERT INTO provenance (id_image, provider_id, page_url, download_url, license_code, localisation) VALUES (?, ?, ?, ?, ?, ?)",
                    (id_image, provider_id, page_url, download_url, license_code, location)
                )
                con.commit()
                prov_ok += 1
                print("  -> provenance ok (id_image={})".format(id_image))

            # je ne veut que "synced" 
              col.update_one({"_id": d["_id"]}, {"$set": {"status": "synced"}})
        except sqlite3.IntegrityError:
            # deja là on marque synced quand meme
            skip += 1
            print("deja là, on marque synced:", nom_image)
            col.update_one({"_id": d["_id"]}, {"$set": {"status": "synced"}})
        except Exception as e:
            err += 1
            print("erreur:", e)
            

    con.close()
    client.close()

    resume = {
        "inserted": ins,
        "skipped": skip,
        "provenance_ok": prov_ok,
        "errors": err,
        "processed": len(docs)
    }
    print("resume:", resume)
    return resume

if __name__ == "__main__":
    sync_mongo_to_sqlite()
