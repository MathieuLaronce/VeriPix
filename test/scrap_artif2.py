from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
import requests, time, os



#Options Firefox (mode sans interface graphique)
options = webdriver.FirefoxOptions()
options.add_argument("--headless")  # pas de fenêtre visible
options.add_argument("--width=1920")
options.add_argument("--height=1080")

# 🚀 Lancer Firefox automatiquement (Geckodriver se télécharge tout seul)
driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

try:
    print("Ouverture de la page...")
    driver.get("https://www.artbreeder.com/browse")
    time.sleep(5)  # ⏳ attendre que la page se charge

    print("🔍 Récupération des images...")
    imgs = driver.find_elements(By.TAG_NAME, "img")

    # 🖼️ Télécharger les 20 premières images visibles
    for i, img in enumerate(imgs[:20]):
        src = img.get_attribute("src")
        if src and src.startswith("http"):
            img_data = requests.get(src).content
            with open(f"dataset/artificielle/image_{i+1}.jpg", "wb") as f:
                f.write(img_data)
            print(f"✅ image_{i+1}.jpg téléchargée")

finally:
    driver.quit()
    print("🧹 Fermeture du navigateur.")
