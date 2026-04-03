import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate, make_msgid
from pathlib import Path

from core.models import JobOffer, LocalCompany, EmailConfig

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self, config: EmailConfig):
        self.config = config

    def _cargar_template(self, path: Path) -> str:
        if not path.exists():
            logger.warning(f"Template no encontrado: {path}")
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _construir_asunto(self, template_path: Path, **kwargs) -> str:
        template = self._cargar_template(template_path).strip()
        # Eliminar prefijos espurios que activan filtros de spam
        for prefijo in ("Asunto:", "Subject:", "Re:", "Fwd:"):
            if template.startswith(prefijo):
                template = template[len(prefijo):].strip()
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Error en template asunto: {e}")
            return f"Postulación - {kwargs.get('puesto', 'trabajo')}"

    def _construir_cuerpo(self, template_path: Path, **kwargs) -> str:
        # Asegurar que {nombre} siempre tenga valor desde config
        kwargs.setdefault("nombre", self.config.nombre_remitente)
        template = self._cargar_template(template_path)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Error en template cuerpo: {e}")
            return f"Estimados,\n\nAdjunto mi CV.\n\nSaludos cordiales,\n{self.config.nombre_remitente}"

    def _nombre_adjunto(self) -> str:
        if not self.config.nombre_remitente:
            logger.error("NOMBRE_REMITENTE no configurado, no se puede construir nombre de adjunto")
            return "CV.pdf"
        nombre_limpio = self.config.nombre_remitente.replace(" ", "_")
        return f"CV_{nombre_limpio}.pdf"

    def _texto_a_html(self, texto: str) -> str:
        """Convierte texto plano a HTML mínimo válido."""
        parrafos = texto.strip().split("\n")
        lineas_html = []
        for linea in parrafos:
            linea_esc = (linea
                         .replace("&", "&amp;")
                         .replace("<", "&lt;")
                         .replace(">", "&gt;"))
            if linea_esc.strip():
                lineas_html.append(f"<p>{linea_esc}</p>")
            else:
                lineas_html.append("<br>")
        cuerpo_html = "\n".join(lineas_html)
        return (
            "<!DOCTYPE html><html><head>"
            '<meta charset="utf-8"></head><body>'
            f"{cuerpo_html}"
            "</body></html>"
        )

    def _enviar(self, destinatario: str, asunto: str, cuerpo_plain: str) -> bool:
        if not self.config.nombre_remitente:
            logger.error("NOMBRE_REMITENTE vacío, abortando envío")
            return False

        try:
            # Mensaje externo: mixed (texto + adjunto)
            msg = MIMEMultipart("mixed")
            msg["From"] = f"{self.config.nombre_remitente} <{self.config.usuario}>"
            msg["To"] = destinatario
            msg["Subject"] = asunto
            msg["Reply-To"] = self.config.usuario
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = make_msgid(domain=self.config.usuario.split("@")[-1])

            # Parte alternativa: plain + html
            alternativa = MIMEMultipart("alternative")
            alternativa.attach(MIMEText(cuerpo_plain, "plain", "utf-8"))
            alternativa.attach(MIMEText(self._texto_a_html(cuerpo_plain), "html", "utf-8"))
            msg.attach(alternativa)

            # Adjunto CV
            with open(self.config.ruta_cv, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            nombre_cv = self._nombre_adjunto()
            part.add_header("Content-Disposition", f'attachment; filename="{nombre_cv}"')
            msg.attach(part)

            server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
            server.starttls()
            server.login(self.config.usuario, self.config.password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Email enviado a {destinatario} | Asunto: {asunto}")
            return True

        except Exception as e:
            logger.error(f"Error al enviar email a {destinatario}: {e}")
            return False

    def enviar_cv(self, oferta: JobOffer, destinatario: str) -> bool:
        if not destinatario or not destinatario.strip():
            logger.warning(f"Email no válido para oferta: {oferta.titulo}")
            return False

        asunto = self._construir_asunto(
            Path(self.config.asunto_template),
            puesto=oferta.titulo,
            empresa=oferta.empresa
        )
        cuerpo = self._construir_cuerpo(
            Path(self.config.cuerpo_template),
            puesto=oferta.titulo,
            empresa=oferta.empresa,
            portal=oferta.portal_origen.capitalize()
        )
        return self._enviar(destinatario, asunto, cuerpo)

    def enviar_cv_directo(self, empresa: LocalCompany) -> bool:
        if not empresa.email or not empresa.email.strip():
            logger.warning(f"Email no válido para empresa: {empresa.nombre}")
            return False

        asunto = f"Presentación espontánea - {self.config.nombre_remitente}"
        cuerpo = self._construir_cuerpo(
            Path(self.config.cuerpo_espontaneo_template),
            empresa=empresa.nombre,
            rubro=empresa.rubro
        )
        return self._enviar(empresa.email, asunto, cuerpo)

    def enviar_texto(self, destinatario: str, asunto: str, cuerpo: str) -> bool:
        """Envía un email de texto sin adjunto CV. Usado para reportes."""
        if not destinatario or not destinatario.strip():
            logger.warning("Destinatario vacío en enviar_texto")
            return False
        if not self.config.usuario or not self.config.password:
            logger.error("Credenciales SMTP vacías, no se puede enviar texto")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.config.nombre_remitente} <{self.config.usuario}>"
            msg["To"] = destinatario
            msg["Subject"] = asunto
            msg["Reply-To"] = self.config.usuario
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = make_msgid(domain=self.config.usuario.split("@")[-1])

            msg.attach(MIMEText(cuerpo, "plain", "utf-8"))
            msg.attach(MIMEText(self._texto_a_html(cuerpo), "html", "utf-8"))

            server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
            server.starttls()
            server.login(self.config.usuario, self.config.password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Texto enviado a {destinatario} | Asunto: {asunto}")
            return True

        except Exception as e:
            logger.error(f"Error al enviar texto a {destinatario}: {e}")
            return False
