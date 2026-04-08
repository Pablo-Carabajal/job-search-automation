import logging
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from core.models import JobOffer


logger = logging.getLogger(__name__)


class ComputrabajoApplicant:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)

    def login(self) -> bool:
        logger.info("Iniciando login en Computrabajo...")
        try:
            self.driver.get("https://ar.computrabajo.com/candidate/login")
            time.sleep(2)

            self.wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(self.email)
            self.driver.find_element(By.ID, "password").send_keys(self.password)
            self.driver.find_element(By.ID, "btn-ingresar").click()

            time.sleep(3)

            if "/login" in self.driver.current_url:
                logger.warning("Login falló, reintentando en 30s...")
                time.sleep(30)
                self.driver.get("https://ar.computrabajo.com/candidate/login")
                time.sleep(2)
                self.wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(self.email)
                self.driver.find_element(By.ID, "password").send_keys(self.password)
                self.driver.find_element(By.ID, "btn-ingresar").click()
                time.sleep(3)

            if "/login" in self.driver.current_url:
                logger.error("Login falló definitivamente")
                return False

            logger.info("Login exitoso")
            return True

        except Exception as e:
            logger.error(f"Error durante login: {e}")
            return False

    def buscar_ofertas(self) -> list[JobOffer]:
        logger.info("Buscando ofertas en Computrabajo...")
        ofertas = []
        base_url = "https://ar.computrabajo.com/trabajo-en-san-francisco-cordoba"

        for pagina in range(1, 6):
            url = f"{base_url}?page={pagina}" if pagina > 1 else base_url
            logger.info(f"Página {pagina}: {url}")
            self.driver.get(url)
            time.sleep(2)

            try:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, "div.box_oferta")
                if not elementos:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, "article")
                if not elementos:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, ".job")

                if not elementos:
                    logger.info(f"No hay más ofertas en página {pagina}")
                    break

                for elem in elementos:
                    try:
                        titulo_elem = elem.find_element(By.CSS_SELECTOR, "h2 a") or elem.find_element(By.CSS_SELECTOR, ".title a") or elem.find_element(By.CSS_SELECTOR, "a.titulo")
                        titulo = titulo_elem.text.strip()
                        url_oferta = titulo_elem.get_attribute("href")

                        try:
                            empresa = elem.find_element(By.CSS_SELECTOR, ".company .name").text.strip()
                        except:
                            try:
                                empresa = elem.find_element(By.CSS_SELECTOR, ".company-name").text.strip()
                            except:
                                empresa = "desconocida"

                        oferta = JobOffer(
                            id=url_oferta.split("/")[-1] if url_oferta else f"ct_{len(ofertas)}",
                            titulo=titulo,
                            empresa=empresa,
                            email_contacto=None,
                            url_oferta=url_oferta,
                            portal_origen="computrabajo",
                            fecha_publicacion=None,
                            descripcion="",
                            ciudad="San Francisco, Córdoba"
                        )
                        ofertas.append(oferta)

                    except Exception as e:
                        logger.warning(f"Error extrayendo oferta: {e}")
                        continue

            except Exception as e:
                logger.warning(f"Error en página {pagina}: {e}")
                break

        logger.info(f"Total ofertas encontradas: {len(ofertas)}")
        return ofertas

    def postularse(self, oferta: JobOffer) -> bool:
        logger.info(f"Postulando a: {oferta.titulo}")
        try:
            self.driver.get(oferta.url_oferta)
            time.sleep(2)

            try:
                boton = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Postularme')]")
                boton.click()
                time.sleep(2)
                logger.info(f"Postulación exitosa: {oferta.titulo}")
                return True
            except NoSuchElementException:
                try:
                    boton = self.driver.find_element(By.CSS_SELECTOR, "button.btn-primary")
                    if "Postular" in boton.text:
                        boton.click()
                        time.sleep(2)
                        logger.info(f"Postulación exitosa: {oferta.titulo}")
                        return True
                except:
                    pass
                logger.warning(f"Botón Postularme no encontrado para: {oferta.titulo}")
                return False

        except Exception as e:
            logger.error(f"Error al postularse a {oferta.titulo}: {e}")
            return False

    def cerrar(self):
        logger.info("Cerrando driver...")
        self.driver.quit()