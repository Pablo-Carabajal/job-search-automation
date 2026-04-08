import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT") or "587")
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    NOMBRE_REMITENTE = os.getenv("NOMBRE_REMITENTE", "Pablo Ezequiel Carabajal")

    RUTA_CV = BASE_DIR / os.getenv("RUTA_CV", "assets/cv.pdf")
    RUTA_HISTORIAL = BASE_DIR / os.getenv("RUTA_HISTORIAL", "data/historial.db")
    RUTA_BLACKLIST = BASE_DIR / os.getenv("RUTA_BLACKLIST", "data/blacklist.txt")

    COMPUTRABAJO_EMAIL = os.getenv("COMPUTRABAJO_EMAIL")
    COMPUTRABAJO_PASSWORD = os.getenv("COMPUTRABAJO_PASSWORD")

    COOLDOWN_DIAS = int(os.getenv("COOLDOWN_DIAS") or "20")
    MAX_POSTULACIONES_DIA = int(os.getenv("MAX_POSTULACIONES_DIA") or "7")
    DELAY_ENTRE_ENVIOS = int(os.getenv("DELAY_ENTRE_ENVIOS") or "45")
    MAX_PAGINAS_PORTAL = int(os.getenv("MAX_PAGINAS_PORTAL") or "5")

    CATEGORIAS = [c.strip() for c in os.getenv("CATEGORIAS", "").split(",") if c.strip()]

    CIUDAD = "San Francisco"
    PROVINCIA = "Córdoba"
    PAIS = "Argentina"

    CANDIDATO_EMAIL = os.getenv("CANDIDATO_EMAIL", "carabajalpabloezequiel@gmail.com")