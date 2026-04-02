import hashlib
import logging
import time
from datetime import date

from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from core.models import JobOffer

logger = logging.getLogger(__name__)


class ScraperZonaJobs(BaseScraper):
    BASE_URL = "https://www.zonajobs.com.ar"
    SEARCH_URL = f"{BASE_URL}/empleos-en-san-francisco-cordoba.html"

    def scrape(self) -> list[JobOffer]:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
        except ImportError:
            logger.error("Selenium no instalado. Ejecutar: pip install selenium")
            return []

        ofertas = []
        driver = None

        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument(f"user-agent={self.headers['User-Agent']}")

            driver = webdriver.Chrome(options=options)
            logger.info(f"Scraping ZonaJobs: {self.SEARCH_URL}")

            max_paginas = 3
            for pagina in range(1, max_paginas + 1):
                url = self.SEARCH_URL if pagina == 1 else f"{self.SEARCH_URL}?page={pagina}"
                driver.get(url)

                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "article"))
                    )
                except Exception:
                    time.sleep(4)

                soup = BeautifulSoup(driver.page_source, "html.parser")
                ofertas_pagina = self._parse_listado(soup)

                if not ofertas_pagina:
                    break

                ofertas.extend(ofertas_pagina)
                self._delay(3, 6)

        except Exception as e:
            logger.error(f"Error en ScraperZonaJobs: {e}")
        finally:
            if driver:
                driver.quit()

        logger.info(f"ZonaJobs: {len(ofertas)} ofertas encontradas")
        return ofertas

    def _parse_listado(self, soup: BeautifulSoup) -> list[JobOffer]:
        ofertas = []

        # ZonaJobs comparte estructura con Bumeran (mismo grupo Adevinta)
        cards = soup.find_all("div", attrs={"data-qa": "posting"})
        if not cards:
            cards = soup.find_all("article")

        for card in cards:
            try:
                titulo_elem = (
                    card.find("h2") or
                    card.find(attrs={"data-qa": "posting-name"})
                )
                if not titulo_elem:
                    continue

                titulo = titulo_elem.get_text(strip=True)
                link = titulo_elem.find("a") or card.find("a")
                url_oferta = ""
                if link:
                    href = link.get("href", "")
                    url_oferta = href if href.startswith("http") else self.BASE_URL + href

                empresa_elem = (
                    card.find(attrs={"data-qa": "posting-company-name"}) or
                    card.find("span", class_=lambda c: c and "company" in c.lower())
                )
                empresa = empresa_elem.get_text(strip=True) if empresa_elem else "desconocida"

                id_base = url_oferta if empresa == "desconocida" else empresa
                oferta_id = self._generar_id(id_base, titulo)

                oferta = JobOffer(
                    id=oferta_id,
                    titulo=titulo,
                    empresa=empresa,
                    email_contacto=None,
                    url_oferta=url_oferta,
                    portal_origen="zonajobs",
                    fecha_publicacion=date.today(),
                    descripcion="",
                    ciudad=self.ciudad,
                    categoria=None,
                    salary=None
                )
                ofertas.append(oferta)

            except Exception as e:
                logger.debug(f"Error parseando oferta ZonaJobs: {e}")
                continue

        return ofertas

    def _generar_id(self, base: str, titulo: str) -> str:
        raw = f"{base.lower()}|{titulo.lower()}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]
