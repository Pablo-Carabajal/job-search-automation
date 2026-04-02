from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class JobOffer:
    id: str
    titulo: str
    empresa: str
    email_contacto: Optional[str]
    url_oferta: str
    portal_origen: str
    fecha_publicacion: date
    descripcion: str
    ciudad: str
    categoria: Optional[str] = None
    salary: Optional[str] = None


@dataclass
class LocalCompany:
    nombre: str
    email: str
    rubro: str
    direccion: Optional[str] = None


@dataclass
class SendRecord:
    id: Optional[int] = None
    empresa: str = ""
    email_destino: str = ""
    fecha_envio: Optional[date] = None
    tipo: str = ""
    estado: str = ""
    url_oferta: Optional[str] = None
    notas: Optional[str] = None


@dataclass
class EmailConfig:
    smtp_host: str
    smtp_port: int
    usuario: str
    password: str
    nombre_remitente: str
    ruta_cv: str
    asunto_template: str
    cuerpo_template: str
    cuerpo_espontaneo_template: str