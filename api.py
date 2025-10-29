import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

import jwt 

DB = "./data/veripix.db"

# --- Secrets JWT ---
SECRET_KEY = os.getenv("VERIPIX_JWT_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# --- Utilisateur démo (remplacer par une vraie persistance si besoin) ---
FAKE_USER = {
    "username": os.getenv("VERIPIX_USER", "veripix"),
    "password": os.getenv("VERIPIX_PASS", "veripix"),  # en clair pour la démo
}

# ---------- OpenAPI meta (tags & doc) ----------
tags_metadata = [
    {"name": "Système", "description": "Santé du service et version."},
    {"name": "Auth", "description": "Authentification OAuth2 / JWT."},
    {"name": "Images", "description": "Lister et consulter des images."},
    {"name": "Stats", "description": "Statistiques et agrégations."},
    {"name": "Admin", "description": "Actions d’administration"},
]

app = FastAPI(
    title="VeriPix API",
    version="1.0",
    description="API pour la plateforme VeriPix (images, mesures, stats).",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (utile si un front va consommer l’API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # à restreindre en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 (affiche le cadenas dans Swagger)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ---------- DB helper ----------

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# ---------- AUTH / JWT utils ----------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str) -> bool:
    return username == FAKE_USER["username"] and password == FAKE_USER["password"]


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Vérifie le JWT (Authorization: Bearer <token>) et renvoie le username."""
    credentials_exception = HTTPException(status_code=401, detail="Token invalide ou expiré")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    return username

# ---------- Schemas (Pydantic) ----------

class ImageOut(BaseModel):
    id_image: int
    nom_image: Optional[str] = None
    type_image: Optional[str] = None
    source: Optional[str] = None
    path_local: Optional[str] = None
    format: Optional[str] = None
    largeur: Optional[int] = None
    hauteur: Optional[int] = None
    taille_ko: Optional[float] = None
    has_exif: Optional[bool] = None
    date_import: Optional[str] = None


class ImageDetailOut(ImageOut):
    ela_score: Optional[float] = None
    laplacian_var: Optional[float] = None
    edge_density: Optional[float] = None
    mean_r: Optional[float] = None
    mean_g: Optional[float] = None
    mean_b: Optional[float] = None
    date_analyse: Optional[str] = None


# ---------- Routers par domaine (un seul fichier) ----------

auth = APIRouter(prefix="/auth", tags=["Auth"])
system = APIRouter(tags=["Système"])  # pas de prefix (health/version)
images = APIRouter(prefix="/images", tags=["Images"])
stats = APIRouter(prefix="/stats", tags=["Stats"])
admin = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(get_current_user)])


# ===== Auth =====

@auth.post(
    "/login",
    summary="Login (OAuth2)",
    description="Envoie username/password (form-data). Retourne un access token JWT.",
)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not authenticate_user(form_data.username, form_data.password):
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    token = create_access_token({"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}


# ===== Système =====

@system.get("/health", summary="Health")
def health():
    return {"status": "ok"}


@system.get("/version", summary="Version")
def version():
    return {"app": "VeriPix API", "version": "1.0"}


# ===== Images =====

@images.get(
    "/",
    summary="List Images",
    description="Retourne la liste paginée des images (limit/offset).",
    response_model=List[ImageOut],
)
def list_images(limit: int = 50, offset: int = 0, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        """
        SELECT id_image, nom_image, type_image, source, path_local, format,
               largeur, hauteur, taille_ko, has_exif, date_import
        FROM images
        ORDER BY id_image
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    )
    rows = cur.fetchall()
    return [ImageOut(**dict(r)) for r in rows]


@images.get(
    "/{id_image}",
    summary="One Image",
    description="Retourne une image et ses mesures si disponibles.",
    response_model=ImageDetailOut,
)
def one_image(id_image: int, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        """
        SELECT i.*, m.ela_score, m.laplacian_var, m.edge_density,
               m.mean_r, m.mean_g, m.mean_b, m.date_analyse
        FROM images i
        LEFT JOIN mesures m ON m.id_image = i.id_image
        WHERE i.id_image = ?
        """,
        (id_image,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Image non trouvée")
    return ImageDetailOut(**dict(row))


# ===== Stats =====

@stats.get(
    "/ela-by-type",
    summary="ELA par type d’image",
)
def ela_by_type(db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        """
        SELECT i.type_image,
               ROUND(AVG(m.ela_score), 4) AS avg_ela,
               COUNT(*) AS n
        FROM images i JOIN mesures m ON m.id_image = i.id_image
        GROUP BY i.type_image
        ORDER BY i.type_image
        """
    )
    return [dict(r) for r in cur.fetchall()]


@stats.get(
    "/basic",
    summary="Stats globales",
    description="Renvoie différents agrégats sur images et mesures.",
)
def stats_basic(db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    out = {}

    cur.execute("SELECT COUNT(*) AS n FROM images")
    out["images_total"] = cur.fetchone()["n"]

    cur.execute("SELECT type_image, COUNT(*) AS n FROM images GROUP BY type_image")
    out["images_par_type"] = [dict(r) for r in cur.fetchall()]

    cur.execute(
        """
        SELECT ROUND(AVG(taille_ko),2) AS avg_ko,
               ROUND(AVG(largeur),1) AS avg_w,
               ROUND(AVG(hauteur),1) AS avg_h
        FROM images
        """
    )
    out["images_moyennes"] = dict(cur.fetchone())

    cur.execute(
        """
        SELECT ROUND(AVG(ela_score),4) AS avg_ela,
               ROUND(AVG(laplacian_var),4) AS avg_lap,
               ROUND(AVG(edge_density),4) AS avg_edges
        FROM mesures
        """
    )
    out["mesures_moyennes"] = dict(cur.fetchone())
    return out


# ===== Admin =====

@admin.post(
    "/reindex",
    summary="Reindex (purge mesures)",
    description="Purge la table mesures pour démo. Nécessite un JWT.",
)
def admin_reindex(db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("DELETE FROM mesures")
    db.commit()
    return {"ok": True, "msg": "Mesures supprimées. Relance transform_features.py pour recalculer."}


@admin.post(
    "/label/{id_image}",
    summary="Relabel d’une image",
    description="Change le type d’une image (reelle/artificielle). Nécessite un JWT.",
)
def admin_label(id_image: int, label: str, db: sqlite3.Connection = Depends(get_db)):
    if label not in ("reelle", "artificielle"):
        raise HTTPException(400, "label doit être 'reelle' ou 'artificielle'")
    cur = db.cursor()
    cur.execute("UPDATE images SET type_image=? WHERE id_image=?", (label, id_image))
    db.commit()
    return {"ok": True, "id_image": id_image, "new_label": label}


# ---------- Montage des routers ----------
app.include_router(auth)
app.include_router(system)
app.include_router(images)
app.include_router(stats)
app.include_router(admin)
