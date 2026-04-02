import logging
import sys
import time
import random
from datetime import date

from config import Config
from core.models import JobOffer, LocalCompany, SendRecord, EmailConfig
from core.history_manager import HistoryManager
from core.job_filter import JobFilter
from core.email_sender import EmailSender
from core.fallback import LocalCompanyFallback

from scrapers.computrabajo import ScraperComputrabajo
from scrapers.bumeran import ScraperBumeran
from scrapers.zonajobs import ScraperZonaJobs


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/app.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def buscar_ofertas_todos_portales() -> list[JobOffer]:
    logging.info("Iniciando búsqueda de ofertas en portales...")
    
    scrapers = [
        ScraperComputrabajo(),
        ScraperBumeran(),
        ScraperZonaJobs()
    ]
    
    todas_ofertas = []
    
    for scraper in scrapers:
        try:
            logging.info(f"Scraping {scraper.__class__.__name__}...")
            ofertas = scraper.scrape()
            logging.info(f"{scraper.__class__.__name__}: {len(ofertas)} ofertas encontradas")
            todas_ofertas.extend(ofertas)
        except Exception as e:
            logging.warning(f"Error en {scraper.__class__.__name__}: {e}")
        
        delay = random.uniform(3, 8)
        logging.debug(f"Esperando {delay:.1f}s antes del siguiente scraper...")
        time.sleep(delay)
    
    seen_ids = set()
    ofertas_unicas = []
    for oferta in todas_ofertas:
        if oferta.id not in seen_ids:
            seen_ids.add(oferta.id)
            ofertas_unicas.append(oferta)
    
    logging.info(f"Total ofertas únicas: {len(ofertas_unicas)}")
    return ofertas_unicas


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
        asunto_template=Config.ASUNTO_OFERTA_TEMPLATE,
        cuerpo_template=Config.CUERPO_OFERTA_TEMPLATE,
        cuerpo_espontaneo_template=Config.CUERPO_ESPONTANEO_TEMPLATE
    )
    sender = EmailSender(email_config)
    
    ofertas_raw = buscar_ofertas_todos_portales()
    logging.info(f"Ofertas encontradas: {len(ofertas_raw)}")
    
    ofertas_validas = filtro.filtrar(ofertas_raw, Config.CATEGORIAS)
    logging.info(f"Ofertas habilitadas para envío: {len(ofertas_validas)}")
    
    envios_exitosos = 0
    envios_error = 0
    
    if ofertas_validas:
        for oferta in ofertas_validas:
            logging.info(f"Procesando: {oferta.titulo} en {oferta.empresa}")
            
            if not oferta.email_contacto:
                logging.info(f"Oferta sin email de contacto, omitiendo: {oferta.titulo}")
                record = SendRecord(
                    empresa=oferta.empresa if oferta.empresa != "desconocida" else oferta.id,
                    email_destino="sin_email",
                    fecha_envio=date.today(),
                    tipo="oferta_portal",
                    estado="omitido",
                    url_oferta=oferta.url_oferta,
                    notas=f"Sin email de contacto. Portal: {oferta.portal_origen}"
                )
                history.registrar_envio(record)
                continue
            
            exito = sender.enviar_cv(oferta, oferta.email_contacto)
            
            clave_empresa = oferta.empresa if oferta.empresa != "desconocida" else oferta.id
            estado = "enviado" if exito else "error"
            record = SendRecord(
                empresa=clave_empresa,
                email_destino=oferta.email_contacto,
                fecha_envio=date.today(),
                tipo="oferta_portal",
                estado=estado,
                url_oferta=oferta.url_oferta,
                notas=f"Portal: {oferta.portal_origen}"
            )
            history.registrar_envio(record)
            
            if exito:
                envios_exitosos += 1
            else:
                envios_error += 1
            
            delay = random.uniform(Config.DELAY_ENTRE_ENVIOS - 15, Config.DELAY_ENTRE_ENVIOS + 15)
            logging.debug(f"Esperando {delay:.1f}s antes del siguiente envío...")
            time.sleep(delay)
    else:
        logging.info("Sin ofertas disponibles. Activando fallback empresas locales...")
        
        fallback = LocalCompanyFallback(Config.RUTA_EMPRESAS_LOCALES, history)
        empresas = fallback.obtener_empresas_habilitadas(Config.MAX_FALLBACK_POR_DIA)
        
        logging.info(f"Empresas locales habilitadas: {len(empresas)}")
        
        for empresa in empresas:
            logging.info(f"Enviando a empresa local: {empresa.nombre}")
            
            exito = sender.enviar_cv_directo(empresa)
            
            estado = "enviado" if exito else "error"
            record = SendRecord(
                empresa=empresa.nombre,
                email_destino=empresa.email,
                fecha_envio=date.today(),
                tipo="empresa_local",
                estado=estado,
                notas=f"Rubro: {empresa.rubro}"
            )
            history.registrar_envio(record)
            
            if exito:
                envios_exitosos += 1
            else:
                envios_error += 1
            
            delay = random.uniform(Config.DELAY_ENTRE_FALLBACK - 30, Config.DELAY_ENTRE_FALLBACK + 30)
            logging.debug(f"Esperando {delay:.1f}s...")
            time.sleep(delay)
    
    logging.info(f"Ciclo completado. Éxitos: {envios_exitosos}, Errores: {envios_error}")
    logging.info("=" * 50)


def main():
    setup_logging()
    
    try:
        ejecutar_ciclo_diario()
    except Exception as e:
        logging.error(f"Error en ciclo principal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()