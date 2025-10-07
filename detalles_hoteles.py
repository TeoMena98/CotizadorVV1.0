# detalles_hoteles.py
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from utils import esperar_paneles_habitacion
from hoteles import (
    aceptar_cookies,
    aplicar_filtros_iniciales,
    aplicar_filtros_todo_incluido,
    obtener_hoteles_ordenados,
    buscar_y_agregar_hotel,
    obtener_trm_actual,
    buscar_hoteles
)


def obtener_info_hotel(driver, wait, hotel_element):
    try:
        enlace = hotel_element.find_element(
            By.XPATH, ".//a[contains(@class,'c-card__button--details')]"
        ).get_attribute("href")
    except:
        return None

    driver.execute_script("window.open(arguments[0], '_blank');", enlace)
    driver.switch_to.window(driver.window_handles[-1])

    info_habitaciones = []

    try:
        wait.until(EC.presence_of_element_located((By.ID, "sheethotelName")))

        try:
            btn_ver_opciones = driver.find_element(
                By.XPATH, "//a[contains(text(),'Ver opciones') or contains(text(),'View options')]"
            )
            btn_ver_opciones.click()
        except:
            pass

        if not esperar_paneles_habitacion(driver, wait, timeout=15):
            print(f"[ADVERTENCIA] No se cargaron habitaciones del hotel: {hotel_element.get_attribute('data-hotelname')}")
            return None

        habitaciones = driver.find_elements(By.CSS_SELECTOR, ".hotelCombinationPanel")

        for hab in habitaciones:
            try:
                hab_nombre = hab.find_element(By.CSS_SELECTOR, ".dev-room").text.strip()
                plan = hab.find_element(By.CSS_SELECTOR, ".dev-mealplan").text.strip()
                precio_txt = hab.find_element(By.CSS_SELECTOR, ".dev-combination-price p").text.strip()
                precio_num = float(precio_txt.replace("COP", "").replace("$", "").replace(".", "").replace(",", "").strip())
                try:
                    cancelacion = hab.find_element(By.XPATH, ".//*[contains(translate(., 'CANCELACION','cancelacion'),'cancelacion')]").text.strip()
                except:
                    cancelacion = "No especificada"
                info_habitaciones.append((hab_nombre, plan, precio_num, cancelacion))
            except:
                continue

        return info_habitaciones if info_habitaciones else None

    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])


def mostrar_hoteles_legible(hoteles_info, nombre_hotel="Hotel"):
    if hoteles_info and isinstance(hoteles_info[0], list):
        hoteles_info = [hab for sub in hoteles_info for hab in sub]

    for idx, hab in enumerate(hoteles_info[:1], start=1):
        try:
            nombre_hab, plan, precio, cancelacion_full = hab
            cancelacion_linea = ""
            for line in cancelacion_full.split("\n"):
                if "Cancel" in line or "cancel" in line:
                    cancelacion_linea = line
                    break
        except Exception as e:
            print(f"[ERROR] No se pudo mostrar la habitación: {hab} -> {e}")


