from PIL import Image, ImageChops, ImageEnhance
import os, sqlite3, time

path = "/home/mathieu/iadev/veripix/dataset/reelle" and "/home/mathieu/iadev/veripix/dataset/artificielle"

DB_PATH = "./data/veripix.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Boucle sur toutes les images du dossier
for filename in os.listdir(path):

    # ignore les fichiers temporaires créés par ELA
    if filename.endswith(".resaved.jpg") or filename.endswith(".ela.png"):
        continue

    # on garde uniquement les vrais formats d’image
    if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    filepath = os.path.join(path, filename)
    print("\n➡ Traitement de :", filepath)

    resaved = filepath + '.resaved.jpg'
    ela = filepath + '.ela.png'

    im = Image.open(filepath).convert("RGB")
    im.save(resaved, 'JPEG', quality=95)
    resaved_im = Image.open(resaved)

    ela_im = ImageChops.difference(im, resaved_im)
    extrema = ela_im.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    scale = 255.0 / max_diff if max_diff else 1
    ela_im = ImageEnhance.Brightness(ela_im).enhance(scale)

    print("Maximum difference was", max_diff)

    # --- Enregistre le score dans la BDD ---
    filename_abs = os.path.abspath(filepath)
    basename = os.path.basename(filepath)

    cur.execute("""
        SELECT id_image FROM images
        WHERE path_local = ? OR path_local = ? OR nom_image = ?
        LIMIT 1
    """, (filename_abs, filepath, basename))
    row = cur.fetchone()

    if row:
        id_image = row[0]
        cur.execute("SELECT 1 FROM mesures WHERE id_image = ?", (id_image,))
        if cur.fetchone():
            cur.execute(
                "UPDATE mesures SET ela_score=?, date_analyse=? WHERE id_image=?",
                (float(max_diff), time.strftime("%Y-%m-%d %H:%M:%S"), id_image)
            )
        else:
            cur.execute(
                "INSERT INTO mesures (id_image, ela_score, date_analyse) VALUES (?, ?, ?)",
                (id_image, float(max_diff), time.strftime("%Y-%m-%d %H:%M:%S"))
            )
        print(f"ELA enregistré pour id_image={id_image}")
    else:
        print("Image non trouvée dans 'images' (penses à lancer scan_to_db.py).")

    try:
        os.remove(resaved)  # nettoie les fichiers temporaires
    except OSError:
        pass

conn.commit()
conn.close()
print("scores ELA enregistrés.")
