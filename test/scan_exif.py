# pip install pillow exifread
from PIL import Image, ExifTags
import exifread
import os

image_path = "dataset/reelle/inaturalist_1.jpg"

def print_kv(d):
    for k, v in d.items():
        print(f"{k}: {v}")

def read_with_pillow(path):
    img = Image.open(path)
    print(f"Format détecté: {img.format}, taille: {img.size}, mode: {img.mode}")
    exif = img.getexif() 
    if not exif or len(exif) == 0:
        return {}
    out = {}
    for tag_id, value in exif.items():
        tag = ExifTags.TAGS.get(tag_id, tag_id)
        out[tag] = value
    return out

def read_with_exifread(path):
    with open(path, "rb") as f:
        tags = exifread.process_file(f, details=False)
    # exifread retourne un dict avec des clés "Image Make", "EXIF DateTimeOriginal", etc.
    return {k: str(v) for k, v in tags.items()}

def read_png_info(path):
    # Pour PNG/WebP, Pillow expose parfois des infos dans image.info (pas EXIF)
    img = Image.open(path)
    return img.info  # dictionnaire 

if not os.path.exists(image_path):
    print(" Le chemin ne pointe pas vers un fichier existant.")
else:
    # 1) Tentative Pillow EXIF
    try:
        pil_exif = read_with_pillow(image_path)
        if pil_exif:
            print(" EXIF trouvées avec Pillow:")
            print_kv(pil_exif)
        else:
            print("ℹAucune EXIF via Pillow essaie exifread...")
            # 2) Tentative exifread (souvent plus verbeux sur JPEG/TIFF)
            exifr = read_with_exifread(image_path)
            if exifr:
                print("EXIF trouvées avec exifread:")
                print_kv(exifr)
            else:
                # 3) Si c'est un PNG/WebP, on regarde les infos non-EXIF
                img = Image.open(image_path)
                if img.format in ("PNG", "WEBP"):
                    info = read_png_info(image_path)
                    if info:
                        print("ℹPas d’EXIF (normal pour PNG/WebP), infos du fichier:")
                        print_kv(info)
                    else:
                        print("Aucun EXIF/infos utiles trouvés (format PNG/WebP ou fichier nettoyé).")
                else:
                    print("Aucun EXIF trouvés. Possible que l’image ait été nettoyée (réseaux sociaux, export).")
    except Exception as e:
        print(f"Erreur lecture: {e}")
