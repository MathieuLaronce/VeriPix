from PIL import Image, ImageChops, ImageEnhance

def ela_score(path, quality=85):
    im = Image.open(path).convert("RGB").resize((1024, 1024))

    tmp = "/home/mathieu/iadev/veripix/dataset/tmp_ela3.jpg"
    im.save(tmp, "JPEG", quality=quality)
    recompressed = Image.open(tmp)

    diff = ImageChops.difference(im, recompressed)
    enhancer = ImageEnhance.Brightness(diff)
    diff = enhancer.enhance(10)

    # Correction ici 👇
    hist = diff.convert("L").histogram()  # convertit en niveaux de gris
    total = sum(i * v for i, v in enumerate(hist))  # i = intensité, v = nombre de pixels
    count = sum(hist)
    avg = total / max(count, 1)

    return avg

print("ELA score:", ela_score("/home/mathieu/iadev/veripix/dataset/test3.jpeg"))

