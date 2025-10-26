import requests
from bs4 import BeautifulSoup
import os

# URL à scraper
url = "https://www.artbreeder.com/browse"

# Dossier de destination
save_dir = "dataset/artificielle"
os.makedirs(save_dir, exist_ok=True)

# On récupère le code HTML de la page
response = requests.get(url)
if response.status_code != 200:
    print("❌ Erreur de connexion :", response.status_code)
else:
    # On parse le HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # On cherche toutes les balises <img>
    images = soup.find_all("img class")

    print(f"✅ {len(images)} images trouvées sur la page.")

    # On prend seulement les 20 premières
    for i, img in enumerate(images[:20]):
        src = img.get("src")

        if src and src.startswith("http"):
            try:
                # Télécharger l'image
                img_data = requests.get(src).content
                filename = os.path.join(save_dir, f"image_{i+1}.jpg")
                with open(filename, "wb") as f:
                    f.write(img_data)
                print(f"🖼️  Image {i+1} enregistrée → {filename}")
            except Exception as e:
                print(f"⚠️  Erreur pour {src} : {e}")
        else:
            print(f"⏭️  Image ignorée (URL invalide) : {src}")
