from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import re

def buscar_vuelos(fecha_ida, fecha_regreso, adultos, ninos, infantes, edades_ninos, origen, destino):
    """
    Versión importable del script original.
    - Reemplaza print(...) por acumulación de texto y return final.
    - Mantiene la lógica intacta.
    """
    salida_final = []
    def _p(texto):
        salida_final.append(str(texto))

    # Asegurar tipos numéricos como en el original
    adultos = int(adultos)
    ninos = int(ninos)
    infantes = int(infantes)
    origen = str(origen)
    destino = str(destino)
    fecha_ida = str(fecha_ida)
    fecha_regreso = str(fecha_regreso)
    
    if edades_ninos:
        # Contamos cuántos niños son mayores de 11 años
        nuevos_adultos = sum(1 for edad in edades_ninos if edad > 11)
        ninos = ninos - nuevos_adultos  # Reducimos el número de niños
        adultos = adultos + nuevos_adultos  # Aumentamos los adultos

        # Evitar números negativos
        if ninos < 0:
            ninos = 0

    options = Options()
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-popup-blocking')
    options.add_argument("--start-minimized")
    # options.add_argument('--headless')  # Puedes activar si quieres sin interfaz
    driver = webdriver.Chrome(options=options)
    driver.minimize_window()
    driver.get("https://www.google.com/travel/flights?tfs=CBsQAhoqEgoyMDI1LTA4LTIxag0IAhIJL20vMDF4XzZzcg0IAhIJL20vMDFkenljGioSCjIwMjUtMDgtMjdqDQgCEgkvbS8wMWR6eWNyDQgCEgkvbS8wMXhfNnNAAUgBUgNDT1BwAXpsQ2pSSVZEWmxRbTFxTVdkVFNqaEJRelJDUzFGQ1J5MHRMUzB0TFMwdExTMTJkSFZyT1VGQlFVRkJSMmxOTlRkclJrZzNTSGxCRWdaS1FUVXhNVGNhQ3dqaW5ROFFBQm9EUTA5UU9CeHdqeTg9mAEBsgETGAEgASoNCAMSCS9tLzAxZHp5Yw&tfu=GgA&hl=es-419&gl=CO&sa=X&ved=0CAoQtY0DahgKEwigmoHR_-mOAxUAAAAAHQAAAAAQmQI")

    wait = WebDriverWait(driver, 20)

    # === NUEVO: abrir modal de pasajeros y ajustar cantidades ===
    try:
        # Abrir modal de pasajeros (botón con aria-label "... pasajero(s)")
        btn_pasajeros = wait.until(EC.element_to_be_clickable((
            By.XPATH, '//button[@aria-haspopup="dialog" and contains(@aria-label,"pasajero")]'
        )))
        driver.execute_script("arguments[0].click();", btn_pasajeros)
        time.sleep(1)

        def set_pasajeros(etiqueta, cantidad):
            """
            Ajusta la cantidad de pasajeros para una fila del modal.
            etiqueta: texto parcial, ej. 'Adultos', 'Niños', 'sin asiento'
            cantidad: número entero
            """
            try:
                fila = wait.until(EC.presence_of_element_located((
                    By.XPATH, f'//li[label[contains(., "{etiqueta}")]]'
                )))

                btn_mas = fila.find_element(By.XPATH, './/button[contains(@aria-label, "Agregar")]')
                btn_menos = fila.find_element(By.XPATH, './/button[contains(@aria-label, "Quitar")]')
                valor_elem = fila.find_element(By.XPATH, './/span[@jsname="NnAfwf"]')

                actual = int(valor_elem.text)

                while actual < cantidad:
                    btn_mas.click()
                    actual = int(valor_elem.text)
                    time.sleep(0.3)

                while actual > cantidad:
                    btn_menos.click()
                    actual = int(valor_elem.text)
                    time.sleep(0.3)

            except Exception as e:
                _p(f"[ADVERTENCIA] No se pudo ajustar {etiqueta}: {e}")

        # ✅ Aplicar cantidades
        set_pasajeros("Adultos", adultos)
        set_pasajeros("Niños de entre 2", ninos)  # match parcial
        set_pasajeros("sin asiento", infantes)    # Infantes (3 a 12 meses sin asiento)

        # Cerrar modal con "Listo"
        try:
            btn_listo_pasajeros = wait.until(EC.element_to_be_clickable((
                By.XPATH, '//span[text()="Listo"]/ancestor::button'
            )))
            driver.execute_script("arguments[0].click();", btn_listo_pasajeros)
            time.sleep(1)
        except Exception as e:
            _p("[ADVERTENCIA] No se pudo hacer clic en 'Listo': " + str(e))

    except Exception as e:
        _p("[ADVERTENCIA] No se pudo abrir o configurar pasajeros: " + str(e))

    # Seleccionar destino
    # Diccionario de ciudades principales de Colombia con sus códigos IATA
    ciudades_iata = {
        "bogota": "BOG",
        "cali": "CLO",
        "medellin": "MDE",
        "cartagena": "CTG",
        "barranquilla": "BAQ",
        "bucaramanga": "BGA",
        "leticia": "LET",
        "armenia": "AXM",
        "pereira": "PEI",
        "pasto": "PSO",
        "popayan": "PPN",
        "santa marta": "SMR",
        "monteria": "MTR",
        "riohacha": "RCH",
        "mitu": "MVP",
        "ibague": "IBE",
        "neiva": "NVA"
    }

    # Normalizar la entrada
    ciudad = origen.strip().lower()
    iata_code = ciudades_iata.get(ciudad, origen)  # si no está en el diccionario, usar lo que venga

    # Seleccionar destino (input origen)
    origen_input = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, 'input[jsname="yrriRe"][aria-label="¿Desde dónde?"]')
    ))
    origen_input.clear()
    origen_input.send_keys(iata_code)
    time.sleep(1.5)

    try:
        # Esperar opciones de autocompletado
        opciones = wait.until(EC.presence_of_all_elements_located((
            By.CSS_SELECTOR, 'ul[role="listbox"] li[role="option"]'
        )))

        seleccion_hecha = False
        for opcion in opciones:
            texto = opcion.text.strip().lower()

            # Validar coincidencia con el código IATA o la ciudad escrita
            if iata_code.lower() in texto or ciudad in texto:
                opcion.click()
                seleccion_hecha = True
                break

        # Si no se encontró coincidencia, usar flechas + Enter
        if not seleccion_hecha:
            _p(f"No se encontró coincidencia para '{origen}', seleccionando primer resultado con Enter.")
            origen_input.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.3)
            origen_input.send_keys(Keys.ENTER)

    except Exception as e:
        _p(f"Error buscando el aeropuerto: {e}, usando flecha + enter.")
        origen_input.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.3)
        origen_input.send_keys(Keys.ENTER)

    time.sleep(1)

    # Seleccionar destino
    destino_input = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, 'input[jsname="yrriRe"][aria-label="¿A dónde quieres ir?"]')
    ))
    destino_input.clear()
    destino_input.send_keys(destino)
    time.sleep(2)

    try:
        # Esperar a que aparezca la lista de opciones
        opciones = wait.until(EC.presence_of_all_elements_located((
            By.CSS_SELECTOR, 'ul[role="listbox"] li[role="option"]'
        )))

        seleccion_hecha = False
        for opcion in opciones:
            texto = opcion.text.strip().lower()
            
            if "aeropuerto" in texto and destino.lower() in texto:
                opcion.click()
                seleccion_hecha = True
                break

        if not seleccion_hecha:
            _p("No se encontró el aeropuerto exacto, seleccionando primer resultado con Enter.")
            destino_input.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.3)
            destino_input.send_keys(Keys.ENTER)

    except Exception as e:
        _p("Error buscando el aeropuerto, usando flecha + enter.")
        destino_input.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.3)
        destino_input.send_keys(Keys.ENTER)

    time.sleep(1)

    driver.find_element(By.CSS_SELECTOR, 'body').click()
    time.sleep(1)

    # Seleccionar fecha de ida
    fecha_ida_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Salida"]')))
    driver.execute_script("arguments[0].click();", fecha_ida_input)

    time.sleep(1)

    fecha_ida_dia = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, f'div[jsname="mG3Az"][data-iso="{fecha_ida}"]')
    ))
    fecha_ida_dia.click()
    time.sleep(1)
    # Seleccionar fecha de regreso
    fecha_regreso_dia = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, f'div[jsname="mG3Az"][data-iso="{fecha_regreso}"]')
    ))
    fecha_regreso_dia.click()
    time.sleep(1)

    # Clic al botón "Listo" tras seleccionar fechas
    boton_listo = wait.until(EC.element_to_be_clickable((
        By.XPATH, '//div[@jsname="WCieBd"]//button[.//span[text()="Listo"]]'
    )))
    driver.execute_script("arguments[0].click();", boton_listo)

    # Esperar unos segundos para que los cambios se carguen
    time.sleep(5)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.Rk10dc')))

    # Obtener todos los elementos de vuelo
    vuelos = driver.find_elements(By.CSS_SELECTOR, 'ul.Rk10dc > li.pIav2d')

    # -------------------------------
    # Normalizar tipo de vuelo
    # -------------------------------
    def es_vuelo_directo(tipo_vuelo: str, texto_tarjeta: str) -> bool:
        """
        Determina si el vuelo es directo usando:
        - el texto específico (tipo_vuelo) si existe, y
        - un fallback robusto sobre TODO el texto visible de la tarjeta (texto_tarjeta).
        """
        t1 = (tipo_vuelo or "").lower()
        t2 = (texto_tarjeta or "").lower()

        # Señales claras de directos que suele mostrar Google Flights
        DIRECTO_KEYWORDS = ("directo", "sin escalas")
        # Señales de escalas/paradas
        ESCALA_KEYWORDS = ("escala", "escalas", "parada", "paradas", "boletos separados")

        # 1) Si explícitamente dice directo / sin escalas en cualquiera de los dos textos
        if any(k in t1 for k in DIRECTO_KEYWORDS) or any(k in t2 for k in DIRECTO_KEYWORDS):
            return True

        # 2) Si menciona escalas/paradas/boletos separados en cualquiera de los dos textos
        if any(k in t1 for k in ESCALA_KEYWORDS) or any(k in t2 for k in ESCALA_KEYWORDS):
            return False

        # 3) Fallback sensato: si no encontramos nada que diga "escala" o "parada",
        # asumimos DIRECTO (porque Google suele siempre escribir "1 escala" cuando la hay).
        return True


    
    def normalizar_hora(hora_str: str):
        """
        Normaliza el formato de hora que devuelve Google Flights,
        eliminando caracteres extraños y asegurando AM/PM estándar.
        """
        hora = hora_str.lower().replace(".", "").replace(" ", "")
        hora = hora.replace("am", "AM").replace("pm", "PM")
        return hora.upper()

    mejores_vuelos = []

    for vuelo in vuelos:
        try:
            texto_tarjeta = ""
            try:
                texto_tarjeta = vuelo.text
            except:
                texto_tarjeta = ""
            try:
                hora_salida_raw = vuelo.find_element(By.CSS_SELECTOR, '[aria-label^="Hora de salida"]').text.strip()
            except:
                hora_salida_raw = ""

            if not hora_salida_raw:
                continue  # no se pudo extraer hora de salida

            # Normalizar y convertir a datetime
            try:
                hora_norm = normalizar_hora(hora_salida_raw)
                salida_dt = datetime.strptime(hora_norm, "%I:%M%p")
            except Exception as e:
                _p(f"[ERROR parseando hora de salida] {hora_salida_raw} -> {e}")
                continue

       
            if not (5 <= salida_dt.hour < 12):
                continue
            try:
                hora_llegada = vuelo.find_element(By.CSS_SELECTOR, '[aria-label^="Hora de llegada"]').text.strip()
            except:
                hora_llegada = ""
            try:
                duracion = vuelo.find_element(By.CSS_SELECTOR, '[aria-label^="Duración total"]').text.strip()
            except:
                duracion = ""
            try:
                precio = vuelo.find_element(By.CSS_SELECTOR, 'span[aria-label*="pesos colombianos"]').text.strip()
            except:
                precio = ""
            try:
                aerolinea = vuelo.find_element(By.CSS_SELECTOR, '.sSHqwe span').text.strip()
            except:
                aerolinea = ""
            try:
                tipo_vuelo = vuelo.find_element(By.CSS_SELECTOR, 'div[aria-label^="Vuelo"]').text.strip().lower()
            except:
                tipo_vuelo = ""

            # Validar campos
            if not all([hora_llegada, duracion, precio, aerolinea]):
                continue

            # Convertir duración a minutos
            duracion_min = 0
            horas_match = re.search(r"(\d+)\s*h", duracion)
            minutos_match = re.search(r"(\d+)\s*min", duracion)

            if horas_match:
                duracion_min += int(horas_match.group(1)) * 60
            if minutos_match:
                duracion_min += int(minutos_match.group(1))

            if duracion_min == 0:
                duracion_min = 9999  # Valor inválido por defecto si no se logró extraer duración

            # Convertir precio a número
            precio_num = int(re.sub(r"[^\d]", "", precio))
            es_directo = es_vuelo_directo(tipo_vuelo, texto_tarjeta)

            # Guardar
            mejores_vuelos.append({
                "aerolinea": aerolinea,
                "hora_salida": hora_salida_raw,
                "hora_llegada": hora_llegada,
                "duracion_min": duracion_min,
                "precio": precio,
                "precio_num": precio_num,
                "directo": es_directo,

            })

        except Exception as e:
            _p("Error extrayendo vuelo: " + str(e))

    # Elegir el mejor
    def formato_duracion(minutos):
        if minutos < 60:
            return f"{minutos} minutos"
        horas = minutos // 60
        mins = minutos % 60
        if mins == 0:
            return f"{horas} hora{'s' if horas > 1 else ''}"
        return f"{horas} hora{'s' if horas > 1 else ''} y {mins} minutos"

    if mejores_vuelos:
    # Filtrar solo vuelos con duración <= 10 horas (600 min)
        candidatos = [v for v in mejores_vuelos if v["duracion_min"] <= 600]

        if candidatos:
        # Ordenar primero por precio, luego duración
            candidatos.sort(key=lambda x: (x["precio_num"], x["duracion_min"]))
            mejor = candidatos[0]

            tipo = "Directo" if mejor["directo"] else "Con escala"
            duracion_total = mejor['duracion_min']
            duracion_legible = formato_duracion(duracion_total)

            # Formato legible
            fecha_ida_legible = datetime.strptime(fecha_ida, "%Y-%m-%d").strftime("%d de %B de %Y")
            fecha_regreso_legible = datetime.strptime(fecha_regreso, "%Y-%m-%d").strftime("%d de %B de %Y")

            # Imprimir encabezado con fechas
            _p("Búsqueda para:")
            _p(f" Fecha de ida: {fecha_ida_legible}")
            _p(f" Fecha de regreso: {fecha_regreso_legible}\n")

            _p("Mejor opción de vuelo IDA encontrada:")
            _p(f" Aerolínea: {mejor['aerolinea']}")
            _p(f" Salida: {mejor['hora_salida']}  Llegada: {mejor['hora_llegada']}")
            _p(f" Duración: {duracion_legible}")
            _p(f" Tipo: {tipo}")
        else:
            _p(" No se encontraron vuelos de ida dentro del límite de 10 horas.")
    else:
        _p(" No se encontraron vuelos que cumplan todos los criterios.")


    # ==========================================================
    # ABRIR LA PÁGINA DE REGRESO DESDE EL MEJOR VUELO DE IDA
    # (añadir justo antes de driver.quit())
    # ==========================================================
    try:
        if mejores_vuelos and candidatos:  # solo si hubo ida válida
            # Buscar en la lista visible el <li> que coincide con el "mejor" de ida
            hizo_click_ida = False
            for li in driver.find_elements(By.CSS_SELECTOR, 'ul.Rk10dc > li.pIav2d'):
                try:
                    al = li.find_element(By.CSS_SELECTOR, '.sSHqwe span').text.strip()
                    hs = li.find_element(By.CSS_SELECTOR, '[aria-label^="Hora de salida"]').text.strip()
                    hl = li.find_element(By.CSS_SELECTOR, '[aria-label^="Hora de llegada"]').text.strip()

                    if al.startswith(mejor['aerolinea']) and hs == mejor['hora_salida'] and hl == mejor['hora_llegada']:
                        try:
                            btn = li.find_element(By.XPATH, './/button[.//span[normalize-space()="Seleccionar vuelo"]]')
                            driver.execute_script("arguments[0].click();", btn)
                        except:
                            driver.execute_script("arguments[0].click();", li)
                        hizo_click_ida = True
                        break
                except:
                    continue

            if not hizo_click_ida:
                _p("No pude identificar el botón del vuelo de ida seleccionado. Intento con el primer botón visible…")
                try:
                    btn_cualquiera = driver.find_element(By.XPATH, '(//button[.//span[normalize-space()="Seleccionar vuelo"]])[1]')
                    driver.execute_script("arguments[0].click();", btn_cualquiera)
                except:
                    pass

            # Esperar a que aparezca la sección "Regreso"
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, '//span[normalize-space()="Regreso"]')))
            except:
                time.sleep(2)

            time.sleep(1)  # margen para que carguen las tarjetas

            # ----------------------------------------------------------
            # CAPTURAR Y EVALUAR VUELOS DE REGRESO
            # ----------------------------------------------------------
            tarjetas_regreso = [c for c in driver.find_elements(By.CSS_SELECTOR, 'div.yR1fYc') if c.is_displayed()]
            candidatos_regreso = []

            for card in tarjetas_regreso:
                try:
                    texto_card = card.text if card.text else ""

                    hora_salida_r = card.find_element(By.CSS_SELECTOR, '[aria-label^="Hora de salida"]').text.strip()
                    hora_llegada_r = card.find_element(By.CSS_SELECTOR, '[aria-label^="Hora de llegada"]').text.strip()
                    duracion_r = card.find_element(By.CSS_SELECTOR, '[aria-label^="Duración total"]').text.strip()
                    precio_r = card.find_element(By.CSS_SELECTOR, 'span[aria-label*="pesos colombianos"]').text.strip()
                    aerolinea_r = card.find_element(By.CSS_SELECTOR, '.sSHqwe span').text.strip()

                    try:
                        tipo_vuelo_r = card.find_element(By.CSS_SELECTOR, 'div[aria-label^="Vuelo"]').text.strip().lower()
                    except:
                        tipo_vuelo_r = ""

                    salida_dt_r = datetime.strptime(hora_salida_r.replace(".", "").lower(), "%I:%M %p")
                    if salida_dt_r.hour < 12:  # solo después del mediodía
                        continue

                    # Duración a minutos
                    dur_min_r = 0
                    hm = re.search(r"(\d+)\s*h", duracion_r)
                    mm = re.search(r"(\d+)\s*min", duracion_r)
                    if hm:
                        dur_min_r += int(hm.group(1)) * 60
                    if mm:
                        dur_min_r += int(mm.group(1))
                    if dur_min_r == 0:
                        dur_min_r = 9999

                    # Filtrar > 10 horas
                    if dur_min_r > 600:
                        continue

                    # Precio a número
                    precio_num_r = int(re.sub(r"[^\d]", "", precio_r))

                    candidatos_regreso.append({
                        "aerolinea": aerolinea_r,
                        "hora_salida": hora_salida_r,
                        "hora_llegada": hora_llegada_r,
                        "duracion_min": dur_min_r,
                        "precio": precio_r,
                        "precio_num": precio_num_r,
                        "directo": es_vuelo_directo(tipo_vuelo_r, texto_card),
                    })
                except:
                    continue

            if candidatos_regreso:
                # Ordenar por precio primero, luego duración
                candidatos_regreso.sort(key=lambda x: (x["precio_num"], x["duracion_min"]))
                mejor_regreso = candidatos_regreso[0]

                _p("\nMejor opción de vuelo de REGRESO encontrado:")
                _p(f" Aerolínea: {mejor_regreso['aerolinea']}")
                _p(f" Salida: {mejor_regreso['hora_salida']}  Llegada: {mejor_regreso['hora_llegada']}")
                _p(f" Duración: {formato_duracion(mejor_regreso['duracion_min'])}")
                _p(f" Tipo: {'Directo' if mejor_regreso['directo'] else 'Con escala'}")
                _p("\nPRECIO DEL VUELO:")
                _p(f"Precio: {mejor_regreso['precio']}")
            else:
                _p("\nNo se encontraron vuelos de regreso dentro del límite de 10 horas.")
        else:
            _p("\nNo había vuelos de ida válidos, por eso no se abrió la página de regreso.")
    except Exception as e:
        _p("\nError al abrir/leer la sección de regreso: " + str(e))

    driver.quit()
    return "\n".join(salida_final)
