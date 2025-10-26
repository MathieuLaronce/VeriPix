from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import os
import time

# Configuration du navigateur
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

# URL cible
url = "https://www.artbreeder.com/browse"
driver.get(url)

# Scroll pour charger plus d'images
SCROLL_PAUSE_TIME = 2
last_height = driver.execute_script("return document.body.scrollHeight")

for _ in range(5):  # nombre de scrolls
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE_TIME)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height
# Récupérer le HTML après chargement JS
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# Créer le dossier de sauvegarde
save_dir = "dataset/artificielle"


# Extraire les images
images = soup.find_all("img")
print(f"{len(images)} images trouvées.")

# Télécharger les 25 premières valides
count = 0
for img in images:
    src = img.get("src")
    if src and src.startswith("http"):
        try:
            img_data = requests.get(src).content
            filename = os.path.join(save_dir, f"image_{count+1}.jpg")
            with open(filename, "wb") as f:
                f.write(img_data)
            print(f"Image {count+1} enregistrée → {filename}")
            count += 1
            if count >= 25:
                break
        except Exception as e:
            print(f"Erreur pour {src} : {e}")
    else:
        print(f"Image ignorée (URL invalide) : {src}")