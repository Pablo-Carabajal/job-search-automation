"""
Debug login Computrabajo - simula tipeo humano para activar validaciones JS.
"""

import os
import time
import random
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

load_dotenv()

EMAIL = os.getenv("COMPUTRABAJO_EMAIL")
PASSWORD = os.getenv("COMPUTRABAJO_PASSWORD")

SCREENSHOTS_DIR = Path("debug_screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True)


def screenshot(driver, nombre):
    ruta = SCREENSHOTS_DIR / f"{nombre}.png"
    driver.save_screenshot(str(ruta))
    print(f"  [SCREENSHOT] {ruta}")


def tipear(campo, texto):
    """Simula tipeo humano caracter por caracter."""
    campo.click()
    time.sleep(0.3)
    for char in texto:
        campo.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))
    time.sleep(0.5)


def crear_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=options)


def debug_login():
    print("=" * 60)
    print("DEBUG LOGIN - COMPUTRABAJO (tipeo humano)")
    print("=" * 60)

    if not EMAIL or not PASSWORD:
        print("[ERROR] Faltan credenciales en .env")
        return

    print(f"[OK] Email: {EMAIL}")

    driver = crear_driver()
    wait = WebDriverWait(driver, 20)

    try:
        # PASO 1: Ir al login
        print("\nPASO 1: Navegando al login ...")
        driver.get("https://candidato.ar.computrabajo.com/acceso/")
        time.sleep(5)
        screenshot(driver, "01_login")
        print(f"  URL: {driver.current_url}")

        # PASO 2: Tipear email caracter por caracter
        print("\nPASO 2: Tipeando email ...")
        campo_email = wait.until(EC.element_to_be_clickable((By.NAME, "Email")))
        driver.execute_script("arguments[0].scrollIntoView(true);", campo_email)
        tipear(campo_email, EMAIL)
        print(f"  Email tipeado")
        screenshot(driver, "02_email_tipeado")

        # Verificar estado del boton Continuar
        continuar = driver.find_element(By.ID, "continueWithMailButton")
        clase_antes = continuar.get_attribute("class")
        print(f"  Boton Continuar clase: '{clase_antes}'")
        habilitado = driver.execute_script("return !arguments[0].disabled;", continuar)
        print(f"  Boton habilitado: {habilitado}")

        # PASO 3: Clic en Continuar
        print("\nPASO 3: Clic en Continuar ...")
        driver.execute_script("arguments[0].click();", continuar)
        time.sleep(4)
        screenshot(driver, "03_post_continuar")

        # Verificar si el campo password es visible/interactuable
        campo_pass = driver.find_element(By.NAME, "Password")
        pass_visible = driver.execute_script("return arguments[0].offsetParent !== null;", campo_pass)
        print(f"  Password visible: {pass_visible}")

        # PASO 4: Tipear password
        print("\nPASO 4: Tipeando password ...")
        if pass_visible:
            driver.execute_script("arguments[0].scrollIntoView(true);", campo_pass)
            tipear(campo_pass, PASSWORD)
            print("  Password tipeado")
        else:
            print("  [WARN] Password no visible, intentando igual...")
            tipear(campo_pass, PASSWORD)

        screenshot(driver, "04_password_tipeado")

        # Verificar estado del boton submit
        botones = driver.find_elements(By.TAG_NAME, "button")
        print(f"\n  Botones despues de tipear password:")
        for b in botones:
            clase = b.get_attribute("class") or ""
            habilitado = driver.execute_script("return !arguments[0].disabled;", b)
            print(f"    id='{b.get_attribute('id')}' class='{clase}' habilitado={habilitado} texto='{b.text.strip()[:40]}'")

        # PASO 5: Submit - intentar Enter primero (mas confiable)
        print("\nPASO 5: Submit via Enter ...")
        campo_pass.send_keys(Keys.RETURN)
        time.sleep(8)
        screenshot(driver, "05_post_enter")
        print(f"  URL post-Enter: {driver.current_url}")

        url = driver.current_url
        if "login" not in url.lower() and "account" not in url.lower():
            print("\n[OK] LOGIN EXITOSO via Enter!")
        else:
            # Intentar clic en el boton
            print("  Enter no funciono, intentando clic en boton ...")
            botones = driver.find_elements(By.TAG_NAME, "button")
            if botones:
                b = botones[-1]
                print(f"  Clic en: id='{b.get_attribute('id')}' clase='{b.get_attribute('class')}'")
                driver.execute_script("arguments[0].click();", b)
                time.sleep(8)
                screenshot(driver, "06_post_click")
                print(f"  URL post-click: {driver.current_url}")

                url = driver.current_url
                if "login" not in url.lower() and "account" not in url.lower():
                    print("\n[OK] LOGIN EXITOSO via click!")
                else:
                    print("\n[ERROR] LOGIN FALLIDO")
                    # Mensajes de error
                    for sel in [".validation-summary-errors li", ".error", "[class*='error']"]:
                        for e in driver.find_elements(By.CSS_SELECTOR, sel):
                            if e.text.strip():
                                print(f"  Mensaje: '{e.text.strip()}'")

    except Exception as e:
        print(f"\n[ERROR] ERROR INESPERADO: {e}")
        screenshot(driver, "error_inesperado")
        raise
    finally:
        print("\nCerrando browser...")
        driver.quit()


if __name__ == "__main__":
    debug_login()
