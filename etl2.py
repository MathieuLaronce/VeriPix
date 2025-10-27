# etl.py — version débutant

from scrap_artif import run_scrap_artif
from api_reelle3 import run_api_reelle
from json_to_mongo2 import load_jsons_to_mongo
from sync_mongo_to_sqlite import sync_mongo_to_sqlite

# (facultatif) si tu as le fichier transform_features.py
try:
    from transform_features import enrich_images_and_mesures
except ImportError:
    enrich_images_and_mesures = None


def run_etl():
    """
    Pipeline VeriPix (simple) :
      1) Extract  : récupère les images + crée les JSON (scraping + API)
      2) Stage    : charge les JSON dans Mongo
      3) Load     : copie Mongo -> SQLite
      4) Transform: enrichit SQLite (largeur, hauteur, taille_ko, ELA) si dispo
    """
    print("Démarrage ETL")

    try:
        #EXTRACT
        print("[1/4] EXTRACT")
        res_artif = run_scrap_artif(max_images=30)
        print(" - Scraping artificiel OK :", res_artif)

        res_reelle = run_api_reelle(taxon_id=47144, n=30)
        print(" - API iNaturalist OK     :", res_reelle)

        # (JSON -> Mongo)
        print("[2/4] (JSON -> Mongo)")
        res_stage = load_jsons_to_mongo()
        print(" - Chargement Mongo OK    :", res_stage)

        #(Mongo -> SQLite)
        print("[3/4] LOAD (Mongo -> SQLite)")
        res_load = sync_mongo_to_sqlite()
        print(" - Copie vers SQLite OK   :", res_load)

        # 4) TRANSFORM (facultatif)
        print("[4/4] TRANSFORM (features)")
        if enrich_images_and_mesures is not None:
            enrich_images_and_mesures()
            print(" - Enrichissement OK (taille + ELA)")
        else:
            print(" - Enrichissement sauté (module absent)")

        print("ETL terminé avec succès.")

    except Exception as e:
        # Si une étape plante, on affiche l'erreur simplement
        print(" ETL interrompu à cause d'une erreur :", e)


if __name__ == "__main__":
    run_etl()
