from scrap_artif import run_scrap_artif
from api_reelle3 import run_api_reelle
from json_to_mongo2 import load_jsons_to_mongo
from sync_mongo_to_sqlite import sync_mongo_to_sqlite
from transform_features import enrich_images_and_mesures


def run_etl():
    print("=== ETL VeriPix ===")

    # 1) EXTRACT
    print("[1/4] EXTRACT — scraping artificiel…")
    run_scrap_artif(max_images=30)

    print("[1/4] EXTRACT — API iNaturalist…")
    run_api_reelle(taxon_id=47144, n=30)

    # 2) STAGE (JSON -> Mongo)
    print("[2/4] STAGE — JSON -> Mongo…")
    stage_summary = load_jsons_to_mongo()
    print("  STAGE résumé:", stage_summary)

    # 3) LOAD (Mongo -> SQLite)
    print("[3/4] LOAD — Mongo -> SQLite…")
    load_summary = sync_mongo_to_sqlite()
    print("  LOAD résumé:", load_summary)

    # 4) TRANSFORM (features)
    print("[4/4] TRANSFORM — features…")
    if enrich_images_and_mesures is not None:
        tf_summary = enrich_images_and_mesures()
        print("  TRANSFORM résumé:", tf_summary)
    else:
        print("  transform_features.py absent — étape sautée")

    print("=== ETL terminé ===")


if __name__ == "__main__":
    run_etl()
