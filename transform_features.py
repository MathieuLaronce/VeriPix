import os, time, sqlite3
from PIL import Image, ImageChops
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

DB = "./data/veripix.db"


# Utilitaires

def has_exif_pillow(path: str) -> bool:
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            return bool(exif and len(exif) > 0)
    except Exception:
        return False

def _open_rgb_resized(path: str, max_side: int = 1024) -> Image.Image:
    """Ouvre en RGB et limite le plus grand côté pour stabiliser les scores."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    if max(w, h) > max_side:
        if w >= h:
            new_w = max_side
            new_h = int(h * (max_side / w))
        else:
            new_h = max_side
            new_w = int(w * (max_side / h))
        im = im.resize((new_w, new_h), Image.LANCZOS)
    return im

def to_rgb_array(path: str, max_side: int = 1024) -> np.ndarray:
    """Retourne un array float32 HxWx3, redimensionné."""
    im = _open_rgb_resized(path, max_side=max_side)
    return np.asarray(im, dtype=np.float32)

def ela_p99_robust(path: str, base_quality: int = 98, test_quality: int = 85, max_side: int = 1024) -> float:
    """
  
    1) Normalise l'image (RGB + resize)
    2) Sauvegarde une base JPG (qualité haute)
    3) Re-sauvegarde la base en JPG (qualité plus basse)
    4) ELA = percentile 99 de la différence (en niveaux de gris)
    """
    base_tmp = path + ".ela_base.jpg"
    test_tmp = path + ".ela_test.jpg"
    try:
        base = _open_rgb_resized(path, max_side=max_side)
        base.save(base_tmp, "JPEG", quality=base_quality)

        with Image.open(base_tmp).convert("RGB") as base2:
            base2.save(test_tmp, "JPEG", quality=test_quality)

        with Image.open(base_tmp).convert("RGB") as a, Image.open(test_tmp).convert("RGB") as b:
            diff = ImageChops.difference(a, b).convert("L")

        arr = np.array(diff, dtype=np.uint8).ravel()
        if arr.size == 0:
            return 0.0
        return float(np.percentile(arr, 99))
    except Exception:
        return 0.0
    finally:
        for tmp in (base_tmp, test_tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass

def laplacian_variance_gray(arr_rgb: np.ndarray) -> float:
    """Variance du Laplacien (netteté) sur une version niveau de gris."""
    gray = 0.2989*arr_rgb[...,0] + 0.5870*arr_rgb[...,1] + 0.1140*arr_rgb[...,2]
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    kern = np.array([[0, 1, 0],
                     [1,-4, 1],
                     [0, 1, 0]], dtype=np.float32)
    win = sliding_window_view(gray, (3,3))
    conv = (win * kern).sum(axis=(2,3))
    return float(conv.var())

def edge_density_sobel(arr_rgb: np.ndarray, thresh: float = 25.0) -> float:
    """Densité de bords via Sobel, proportion de pixels > seuil."""
    gray = 0.2989*arr_rgb[...,0] + 0.5870*arr_rgb[...,1] + 0.1140*arr_rgb[...,2]
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    kx = np.array([[-1,0,1],[-2,0,2],[-1,0,1]], dtype=np.float32)
    ky = np.array([[-1,-2,-1],[0,0,0],[1,2,1]], dtype=np.float32)
    win = sliding_window_view(gray, (3,3))
    gx = (win * kx).sum(axis=(2,3))
    gy = (win * ky).sum(axis=(2,3))
    mag = np.hypot(gx, gy)
    return float((mag > thresh).mean())


# Enrichissement BDD

def enrich_images_and_mesures():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # 1) Compléter largeur/hauteur/taille_ko/has_exif si NULL
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
            """, 
            (w, h, taille_ko, exif_flag, id_image))
            info_updated += 1
        except Exception as e:
            print(f"MAJ infos échouée id_image={id_image} : {e}")

    if info_updated:
        conn.commit()
        print(f"Infos mises à jour pour {info_updated} image(s).")
    else:
        print("Aucune info à compléter.")

    # 2) Calcul features & upsert mesures
    cur.execute("SELECT id_image, path_local FROM images")
    todo = cur.fetchall()

    ins = upd = 0
    for id_image, path in todo:
        if not path or not os.path.isfile(path):
            continue
        try:
            base = os.path.basename(path)
            if base.endswith(".resaved.jpg") or base.endswith(".ela.png") \
               or base.endswith(".ela_base.jpg") or base.endswith(".ela_test.jpg"):
                continue

            # ELA
            ela_raw = ela_p99_robust(path, base_quality=98, test_quality=85, max_side=1024)
            ela     = round(ela_raw, 4)

            # RGB array (pour les autres features)
            arr   = to_rgb_array(path, max_side=1024)
            mean_r = round(float(arr[...,0].mean()), 4)
            mean_g = round(float(arr[...,1].mean()), 4)
            mean_b = round(float(arr[...,2].mean()), 4)
            lapv   = round(laplacian_variance_gray(arr), 4)
            edens  = round(edge_density_sobel(arr, thresh=25.0), 4)

            cur.execute("SELECT 1 FROM mesures WHERE id_image=?", (id_image,))
            exists = cur.fetchone() is not None

            if exists:
                cur.execute("""
                    UPDATE mesures
                    SET ela_score=?, laplacian_var=?, edge_density=?,
                        mean_r=?, mean_g=?, mean_b=?, date_analyse=?
                    WHERE id_image=?
                """, (ela, lapv, edens, mean_r, mean_g, mean_b,
                      time.strftime("%Y-%m-%d %H:%M:%S"), id_image))
                upd += 1
            else:
                cur.execute("""
                    INSERT INTO mesures
                    (id_image, ela_score, laplacian_var, edge_density,
                     mean_r, mean_g, mean_b, date_analyse)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (id_image, ela, lapv, edens, mean_r, mean_g, mean_b,
                      time.strftime("%Y-%m-%d %H:%M:%S")))
                ins += 1

        except Exception as e:
            print(f"Features échoués id_image={id_image} : {e}")

    conn.commit()
    conn.close()

    print(f"mesures: insérés={ins}, mis à jour={upd}")
    return {"images_info_updated": info_updated, "mesures_inserted": ins, "mesures_updated": upd}

if __name__ == "__main__":
    print("chargemenrt en cours")
    res = enrich_images_and_mesures()
    print("Terminé :", res)
