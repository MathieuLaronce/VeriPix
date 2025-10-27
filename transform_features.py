# transform_features.py (seules les parties ELA changent)
import os, time, sqlite3
from PIL import Image, ExifTags, ImageChops  # Brightness inutile ici
import numpy as np

DB = "./data/veripix.db"

def has_exif_pillow(path: str) -> bool:
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            return bool(exif and len(exif) > 0)
    except Exception:
        return False

def _open_rgb_resized(path: str, max_side: int = 1024) -> Image.Image:
    """Ouvre l'image en RGB et limite le plus grand côté à max_side pour stabiliser le score."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    if max(w, h) > max_side:
        # conserve le ratio
        if w >= h:
            new_w = max_side
            new_h = int(h * (max_side / w))
        else:
            new_h = max_side
            new_w = int(w * (max_side / h))
        im = im.resize((new_w, new_h), Image.LANCZOS)
    return im

def ela_p99_robust(path: str, base_quality: int = 98, test_quality: int = 85, max_side: int = 1024) -> float:
    """
    ELA robuste (normalisé) :
    1) ouvre l'image en RGB + redimensionne (max_side)
    2) sauvegarde une BASE commune en JPEG(base_quality)
    3) re-sauvegarde cette BASE en JPEG(test_quality)
    4) ELA = P99(diff(BASE, RESAVED))
    -> réduit la dépendance à la compression/format d'origine.
    """
    base_tmp = path + ".ela_base.jpg"
    test_tmp = path + ".ela_test.jpg"
    try:
        base = _open_rgb_resized(path, max_side=max_side)
        base.save(base_tmp, "JPEG", quality=base_quality)

        # on repart de la base normalisée (pas de l'original)
        with Image.open(base_tmp).convert("RGB") as base2:
            base2.save(test_tmp, "JPEG", quality=test_quality)

        with Image.open(base_tmp).convert("RGB") as a, Image.open(test_tmp).convert("RGB") as b:
            diff = ImageChops.difference(a, b).convert("L")

        arr = np.array(diff, dtype=np.uint8).ravel()
        if arr.size == 0:
            return 0.0
        return float(np.percentile(arr, 99))  # P99 stable
    except Exception:
        return 0.0
    finally:
        # nettoyage fichiers temporaires
        for tmp in (base_tmp, test_tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass

def enrich_images_and_mesures():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # 1) Compléter largeur/hauteur/taille_ko/has_exif si NULL (inchangé)
    cur.execute("""
        SELECT id_image, path_local
        FROM images
        WHERE largeur IS NULL OR hauteur IS NULL OR taille_ko IS NULL OR has_exif IS NULL
    """)
    rows = cur.fetchall()

    info_updated = 0
    for id_image, path in rows:
        if not path or not os.path.isfile(path):
            continue
        try:
            with Image.open(path) as im:
                w, h = im.size
            taille_ko = round(os.path.getsize(path) / 1024.0, 2)
            exif_flag = 1 if has_exif_pillow(path) else 0

            cur.execute("""
                UPDATE images
                SET largeur=?, hauteur=?, taille_ko=?, has_exif=?
                WHERE id_image=?
            """, (w, h, taille_ko, exif_flag, id_image))
            info_updated += 1
        except Exception as e:
            print(f"⚠️ MAJ infos échouée id_image={id_image} : {e}")

    if info_updated:
        conn.commit()
        print(f"📐 Infos mises à jour pour {info_updated} image(s).")
    else:
        print("📐 Aucune info à compléter.")

    # 2) ELA normalisé (P99 entre BASE98 et TEST85) -> upsert mesures
    cur.execute("SELECT id_image, path_local FROM images")
    todo = cur.fetchall()

    ela_inserted = 0
    ela_updated  = 0
    for id_image, path in todo:
        if not path or not os.path.isfile(path):
            continue
        try:
            base = os.path.basename(path)
            if base.endswith(".resaved.jpg") or base.endswith(".ela.png") or base.endswith(".ela_base.jpg") or base.endswith(".ela_test.jpg"):
                continue

            score = ela_p99_robust(path, base_quality=98, test_quality=85, max_side=1024)

            cur.execute("SELECT 1 FROM mesures WHERE id_image=?", (id_image,))
            exists = cur.fetchone() is not None

            if exists:
                cur.execute("""
                    UPDATE mesures SET ela_score=?, date_analyse=?
                    WHERE id_image=?
                """, (score, time.strftime("%Y-%m-%d %H:%M:%S"), id_image))
                ela_updated += 1
            else:
                cur.execute("""
                    INSERT INTO mesures (id_image, ela_score, date_analyse)
                    VALUES (?, ?, ?)
                """, (id_image, score, time.strftime("%Y-%m-%d %H:%M:%S")))
                ela_inserted += 1

        except Exception as e:
            print(f"⚠️ ELA échoué id_image={id_image} : {e}")

    conn.commit()
    conn.close()

    print(f"✨ ELA(normalisé P99) insérés: {ela_inserted}, mis à jour: {ela_updated}")
    return {"images_updated": info_updated, "ela_inserted": ela_inserted, "ela_updated": ela_updated}

if __name__ == "__main__":
    print("🔧 Enrichissement en cours…")
    res = enrich_images_and_mesures()
    print("✅ Terminé :", res)
