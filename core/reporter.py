import logging
from datetime import date
from pathlib import Path
from typing import Optional

from core.models import SendRecord, EmailConfig
from core.history_manager import HistoryManager
from core.email_sender import EmailSender

logger = logging.getLogger(__name__)

TEMPLATE_REPORTE = Path("templates/reporte_diario.txt")


class Reporter:
    def __init__(self, history: HistoryManager, email_config: EmailConfig):
        self.history = history
        self.sender = EmailSender(email_config)

    def _construir_lineas_envios(self, registros: list[SendRecord]) -> str:
        if not registros:
            return ""

        TIPO_LEGIBLE = {
            "oferta_portal": "Oferta de portal",
            "empresa_local": "Envío espontáneo (fallback)",
        }
        ESTADO_EMOJI = {
            "enviado": "✓",
            "error": "✗",
            "omitido": "—",
        }

        lineas = []
        for r in registros:
            tipo = TIPO_LEGIBLE.get(r.tipo, r.tipo)
            emoji = ESTADO_EMOJI.get(r.estado, "?")
            empresa = r.empresa if r.empresa else "Desconocida"
            lineas.append(
                f"• {empresa} <{r.email_destino}>\n"
                f"  Tipo   : {tipo}\n"
                f"  Puesto : {r.notas or 'No especificado'}\n"
                f"  Estado : {emoji} {r.estado}"
            )
        return "\n\n".join(lineas)

    def generar_reporte(
        self,
        fecha: date,
        envios_exitosos: int,
        envios_error: int,
        registros: list[SendRecord],
        motivo_sin_envios: Optional[str] = None,
    ) -> str:
        try:
            template = TEMPLATE_REPORTE.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"No se pudo leer template de reporte: {e}")
            template = (
                "Reporte {fecha}\n"
                "Exitosos: {envios_exitosos} | Errores: {envios_error}\n"
                "{seccion_envios}{seccion_sin_envios}"
            )

        total = envios_exitosos + envios_error

        if registros:
            seccion_envios = "DETALLE DE ENVÍOS\n-----------------\n" + self._construir_lineas_envios(registros) + "\n\n"
            seccion_sin_envios = ""
        else:
            seccion_envios = ""
            motivo = motivo_sin_envios or "No se realizaron envíos en este ciclo."
            seccion_sin_envios = f"SIN ENVÍOS HOY\n--------------\nMotivo: {motivo}\n\n"

        return template.format(
            fecha=fecha.strftime("%d/%m/%Y"),
            envios_exitosos=envios_exitosos,
            envios_error=envios_error,
            total=total,
            seccion_envios=seccion_envios,
            seccion_sin_envios=seccion_sin_envios,
        )

    def enviar_reporte(
        self,
        destinatario: str,
        fecha: date,
        envios_exitosos: int,
        envios_error: int,
        registros: list[SendRecord],
        motivo_sin_envios: Optional[str] = None,
    ) -> bool:
        try:
            cuerpo = self.generar_reporte(
                fecha, envios_exitosos, envios_error, registros, motivo_sin_envios
            )
            asunto = f"[Job Search] Reporte diario - {fecha.strftime('%d/%m/%Y')} | {envios_exitosos} envíos exitosos"
            resultado = self.sender.enviar_texto(destinatario, asunto, cuerpo)
            if resultado:
                logger.info(f"Reporte diario enviado a {destinatario}")
            else:
                logger.warning(f"No se pudo enviar el reporte a {destinatario}")
            return resultado
        except Exception as e:
            logger.error(f"Error al enviar reporte a {destinatario}: {e}")
            return False
