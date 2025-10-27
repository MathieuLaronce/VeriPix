from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import os
import time

# 🧩 Ajout Mongo
from pymongo import MongoClient
from datetime import datetime

# Connexion MongoDB
client = MongoClient("mongodb://veripix:veripix@localhost:27017/veripix?authSource=veripix")
db = client["veripix"]
raw = db["images_raw"]
raw.create_index("path_local", unique=True)

# Configuration du navigateur
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

source = "artbreeder"
url = "https://www.artbreeder.com/browse"
driver.get(url)

# Scroll pour charger plus d’images
SCROLL_PAUSE_TIME = 2
last_height = driver.execute_script("return document.body.scrollHeight")

for _ in range(5):  # nombre de scrolls
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE_TIME)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Récupération du HTML
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# Dossier de sauvegarde
save_dir = "dataset/artificielle"
os.makedirs(save_dir, exist_ok=True)

# Extraction des images
images = soup.find_all("img")

# Téléchargement des images valides
count = 0
for img in images:
    src = img.get("src")
    if src and src.startswith("http"):
        try:
            img_data = requests.get(src).content
            filename = os.path.join(save_dir, f"image_{count+1}.jpg")
            with open(filename, "wb") as f:
                f.write(img_data)
            count += 1

            # 🧩 Ajout Mongo : enregistre la provenance de chaque image
            doc = {
                "path_local": os.path.abspath(filename),
                "nom_image": os.path.basename(filename),
                "type_image": "artificielle",
                "source": "artbreeder",
                "page_url": url,
                "download_url": src,
                "collected_at": datetime.utcnow(),
                "status": "new"
            }
            try:
                raw.insert_one(doc)
                print(f"🟢 Image ajoutée dans Mongo : {filename}")
            except Exception as e:
                if "duplicate key" in str(e):
                    print(f"⏭️ Déjà présente dans Mongo : {filename}")
                else:
                    print(f"⚠️ Erreur Mongo pour {filename} : {e}")

            if count >= 30:
                break
        except:
            continue  # ignore les erreurs sans afficher

print(f"{count} images enregistrées dans '{save_dir}'.")
