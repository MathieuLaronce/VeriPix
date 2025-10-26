from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import os
import time

# Configuration du navigateur
options = Options()
options.add_argument("--headless")  # Mode sans interface
driver = webdriver.Chrome(options=options)

# URL cible
url = "https://www.artbreeder.com/browse"
driver.get(url)

# Attendre le chargement des images
time.sleep(5)

# Récupérer le HTML après chargement JS
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# Créer le dossier de sauvegarde
save_dir = "dataset/artificielle"

# Extraire les images
images = soup.find_all("img")
print(f"{len(images)} images trouvées.")

# Télécharger les 20 premières
for i, img in enumerate(images[:25]):
    src = img.get("src")
    if src and src.startswith("http"):
        try:
            img_data = requests.get(src).content
            filename = os.path.join(save_dir, f"image_{i+1}.jpg")
            with open(filename, "wb") as f:
                f.write(img_data)
            print(f"Image {i+1} enregistrée → {filename}")
        except Exception as e:
            print(f"Erreur pour {src} : {e}")
    else:
        print(f"Image ignorée (URL invalide) : {src}")