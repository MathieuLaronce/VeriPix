import requests, os, time, json

def run_api_reelle(taxon_id=47144, n=30, out_dir="dataset/reelle"):
    """
    Récupère des images réelles via l'API iNaturalist, les enregistre sur disque
    et exporte les métadonnées en JSON 
    """
    os.makedirs(out_dir, exist_ok=True)
    source = "inaturalist"

    params = {
        "taxon_id": taxon_id,                # 47144=chien 118552=chat
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
            if not url:
                continue
            # URL iNat : remplace 'square' par la taille souhaitée (e.g. 'original' si dispo)
            url = url.replace("square", "large")
            img = requests.get(url, timeout=30).content
            i += 1
            ext = ".jpg"
            with open(os.path.join(out_dir, f"inaturalist_{i}{ext}"), "wb") as f:
                f.write(img)
            print(i, url)
            time.sleep(0.2)
            if i >= n:
                break
        if i >= n:
            break

    # Sauvegarde des métadonnées en JSON 
    meta_dir = "data"
    os.makedirs(meta_dir, exist_ok=True)
    json_path = os.path.join(meta_dir, "inaturalist_meta.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(hits, f, indent=2, ensure_ascii=False)
    print(f"Métadonnées exportées en JSON → {json_path}")

    return {"source": source, "taxon_id": taxon_id, "nb_images": i, "json": json_path}

if __name__ == "__main__":
    run_api_reelle()
