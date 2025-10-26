from PIL import Image, ImageChops, ImageEnhance
import os, sqlite3, time


path = "/home/mathieu/iadev/veripix/dataset/reelle"

# Boucle sur toutes les images du dossier
for filename in os.listdir(path):
    if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    filepath = os.path.join(path, filename)
    print("\n➡ Traitement de :", filepath)

    resaved = filepath + '.resaved.jpg'
    ela = filepath + '.ela.png'

    im = Image.open(filepath)
    im.save(resaved, 'JPEG', quality=95)
    resaved_im = Image.open(resaved)

    ela_im = ImageChops.difference(im, resaved_im)
    extrema = ela_im.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    scale = 255.0 / max_diff if max_diff else 1
    ela_im = ImageEnhance.Brightness(ela_im).enhance(scale)

    print("Maximum difference was", max_diff)

    # Enregistre dans la bdd
    DB_PATH = "./data/veripix.db"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id_image FROM images WHERE path_local = ?", (filepath,))
    row = cur.fetchone()
    if row:
        id_image = row[0]
        cur.execute("UPDATE mesures SET ela_score=?, date_analyse=? WHERE id_image=?",
                    (float(max_diff), time.strftime("%Y-%m-%d %H:%M:%S"), id_image))
        conn.commit()
        print(f"Score ELA enregistré pour {id_image}")
    conn.close()
