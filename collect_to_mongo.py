# collect_to_mongo.py
"""
Ajoute automatiquement dans MongoDB les infos des images collectées
depuis les dossiers dataset/reelle et dataset/artificielle.
"""

from pymongo import MongoClient
from datetime import datetime
import os

#Connexion Mongo
client = MongoClient("mongodb://isen:isen@localhost:27017/admin?authSource=admin")
db = client["veripix"]                # base Mongo
raw = db["images_raw"]                # collection
raw.create_index("path_local", unique=True)  # évite les doublons

#Dossiers à explorer
folders = {
    "reelle": "dataset/reelle",
    "artificielle": "dataset/artificielle"
}

def collect_images():
    total = 0
    for type_image, folder in folders.items():
        if not os.path.exists(folder):
            print(f"Dossier introuvable : {folder}")
            continue

        print(f"Scan du dossier : {folder}")
        for file in os.listdir(folder):
            if not file.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            path = os.path.abspath(os.path.join(folder, file))

            doc = {
                "path_local": path,
                "nom_image": file,
                "type_image": type_image,
                "source": "wikimedia" if type_image == "reelle" else "thispersondoesnotexist",
                "collected_at": datetime.utcnow(),
                "status": "new"
            }

            try:
                raw.insert_one(doc)
                total += 1
                print(f"Ajouté dans Mongo : {file}")
            except Exception as e:
                if "duplicate key error" in str(e):
                    print(f"⏭Déjà présent : {file}")
                else:
                    print(f"Erreur insertion {file} : {e}")

    print(f"Total inséré : {total}")
    print("Collecte Mongo terminée.")

if __name__ == "__main__":
    collect_images()
