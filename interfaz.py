from tkcalendar import DateEntry 
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import locale
import os
import shutil
import json
import tempfile
import re
from datetime import date, timedelta
import sys
# Detecta la codificación del sistema
encoding_sistema = locale.getpreferredencoding()
contenido_salida = ""
# Variable para controlar la animación
animando = False
pos_animacion = 0
# Variables para animación de cotización
animando_coti = False
pos_animacion_coti = 0

mensaje_base = "Cargando resultados... "
mensaje_coti = "Generando cotizacion... "

def escribir_salida(texto):
    global contenido_salida
    salida_text.insert(tk.END, texto + "\n")
    salida_text.see(tk.END)  # hace scroll automático
    contenido_salida += texto + "\n"


from datetime import datetime, timedelta

def vuelo_manual():
    def formatear_hora(hora, minuto, meridiano):
        try:
            hora_str = f"{hora}:{minuto} {meridiano}"
            dt = datetime.strptime(hora_str, "%I:%M %p")
        # salida estilo automático → "5:04 a.m."
            return dt.strftime("%-I:%M %p").lower().replace("am", "a.m.").replace("pm", "p.m.")
        except:
            return hora_str
    
    def calcular_duracion(hora_salida, minuto_salida, meridiano_salida,
                      hora_llegada, minuto_llegada, meridiano_llegada,
                      entry_destino, escalas_entries=None):
        try:
            salida_str = f"{hora_salida.get()}:{minuto_salida.get()} {meridiano_salida.get()}"
            llegada_str = f"{hora_llegada.get()}:{minuto_llegada.get()} {meridiano_llegada.get()}"

            formato = "%I:%M %p"
            salida_dt = datetime.strptime(salida_str, formato)
            llegada_dt = datetime.strptime(llegada_str, formato)

            if llegada_dt <= salida_dt:
                llegada_dt += timedelta(days=1)

            diff = llegada_dt - salida_dt

            if escalas_entries:
                for horas_e, minutos_e in escalas_entries:
                    try:
                        diff += timedelta(hours=int(horas_e.get()), minutes=int(minutos_e.get()))
                    except:
                        pass

            horas, resto = divmod(diff.seconds, 3600)
            minutos = resto // 60

            # Construir texto con singular/plural
            if horas > 0 and minutos > 0:
                duracion = f"Duración: {horas} {'hora' if horas == 1 else 'horas'} y {minutos} {'minuto' if minutos == 1 else 'minutos'}"
            elif horas > 0:
                duracion = f"Duración: {horas} {'hora' if horas == 1 else 'horas'}"
            else:
                duracion = f"Duración: {minutos} {'minuto' if minutos == 1 else 'minutos'}"

            entry_destino.config(state="normal")
            entry_destino.delete(0, tk.END)
            entry_destino.insert(0, duracion)
            entry_destino.config(state="readonly")

        except Exception as e:
            print("Error calculando duración:", e)


    def crear_inputs_escalas(frame, num_var, lista_frames, row_inicio, 
                             salida_hora, salida_minuto, salida_meridiano,
                             llegada_hora, llegada_minuto, llegada_meridiano,
                             entry_duracion):
        for f in lista_frames:
            f.destroy()
        lista_frames.clear()

        try:
            n = int(num_var.get())
        except:
            n = 0

        escalas_entries = []
        for i in range(n):
            f = tk.Frame(frame, bg="black")
            f.grid(row=row_inicio+i, column=0, columnspan=2, pady=2, sticky="w")

            tk.Label(f, text=f"Escala {i+1} (h:m):", fg="white", bg="black").pack(side=tk.LEFT, padx=5)
            h = tk.Spinbox(f, from_=0, to=12, width=3, justify="center")
            h.pack(side=tk.LEFT, padx=2)
            m = tk.Spinbox(f, from_=0, to=59, increment=5, width=3, justify="center")
            m.pack(side=tk.LEFT, padx=2)

            # Bind automático para recalcular si cambian horas/minutos de escalas
            h.bind("<FocusOut>", lambda e: calcular_duracion(salida_hora, salida_minuto, salida_meridiano,
                                                             llegada_hora, llegada_minuto, llegada_meridiano,
                                                             entry_duracion, escalas_entries))
            m.bind("<FocusOut>", lambda e: calcular_duracion(salida_hora, salida_minuto, salida_meridiano,
                                                             llegada_hora, llegada_minuto, llegada_meridiano,
                                                             entry_duracion, escalas_entries))

            escalas_entries.append((h, m))
            lista_frames.append(f)

        calcular_duracion(salida_hora, salida_minuto, salida_meridiano,
                          llegada_hora, llegada_minuto, llegada_meridiano,
                          entry_duracion, escalas_entries)

        return escalas_entries

    def guardar_vuelo():
        salida_ida = formatear_hora(
    entrada_salida_ida_hora.get(),
    entrada_salida_ida_minuto.get(),
    entrada_salida_ida_meridiano.get()
)
        llegada_ida = formatear_hora(
    entrada_llegada_ida_hora.get(),
    entrada_llegada_ida_minuto.get(),
    entrada_llegada_ida_meridiano.get()
)

        salida_regreso = formatear_hora(
    entrada_salida_regreso_hora.get(),
    entrada_salida_regreso_minuto.get(),
    entrada_salida_regreso_meridiano.get()
)
        llegada_regreso = formatear_hora(
    entrada_llegada_regreso_hora.get(),
    entrada_llegada_regreso_minuto.get(),
    entrada_llegada_regreso_meridiano.get()
)

        fecha_ida = entrada_fecha_ida.get_date().strftime("%d/%m/%Y")
        fecha_regreso = entrada_fecha_regreso.get_date().strftime("%d/%m/%Y")
        aerolinea_ida = entrada_aerolinea_ida.get()
        duracion_ida = entrada_duracion_ida.get()
        tipo_ida = entrada_tipo_ida.get()

        aerolinea_regreso = entrada_aerolinea_regreso.get()
        duracion_regreso = entrada_duracion_regreso.get()
        tipo_regreso = entrada_tipo_regreso.get()

        precio = entrada_precio.get()

        resultado = f"""
Búsqueda para:
 Fecha de ida: {fecha_ida}
 Fecha de regreso: {fecha_regreso}

Mejor opción de vuelo IDA encontrada:
 Aerolínea: {aerolinea_ida}
 Salida: {salida_ida}  Llegada: {llegada_ida}
 Duración: {duracion_ida}
 Tipo: {tipo_ida}

Mejor opción de vuelo de REGRESO encontrado:
 Aerolínea: {aerolinea_regreso}
 Salida: {salida_regreso}  Llegada: {llegada_regreso}
 Duración: {duracion_regreso}
 Tipo: {tipo_regreso}

PRECIO DEL VUELO:
Precio: {precio}
"""
        salida_text.delete(1.0, tk.END)
        escribir_salida(resultado.strip())
        boton_cotizacion.pack(side=tk.LEFT, padx=5)
        ventana_manual.destroy()

    ventana_manual = tk.Toplevel(ventana)
    ventana_manual.title("✍ Ingresar Vuelo Manual")
    ventana_manual.configure(bg="black")

    tk.Label(ventana_manual, text="Formulario de Vuelo Manual",
             font=("Arial", 16, "bold"), fg="white", bg="black").pack(pady=10)

    frame_form = tk.Frame(ventana_manual, bg="black")
    frame_form.pack(padx=20, pady=10)

    def crear_fila(parent, texto, row, default="", readonly=False):
        lbl = tk.Label(parent, text=texto, fg="white", bg="black", font=("Arial", 11))
        lbl.grid(row=row, column=0, sticky="e", padx=5, pady=4)
        entry = tk.Entry(parent, width=25, state="readonly" if readonly else "normal")
        if default:
            entry.insert(0, default)
        entry.grid(row=row, column=1, padx=5, pady=4)
        return entry

    # --- IDA ---
    tk.Label(frame_form, text="✈ Vuelo de IDA", font=("Arial", 13, "bold"), fg="cyan", bg="black").grid(row=0, column=0, columnspan=2, pady=(5, 10))

    entrada_fecha_ida = DateEntry(frame_form, width=12, background="darkblue", foreground="white",
                                  borderwidth=2, date_pattern='dd/MM/yyyy', locale='es_ES',
                                  state="readonly", mindate=date.today())
    entrada_fecha_ida.grid(row=1, column=1, padx=5, pady=4)
    tk.Label(frame_form, text="Fecha Ida:", fg="white", bg="black").grid(row=1, column=0, sticky="e", padx=5, pady=4)

    entrada_aerolinea_ida = crear_fila(frame_form, "Aerolínea:", 2)

    # Hora salida IDA
    frame_salida_ida = tk.Frame(frame_form, bg="black")
    frame_salida_ida.grid(row=3, column=1, padx=5, pady=4)
    entrada_salida_ida_hora = tk.Spinbox(frame_salida_ida, from_=1, to=12, width=3, justify="center")
    entrada_salida_ida_hora.pack(side=tk.LEFT, padx=2)
    entrada_salida_ida_minuto = tk.Spinbox(frame_salida_ida, from_=0, to=59, increment=1, width=3, justify="center", format="%02.0f")
    entrada_salida_ida_minuto.pack(side=tk.LEFT, padx=2)
    entrada_salida_ida_meridiano = ttk.Combobox(frame_salida_ida, values=["AM", "PM"], width=5, state="readonly")
    entrada_salida_ida_meridiano.current(0)
    entrada_salida_ida_meridiano.pack(side=tk.LEFT, padx=2)
    tk.Label(frame_form, text="Hora salida:", fg="white", bg="black").grid(row=3, column=0, sticky="e", padx=5, pady=4)

    # Hora llegada IDA
    frame_llegada_ida = tk.Frame(frame_form, bg="black")
    frame_llegada_ida.grid(row=4, column=1, padx=5, pady=4)
    entrada_llegada_ida_hora = tk.Spinbox(frame_llegada_ida, from_=1, to=12, width=3, justify="center")
    entrada_llegada_ida_hora.pack(side=tk.LEFT, padx=2)
    entrada_llegada_ida_minuto = tk.Spinbox(frame_llegada_ida, from_=0, to=59, increment=1, width=3, justify="center", format="%02.0f")
    entrada_llegada_ida_minuto.pack(side=tk.LEFT, padx=2)
    entrada_llegada_ida_meridiano = ttk.Combobox(frame_llegada_ida, values=["AM", "PM"], width=5, state="readonly")
    entrada_llegada_ida_meridiano.current(0)
    entrada_llegada_ida_meridiano.pack(side=tk.LEFT, padx=2)
    tk.Label(frame_form, text="Hora llegada:", fg="white", bg="black").grid(row=4, column=0, sticky="e", padx=5, pady=4)

    entrada_duracion_ida = crear_fila(frame_form, "Duración:", 5, readonly=True)

    entrada_tipo_ida = ttk.Combobox(frame_form, values=["Directo", "Con escala"], width=15, state="readonly")
    entrada_tipo_ida.grid(row=6, column=1, padx=5, pady=4)
    tk.Label(frame_form, text="Tipo:", fg="white", bg="black").grid(row=6, column=0, sticky="e", padx=5, pady=4)

    num_escalas_ida = tk.StringVar(value="0")
    lista_escalas_ida = []

    def mostrar_escalas_ida(event=None):
        if entrada_tipo_ida.get() == "Con escala":
            spin = tk.Spinbox(frame_form, from_=1, to=5, textvariable=num_escalas_ida, width=5, justify="center")
            spin.grid(row=7, column=1, sticky="w", padx=5, pady=4)
            tk.Label(frame_form, text="Número de escalas:", fg="white", bg="black").grid(row=7, column=0, sticky="e", padx=5, pady=4)

            def crear_campos(_):
                crear_inputs_escalas(frame_form, num_escalas_ida, lista_escalas_ida, 8,
                                     entrada_salida_ida_hora, entrada_salida_ida_minuto, entrada_salida_ida_meridiano,
                                     entrada_llegada_ida_hora, entrada_llegada_ida_minuto, entrada_llegada_ida_meridiano,
                                     entrada_duracion_ida)
            spin.bind("<FocusOut>", crear_campos)
            spin.bind("<KeyRelease>", crear_campos)
        else:
            for f in lista_escalas_ida:
                f.destroy()
            lista_escalas_ida.clear()
            calcular_duracion(entrada_salida_ida_hora, entrada_salida_ida_minuto, entrada_salida_ida_meridiano,
                              entrada_llegada_ida_hora, entrada_llegada_ida_minuto, entrada_llegada_ida_meridiano,
                              entrada_duracion_ida)

    entrada_tipo_ida.bind("<<ComboboxSelected>>", mostrar_escalas_ida)

    # --- REGRESO ---
    tk.Label(frame_form, text="✈ Vuelo de REGRESO", font=("Arial", 13, "bold"), fg="cyan", bg="black").grid(row=20, column=0, columnspan=2, pady=(15, 10))

    entrada_fecha_regreso = DateEntry(frame_form, width=12, background="darkblue", foreground="white",
                                      borderwidth=2, date_pattern='dd/MM/yyyy', locale='es_ES',
                                      state="readonly", mindate=date.today())
    entrada_fecha_regreso.grid(row=21, column=1, padx=5, pady=4)
    tk.Label(frame_form, text="Fecha Regreso:", fg="white", bg="black").grid(row=21, column=0, sticky="e", padx=5, pady=4)

    entrada_aerolinea_regreso = crear_fila(frame_form, "Aerolínea:", 22)

    # Hora salida REGRESO
    frame_salida_regreso = tk.Frame(frame_form, bg="black")
    frame_salida_regreso.grid(row=23, column=1, padx=5, pady=4)
    entrada_salida_regreso_hora = tk.Spinbox(frame_salida_regreso, from_=1, to=12, width=3, justify="center")
    entrada_salida_regreso_hora.pack(side=tk.LEFT, padx=2)
    entrada_salida_regreso_minuto = tk.Spinbox(frame_salida_regreso, from_=0, to=59, increment=1, width=3, justify="center", format="%02.0f")
    entrada_salida_regreso_minuto.pack(side=tk.LEFT, padx=2)
    entrada_salida_regreso_meridiano = ttk.Combobox(frame_salida_regreso, values=["AM", "PM"], width=5, state="readonly")
    entrada_salida_regreso_meridiano.current(0)
    entrada_salida_regreso_meridiano.pack(side=tk.LEFT, padx=2)
    tk.Label(frame_form, text="Hora salida:", fg="white", bg="black").grid(row=23, column=0, sticky="e", padx=5, pady=4)

    # Hora llegada REGRESO
    frame_llegada_regreso = tk.Frame(frame_form, bg="black")
    frame_llegada_regreso.grid(row=24, column=1, padx=5, pady=4)
    entrada_llegada_regreso_hora = tk.Spinbox(frame_llegada_regreso, from_=1, to=12, width=3, justify="center")
    entrada_llegada_regreso_hora.pack(side=tk.LEFT, padx=2)
    entrada_llegada_regreso_minuto = tk.Spinbox(frame_llegada_regreso, from_=0, to=59, increment=1, width=3, justify="center", format="%02.0f")
    entrada_llegada_regreso_minuto.pack(side=tk.LEFT, padx=2)
    entrada_llegada_regreso_meridiano = ttk.Combobox(frame_llegada_regreso, values=["AM", "PM"], width=5, state="readonly")
    entrada_llegada_regreso_meridiano.current(0)
    entrada_llegada_regreso_meridiano.pack(side=tk.LEFT, padx=2)
    tk.Label(frame_form, text="Hora llegada:", fg="white", bg="black").grid(row=24, column=0, sticky="e", padx=5, pady=4)

    entrada_duracion_regreso = crear_fila(frame_form, "Duración:", 25, readonly=True)

    entrada_tipo_regreso = ttk.Combobox(frame_form, values=["Directo", "Con escala"], width=15, state="readonly")
    entrada_tipo_regreso.grid(row=26, column=1, padx=5, pady=4)
    tk.Label(frame_form, text="Tipo:", fg="white", bg="black").grid(row=26, column=0, sticky="e", padx=5, pady=4)

    num_escalas_regreso = tk.StringVar(value="0")
    lista_escalas_regreso = []

    def mostrar_escalas_regreso(event=None):
        if entrada_tipo_regreso.get() == "Con escala":
            spin = tk.Spinbox(frame_form, from_=1, to=5, textvariable=num_escalas_regreso, width=5, justify="center")
            spin.grid(row=27, column=1, sticky="w", padx=5, pady=4)
            tk.Label(frame_form, text="Número de escalas:", fg="white", bg="black").grid(row=27, column=0, sticky="e", padx=5, pady=4)

            def crear_campos(_):
                crear_inputs_escalas(frame_form, num_escalas_regreso, lista_escalas_regreso, 28,
                                     entrada_salida_regreso_hora, entrada_salida_regreso_minuto, entrada_salida_regreso_meridiano,
                                     entrada_llegada_regreso_hora, entrada_llegada_regreso_minuto, entrada_llegada_regreso_meridiano,
                                     entrada_duracion_regreso)
            spin.bind("<FocusOut>", crear_campos)
            spin.bind("<KeyRelease>", crear_campos)
        else:
            for f in lista_escalas_regreso:
                f.destroy()
            lista_escalas_regreso.clear()
            calcular_duracion(entrada_salida_regreso_hora, entrada_salida_regreso_minuto, entrada_salida_regreso_meridiano,
                              entrada_llegada_regreso_hora, entrada_llegada_regreso_minuto, entrada_llegada_regreso_meridiano,
                              entrada_duracion_regreso)

    entrada_tipo_regreso.bind("<<ComboboxSelected>>", mostrar_escalas_regreso)

    # --- PRECIO ---
        # --- PRECIO ---
    tk.Label(frame_form, text="💰 Precio", font=("Arial", 13, "bold"), fg="cyan", bg="black").grid(row=40, column=0, columnspan=2, pady=(15, 10))
    entrada_precio = crear_fila(frame_form, "Precio:", 41, "COP ")
    
    def format_precio(event=None):
    # Tomar solo dígitos del input
        valor = entrada_precio.get().replace("COP", "").replace(".", "").replace(",", "").strip()
        if valor.isdigit():
            numero = f"COP {int(valor):,}"  # COP 3,135,140
            # Evitar loop infinito al escribir
            entrada_precio.delete(0, tk.END)
            entrada_precio.insert(0, numero)

