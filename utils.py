# utils.py
import re
import os
import tempfile
import time
import requests
from datetime import datetime
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from jinja2 import Template
from playwright.sync_api import sync_playwright
import sys

def js_click(driver, element):
    driver.execute_script("arguments[0].click();", element)


def js_set_value_and_change(driver, element, value):
    driver.execute_script("""
        const el = arguments[0];
        const val = arguments[1];
        el.value = val;
        el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
    """, element, value)


def esperar_resultados(wait, driver):
    try:
        wait.until(lambda d: len(d.find_elements(By.XPATH, "//div[contains(@class,'hotel') or contains(@class,'result')]")) > 0)
        hoteles = driver.find_elements(By.XPATH, "//div[contains(@class,'hotel') or contains(@class,'result')]")
        return hoteles
    except:
        print("[ERROR] No se cargaron resultados a tiempo.")
        return []


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def parse_vuelo(texto, tipo):
    """Extrae los datos de un vuelo desde el contenido_salida"""
    vuelo = {}
    regex = rf"{tipo}:\s*(.*?) - Aerolínea: (.*?) - Salida: (.*?) Llegada: (.*?) - Duración: (.*?) - Tipo: (.*)"
    match = re.search(regex, texto, re.IGNORECASE)
    if match:
        vuelo["fecha"] = match.group(1)
        vuelo["aerolinea"] = match.group(2)
        vuelo["hora_salida"] = match.group(3)
        vuelo["hora_llegada"] = match.group(4)
        vuelo["duracion"] = match.group(5)
        vuelo["tipo"] = match.group(6)
    else:
        # valores por defecto si no encuentra nada
        vuelo["fecha"] = ""
        vuelo["aerolinea"] = ""
        vuelo["hora_salida"] = ""
        vuelo["hora_llegada"] = ""
        vuelo["duracion"] = ""
        vuelo["tipo"] = ""
    return vuelo


def generar_pdf(datos, telefono):
    import tempfile
    import os

    # --- 1. Cargar plantilla HTML ---
    plantilla = resource_path(os.path.join("templates", "Prueba.html"))
    with open(plantilla, "r", encoding="utf-8") as f:
        template_html = f.read()

    # --- 2. Reemplazar rutas de imágenes y fuentes ---
    reemplazos = {
        "Banner.png": "assets/Banner.png",
        "Vuelos.png": "assets/Vuelos.png",
        "Hoteles.png": "assets/Hoteles.png",
        "Alimentación.png": "assets/Alimentación.png",
        "Traslados.png": "assets/Traslados.png",
        "Asistencia.png": "assets/Asistencia.png",
        "Concierge.png": "assets/Concierge.png",
        "Vuelos seleccionados.png": "assets/Vuelos seleccionados.png",
        "Condiciones.png": "assets/Condiciones.png",
        "Equipo.png": "assets/Equipo.png",
        "./fonts/Caros.otf": "fonts/Caros.otf",
        "./fonts/Caros Medium.otf": "fonts/Caros Medium.otf",
        "./fonts/Caros Bold.otf": "fonts/Caros Bold.otf",
    }

    for original, ruta_relativa in reemplazos.items():
        ruta_absoluta = resource_path(ruta_relativa)
        template_html = template_html.replace(original, ruta_absoluta.replace("\\", "/"))

    # --- 3. Renderizar plantilla con datos ---
    template = Template(template_html)
    resultado_html = template.render(**datos)

    # --- 4. Guardar HTML temporal en carpeta segura ---
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp_file:
        tmp_file.write(resultado_html)
        ruta_temp_html = tmp_file.name

    # --- 5. Generar PDF con Playwright ---
    telefono_limpio = re.sub(r"\D", "", telefono)
    if not telefono_limpio:
        telefono_limpio = "0000"
        
    carpeta_documentos = os.path.join(os.path.expanduser("~"), "Documents")
    ruta_pdf = os.path.join(carpeta_documentos, f"cotizacion_generada_{telefono_limpio}.pdf")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=resource_path("ms-playwright/chromium-1181/chrome-win/chrome.exe")
        )
        page = browser.new_page()
        page.goto(f"file:///{ruta_temp_html}", wait_until="load")

        # Ajustar altura del PDF
        content_height = page.evaluate("document.body.scrollHeight")
        content_height -= 1500
        page.pdf(
            path=ruta_pdf,
            width="1320px",
            height=f"{content_height}px",
            print_background=True,
            prefer_css_page_size=True
        )
        browser.close()

    # --- 6. Borrar archivo temporal ---
    try:
        os.remove(ruta_temp_html)
    except:
        pass

    print(f"Cotización generada en: {ruta_pdf}")
    
    return ruta_pdf





def esperar_paneles_habitacion(driver, wait, timeout=10):
    try:
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".hotelCombinationPanel")) > 0)
        return True
    except TimeoutException:
        return False


def aceptar_cookies(driver, wait):
    try:
        boton_cookies = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'ACEPTAR', 'aceptar'), 'aceptar') or contains(., 'Aceptar todas')]"))
        )
        boton_cookies.click()
        time.sleep(0.5)
    except Exception:
        print("No apareció el banner de cookies.")


def obtener_trm_actual():
    fecha_hoy = datetime.today().strftime("%Y-%m-%d")
    url = f"https://trm-colombia.vercel.app/?date={fecha_hoy}"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        if data.get("data", {}).get("success"):
            return float(data["data"]["value"])
    print("No se encontró la TRM, usando 1 como fallback")
    return 1
