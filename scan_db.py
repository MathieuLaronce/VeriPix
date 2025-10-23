import os, time, sqlite3
from PIL import Image

DB = "./data/veripix.db"
DATASET = "./dataset"  # avec ./dataset/reelle et ./dataset/artificielle

def has_exif(path):
    try:
        im = Image.open(path)
        return bool(im.getexif())
    except Exception:
        return False

def info_image(path):
    try:
        im = Image.open(path)
        w, h = im.size
        fmt = im.format or "UNK"
        size_ko = os.path.getsize(path) / 1024.0
        return fmt, w, h, size_ko
    except Exception:
        return None

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    for t in ("reelle", "artificielle"):
        folder = os.path.join(DATASET, t)
        if not os.path.isdir(folder):
            continue
        for name in os.listdir(folder):
            if not name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            path = os.path.join(folder, name)

            # évite les doublons grâce à path_local UNIQUE
            cur.execute("SELECT 1 FROM images WHERE path_local = ?", (path,))
            if cur.fetchone():
                continue

            info = info_image(path)
            if not info:
                print("Image illisible :", path)
                continue
            fmt, w, h, size_ko = info
            cur.execute("""
                INSERT INTO images(nom_image, type_image, source, path_local, format,
                                   largeur, hauteur, taille_ko, has_exif, date_import)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, t, "local", path, fmt, w, h, size_ko,
                1 if has_exif(path) else 0,
                time.strftime("%Y-%m-%d %H:%M:%S")
            ))
            print("indexée :", path)

    conn.commit()
    conn.close()
    print("Scan terminé")

if __name__ == "__main__":
    main()
