import sqlite3
import os

DB_PATH = "./data/veripix.db"
os.makedirs("data", exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ========================
# 1️TABLE IMAGES
# ========================
cur.executescript("""
DROP TABLE IF EXISTS images;

CREATE TABLE images (
    id_image INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_image TEXT,
    type_image TEXT CHECK(type_image IN ('reelle','artificielle')),
    source TEXT,
    source_id INTEGER,
    path_local TEXT UNIQUE,
    format TEXT,
    largeur INTEGER,
    hauteur INTEGER,
    taille_ko REAL,
    has_exif BOOLEAN,
    date_import TEXT
);
""")

# ========================
# 2️TABLE SOURCES
# ========================
cur.executescript("""
DROP TABLE IF EXISTS sources;

CREATE TABLE sources (
    id_source INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    kind TEXT CHECK(kind IN ('api','scraping','fichier','sql','bigdata')),
    base_url TEXT,
    notes TEXT
);
""")

# Remplissage initial
cur.executescript("""
INSERT OR IGNORE INTO sources (name, kind, base_url) VALUES
('inaturalist','api','https://api.inaturalist.org/'),
('artbreeder','scraping','https://www.artbreeder.com/'),
('local','fichier','perso');
""")

# ========================
# 3️TABLE PROVENANCE
# ========================
cur.executescript("""
DROP TABLE IF EXISTS provenance;

CREATE TABLE provenance (
    id_prov INTEGER PRIMARY KEY AUTOINCREMENT,
    id_image INTEGER NOT NULL,
    provider_id TEXT,
    page_url TEXT,
    download_url TEXT,
    license_code TEXT,
    location TEXT,
    raw_json TEXT,
    FOREIGN KEY (id_image) REFERENCES images(id_image)
);
""")

# ========================
# 4 TABLE MESURES
# ========================
cur.executescript("""
DROP TABLE IF EXISTS mesures;

CREATE TABLE mesures (
    id_feature INTEGER PRIMARY KEY AUTOINCREMENT,
    id_image INTEGER,
    ela_score REAL,
    laplacian_var REAL,
    edge_density REAL,
    mean_r REAL,
    mean_g REAL,
    mean_b REAL,
    date_analyse TEXT,
    FOREIGN KEY(id_image) REFERENCES images(id_image)
);
""")

# ========================
# 6TABLE PREDICTIONS
# ========================
cur.executescript("""
DROP TABLE IF EXISTS predictions;

CREATE TABLE predictions (
    id_prediction INTEGER PRIMARY KEY AUTOINCREMENT,
    id_image INTEGER,
    label_pred TEXT CHECK(label_pred IN ('reelle','artificielle')),
    probabilite REAL,
    model_version TEXT,
    created_at TEXT,
    FOREIGN KEY(id_image) REFERENCES images(id_image)
);
""")



conn.commit()
conn.close()

print("Base crée")
