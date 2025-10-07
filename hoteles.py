# hoteles.py
import time
import re
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from utils import js_click, js_set_value_and_change, esperar_resultados, esperar_paneles_habitacion
from habitaciones import distribuir_huespedes, configurar_habitaciones
from habitacionesAdultos import distribuir_huespedesAdultos, configurar_habitacionesAdultos

# Diccionario de destinos: nombre -> código IATA
DESTINOS_IATA = {
    "punta cana": "PUJ",
    "cancún": "CUN",
    "cartagena": "CTG",
    "medellín": "MDE",
    "bogotá": "BOG"
    # puedes agregar más destinos según necesidad
}


def aceptar_cookies(driver, wait):
    try:
        boton_cookies = wait.until(
            EC.element_to_be_clickable((By.XPATH,
                "//button[contains(translate(., 'ACEPTAR', 'aceptar'), 'aceptar') or contains(., 'Aceptar todas')]"
            ))
        )
        boton_cookies.click()
        time.sleep(0.5)
    except Exception:
        print("No apareció el banner de cookies.")


def buscar_hoteles(driver, wait, DESTINO, CHECKIN_ddmmyyyy, CHECKOUT_ddmmyyyy, ADULTOS, NINOS, edades_ninos, edades_infantes):
    destino_iata = DESTINOS_IATA.get(DESTINO.lower())
    if not destino_iata:
        print(f"[ERROR] Destino '{DESTINO}' no está configurado en el diccionario")
        return []

    dest_input = wait.until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, "input[id$='destinationOnlyAccommodation_input']")))
    dest_input.clear()
    dest_input.send_keys(DESTINO)
    time.sleep(0.8)

    try:
        opcion_destino = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            f"//tr[@data-item-value and starts-with(@data-item-value,'Destination::') and contains(@data-item-value,'{destino_iata}')]"
        )))
        opcion_destino.click()
    except Exception:
        dest_input.send_keys(Keys.ARROW_DOWN)
        dest_input.send_keys(Keys.TAB)

    # Check-in y Check-out
    checkin_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id$='departureOnlyAccommodation:input']")))
    js_set_value_and_change(driver, checkin_input, CHECKIN_ddmmyyyy)
    checkin_input.send_keys(Keys.TAB)

    checkout_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id$='arrivalOnlyAccommodation:input']")))
    js_set_value_and_change(driver, checkout_input, CHECKOUT_ddmmyyyy)
    checkout_input.send_keys(Keys.TAB)
    time.sleep(0.8)

    # Configurar habitaciones
    try:
        if int(NINOS) < 2:
            print(int(NINOS))
            # Si hay más de 2 niños
            habitaciones = distribuir_huespedesAdultos(int(ADULTOS), int(NINOS))
            configurar_habitacionesAdultos(driver, wait, habitaciones, edades_ninos, edades_infantes)
        else:
            # Caso normal
            habitaciones = distribuir_huespedes(int(ADULTOS), int(NINOS))
            configurar_habitaciones(driver, wait, habitaciones, edades_ninos, edades_infantes)
    except Exception as e:
        msg = f"[ADVERTENCIA] No se pudo configurar habitaciones: {str(e)}"
        print(msg.encode("utf-8", errors="replace").decode("utf-8"))


    # Botón buscar
    buscar_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "//*[self::button or self::a or self::span][contains(translate(., 'BUSCAR', 'buscar'),'buscar')]"
    )))
    js_click(driver, buscar_btn)

    try:
        resultados = wait.until(EC.presence_of_all_elements_located((
            By.CSS_SELECTOR, ".hotel-card, .result-item, div[class*='results']"
        )))
        print(f"[INFO] Resultados cargados: {len(resultados)} hoteles encontrados")
        return resultados
    except Exception:
        return esperar_resultados(wait, driver)


# ------------------ FILTROS ------------------
def activar_filtro(driver, wait, label_text):
    try:
        if label_text.lower() == "cancelacion gratis":
            container = wait.until(EC.presence_of_element_located((
                By.XPATH, f"//span[contains(text(), '{label_text}')]/ancestor::div[contains(@class,'ui-selectbooleancheckbox')]"
            )))
            cb_div = container.find_element(By.CSS_SELECTOR, "div.ui-chkbox-box")
            driver.execute_script("arguments[0].click();", cb_div)

        elif label_text.lower() in ["solo alojamiento", "alojamiento y desayuno", "media pensión", "pensión completa", "todo incluido"]:
            container = wait.until(EC.presence_of_element_located((
                By.XPATH, f"//div[@id='mealPlanFilter']//label[contains(text(), '{label_text}')]"
            )))
            cb_div = container.find_element(By.XPATH, "./preceding-sibling::div[contains(@class,'ui-chkbox')]/div[contains(@class,'ui-chkbox-box')]")
            driver.execute_script("arguments[0].click();", cb_div)

        else:
            label_elem = wait.until(EC.presence_of_element_located((
                By.XPATH, f"//label[contains(text(), '{label_text}')]"
            )))
            checkbox_id = label_elem.get_attribute("for")
            checkbox = driver.find_element(By.ID, checkbox_id)
            driver.execute_script("arguments[0].click();", checkbox)

        time.sleep(0.8)

    except Exception as e:
        print(f"[ERROR] No se pudo activar filtro '{label_text}': {e}")