# Formatea cuando el usuario termina de escribir
    entrada_precio.bind("<FocusOut>", format_precio)
    entrada_precio.bind("<KeyRelease>", format_precio)

    # --- Bind automáticos para calcular duración IDA ---
    for widget in [entrada_salida_ida_hora, entrada_salida_ida_minuto, entrada_salida_ida_meridiano,
                   entrada_llegada_ida_hora, entrada_llegada_ida_minuto, entrada_llegada_ida_meridiano]:
        widget.bind("<FocusOut>", lambda e: calcular_duracion(
            entrada_salida_ida_hora, entrada_salida_ida_minuto, entrada_salida_ida_meridiano,
            entrada_llegada_ida_hora, entrada_llegada_ida_minuto, entrada_llegada_ida_meridiano,
            entrada_duracion_ida, lista_escalas_ida
        ))
        widget.bind("<<ComboboxSelected>>", lambda e: calcular_duracion(
            entrada_salida_ida_hora, entrada_salida_ida_minuto, entrada_salida_ida_meridiano,
            entrada_llegada_ida_hora, entrada_llegada_ida_minuto, entrada_llegada_ida_meridiano,
            entrada_duracion_ida, lista_escalas_ida
        ))

    # --- Bind automáticos para calcular duración REGRESO ---
    for widget in [entrada_salida_regreso_hora, entrada_salida_regreso_minuto, entrada_salida_regreso_meridiano,
                   entrada_llegada_regreso_hora, entrada_llegada_regreso_minuto, entrada_llegada_regreso_meridiano]:
        widget.bind("<FocusOut>", lambda e: calcular_duracion(
            entrada_salida_regreso_hora, entrada_salida_regreso_minuto, entrada_salida_regreso_meridiano,
            entrada_llegada_regreso_hora, entrada_llegada_regreso_minuto, entrada_llegada_regreso_meridiano,
            entrada_duracion_regreso, lista_escalas_regreso
        ))
        widget.bind("<<ComboboxSelected>>", lambda e: calcular_duracion(
            entrada_salida_regreso_hora, entrada_salida_regreso_minuto, entrada_salida_regreso_meridiano,
            entrada_llegada_regreso_hora, entrada_llegada_regreso_minuto, entrada_llegada_regreso_meridiano,
            entrada_duracion_regreso, lista_escalas_regreso
        ))

    # --- Botón Guardar ---
    boton_guardar = tk.Button(
        ventana_manual,
        text="💾 Guardar Vuelo",
        command=guardar_vuelo,
        font=("Arial", 12, "bold"),
        bg="#444444",
        fg="white",
        activebackground="#666666",
        activeforeground="white",
        relief="raised",
        width=20
    )
    boton_guardar.pack(pady=15)