def main(driver, wait, URL, DESTINO, ORIGEN, CHECKIN_ddmmyyyy, CHECKOUT_ddmmyyyy, ADULTOS, NINOS, noches, edades_ninos, edades_infantes):
    driver.get(URL)
    aceptar_cookies(driver, wait)
    buscar_hoteles(driver, wait, DESTINO, CHECKIN_ddmmyyyy, CHECKOUT_ddmmyyyy, ADULTOS, NINOS, edades_ninos, edades_infantes)
    

    wait.until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, "div.dev-incremental-completed"),
            "Búsqueda completada"
        )
    )

    aplicar_filtros_iniciales(driver, wait)
    lista_hoteles = obtener_hoteles_ordenados(driver, wait, NINOS)

    if NINOS > 0:
        lista_hoteles = [h for h in lista_hoteles if "adults only" not in h[0].lower()]

    datos = None
    trm_actual = obtener_trm_actual()

    if lista_hoteles:
        hotel_base = obtener_info_hotel(driver, wait, lista_hoteles[0][2])

        adicionales = []
        for h in lista_hoteles[1:3]:
            info = obtener_info_hotel(driver, wait, h[2])
            if info:
                adicionales.append(info)
            else:
                print(f"[ADVERTENCIA] No se pudo obtener info del hotel: {h[0]}")

        datos = {
            "destino": DESTINO,
            "checkin": CHECKIN_ddmmyyyy,
            "checkout": CHECKOUT_ddmmyyyy,
            "adultos": ADULTOS,
            "ninos": NINOS,
            "TRM": trm_actual,
            "hotel_base": {
                "nombre": lista_hoteles[0][0],
                "habitaciones": [
                    {
                        "habitacion": hab[0],
                        "plan": hab[1],
                        "precio_num": int(hab[2]),
                        "precio_str": f"${int(hab[2]):,} COP",
                        "cancelacion": hab[3]
                    }
                    for hab in hotel_base
                ]
            },
            "hoteles_adicionales": [
                {
                    "nombre": lista_hoteles[i+1][0],
                    "habitaciones": [
                        {
                            "habitacion": hab[0],
                            "plan": hab[1],
                            "precio_num": int(hab[2]),
                            "precio_str": f"${int(hab[2]):,} COP",
                            "cancelacion": hab[3]
                        }
                        for hab in adicionales[i]
                    ]
                }
                for i in range(len(adicionales))
            ]
        }

        valor_persona = hotel_base[0][2]
        valor_total = valor_persona * (datos["adultos"] + datos["ninos"])

        datos["valor_persona"] = f"${valor_persona:,.0f} COP"
        datos["valor_total"] = f"${valor_total:,.0f} COP"

        nro_personas = datos["adultos"] + datos["ninos"]
        asistencia = 1.2 * nro_personas * noches * trm_actual * 1.15
        asistencia_str = f"${int(asistencia):,.0f} COP"
        valor_total_con_asistencia = valor_total + asistencia

        datos["asistencia"] = asistencia_str
        datos["valor_total_con_asistencia"] = f"${int(valor_total_con_asistencia):,.0f} COP"
    else:
        print("[ERROR] No se encontraron hoteles tras aplicar filtros iniciales.")
        return None

    # === HOTELS TODO INCLUIDO ===
    aplicar_filtros_todo_incluido(driver, wait)
    lista_ti = obtener_hoteles_ordenados(driver, wait, NINOS)

    if lista_ti:
        hoteles_todo_incluido = []

        # 1) Agregar hoteles hasta 10 por precio
        for h in lista_ti:
            if not any(ht["nombre"].lower() == h[0].lower() for ht in hoteles_todo_incluido):
                info = obtener_info_hotel(driver, wait, h[2])
                if not info:
                    continue
                primera = info[0]
                hoteles_todo_incluido.append({
                    "nombre": h[0],
                    "habitaciones": [{
                        "habitacion": primera[0],
                        "plan": primera[1],
                        "precio_num": int(primera[2]),
                        "precio_str": f"${int(primera[2]):,} COP",
                        "cancelacion": primera[3]
                    }]
                })
            if len(hoteles_todo_incluido) == 10:
                break

        # 2) Validar obligatorios
        marcas_objetivo = [
            ["riu republica", "riu palace"],
            ["palladium"],
            ["ocean blue and sand", "ocean el faro"],
            ["grand sirenis"],
            ["hard rock"],
            ["nickelodeon"]
        ]
        obligatorios_flat = {n for g in marcas_objetivo for n in g}

        for grupo in marcas_objetivo:
            ya_esta = any(
                any(nombre in h["nombre"].lower() for nombre in grupo)
                for h in hoteles_todo_incluido
            )
            if ya_esta:
                continue

            for nombre in grupo:
                hotel_obligatorio = buscar_y_agregar_hotel(driver, wait, nombre)

                # ✅ Validación añadida: excluir Adults Only si hay niños
                if hotel_obligatorio and NINOS > 0 and "adults only" in hotel_obligatorio["nombre"].lower():
                    print(f"[INFO] Se omitió {hotel_obligatorio['nombre']} por ser Adults Only (hay niños).")
                    continue

                if hotel_obligatorio and not any(
                    h["nombre"].lower() == hotel_obligatorio["nombre"].lower()
                    for h in hoteles_todo_incluido
                ):
                    if len(hoteles_todo_incluido) >= 10:
                        no_obligatorios = [
                            h for h in hoteles_todo_incluido
                            if not any(o in h["nombre"].lower() for o in obligatorios_flat)
                        ]
                        if no_obligatorios:
                            no_obligatorios.sort(key=lambda x: x["habitaciones"][0]["precio_num"])
                            eliminado = no_obligatorios[-1]
                            hoteles_todo_incluido.remove(eliminado)
                            print(f"[INFO] Reemplazado {eliminado['nombre']} por obligatorio {hotel_obligatorio['nombre']}")
                        else:
                            hoteles_todo_incluido.sort(key=lambda x: x["habitaciones"][0]["precio_num"])
                            eliminado = hoteles_todo_incluido.pop(-1)
                            print(f"[INFO] Reemplazado {eliminado['nombre']} (obligatorio) por {hotel_obligatorio['nombre']}")
                    hoteles_todo_incluido.append(hotel_obligatorio)
                    break

        # 3) Si faltan, rellenar hasta 10
        if len(hoteles_todo_incluido) < 10:
            for h in lista_ti:
                if not any(ht["nombre"].lower() == h[0].lower() for ht in hoteles_todo_incluido):
                    info = obtener_info_hotel(driver, wait, h[2])
                    if not info:
                        continue
                    primera = info[0]
                    hoteles_todo_incluido.append({
                        "nombre": h[0],
                        "habitaciones": [{
                            "habitacion": primera[0],
                            "plan": primera[1],
                            "precio_num": int(primera[2]),
                            "precio_str": f"${int(primera[2]):,} COP",
                            "cancelacion": primera[3]
                        }]
                    })
                if len(hoteles_todo_incluido) == 10:
                    break

        # 4) Ordenar por precio y dejar solo 10
        hoteles_todo_incluido.sort(key=lambda h: h["habitaciones"][0]["precio_num"])
        datos["hoteles_todo_incluido"] = hoteles_todo_incluido[:10]

        return datos
    else:
        print("[ERROR] No se encontraron hoteles tras aplicar filtros todo incluido.")
        return datos
