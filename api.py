from fastapi import FastAPI
import sqlite3

DB = "./data/veripix.db"

app = FastAPI(title="VeriPix API", version="0.1")

def q(query, params=()):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/images")
def list_images():
    return q("""
        SELECT i.id_image, i.nom_image, i.type_image, i.path_local,
               m.ela_score, m.date_analyse
        FROM images i
        LEFT JOIN mesures m ON m.id_image = i.id_image
        ORDER BY i.id_image
    """)

@app.get("/images/{id_image}")
def one_image(id_image: int):
    rows = q("""
        SELECT i.*, m.ela_score, m.date_analyse
        FROM images i
        LEFT JOIN mesures m ON m.id_image = i.id_image
        WHERE i.id_image = ?
    """, (id_image,))
    return rows[0] if rows else {"error": "not found"}

@app.get("/stats/ela-by-type")
def ela_by_type():
    return q("""
        SELECT i.type_image, ROUND(AVG(m.ela_score),2) AS avg_ela, COUNT(*) AS n
        FROM images i JOIN mesures m ON m.id_image = i.id_image
        GROUP BY i.type_image
    """)
