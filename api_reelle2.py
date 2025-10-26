import requests, os, time

TAXON_ID = 47144   # 47144=chien, 118552=chat
N = 30
OUT = "dataset/reelle"; os.makedirs(OUT, exist_ok=True)
source = "inaturalist"


params = {
    "taxon_id": TAXON_ID,
    "photos": "true",
    "photo_licenses": "cc0,cc-by,cc-by-sa",
    "per_page": 50,
    "order": "desc", "order_by": "created_at"
}
r = requests.get("https://api.inaturalist.org/v1/observations", params=params, timeout=30)
r.raise_for_status()
hits = r.json().get("results", [])

i = 0
for obs in hits:
    for p in obs.get("photos", []):
        url = p.get("url") or p.get("medium_url") or p.get("large_url")
        if not url: continue
        # URL iNat : remplace 'square' par la taille souhaitée (e.g. 'original' si dispo)
        url = url.replace("square", "large")
        img = requests.get(url, timeout=30).content
        i += 1
        ext = ".jpg"
        with open(os.path.join(OUT, f"inaturalist_{i}{ext}"), "wb") as f:
            f.write(img)
        print(i, url)
        time.sleep(0.2)
        if i >= N: break
    if i >= N: break
