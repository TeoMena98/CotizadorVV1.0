# habitaciones.py
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


def distribuir_huespedesAdultos(total_adultos, total_ninos, max_adultos=2, max_ninos=3):
    habitaciones = []

    if total_adultos % 2 == 1:
        max_adultos = 3
    else:
        max_adultos = 2

    while total_adultos > 0 and len(habitaciones) < 4:
        hab_adultos = min(total_adultos, max_adultos)
        habitaciones.append({"adultos": hab_adultos, "ninos": 0})
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


def configurar_habitacionesAdultos(driver, wait, habitaciones, edades_ninos=[], edades_infantes=[]):
    todas_edades = edades_ninos + edades_infantes
    edad_idx = 0

    try:
        dropdown_btn = wait.until(EC.element_to_be_clickable((
            By.ID, "j_id_6v:init-compositor-all:roomsSH:dropdown"
        )))
        dropdown_btn.click()
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".c-choose-rooms__row")))
    except Exception:
        print("[ADVERTENCIA] No se pudo abrir el dropdown de habitaciones")
        return

    habitaciones_existentes = wait.until(EC.presence_of_all_elements_located((
        By.CSS_SELECTOR, ".c-choose-rooms__row"
    )))
    num_existentes = len(habitaciones_existentes)

    while num_existentes < len(habitaciones):
        btn_add = wait.until(EC.element_to_be_clickable((
            By.ID, "j_id_6v:init-compositor-all:roomsSH:addRoom"
        )))
        btn_add.click()
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".c-choose-rooms__row")) > num_existentes)
        num_existentes += 1

        i = num_existentes - 1
        hab = habitaciones[i]

        select_adultos = wait.until(EC.element_to_be_clickable((
            By.ID, f"j_id_6v:init-compositor-all:roomsSH:distri:{i}:adults"
        )))
        Select(select_adultos).select_by_value(str(hab["adultos"]))
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", select_adultos)

        select_ninos = wait.until(EC.element_to_be_clickable((
            By.ID, f"j_id_6v:init-compositor-all:roomsSH:distri:{i}:children"
        )))
        Select(select_ninos).select_by_value(str(hab["ninos"]))
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", select_ninos)

        for n in range(hab["ninos"]):
            select_edad = wait.until(EC.element_to_be_clickable((
                By.ID, f"j_id_6v:init-compositor-all:roomsSH:distri:{i}:childAges:{n}:age"
            )))
            edad = str(todas_edades[edad_idx]) if edad_idx < len(todas_edades) else "5"
            Select(select_edad).select_by_value(edad)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", select_edad)
            edad_idx += 1

    for i, hab in enumerate(habitaciones):
        select_adultos = wait.until(EC.element_to_be_clickable((
            By.ID, f"j_id_6v:init-compositor-all:roomsSH:distri:{i}:adults"
        )))
        Select(select_adultos).select_by_value(str(hab["adultos"]))
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", select_adultos)

        select_ninos = wait.until(EC.element_to_be_clickable((
            By.ID, f"j_id_6v:init-compositor-all:roomsSH:distri:{i}:children"
        )))
        Select(select_ninos).select_by_value(str(hab["ninos"]))
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", select_ninos)

        for n in range(hab["ninos"]):
            select_edad = wait.until(EC.element_to_be_clickable((
                By.ID, f"j_id_6v:init-compositor-all:roomsSH:distri:{i}:childAges:{n}:age"
            )))
            edad = str(todas_edades[edad_idx]) if edad_idx < len(todas_edades) else "5"
            Select(select_edad).select_by_value(edad)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", select_edad)
            edad_idx += 1

    btn_aceptar = wait.until(EC.element_to_be_clickable((
        By.ID, "j_id_6v:init-compositor-all:roomsSH:accept"
    )))
    btn_aceptar.click()
    wait.until(EC.invisibility_of_element_located((By.ID, "j_id_6v:init-compositor-all:roomsSH:accept")))
