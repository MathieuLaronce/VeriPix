# save as pixabay_scrape_20_cf.py
import os, re, time
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

SEARCH_URL = "https://pixabay.com/fr/images/search/photo%20ia/"
BASE = "https://pixabay.com"
OUTDIR = "pixabay_ia_20"
LIMIT = 20

# cloudscraper crée une session "requests" compatible, qui gère mieux Cloudflare
scraper = cloudscraper.create_scraper(
    browser={
        "browser": "chrome",
        "platform": "linux",
        "mobile": False,
        "desktop": True,
    }
)

HEADERS = {
    "User-Agent": scraper.headers.get("User-Agent", "Mozilla/5.0"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Referer": "https://pixabay.com/",
}

def get_soup(url: str) -> BeautifulSoup:
    r = scraper.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def pick_largest_from_srcset(srcset: str):
    if not srcset: return None
    best_url, best_w = None, -1
    for part in srcset.split(","):
        p = part.strip().split()
        if not p: continue
        u = p[0]
        w = 0
        if len(p) > 1 and p[1].endswith("w"):
            try: w = int(re.sub(r"[^\d]", "", p[1]))
            except: w = 0
        if w > best_w:
            best_w, best_url = w, u
    return best_url

def sanitize_filename(name: str) -> str:
    return re.sub(r"[^\w\-\.]+", "_", name.strip())[:200] or "image"

def image_filename_from_url(url: str, idx: int) -> str:
    base = os.path.basename(urlparse(url).path) or f"img_{idx:02d}.jpg"
    base = sanitize_filename(base)
    if not re.search(r"\.(jpg|jpeg|png|webp)$", base, re.I):
        base += ".jpg"
    return f"{idx:02d}_" + base

def extract_detail_links(soup: BeautifulSoup):
    links, seen = [], set()
    for a in soup.select("a[href*='/photos/']"):
        href = a.get("href")
        if not href: continue
        if not re.search(r"/photos/.*-\d+/?$", href):  # garder les pages photo
            continue
        full = urljoin(BASE, href)
        if full not in seen:
            seen.add(full); links.append(full)
    return links

def extract_best_image_url(soup: BeautifulSoup):
    # 1) l'image principale avec srcset (de loin le mieux)
    main_img = soup.select_one("img[srcset]")
    if main_img:
        u = pick_largest_from_srcset(main_img.get("srcset", ""))
        if u: return u
    # 2) og:image en fallback
    og = soup.select_one('meta[property="og:image"]')
    if og and og.get("content"):
        return og["content"]
    # 3) dernier recours
    candidates = []
    for img in soup.select("img"):
        src = img.get("src") or ""
        srcset = img.get("srcset")
        if srcset:
            u = pick_largest_from_srcset(srcset)
            if u: candidates.append(u)
        elif src.startswith("http"):
            candidates.append(src)
    if candidates:
        candidates.sort(key=len, reverse=True)
        return candidates[0]
    return None

def download(url: str, dest_path: str):
    with scraper.get(url, headers=HEADERS, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(1024):
                if chunk: f.write(chunk)

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    print("→ Chargement de la page de recherche…")
    soup = get_soup(SEARCH_URL)

    links = extract_detail_links(soup)
    if not links:
        raise SystemExit("Aucun lien d'image trouvé.")

    links = links[:LIMIT]
    print(f"→ {len(links)} pages d’images à visiter.")
    count = 0

    for i, link in enumerate(links, start=1):
        try:
            dsoup = get_soup(link)
            img_url = extract_best_image_url(dsoup)
            if not img_url:
                print(f"  ✗ Aucune image trouvée : {link}")
                continue
            img_url = urljoin(BASE, img_url)
            dest = os.path.join(OUTDIR, image_filename_from_url(img_url, i))
            download(img_url, dest)
            print(f"  ✓ {dest}")
            count += 1
        except Exception as e:
            print(f"  ✗ {link} — {e}")
        time.sleep(0.3)

    print(f"✅ Terminé : {count}/{LIMIT} fichiers dans ./{OUTDIR}")

if __name__ == "__main__":
    main()