def generar_resumen_vuelos(contenido):
    lineas = [l.strip() for l in contenido.splitlines() if l.strip()]

    fecha_ida = ""
    fecha_regreso = ""
    ida = {}
    regreso = {}
    precio_entero = 0
    precio_str = ""

    i = 0
    while i < len(lineas):
        l = lineas[i]
        if l.startswith("Fecha de ida:"):
            fecha_ida = l.split(":",1)[1].strip()
        elif l.startswith("Fecha de regreso:"):
            fecha_regreso = l.split(":",1)[1].strip()
        elif l == "Mejor opción de vuelo IDA encontrada:":
            ida["aerolinea"] = lineas[i+1].split(":",1)[1].strip()
            salida_llegada_linea = lineas[i+2]
            if "Salida:" in salida_llegada_linea and "Llegada:" in salida_llegada_linea:
                ida["salida"] = salida_llegada_linea.split("Salida:")[1].split("Llegada:")[0].strip()
                ida["llegada"] = salida_llegada_linea.split("Llegada:")[1].strip()
            ida["duracion"] = lineas[i+3].split(":",1)[1].strip()
            ida["tipo"] = lineas[i+4].split(":",1)[1].strip()
            i += 4
        elif l == "Mejor opción de vuelo de REGRESO encontrado:":
            regreso["aerolinea"] = lineas[i+1].split(":",1)[1].strip()
            salida_llegada_linea = lineas[i+2]
            if "Salida:" in salida_llegada_linea and "Llegada:" in salida_llegada_linea:
                regreso["salida"] = salida_llegada_linea.split("Salida:")[1].split("Llegada:")[0].strip()
                regreso["llegada"] = salida_llegada_linea.split("Llegada:")[1].strip()
            regreso["duracion"] = lineas[i+3].split(":",1)[1].strip()
            regreso["tipo"] = lineas[i+4].split(":",1)[1].strip()
            i += 4
        elif l.startswith("Precio:"):
            precio_str = l.split(":",1)[1].strip()
            # Convertir a entero seguro
            try:
                precio_entero = int("".join(filter(str.isdigit, precio_str)))
            except:
                precio_entero = 0
        i += 1

    resumen = []
    if ida:
        resumen.append(
            f"Vuelo de ida: {fecha_ida} - Aerolínea: {ida['aerolinea']} - Salida: {ida['salida']} Llegada: {ida['llegada']} - Duración: {ida['duracion']} - Tipo: {ida['tipo']}"
        )
    if regreso:
        resumen.append(
            f"Vuelo de regreso: {fecha_regreso} - Aerolínea: {regreso['aerolinea']} - Salida: {regreso['salida']} Llegada: {regreso['llegada']} - Duración: {regreso['duracion']} - Tipo: {regreso['tipo']}"
        )
    if precio_str:
        resumen.append(f"Precio del vuelo: {precio_str} (entero: {precio_entero})")

    # Devuelve resumen **y precio entero directamente**
    return "\n".join(resumen), precio_entero


