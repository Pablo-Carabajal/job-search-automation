from datetime import date
from bs4 import BeautifulSoup
import hashlib
import logging
from scrapers.base import BaseScraper
from core.models import JobOffer

logger = logging.getLogger(__name__)


class ScraperComputrabajo(BaseScraper):
    BASE_URL = "https://ar.computrabajo.com"
    CIUDAD_SLUG = "san-francisco"

    def scrape(self) -> list[JobOffer]:
        ofertas = []
        
        url = f"{self.BASE_URL}/empleos-en-cordoba-en-{self.CIUDAD_SLUG}"
        logger.info(f"Scraping Computrabajo: {url}")
        
        response = self._get(url)
        if not response:
            logger.warning("Computrabajo no disponible")
            return ofertas
        
        soup = BeautifulSoup(response.text, "html.parser")
        ofertas += self._parse_listado(soup)
        
        max_paginas = 5
        for pagina in range(2, max_paginas + 1):
            self._delay(3, 6)
            url_pagina = f"{self.BASE_URL}/empleos-en-cordoba-en-{self.CIUDAD_SLUG}?page={pagina}"
            response = self._get(url_pagina)
            if not response:
                break
            soup = BeautifulSoup(response.text, "html.parser")
            ofertas_pagina = self._parse_listado(soup)
            if not ofertas_pagina:
                break
            ofertas += ofertas_pagina
        
        logger.info(f"Computrabajo: {len(ofertas)} ofertas encontradas")
        return ofertas

    def _parse_listado(self, soup: BeautifulSoup) -> list[JobOffer]:
        ofertas = []
        
        articles = soup.find_all("article", class_="box_offer")
        
        for article in articles:
            try:
                titulo_elem = article.find("h2")
                if not titulo_elem:
                    continue
                
                link = titulo_elem.find("a", class_="js-o-link")
                if not link:
                    continue
                
                titulo = link.get_text(strip=True)
                url_oferta = "https://ar.computrabajo.com" + link.get("href", "")
                
                empresa = "desconocida"
                links = article.find_all("a")
                for a in links:
                    href = a.get("href", "")
                    text = a.get_text(strip=True)
                    if href and text and href != "/ofertas-de-trabajo/" and "/ofertas-de-trabajo/" not in href:
                        if "offer-grid-article-company-url" in str(a) or "/fd-" in href or "/empresas/" in href or "/candelaria" in href or "/focus" in href:
                            empresa = text
                            break
                
                tiempo_elem = article.find("p", class_="fs13")
                fecha_publicacion = self._parse_fecha(tiempo_elem.get_text(strip=True) if tiempo_elem else "")
                
                # Si no hay empresa, usar URL para evitar agrupar ofertas distintas
                id_base = url_oferta if empresa == "desconocida" else empresa
                oferta_id = self._generar_id(id_base, titulo)
                
                oferta = JobOffer(
                    id=oferta_id,
                    titulo=titulo,
                    empresa=empresa,
                    email_contacto=None,
                    url_oferta=url_oferta,
                    portal_origen="computrabajo",
                    fecha_publicacion=fecha_publicacion,
                    descripcion="",
                    ciudad=self.ciudad,
                    categoria=None,
                    salary=None
                )
                ofertas.append(oferta)
                
            except Exception as e:
                logger.debug(f"Error parseando oferta: {e}")
                continue
        
        return ofertas

    def _parse_fecha(self, texto_fecha: str) -> date:
        texto = texto_fecha.lower().strip()
        today = date.today()
        
        if "hoy" in texto:
            return today
        elif "ayer" in texto:
            return today
        elif "día" in texto or "días" in texto:
            import re
            match = re.search(r'(\d+)', texto)
            if match:
                dias = int(match.group(1))
                return today
        elif "mes" in texto:
            return today
        
        return today

    def _generar_id(self, empresa: str, titulo: str) -> str:
        raw = f"{empresa.lower()}|{titulo.lower()}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]