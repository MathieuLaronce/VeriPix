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
            if count >= 30:
                break
        except:
            continue  # ignore les erreurs sans afficher
print(f"{count} images enregistrées dans '{save_dir}'.")