def limpiar_cache():
    """
    Elimina carpetas __pycache__ y archivos .pyc
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)
        for f in files:
            if f.endswith(".pyc"):
                try:
                    os.remove(os.path.join(root, f))
                except:
                    pass

def animar_mensaje():
    global pos_animacion
    if animando:
        texto = mensaje_base[pos_animacion:] + mensaje_base[:pos_animacion]
        salida_text.delete(1.0, tk.END)
        salida_text.insert(tk.END, texto)
        pos_animacion = (pos_animacion + 1) % len(mensaje_base)
        ventana.after(150, animar_mensaje)  # Velocidad de animación

def animar_cotizacion():
    global pos_animacion_coti
    if animando_coti:
        texto = mensaje_coti[pos_animacion_coti:] + mensaje_coti[:pos_animacion_coti]

        # Borrar SOLO la última línea y escribir la nueva animación
        salida_text.delete("end-2l", "end-1c")
        salida_text.insert(tk.END, texto + "\n")
        salida_text.see(tk.END)

        pos_animacion_coti = (pos_animacion_coti + 1) % len(mensaje_coti)
        ventana.after(150, animar_cotizacion)

def ejecutar_script():
    global animando, pos_animacion
    fecha_inicio_dt = fecha_inicio.get_date()
    fecha_final_dt = fecha_final.get_date()
    if fecha_final_dt <= fecha_inicio_dt:
        messagebox.showwarning("Fechas inválidas", "La fecha final debe ser mayor que la fecha de inicio.")
        return 
    salida_text.delete(1.0, tk.END)  
    animando = True
    pos_animacion = 0
    animar_mensaje()  # Inicia la animación
    boton.config(state=tk.DISABLED)

    def tarea():
        global animando, contenido_salida
        try:
            limpiar_cache()
            fecha_ida = fecha_inicio.get_date().strftime("%Y-%m-%d")
            fecha_regreso = fecha_final.get_date().strftime("%Y-%m-%d")
            adultos = input_adultos.get()
            ninos = input_ninos.get()
            infantes = input_infantes.get()
            origen = input_origen.get()
            destino = input_destino.get()
            edades_ninos = [int(var.get()) for var in edades_ninos_vars]
            # 🔹 Llamada directa a la función de prueba.py
            import prueba
            resultado = prueba.buscar_vuelos(
                fecha_ida, fecha_regreso,
                int(adultos), int(ninos), int(infantes),  edades_ninos,
                origen, destino
            )

            animando = False  # Detiene la animación
            salida_text.delete(1.0, tk.END)
            contenido_salida = ""

            if resultado.strip():
                escribir_salida(resultado)
                # 🔹 Mostrar botón de cotización SOLO si hay resultados
                boton_cotizacion.pack(side=tk.LEFT, padx=5)
            else:
                boton_cotizacion.pack_forget()

            print(contenido_salida)

        except Exception as e:
            animando = False
            messagebox.showerror("Error", str(e))
            boton_cotizacion.pack_forget()

        finally:
            boton.config(state=tk.NORMAL)

    threading.Thread(target=tarea).start()


# 🔹 Nueva función para ejecutar primero.py
def ejecutar_cotizacion():
    global animando_coti, pos_animacion_coti
    try:
        raw = input_telefono.get().strip()
        telefono = re.sub(r"\D", "", raw)
        if not telefono:
            messagebox.showwarning("Campo obligatorio", "El campo 'Teléfono' es obligatorio.")
            return  

        resumen, precio_entero = generar_resumen_vuelos(contenido_salida)

        payload = {
            "resumen": resumen,
            "precio": precio_entero,
            "noches": (fecha_final.get_date() - fecha_inicio.get_date()).days
        }

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as tmp:
            json.dump(payload, tmp, ensure_ascii=False, indent=2)
            tmp_path = tmp.name

        fecha_ida = fecha_inicio.get_date().strftime("%Y-%m-%d")
        fecha_regreso = fecha_final.get_date().strftime("%Y-%m-%d")
        adultos = input_adultos.get()
        ninos = input_ninos.get()
        infantes = input_infantes.get()
        destino = input_destino.get()
        origen = input_origen.get()

        edades_ninos = [int(var.get()) for var in edades_ninos_vars]
        edades_infantes = [int(var.get()) for var in edades_infantes_vars]

        # Inicia animación
        animando_coti = True
        pos_animacion_coti = 0
        salida_text.insert(tk.END, "\n\nGenerando cotización...\n")
        salida_text.see(tk.END)
        animar_cotizacion()

        def tarea_cotizacion():
            global animando_coti
            try:
                from main import run_cotizacion  # importa tu función refactorizada

                resultado = run_cotizacion(
                    tmp_path,
                    fecha_ida,
                    fecha_regreso,
                    adultos,
                    ninos,
                    infantes,
                    destino,
                    origen,
                    edades_ninos,       # ahora se pasa lista directamente
                    edades_infantes,
                    telefono
                )

                animando_coti = False

                if "error" in resultado:
                    escribir_salida("\n[Errores en cotización]\n" + resultado["error"])
                else:
                    escribir_salida("\n[Cotización]\n" + resultado.get("logs", ""))

            except Exception as e:
                animando_coti = False
                messagebox.showerror("Error", f"No se pudo ejecutar run_cotizacion\n{e}")

        threading.Thread(target=tarea_cotizacion).start()

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo preparar cotización\n{e}")


if not hasattr(sys, "_cont_instancias"):
    sys._cont_instancias = 0
sys._cont_instancias += 1
numero_instancia = sys._cont_instancias

def resource_path(relative_path):
    """Obtiene la ruta absoluta, funciona en .py y en .exe"""
    try:
        base_path = sys._MEIPASS  # Carpeta temporal de PyInstaller
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)



# Crear ventana
ventana = tk.Tk()
ventana.title(f"Cotizador Viaja Vip {numero_instancia}")
ventana.iconbitmap(resource_path("assets/icono.ico"))
ventana.state("zoomed")
ventana.configure(bg="black")

# Título
titulo = tk.Label(
    ventana,
    text="🛫 Buscador de Vuelos",
    font=("Arial", 18, "bold"),
    bg="black",
    fg="white"
)
titulo.pack(pady=10)

# 🔹 Frame superior para inputs de fechas y pasajeros
frame_inputs = tk.Frame(ventana, bg="black")
frame_inputs.pack(pady=5)

# --- Inputs numéricos
lbl_adultos = tk.Label(frame_inputs, text="Adultos:", font=("Arial", 12), bg="black", fg="white")
lbl_adultos.grid(row=0, column=0, padx=5)
input_adultos = tk.Spinbox(frame_inputs, from_=1, to=10, width=5) 
input_adultos.grid(row=0, column=1, padx=5)

lbl_ninos = tk.Label(frame_inputs, text="Niños:", font=("Arial", 12), bg="black", fg="white")
lbl_ninos.grid(row=0, column=2, padx=5)
input_ninos = tk.Spinbox(frame_inputs, from_=0, to=10, width=5)
input_ninos.grid(row=0, column=3, padx=5)

lbl_infantes = tk.Label(frame_inputs, text="Infantes:", font=("Arial", 12), bg="black", fg="white")
lbl_infantes.grid(row=0, column=4, padx=5)
input_infantes = tk.Spinbox(frame_inputs, from_=0, to=10, width=5)
input_infantes.grid(row=0, column=5, padx=5)

frame_edades = tk.Frame(ventana, bg="black")
frame_edades.pack(pady=5)
edades_ninos_vars = []
edades_infantes_vars = []
# Variables globales para almacenar edades
edades_ninos_vars = []
edades_infantes_vars = []

def actualizar_edades(*args):
    # Limpiar frame
    for widget in frame_edades.winfo_children():
        widget.destroy()
    edades_ninos_vars.clear()
    edades_infantes_vars.clear()
    
    n_ninos = int(input_ninos.get())
    n_infantes = int(input_infantes.get())
    
    # 🔹 Fila para niños
    row_ninos = 0
    col = 0
    for i in range(n_ninos):
        lbl = tk.Label(frame_edades, text=f"Edad niño {i+1}:", font=("Arial", 12), bg="black", fg="white")
        lbl.grid(row=row_ninos, column=col, padx=5, pady=2, sticky="e")
        
        var = tk.StringVar(value="2")
        spin = tk.Spinbox(frame_edades, from_=2, to=17, width=5, textvariable=var)
        spin.grid(row=row_ninos, column=col+1, padx=5, pady=2)
        
        edades_ninos_vars.append(var)  # Guardamos la variable
        col += 2

    # 🔹 Fila para infantes
    row_infantes = 1
    col = 0
    for i in range(n_infantes):
        lbl = tk.Label(frame_edades, text=f"Edad infante {i+1}:", font=("Arial", 12), bg="black", fg="white")
        lbl.grid(row=row_infantes, column=col, padx=5, pady=2, sticky="e")
        
        var = tk.StringVar(value="0")
        spin = tk.Spinbox(frame_edades, from_=0, to=1, width=5, textvariable=var)
        spin.grid(row=row_infantes, column=col+1, padx=5, pady=2)
        
        edades_infantes_vars.append(var)  # Guardamos la variable
        col += 2


def actualizar_fecha_final(event):
    try:
        fecha_ini = fecha_inicio.get_date()   # obtener fecha seleccionada
        nueva_fecha = fecha_ini + timedelta(days=1)
        fecha_final.set_date(nueva_fecha)     # asignar automáticamente
    except Exception as e:
        print("Error actualizando fecha final:", e)

input_ninos.config(command=actualizar_edades)
input_infantes.config(command=actualizar_edades)
# --- Inputs Origen y Destino
ciudades = [
    "Bogotá", "Cali", "Medellín", "Cartagena", "Barranquilla",
    "Bucaramanga", "Leticia", "Armenia", "Pereira", "Pasto",
    "Popayán", "Santa Marta", "Montería", "Riohacha", "Mitú",
    "Ibagué", "Neiva"
]

lbl_origen = tk.Label(frame_inputs, text="Origen:", font=("Arial", 12), bg="black", fg="white")
lbl_origen.grid(row=1, column=0, padx=5, pady=5)

# Cambiar Entry por Combobox
input_origen = ttk.Combobox(frame_inputs, values=ciudades, width=15, state="readonly")
input_origen.grid(row=1, column=1, padx=5, pady=5)
input_origen.set(ciudades[2])  # Valor por defecto

lbl_destino = tk.Label(frame_inputs, text="Destino:", font=("Arial", 12), bg="black", fg="white")
lbl_destino.grid(row=1, column=2, padx=5, pady=5)
input_destino = ttk.Combobox(frame_inputs, values=["Punta Cana", "Cancún"], width=12, state="readonly")
input_destino.grid(row=1, column=3, padx=5, pady=5)
input_destino.current(0)  # valor por defecto

def solo_telefono(texto):
    # Permite dígitos, +, -, _, y espacios
    return re.fullmatch(r"[0-9+\-_\s]*", texto) is not None

vcmd = ventana.register(solo_telefono)

lbl_telefono = tk.Label(frame_inputs, text="Teléfono:", font=("Arial", 12), bg="black", fg="white")
lbl_telefono.grid(row=1, column=4, padx=5, pady=5)

input_telefono = tk.Entry(
    frame_inputs,
    width=15,
    validate="key",
    validatecommand=(vcmd, "%P")  # %P = texto resultante (soporta copiar/pegar)
)
input_telefono.grid(row=1, column=5, padx=5, pady=5)

def get_telefono():
    raw = input_telefono.get()
    # Eliminar todo lo que no sea dígito
    numero = re.sub(r"\D", "", raw)
    return numero

# --- Fecha inicio
lbl_inicio = tk.Label(frame_inputs, text="Fecha inicio:", font=("Arial", 12), bg="black", fg="white")
lbl_inicio.grid(row=2, column=0, padx=5, pady=5)
fecha_inicio = DateEntry(
    frame_inputs,
    width=12,
    background="darkblue",
    foreground="white",
    borderwidth=2,
    date_pattern='dd/MM/yyyy',
    locale='es_ES',
    mindate=date.today(),
    state="readonly"
)
fecha_inicio.grid(row=2, column=1, padx=5, pady=5)
fecha_inicio.bind("<Button-1>", lambda e: fecha_inicio.drop_down())
fecha_inicio.bind("<<DateEntrySelected>>", actualizar_fecha_final)  # 🔹 cuando eligen fecha

# --- Fecha final
lbl_final = tk.Label(frame_inputs, text="Fecha final:", font=("Arial", 12), bg="black", fg="white")
lbl_final.grid(row=2, column=2, padx=5, pady=5)
fecha_final = DateEntry(
    frame_inputs,
    width=12,
    background="darkblue",
    foreground="white",
    borderwidth=2,
    date_pattern='dd/MM/yyyy',
    locale='es_ES',
    mindate=date.today(),
    state="readonly"
)
fecha_final.grid(row=2, column=3, padx=5, pady=5)
fecha_final.bind("<Button-1>", lambda e: fecha_final.drop_down())

frame_botones = tk.Frame(ventana, bg="black")
frame_botones.pack(pady=10)

boton = tk.Button(
    frame_botones,
    text="Buscar vuelos",
    font=("Arial", 14),
    command=ejecutar_script,
    bg="#333333",
    fg="white",
    activebackground="#555555",
    activeforeground="white"
)
boton.pack(side=tk.LEFT, padx=5)

boton_manual = tk.Button(
    frame_botones,
    text="Vuelo Manual",
    font=("Arial", 14),
    command=vuelo_manual,
    bg="#333333",
    fg="white",
    activebackground="#555555",
    activeforeground="white"
)
boton_manual.pack(side=tk.LEFT, padx=5)

# Área de salida
salida_text = scrolledtext.ScrolledText(
    ventana,
    wrap=tk.WORD,
    width=100,
    height=25,
    font=("Courier", 10),
    bg="black",
    fg="white",
    insertbackground="white"
)
salida_text.pack(pady=10)

# Frame inferior y botón de cotización (como ya tenías)
frame_inferior = tk.Frame(ventana, bg="black")
frame_inferior.pack(side=tk.BOTTOM, fill="x", padx=20, pady=10)

# Botón a la izquierda
boton_cotizacion = tk.Button(
    frame_inferior,
    text="Generar Cotización",
    font=("Arial", 12, "bold"),
    command=ejecutar_cotizacion,
    bg="#444444",
    fg="white",
    activebackground="#666666",
    activeforeground="white"
)


label_version = tk.Label(
    frame_inferior,
    text="Versión 1.3.0",
    font=("Arial", 8),
    bg="black",
    fg="gray"
)
label_version.pack(side=tk.RIGHT, padx=5)

ventana.mainloop()