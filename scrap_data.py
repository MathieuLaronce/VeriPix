import requests
from pathlib import Path

url = "https://thispersondoesnotexist.com/"
r = requests.get(url, headers={"User-Agent": "VeriPix/0.1"})
if r.status_code == 200:
    Path("dataset/artificielle").mkdir(parents=True, exist_ok=True)
    with open("dataset/artificielle/tpdne_1.jpg", "wb") as f:
        f.write(r.content)
    print("Image enregistrée")
else:
    print("Erreur :", r.status_code)