def desactivar_filtro(driver, wait, label_text):
    try:
        label_elem = wait.until(EC.presence_of_element_located((
            By.XPATH, f"//div[@id='mealPlanFilter']//label[contains(text(), '{label_text}')]"
        )))
        cb_div = label_elem.find_element(By.XPATH, "./preceding-sibling::div[contains(@class,'ui-chkbox')]/div[contains(@class,'ui-chkbox-box')]")

        if "ui-state-active" in cb_div.get_attribute("class"):
            driver.execute_script("arguments[0].click();", cb_div)
            time.sleep(0.5)
        else:
            print(f"• Filtro ya estaba desactivado: {label_text}")
    except Exception as e:
        print(f"[ERROR] No se pudo desactivar filtro '{label_text}': {e}")


def aplicar_filtros_iniciales(driver, wait):
    filtros = ["Cancelacion gratis", "5 estrellas", "4 estrellas", "Alojamiento y desayuno"]
    for filtro in filtros:
        activar_filtro(driver, wait, filtro)
        time.sleep(5)
    return esperar_resultados(wait, driver)


def aplicar_filtros_todo_incluido(driver, wait):
    desactivar_filtro(driver, wait, "Alojamiento y desayuno")
    time.sleep(5)
    activar_filtro(driver, wait, "Todo incluido")
    time.sleep(5)
    return esperar_resultados(wait, driver)


def obtener_trm_actual():
    fecha_hoy = time.strftime("%Y-%m-%d")
    url = f"https://trm-colombia.vercel.app/?date={fecha_hoy}"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        if data.get("data", {}).get("success"):
            return float(data["data"]["value"])
    print("No se encontró la TRM, usando 1 como fallback")
    return 1


def obtener_hoteles_ordenados(driver, wait, NINOS):
    hoteles = driver.find_elements(By.XPATH, "//div[contains(@class,'c-card--accommodation--hotel')]")
    lista = []
    for h in hoteles:
        try:
            nombre = h.get_attribute("data-hotelname").strip()
            if NINOS > 0 and "adults only" in nombre.lower():
                print(f"❌ Excluido por Adults Only: {nombre}")
                continue
            enlace = h.find_element(By.XPATH, ".//a[contains(@class,'dev-open-hotel')]").get_attribute("href")
            lista.append((nombre, enlace, h))
        except Exception as e:
            print("Error leyendo hotel:", e)
            continue
    return lista


def buscar_y_agregar_hotel(driver, wait, nombre_hotel):
    from selenium.webdriver.common.keys import Keys
    from detalles_hoteles import obtener_info_hotel  # import dinámico
    import time

    try:
        # localizar input de filtro de nombre
        input_filtro = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.nameFilter"))
        )
        input_filtro.clear()
        time.sleep(0.3)
        input_filtro.send_keys(nombre_hotel)
        input_filtro.send_keys(Keys.RETURN)

        # esperar que aparezcan hoteles o el mensaje "no hay resultados"
        time.sleep(2)
        wait.until(
            lambda d: d.find_elements(By.CSS_SELECTOR, ".c-card--accommodation--hotel")
            or d.find_elements(By.CSS_SELECTOR, ".dev-no-result-message")
        )

        # si no hay resultados → limpiar input y salir
        if driver.find_elements(By.CSS_SELECTOR, ".dev-no-result-message"):
            print(f"[INFO] No hubo resultados para '{nombre_hotel}' con los filtros actuales.")
            input_filtro.clear()
            input_filtro.send_keys(Keys.RETURN)
            time.sleep(1)
            return None

        # ✅ hay resultados: tomar la primera tarjeta de hotel
        lista_filtrada = obtener_hoteles_ordenados(driver, wait, 0)
        if not lista_filtrada:
            print(f"[ADVERTENCIA] No se encontró el hotel: {nombre_hotel}")
            return None

        h = lista_filtrada[0]  # (nombre, enlace, elemento)
        info = obtener_info_hotel(driver, wait, h[2])  # entrar al hotel
        if not info:
            return None

        primera = info[0]
        hotel_dict = {
            "nombre": h[0],
            "habitaciones": [{
                "habitacion": primera[0],
                "plan": primera[1],
                "precio_num": int(primera[2]),
                "precio_str": f"${int(primera[2]):,} COP",
                "cancelacion": primera[3]
            }]
        }

        # 🔹 limpiar input para futuras búsquedas (NO quitar filtros globales)
        input_filtro.clear()
        input_filtro.send_keys(Keys.RETURN)
        time.sleep(0.5)

        print(f"[OK] Agregado hotel obligatorio: {hotel_dict['nombre']}")
        return hotel_dict

    except Exception as e:
        print(f"[ERROR] Falló búsqueda directa de {nombre_hotel}: {e}")
        return None
