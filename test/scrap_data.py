import requests
from pathlib import Path
import time

Path("dataset/artificielle").mkdir(parents=True, exist_ok=True)

for i in range(1, 21):  # 20 images
    url = "https://thispersondoesnotexist.com/"
    r = requests.get(url, headers={"User-Agent": "VeriPix/0.1"})
    if r.status_code == 200:
        with open(f"dataset/artificielle/tpdne_{i}.jpg", "wb") as f:
            f.write(r.content)
        print(f" Image {i} enregistrée")
    else:
        print(f"Erreur {r.status_code} sur l'image {i}")
    time.sleep(3)  # pause d'une seconde entre chaque téléchargement
