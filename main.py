import logging
import sys
import time
import random
from datetime import date

from config import Config
from core.models import JobOffer, SendRecord, EmailConfig
from core.history_manager import HistoryManager
from core.job_filter import JobFilter
from core.email_sender import EmailSender
from core.computrabajo_applicant import ComputrabajoApplicant
from core.reporter import Reporter


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/app.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def ejecutar_ciclo_diario():
    logging.info("=" * 50)
    logging.info(f"Inicio ciclo: {date.today()}")

    history = HistoryManager(Config.RUTA_HISTORIAL)
    filtro = JobFilter(history, Config.RUTA_BLACKLIST)

    email_config = EmailConfig(
        smtp_host=Config.SMTP_HOST,
        smtp_port=Config.SMTP_PORT,
        usuario=Config.SMTP_USER,
        password=Config.SMTP_PASSWORD,
        nombre_remitente=Config.NOMBRE_REMITENTE,
        ruta_cv=str(Config.RUTA_CV),
        asunto_template="",
        cuerpo_template="",
        cuerpo_espontaneo_template=""
    )
    reporter = Reporter(history, email_config)

    applicant = None
    postulaciones = []
    ofertas = []
    max_postulaciones = Config.MAX_POSTULACIONES_DIA

    try:
        applicant = ComputrabajoApplicant(
            Config.COMPUTRABAJO_EMAIL,
            Config.COMPUTRABAJO_PASSWORD
        )

        if not applicant.login():
            logging.error("No se pudo iniciar sesión en Computrabajo")
            reporter.enviar_reporte(
                Config.CANDIDATO_EMAIL,
                date.today(),
                0, 0, [],
                "No se pudo iniciar sesión en Computrabajo. Revisar credenciales."
            )
            return

        ofertas = applicant.buscar_ofertas()
        logging.info(f"Ofertas encontradas: {len(ofertas)}")

        ofertas_filtradas = filtro.filtrar(ofertas, Config.CATEGORIAS)
        logging.info(f"Ofertas habilitadas para postulación: {len(ofertas_filtradas)}")

        max_postulaciones = Config.MAX_POSTULACIONES_DIA
        postuladas_hoy = 0

        for oferta in ofertas_filtradas:
            if postuladas_hoy >= max_postulaciones:
                logging.info(f"Límite de {max_postulaciones} postulaciones alcanzado")
                break

            exito = applicant.postularse(oferta)

            clave_empresa = oferta.empresa if oferta.empresa != "desconocida" else oferta.id
            estado = "postulado" if exito else "error"
            record = SendRecord(
                empresa=clave_empresa,
                email_destino="computrabajo",
                fecha_envio=date.today(),
                tipo="postulacion_computrabajo",
                estado=estado,
                url_oferta=oferta.url_oferta,
                notas=f"Puesto: {oferta.titulo}"
            )
            history.registrar_envio(record)

            if exito:
                postulaciones.append(record)
                postuladas_hoy += 1
                logging.info(f"Postulado a: {oferta.titulo} en {oferta.empresa}")
            else:
                logging.warning(f"Error al postular a: {oferta.titulo}")

            if postuladas_hoy < max_postulaciones:
                delay = random.uniform(3, 8)
                logging.debug(f"Esperando {delay:.1f}s antes de la siguiente postulación...")
                time.sleep(delay)

        logging.info(f"Ciclo completado. Postulaciones: {len(postulaciones)}")

    except Exception as e:
        logging.error(f"Error en ciclo principal: {e}", exc_info=True)
    finally:
        if applicant:
            applicant.cerrar()

    envios_exitosos = len(postulaciones)
    envios_error = 0
    motivo = None

    if envios_exitosos == 0:
        if not ofertas:
            motivo = "No se encontraron ofertas disponibles"
        else:
            motivo = f"Límite de {max_postulaciones} postulaciones alcanzado sin errores"

    reporter.enviar_reporte(
        Config.CANDIDATO_EMAIL,
        date.today(),
        envios_exitosos,
        envios_error,
        postulaciones,
        motivo
    )


def main():
    setup_logging()

    try:
        ejecutar_ciclo_diario()
    except Exception as e:
        logging.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()