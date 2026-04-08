"""
Script de debug para verificar el login en Computrabajo.
Toma capturas de pantalla en cada paso para diagnosticar problemas.

Uso:
    python debug_login_computrabajo.py

Requiere: selenium, python-dotenv
Genera capturas en: debug_screenshots/
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

load_dotenv()

EMAIL = os.getenv("COMPUTRABAJO_EMAIL")
PASSWORD = os.getenv("COMPUTRABAJO_PASSWORD")

SCREENSHOTS_DIR = Path("debug_screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True)


def screenshot(driver, nombre):
    ruta = SCREENSHOTS_DIR / f"{nombre}.png"
    driver.save_screenshot(str(ruta))
    print(f"  📸 Captura guardada: {ruta}")


def crear_driver(headless=False):
    """Crea el driver. headless=False para ver el browser en pantalla."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=options)


def debug_login():
    print("=" * 60)
    print("DEBUG LOGIN - COMPUTRABAJO")
    print("=" * 60)

    if not EMAIL or not PASSWORD:
        print("❌ ERROR: COMPUTRABAJO_EMAIL o COMPUTRABAJO_PASSWORD no están en .env")
        return

    print(f"✅ Credenciales cargadas: {EMAIL}")
    print()

    # Probar con headless=False primero para ver qué pasa visualmente
    # Cambiar a True para modo silencioso
    driver = crear_driver(headless=False)

    try:
        # --- PASO 1: Página principal ---
        print("PASO 1: Navegando a ar.computrabajo.com ...")
        driver.get("https://ar.computrabajo.com")
        time.sleep(3)
        screenshot(driver, "01_home")
        print(f"  URL actual: {driver.current_url}")
        print(f"  Título: {driver.title}")

        # --- PASO 2: Buscar el link de login ---
        print("\nPASO 2: Buscando link de login ...")
        login_url = None

        # Intentar encontrar el botón/link de login en la página principal
        selectores_login = [
            "a[href*='login']",
            "a[href*='Login']",
            "a[href*='acceder']",
            "a[href*='ingresar']",
            ".login",
            "[data-qa='login']",
        ]
        for sel in selectores_login:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                login_url = el.get_attribute("href")
                print(f"  ✅ Link de login encontrado con '{sel}': {login_url}")
                break
            except NoSuchElementException:
                pass

        if not login_url:
            print("  ⚠️  No se encontró link de login en la home. Probando URL directa...")

        # --- PASO 3: Navegar al login ---
        print("\nPASO 3: Navegando a la página de login ...")

        # Computrabajo Argentina usa esta URL para candidatos
        urls_login = [
            "https://ar.computrabajo.com/candidate/login",
            "https://ar.computrabajo.com/login",
            "https://ar.computrabajo.com/acceder",
        ]

        login_ok = False
        for url in urls_login:
            print(f"  Probando: {url}")
            driver.get(url)
            time.sleep(3)
            screenshot(driver, f"02_login_{url.split('/')[-1]}")
            print(f"  URL actual: {driver.current_url}")
            print(f"  Título: {driver.title}")

            # Verificar si hay un formulario de login
            try:
                campo = driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[id*='email']")
                print(f"  ✅ Campo email encontrado: name='{campo.get_attribute('name')}' id='{campo.get_attribute('id')}'")
                login_ok = True
                break
            except NoSuchElementException:
                print(f"  ❌ No hay campo email en esta URL")

        if not login_ok:
            print("\n❌ No se encontró formulario de login en ninguna URL conocida.")
            print("   Revisá las capturas en debug_screenshots/ para ver qué muestra el sitio.")
            return

        # --- PASO 4: Inspeccionar el formulario ---
        print("\nPASO 4: Inspeccionando el formulario de login ...")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for inp in inputs:
            tipo = inp.get_attribute("type")
            nombre = inp.get_attribute("name")
            id_attr = inp.get_attribute("id")
            placeholder = inp.get_attribute("placeholder")
            print(f"  input: type='{tipo}' name='{nombre}' id='{id_attr}' placeholder='{placeholder}'")

        # --- PASO 5: Completar el formulario ---
        print("\nPASO 5: Completando el formulario ...")

        # Campo email
        campo_email = None
        for sel in ["input[type='email']", "input[name='email']", "input[id*='email']", "input[name='username']"]:
            try:
                campo_email = driver.find_element(By.CSS_SELECTOR, sel)
                print(f"  ✅ Campo email: {sel}")
                break
            except NoSuchElementException:
                pass

        if not campo_email:
            print("  ❌ No se encontró campo email")
            screenshot(driver, "05_error_no_email_field")
            return

        campo_email.clear()
        campo_email.send_keys(EMAIL)
        time.sleep(1)

        # Campo password
        campo_pass = None
        for sel in ["input[type='password']", "input[name='password']", "input[id*='pass']"]:
            try:
                campo_pass = driver.find_element(By.CSS_SELECTOR, sel)
                print(f"  ✅ Campo password: {sel}")
                break
            except NoSuchElementException:
                pass

        if not campo_pass:
            print("  ❌ No se encontró campo password")
            screenshot(driver, "05_error_no_pass_field")
            return

        campo_pass.clear()
        campo_pass.send_keys(PASSWORD)
        time.sleep(1)

        screenshot(driver, "05_formulario_completo")

        # --- PASO 6: Submit ---
        print("\nPASO 6: Haciendo submit ...")
        boton = None
        for sel in [
            "button[type='submit']",
            "input[type='submit']",
            "button.btn-login",
            "button[data-qa='login-submit']",
            "button:contains('Ingresar')",
            "button:contains('Entrar')",
        ]:
            try:
                boton = driver.find_element(By.CSS_SELECTOR, sel)
                print(f"  ✅ Botón submit: {sel} — texto: '{boton.text}'")
                break
            except NoSuchElementException:
                pass

        if not boton:
            # Intentar con XPath para texto
            for texto in ["Ingresar", "Entrar", "Iniciar sesión", "Login"]:
                try:
                    boton = driver.find_element(By.XPATH, f"//button[contains(text(), '{texto}')]")
                    print(f"  ✅ Botón submit por texto: '{texto}'")
                    break
                except NoSuchElementException:
                    pass

        if not boton:
            print("  ❌ No se encontró botón de submit")
            screenshot(driver, "06_error_no_submit")
            return

        boton.click()
        print("  Clic en submit realizado. Esperando redirección...")

        # --- PASO 7: Verificar resultado ---
        print("\nPASO 7: Verificando resultado del login ...")
        time.sleep(5)
        screenshot(driver, "07_post_login")
        print(f"  URL actual: {driver.current_url}")
        print(f"  Título: {driver.title}")

        if "login" in driver.current_url.lower():
            print("\n❌ LOGIN FALLIDO — Seguimos en la página de login")
            # Buscar mensajes de error
            for sel in [".error", ".alert", "[class*='error']", "[class*='alert']"]:
                try:
                    errores = driver.find_elements(By.CSS_SELECTOR, sel)
                    for e in errores:
                        if e.text.strip():
                            print(f"  Mensaje de error: '{e.text.strip()}'")
                except Exception:
                    pass
        else:
            print("\n✅ LOGIN EXITOSO")
            print(f"  Redirigido a: {driver.current_url}")

            # --- PASO 8: Probar búsqueda de ofertas ---
            print("\nPASO 8: Probando búsqueda de ofertas en San Francisco, Córdoba ...")
            driver.get("https://ar.computrabajo.com/trabajo-en-san-francisco-cordoba")
            time.sleep(4)
            screenshot(driver, "08_busqueda_ofertas")
            print(f"  URL: {driver.current_url}")
            print(f"  Título: {driver.title}")

            # Contar ofertas
            for sel in ["article.box_offer", ".offerBlock", "[data-qa='offer-list-item']", ".job-item"]:
                try:
                    ofertas = driver.find_elements(By.CSS_SELECTOR, sel)
                    if ofertas:
                        print(f"  ✅ Ofertas encontradas con '{sel}': {len(ofertas)}")
                        break
                except Exception:
                    pass

    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        screenshot(driver, "error_inesperado")
        raise
    finally:
        print("\nCerrando browser...")
        driver.quit()
        print("Listo. Revisá las capturas en debug_screenshots/")


if __name__ == "__main__":
    debug_login()
