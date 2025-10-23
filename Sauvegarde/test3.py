import os
from PIL import Image, ImageChops, ImageEnhance

def ela_score(path, quality=85):
    try:
        im = Image.open(path).convert("RGB").resize((512, 512))
        tmp = "tmp_ela.jpg"
        im.save(tmp, "JPEG", quality=quality)

        recompressed = Image.open(tmp)
        diff = ImageChops.difference(im, recompressed)
        diff = ImageEnhance.Brightness(diff).enhance(10)

        hist = diff.convert("L").histogram()
        total = sum(i * v for i, v in enumerate(hist))
        count = sum(hist)
        avg = total / max(count, 1)

        os.remove(tmp)
        return avg
    except Exception as e:
        print(f" Erreur sur {path}: {e}")
        return None


def analyze_folder(folder_path):
    print(f"\n🔍 Analyse du dossier : {folder_path}")
    if not os.path.exists(folder_path):
        print("Dossier introuvable.")
        return

    results = []
    for file in os.listdir(folder_path):
        if file.lower().endswith((".jpg", ".jpeg", ".png")):
            img_path = os.path.join(folder_path, file)
            score = ela_score(img_path)
            if score is not None:
                results.append((file, score))
                print(f"✅ {file:30s} → ELA: {score:.3f}")

    # Résumé
    if results:
        avg_score = sum(s for _, s in results) / len(results)
        print("\n Résumé :")
        print(f"  Nombre d'images analysées : {len(results)}")
        print(f"  Moyenne ELA globale : {avg_score:.3f}")
    else:
        print("" Aucune image valide trouvée.")


# Exemple : modifie ces deux lignes selon ton dossier
folder = "/home/mathieu/iadev/veripix/dataset/reelle"
analyze_folder(folder)
