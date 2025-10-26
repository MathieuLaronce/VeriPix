import os
import requests
import time

# Paramètres simples
CATEGORY = "Featured_pictures_of_dogs"  # categorie 
N_IMAGES = 10
OUT_DIR = "dataset/reelle"
os.makedirs(OUT_DIR, exist_ok=True)

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "VeriPix/0.1 (edu)"}

# Récupère des liens d'images
params = {
    "action": "query",
    "format": "json",
    "generator": "categorymembers",
    "gcmtitle": f"Category:{CATEGORY}",
    "gcmnamespace": 6,           
    "gcmlimit": N_IMAGES,        
    "prop": "imageinfo",
    "iiprop": "url",
    "formatversion": 2
}

print("Récupération des liens")
r = requests.get(API, params=params, headers=HEADERS, timeout=30)
data = r.json()  

pages = (data.get("query") or {}).get("pages") or []
urls = [p["imageinfo"][0]["url"] for p in pages if p.get("imageinfo")]

print(f"Téléchargement de {len(urls)} images...")
for i, url in enumerate(urls, 1):
    img = requests.get(url, headers=HEADERS, timeout=30).content
    # extension simple
    ext = ".jpg"
    low = url.lower()
    if ".png" in low: ext = ".png"
    elif ".jpeg" in low: ext = ".jpeg"
    elif ".svg" in low: 
        print(f"⏭  SVG ignoré: {url}")
        continue

    path = os.path.join(OUT_DIR, f"wikimedia_{i}{ext}")
    with open(path, "wb") as f:
        f.write(img)
    print(f" {path}")
    time.sleep(0.5)

print("Terminé.")
