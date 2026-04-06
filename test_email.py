import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from config import Config
from core.models import EmailConfig
from core.email_sender import EmailSender

logging.info("Iniciando prueba de email...")

email_config = EmailConfig(
    smtp_host=Config.SMTP_HOST,
    smtp_port=Config.SMTP_PORT,
    usuario=Config.SMTP_USER,
    password=Config.SMTP_PASSWORD,
    nombre_remitente=Config.NOMBRE_REMITENTE,
    ruta_cv=str(Config.RUTA_CV),
    asunto_template=Config.ASUNTO_OFERTA_TEMPLATE,
    cuerpo_template=Config.CUERPO_OFERTA_TEMPLATE,
    cuerpo_espontaneo_template=Config.CUERPO_ESPONTANEO_TEMPLATE
)

sender = EmailSender(email_config)

destinatario = "elianalazcano@hotmail.com"
asunto = "Prueba - Job Search Automation"
cuerpo = """Hola Eliana,

Esta es una prueba del sistema de envío automático de CV.

El sistema está funcionando correctamente.

Saludos,
Pablo Ezequiel Carabajal"""

logging.info(f"Enviando email de prueba a {destinatario}...")
exito = sender._enviar(destinatario, asunto, cuerpo)

if exito:
    logging.info("✅ Email enviado exitosamente!")
else:
    logging.error("❌ Error al enviar email")

print(f"\nResultado: {'ÉXITO' if exito else 'ERROR'}")