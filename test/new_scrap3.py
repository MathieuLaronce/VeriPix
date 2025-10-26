import os, requests
from bs4 import BeautifulSoup

URL = "https://www.artbreeder.com/browse"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# 1. Télécharger le HTML de la page
html = requests.get(URL, headers=HEADERS).text

# 2. Extraire les liens d’images avec BeautifulSoup
soup = BeautifulSoup(html, "html.parser")
imgs = []
for img in soup.find_all("img"):
    src = img.get("src") or img.get("data-src")
    if src and src.startswith("http") and any(src.lower().endswith(ext) for ext in [".jpg",".jpeg",".png"]):
        imgs.append(src)
imgs = list(dict.fromkeys(imgs))[:20]  # enlever doublons et garder 20



# 4. Télécharger les images une par une
for i, url in enumerate(imgs, 1):
    ext = url.split("?")[0].rsplit(".", 1)[-1]
    nom = f"dataset/artificielle/img_{i:02d}.{ext}"
    print(f"Téléchargement de {nom}")
    with open(nom, "wb") as f:
        f.write(requests.get(url, headers=HEADERS).content)

print("Téléchargement terminé dans dataset/artificielle/")
