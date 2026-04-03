import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    NOMBRE_REMITENTE = os.getenv("NOMBRE_REMITENTE", "Pablo Ezequiel Carabajal")

    RUTA_CV = BASE_DIR / os.getenv("RUTA_CV", "assets/cv.pdf")
    RUTA_HISTORIAL = BASE_DIR / os.getenv("RUTA_HISTORIAL", "data/historial.db")
    RUTA_EMPRESAS_LOCALES = BASE_DIR / os.getenv("RUTA_EMPRESAS_LOCALES", "data/local_companies.json")
    RUTA_BLACKLIST = BASE_DIR / os.getenv("RUTA_BLACKLIST", "data/blacklist.txt")

    COOLDOWN_DIAS = int(os.getenv("COOLDOWN_DIAS", "20"))
    MAX_FALLBACK_POR_DIA = int(os.getenv("MAX_FALLBACK_POR_DIA", "10"))
    MINIMO_ENVIOS_DIARIOS = int(os.getenv("MINIMO_ENVIOS_DIARIOS", "10"))
    DELAY_ENTRE_ENVIOS = int(os.getenv("DELAY_ENTRE_ENVIOS", "45"))
    DELAY_ENTRE_FALLBACK = int(os.getenv("DELAY_ENTRE_FALLBACK", "90"))
    MAX_PAGINAS_PORTAL = int(os.getenv("MAX_PAGINAS_PORTAL", "5"))

    CATEGORIAS = [c.strip() for c in os.getenv("CATEGORIAS", "").split(",") if c.strip()]

    CIUDAD = "San Francisco"
    PROVINCIA = "Córdoba"
    PAIS = "Argentina"

    CANDIDATO_EMAIL = os.getenv("CANDIDATO_EMAIL", "carabajalpabloezequiel@gmail.com")

    ASUNTO_OFERTA_TEMPLATE = "templates/asunto_oferta.txt"
    CUERPO_OFERTA_TEMPLATE = "templates/cuerpo_oferta.txt"
    CUERPO_ESPONTANEO_TEMPLATE = "templates/cuerpo_espontaneo.txt"