# main.py
import json
import re
import sys
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import tkinter as tk
from tkinter import messagebox

from utils import generar_pdf, parse_vuelo, obtener_trm_actual  # utils.py
from detalles_hoteles import main as detalles_main  # detalles_hoteles.py
# hoteles.py and habitaciones.py are used indirectly by detalles_hoteles

URL = "https://viajavipco.paquetedinamico.com/accommodation/onlyAccommodationAvail.xhtml?tripId=1&availPosition=1"

def _ensure_list_from_arg(x):
    """
    A helper to accept either a JSON string (e.g. '[2,5]') or a Python list.
    """
    if x is None:
        return []
    if isinstance(x, str):
        try:
            return json.loads(x)
        except Exception:
            # try to parse single-number strings
            try:
                return [int(x)]
            except:
                return []
    if isinstance(x, (list, tuple)):
        return list(x)
    return [x]


def run_cotizacion(
    json_file,            # ruta al JSON temporal que crea interfaz.py
    fecha_ida,            # 'YYYY-MM-DD'
    fecha_regreso,        # 'YYYY-MM-DD'
    adultos,              # int or str
    ninos,                # int or str
    infantes,             # int or str
    destino,              # string (ej. "Punta Cana")
    origen,               # string
    edades_ninos_arg,     # JSON string or list
    edades_infantes_arg,  # JSON string or list
    telefono              # string
):
    """
    Ejecuta el flujo completo que antes corría en 'primero.py' cuando se llamaba desde la línea de comandos.
    Retorna un dict con keys:
      - 'error' si hubo error (string)
      - 'datos' si todo fue OK (el dict generado)
      - 'logs' con la salida impresa (string) -- aquí preservamos prints; pero devolvemos None si no se usa.
    """
    salida_logs = []

    def _p(msg):
        try:
            print(msg)
        except:
            # evitar fallos si stdout no acepta algún caracter
            try:
                print(str(msg).encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
            except:
                pass
        salida_logs.append(str(msg))

    # Leer JSON (payload) tal como hacía tu script original
    try:
        with open(json_file, encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        err = f"❌ Error al leer JSON: {e}"
        _p(err)
        return {"error": err, "logs": "\n".join(salida_logs)}

    contenido_salida = payload.get("resumen", "")
    precio_raw = str(payload.get("precio", "0"))
    try:
        precio_vuelo = int(re.sub(r"[^\d]", "", precio_raw))
    except:
        precio_vuelo = 0
    precio_vuelo_str = f"${precio_vuelo:,.0f} COP"

    # Normalizar tipos
    adultos = int(adultos)
    ninos = int(ninos)
    infantes = int(infantes)
    edades_ninos = _ensure_list_from_arg(edades_ninos_arg)
    edades_infantes = _ensure_list_from_arg(edades_infantes_arg)

    # Formatear fechas como lo hacía la versión original (DD/MM/YYYY)
    try:
        from datetime import datetime
        checkin_dt = datetime.strptime(fecha_ida, "%Y-%m-%d").strftime("%d/%m/%Y")
        checkout_dt = datetime.strptime(fecha_regreso, "%Y-%m-%d").strftime("%d/%m/%Y")
        # volver a datetime como antes (se usa en noches)
        checkin_dt_dt = datetime.strptime(checkin_dt, "%d/%m/%Y")
        checkout_dt_dt = datetime.strptime(checkout_dt, "%d/%m/%Y")
        CHECKIN_ddmmyyyy = checkin_dt_dt.strftime("%d/%m/%Y")
        CHECKOUT_ddmmyyyy = checkout_dt_dt.strftime("%d/%m/%Y")
        noches = (checkout_dt_dt - checkin_dt_dt).days
    except Exception as e:
        err = f"❌ Error al parsear fechas: {e}"
        _p(err)
        return {"error": err, "logs": "\n".join(salida_logs)}

    # Lanzar navegador (igual que en tu main original)
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-backgrounding-occluded-windows")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 25)
    except Exception as e:
        err = f"❌ No se pudo iniciar WebDriver: {e}"
        _p(err)
        return {"error": err, "logs": "\n".join(salida_logs)}

    datos = None
    try:
        # Llamar al flujo principal que está en detalles_hoteles.main
        datos = detalles_main(
            driver=driver,
            wait=wait,
            URL=URL,
            DESTINO=destino,
            ORIGEN=origen,
            CHECKIN_ddmmyyyy=CHECKIN_ddmmyyyy,
            CHECKOUT_ddmmyyyy=CHECKOUT_ddmmyyyy,
            ADULTOS=adultos,
            NINOS=ninos,
            noches=noches,
            edades_ninos=edades_ninos,
            edades_infantes=edades_infantes
        )

        if not datos:
            _p("❌ No se generó ninguna cotización.")
            try:
                driver.quit()
            except:
                pass
            return {"error": "No se generó ninguna cotización.", "logs": "\n".join(salida_logs)}

        # Agregar info de vuelo parseada
        datos["vuelo_ida"] = parse_vuelo(contenido_salida, "Vuelo de ida")
        datos["vuelo_regreso"] = parse_vuelo(contenido_salida, "Vuelo de regreso")

        datos["contenido_salida"] = contenido_salida
        datos["precio_vuelo"] = precio_vuelo
        datos["precio_vuelo_str"] = precio_vuelo_str
        datos["noches"] = payload.get("noches", noches)
        datos["origen"] = origen
        datos["destino"] = destino

        # Generar PDF (usa la función exacta que tenías)
        try:
            pdf_path = generar_pdf(datos, telefono)
            _p(f"PDF generado correctamente en: {pdf_path}")
        except Exception as e:
            _p("[ERROR] Error generando PDF, Vuelve a intentarlo")
            print(f"Detalles técnicos: {e}")

    except Exception as e:
        _p("[ERROR] Vuelve a intentarlo")
        # Para desarrolladores (no se muestra al usuario)
        print(f"Detalles técnicos: {e}")

        try:
            driver.quit()
        except:
            pass
        return {"error": str(e), "logs": "\n".join(salida_logs)}

    # Cerrar navegador
    try:
        driver.quit()
    except:
        pass

    # Mostrar popup como en tu script original
    try:
        def mostrar_popup():
            popup_root = tk.Tk()
            popup_root.title("Aviso")
            popup_root.lift()
            popup_root.attributes('-topmost', True)
            popup_root.after_idle(popup_root.attributes, '-topmost', False)
            messagebox.showinfo("Éxito", "PDF generado correctamente")
            popup_root.destroy()

    # Ejecutar en el hilo principal
        tk._default_root.after(0, mostrar_popup) if tk._default_root else mostrar_popup()

    except Exception as e:
        _p(f"[WARN] No se pudo mostrar popup: {e}")

    return {"datos": datos, "logs": "\n".join(salida_logs)}