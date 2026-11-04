# ==============================================================================
# SIMULADOR DE SENSORES IoT
# ------------------------------------------------------------------------------
#   Simulador de sensores → (MQTT) → Servicio de ingesta → Base de datos
#
# En este MVP, el "broker MQTT" y el "servicio de ingesta" se sustituyen por
# esta función, que genera una lectura nueva por sensor y la inserta
# directamente en la base de datos. En una implementación productiva, este
# módulo sería reemplazado por un cliente MQTT suscrito a topics como:
#   planta/sensores/ph, planta/sensores/turbidez, planta/equipos/bomba01, etc.
# ==============================================================================

import random
from datetime import datetime

from database import db


def generar_nueva_lectura(sensor_row) -> float:
    """Genera una lectura simulada con una pequeña caminata aleatoria respecto
    a la última medición registrada para ese sensor."""
    ultima = db.fetch_df(
        "SELECT valor FROM mediciones WHERE sensor_id = ? ORDER BY id DESC LIMIT 1",
        (int(sensor_row["id"]),),
    )
    if not ultima.empty:
        base = float(ultima.iloc[0]["valor"])
    else:
        base = (float(sensor_row["umbral_min"]) + float(sensor_row["umbral_max"])) / 2

    variabilidad = (float(sensor_row["umbral_max"]) - float(sensor_row["umbral_min"])) * 0.03
    nuevo_valor = base + random.gauss(0, variabilidad)
    nuevo_valor = max(float(sensor_row["umbral_min"]), min(float(sensor_row["umbral_max"]), nuevo_valor))
    return round(nuevo_valor, 2)


def ejecutar_ciclo_ingesta() -> int:
    """Genera una nueva lectura para cada sensor activo (simula un ciclo de
    ingesta MQTT → base de datos). Devuelve la cantidad de lecturas generadas."""
    sensores = db.fetch_df("SELECT * FROM sensores WHERE activo = 1")
    ahora = datetime.now().isoformat(timespec="seconds")
    filas = []
    for _, sensor in sensores.iterrows():
        valor = generar_nueva_lectura(sensor)
        filas.append((int(sensor["id"]), valor, ahora))
    if filas:
        db.ejecutar_muchos("INSERT INTO mediciones (sensor_id, valor, timestamp) VALUES (?,?,?)", filas)
    return len(filas)
