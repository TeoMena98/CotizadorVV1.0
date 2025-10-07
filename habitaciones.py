# habitaciones.py
import time
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def distribuir_huespedes(total_adultos, total_ninos, max_adultos=2, max_ninos=3):
    # ✅ Caso especial: solo adultos
    if total_ninos == 0 and total_adultos > 2:
        if total_adultos == 3:
            # 🔹 No crear segunda habitación, meter los 3 juntos
            return [{"adultos": 3, "ninos": 0}]
        elif total_adultos % 2 == 1:
            # 🔹 Ej: 5 -> [3,2], 7 -> [4,3], 9 -> [5,4]
            mitad = total_adultos // 2
            return [
                {"adultos": mitad + 1, "ninos": 0},
                {"adultos": mitad, "ninos": 0}
            ]

    # --- Lógica normal (no se toca) ---
    habitaciones = [{"adultos": min(2, total_adultos), "ninos": 0}]
    total_adultos -= habitaciones[0]["adultos"]

    # 🔹 Corte adicional: si no hay niños y ya metimos todos los adultos, no crear más habitaciones
    if total_ninos == 0 and total_adultos == 0:
        return habitaciones

    if (total_adultos + habitaciones[0]["adultos"]) % 2 == 1:
        max_adultos = 3
    else:
        max_adultos = 2

    if total_ninos > 0:
        if habitaciones[0]["adultos"] > 1:
            habitaciones[0]["adultos"] -= 1
            total_adultos += 1

        capacidad = 4 - habitaciones[0]["adultos"]
        hab_ninos = min(total_ninos, capacidad, max_ninos)
        habitaciones[0]["ninos"] = hab_ninos
        total_ninos -= hab_ninos

    while total_adultos > 0 and len(habitaciones) < 4:
        if total_ninos > 0:
            hab_adultos = 1
        else:
            hab_adultos = min(total_adultos, max_adultos)

        capacidad = 4 - hab_adultos
        hab_ninos = 0
        if total_ninos > 0:
            hab_ninos = min(total_ninos, capacidad, max_ninos)
            total_ninos -= hab_ninos

        habitaciones.append({"adultos": hab_adultos, "ninos": hab_ninos})
        total_adultos -= hab_adultos

    i = 0
    while total_ninos > 0 and i < len(habitaciones):
        capacidad_restante = 4 - habitaciones[i]["adultos"] - habitaciones[i]["ninos"]
        if capacidad_restante > 0 and habitaciones[i]["adultos"] > 0:
            hab_ninos = min(total_ninos, capacidad_restante, max_ninos - habitaciones[i]["ninos"])
            if hab_ninos > 0:
                habitaciones[i]["ninos"] += hab_ninos
                total_ninos -= hab_ninos
        i += 1

    while total_ninos > 0 and len(habitaciones) < 4 and total_adultos > 0:
        hab_adultos = min(total_adultos, 1)
        hab_ninos = min(total_ninos, max_ninos, 4 - hab_adultos)
        habitaciones.append({"adultos": hab_adultos, "ninos": hab_ninos})
        total_adultos -= hab_adultos
        total_ninos -= hab_ninos

    return habitaciones







def configurar_habitaciones(driver, wait, habitaciones, edades_ninos=[], edades_infantes=[]):
    """
    habitaciones = [
        {"adultos": 1, "ninos": 2},
        {"adultos": 1, "ninos": 2}
    ]
    edades_ninos = [12, 12, 12, 12]
    """
    todas_edades = edades_ninos + edades_infantes
    edad_idx = 0

    # --- Abrir el dropdown ---
    dropdown_btn = wait.until(EC.element_to_be_clickable((
        By.ID, "j_id_6v:init-compositor-all:roomsSH:dropdown"
    )))
    dropdown_btn.click()
    time.sleep(0.5)

    # --- Configurar la primera habitación (la que ya existe por defecto) ---
    print("Configurando habitación 1...")
    select_adultos = wait.until(EC.element_to_be_clickable((
        By.ID, "j_id_6v:init-compositor-all:roomsSH:distri:0:adults"
    )))
    Select(select_adultos).select_by_value(str(habitaciones[0]["adultos"]))
    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", select_adultos)
    time.sleep(1.5)  # 🔹 Esperar recarga

    select_ninos = wait.until(EC.presence_of_element_located((
        By.ID, "j_id_6v:init-compositor-all:roomsSH:distri:0:children"
    )))
    Select(select_ninos).select_by_value(str(habitaciones[0]["ninos"]))
    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", select_ninos)
    time.sleep(1.5)  # 🔹 Esperar que aparezcan los selects de edad

    for n in range(habitaciones[0]["ninos"]):
        select_edad = wait.until(EC.element_to_be_clickable((
            By.ID, f"j_id_6v:init-compositor-all:roomsSH:distri:0:childAges:{n}:age"
        )))
        if edad_idx < len(todas_edades):
            edad = str(todas_edades[edad_idx])
        else:
            edad = "5"
        Select(select_edad).select_by_value(edad)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", select_edad)
        edad_idx += 1
        time.sleep(0.5)

    # --- Crear y configurar las demás habitaciones ---
    for i in range(1, len(habitaciones)):
        print(f"Creando y configurando habitación {i+1}...")
        btn_add = wait.until(EC.element_to_be_clickable((
            By.ID, "j_id_6v:init-compositor-all:roomsSH:addRoom"
        )))
        btn_add.click()
        time.sleep(1.0)

        # Adultos
        select_adultos = wait.until(EC.element_to_be_clickable((
            By.ID, f"j_id_6v:init-compositor-all:roomsSH:distri:{i}:adults"
        )))
        Select(select_adultos).select_by_value(str(habitaciones[i]["adultos"]))
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", select_adultos)
        time.sleep(1.5)

        # Niños
        select_ninos = wait.until(EC.presence_of_element_located((
            By.ID, f"j_id_6v:init-compositor-all:roomsSH:distri:{i}:children"
        )))
        Select(select_ninos).select_by_value(str(habitaciones[i]["ninos"]))
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", select_ninos)
        time.sleep(1.5)

        # Edades
        for n in range(habitaciones[i]["ninos"]):
            select_edad = wait.until(EC.element_to_be_clickable((
                By.ID, f"j_id_6v:init-compositor-all:roomsSH:distri:{i}:childAges:{n}:age"
            )))
            if edad_idx < len(todas_edades):
                edad = str(todas_edades[edad_idx])
            else:
                edad = "5"
            Select(select_edad).select_by_value(edad)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", select_edad)
            edad_idx += 1
            time.sleep(0.5)

    # --- Aceptar ---
    btn_aceptar = wait.until(EC.element_to_be_clickable((
        By.ID, "j_id_6v:init-compositor-all:roomsSH:accept"
    )))
    btn_aceptar.click()
    time.sleep(0.5)