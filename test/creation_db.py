import sqlite3

sqlite_path = "./data/veripix.db"

conn = sqlite3.connect(sqlite_path)
cur = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS images;
DROP TABLE IF EXISTS mesures;
DROP TABLE IF EXISTS predictions;

CREATE TABLE images (
    id_image INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_image TEXT,
    type_image TEXT CHECK(type_image IN ('reelle', 'artificielle')),
    source TEXT,
    path_local TEXT UNIQUE,
    format TEXT,
    largeur INTEGER,
    hauteur INTEGER,
    taille_ko REAL,
    has_exif BOOLEAN,
    date_import TEXT
);

CREATE TABLE mesures (
    id_feature INTEGER PRIMARY KEY AUTOINCREMENT,
    id_image INTEGER,
    ela_score REAL,
    date_analyse TEXT,
    FOREIGN KEY(id_image) REFERENCES images(id_image)
);

CREATE TABLE predictions (
    id_prediction INTEGER PRIMARY KEY AUTOINCREMENT,
    id_image INTEGER,
    label_pred TEXT CHECK(label_pred IN ('reelle', 'artificielle')),
    probabilite REAL,
    model_version TEXT,
    FOREIGN KEY(id_image) REFERENCES images(id_image)
);
""")

conn.commit()
conn.close()
print("bdd crée")
