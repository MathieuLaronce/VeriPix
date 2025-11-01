from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import os
import time
import json
from urllib.parse import urljoin


def run_scrap_artif(max_images=30):
    """Scrappe Artbreeder et enregistre les images + métadonnées JSON"""
    # Configuration du navigateur
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    source = "artbreeder"
    url = "https://www.artbreeder.com/browse"
    driver.get(url)
    time.sleep(3)  # laisse le temps à la page de charger

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
    print(f"Trouvé {len(images)} balises <img> sur la page.")

    # Téléchargement + collecte métadonnées
    count = 0
    meta = []
    headers = {"User-Agent": "VeriPix/0.1 (edu)"}

    for img in images:
        src = img.get("src") or img.get("data-src") or img.get("srcset")
        if not src:
            continue

        # Si srcset contient plusieurs URL, garde la première
        if "," in src:
            src = src.split(",")[0].strip().split(" ")[0]

        # Ignore les data URI
        if src.startswith("data:"):
            continue

        # Convertit les liens relatifs en absolus
        download_url = urljoin(url, src)

        try:
            r = requests.get(download_url, headers=headers, timeout=15, stream=True)
            ct = r.headers.get("Content-Type", "")
            if r.status_code != 200 or "image" not in ct:
                continue

            # Extension à partir du type MIME
            ext = ".jpg" if "jpeg" in ct else (".png" if "png" in ct else ".jpg")
            filename = os.path.join(save_dir, f"artbreeder_{count+1}{ext}")

            # Sauvegarde du fichier
            with open(filename, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)

            # Ajout des métadonnées
            meta.append({
                "nom_image": f"artbreeder_{count+1}{ext}",
                "path_local": os.path.abspath(filename),
                "type_image": "artificielle",
                "source": source,
                "page_url": url,
                "download_url": download_url,
                "mime": ct,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })

            count += 1
            print(f"Image {count} enregistrée : {filename}")
            if count >= max_images:
                break
        except Exception as e:
            print(f"Erreur téléchargement {src} : {e}")
            continue

    print(f"{count} images enregistrées dans '{save_dir}'.")

    # --- Sauvegarde des métadonnées en JSON ---
    meta_dir = "data"
    os.makedirs(meta_dir, exist_ok=True)

    json_path = os.path.join(meta_dir, "artbreeder_meta.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"Métadonnées exportées → {json_path}")

    # Retour pour l'ETL
    return {"source": source, "nb_images": count, "json": json_path}



if __name__ == "__main__":
    run_scrap_artif()
