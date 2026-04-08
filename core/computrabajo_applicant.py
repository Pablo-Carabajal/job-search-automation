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
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)

    def login(self) -> bool:
        logger.info("Iniciando login en Computrabajo...")
        max_intentos = 2
        intento = 0
        
        while intento < max_intentos:
            try:
                self.driver.get("https://ar.computrabajo.com/")
                time.sleep(5)
                
                try:
                    login_link = self.driver.find_element(By.CSS_SELECTOR, "a[href*='Acceso'], a[href*='login'], a[data-test='btn-login']")
                    login_link.click()
                    time.sleep(3)
                except:
                    pass
                
                url_actual = self.driver.current_url
                logger.info(f"URL actual: {url_actual}")
                
                if "Acceso" not in url_actual and "login" not in url_actual:
                    logger.info("Ya estamos logueados!")
                    return True
                
                try:
                    continuar_btn = self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Continuar')]")))
                    logger.info("Boton Continuar encontrado")
                except:
                    pass
                
                email_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
                logger.info("Email input encontrado")
                
                self.driver.execute_script(f"arguments[0].value = '{self.email}';", email_input)
                logger.info("Email ingreado via JS")
                time.sleep(2)
                
                continuar_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                continuar_btn.click()
                logger.info("Click en boton continuar")
                time.sleep(5)
                
                password_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
                logger.info("Password input encontrado")
                
                self.driver.execute_script(f"arguments[0].value = '{self.password}';", password_input)
                logger.info("Password ingreado via JS")
                time.sleep(2)
                
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                submit_btn.click()
                logger.info("Click en boton login final")
                time.sleep(10)
                
                url_actual = self.driver.current_url
                logger.info(f"URL despues de login: {url_actual}")
                
                if "/Acceso" not in url_actual.lower() and "login" not in url_actual.lower():
                    logger.info("Login exitoso!")
                    return True
                    
            except Exception as e:
                logger.warning(f"Intento {intento + 1}/{max_intentos} fallo: {e}")
                self.driver.save_screenshot(f"login_error_{intento}.png")
                logger.info(f"Screenshot guardado: login_error_{intento}.png")
                intento += 1
                if intento < max_intentos:
                    time.sleep(20)
        
        logger.error("Login fallo definitivamente")
        return False

    def buscar_ofertas(self) -> list[JobOffer]:
        logger.info("Buscando ofertas en Computrabajo...")
        ofertas = []
        base_url = "https://ar.computrabajo.com/empleos-en-cordoba"

        for pagina in range(1, 6):
            url = f"{base_url}?p={pagina}" if pagina > 1 else base_url
            logger.info(f"Página {pagina}: {url}")
            self.driver.get(url)
            time.sleep(5)
            
            self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            time.sleep(3)
            
            try:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, "article")
                
                if not elementos:
                    logger.info(f"No hay ofertas en pagina {pagina}")
                    break
                
                logger.info(f"Encontrados {len(elementos)} elementos")
                
                for elem in elementos:
                    try:
                        titulo_elem = elem.find_element(By.CSS_SELECTOR, "h2 a") or elem.find_element(By.CSS_SELECTOR, ".title a") or elem.find_element(By.CSS_SELECTOR, "a.titulo") or elem.find_element(By.TAG_NAME, "a")
                        titulo = titulo_elem.text.strip()
                        url_oferta = titulo_elem.get_attribute("href")
                        
                        if not url_oferta or not titulo:
                            continue

                        try:
                            empresa = elem.find_element(By.CSS_SELECTOR, ".company .name").text.strip()
                        except:
                            try:
                                empresa = elem.find_element(By.CSS_SELECTOR, ".company-name").text.strip()
                            except:
                                try:
                                    empresa = elem.find_element(By.CSS_SELECTOR, ".empresa").text.strip()
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
                            ciudad="Córdoba"
                        )
                        ofertas.append(oferta)

                    except Exception as e:
                        logger.debug(f"Error extrayendo oferta: {e}")
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
            time.sleep(5)
            self.driver.save_screenshot(f"postular_{oferta.id}.png")
            
            time.sleep(3)
            
            try:
                boton = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Postularme')]")
                boton.click()
                time.sleep(3)
                logger.info(f"Postulación exitosa: {oferta.titulo}")
                return True
            except NoSuchElementException:
                pass
            
            try:
                boton = self.driver.find_element(By.CSS_SELECTOR, "button.btn-primary")
                if "Postular" in boton.text:
                    boton.click()
                    time.sleep(3)
                    logger.info(f"Postulación exitosa: {oferta.titulo}")
                    return True
            except:
                pass
            
            try:
                boton = self.driver.find_element(By.CSS_SELECTOR, "a.btn-primary")
                boton.click()
                time.sleep(3)
                logger.info(f"Postulación exitosa (link): {oferta.titulo}")
                return True
            except:
                pass
                
            try:
                boton = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Postularme')]")
                boton.click()
                time.sleep(3)
                logger.info(f"Postulación exitosa (a): {oferta.titulo}")
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