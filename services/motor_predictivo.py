# ==============================================================================
# MOTOR PREDICTIVO (CAPA ANALÍTICA)
# ------------------------------------------------------------------------------
# Modelos empíricos DEMOSTRATIVOS. Deben calibrarse con datos históricos reales
# de la planta (SCADA/PLC, pruebas de jarras) antes de usarse en producción.
# El riesgo de anomalía usa reglas simples sobre las últimas lecturas; no es
# todavía un modelo de Machine Learning entrenado.
# ==============================================================================

import numpy as np


def calcular_dosis_sugerida(turbidez: float, ph: float = 7.2, caudal: float = 120.0,
                             temperatura: float = 20.0) -> float:
    """Dosis de coagulante sugerida (mg/L) según turbidez, pH, caudal y temperatura."""
    base = 3.0 + 0.9 * (turbidez ** 0.6)
    ajuste_ph = abs(ph - 7.2) * 1.5              # agua muy ácida/alcalina exige más coagulante
    ajuste_caudal = max(0.0, (caudal - 100)) * 0.03   # menor tiempo de contacto a mayor caudal
    ajuste_temp = max(0.0, (15 - temperatura)) * 0.2  # agua fría reduce eficiencia de coagulación
    dosis = base + ajuste_ph + ajuste_caudal + ajuste_temp
    return round(float(np.clip(dosis, 0, 80)), 1)


def calcular_eficiencia_coagulacion(dosis_actual: float, dosis_optima: float) -> float:
    if dosis_optima <= 0:
        return 0.5
    ratio = dosis_actual / dosis_optima
    if 0.9 <= ratio <= 1.15:
        return 0.97
    elif ratio < 0.9:
        return max(0.30, 0.97 - (0.9 - ratio) * 1.8)
    return max(0.35, 0.97 - (ratio - 1.15) * 1.3)


def calcular_turbidez_estimada(turbidez_entrada: float, dosis_actual: float, dosis_optima: float,
                                saturacion_filtro: float = 20.0) -> float:
    eficiencia_quimica = calcular_eficiencia_coagulacion(dosis_actual, dosis_optima)
    turbidez_post_quimica = turbidez_entrada * (1 - eficiencia_quimica)
    eficiencia_filtro = max(0.40, 0.93 - (saturacion_filtro / 100) * 0.35)
    return round(max(0.1, turbidez_post_quimica * (1 - eficiencia_filtro)), 2)


def calcular_costo_dosificacion(dosis_mg_l: float, caudal_l_s: float, costo_usd_kg: float = 1.8) -> float:
    """Convierte dosis (mg/L) y caudal (L/s) a un costo estimado en USD/hora."""
    kg_h = dosis_mg_l * caudal_l_s * 3600 / 1_000_000
    return round(kg_h * costo_usd_kg, 3)


def calcular_riesgo_anomalia_equipo(lecturas_recientes: dict):
    """
    Modelo DEMOSTRATIVO de riesgo de anomalía (0-100%) a partir de las últimas
    lecturas disponibles para un equipo. Devuelve (riesgo, nivel, variables_relacionadas).
    """
    riesgo = 0.0
    variables_relacionadas = []

    vibracion = lecturas_recientes.get("vibracion")
    if vibracion is not None and vibracion > 3.0:
        riesgo += min(40, (vibracion - 3.0) * 25)
        variables_relacionadas.append("Vibración ↑")

    temperatura = lecturas_recientes.get("temperatura")
    if temperatura is not None and temperatura > 32:
        riesgo += min(30, (temperatura - 32) * 3)
        variables_relacionadas.append("Temperatura ↑")

    presion = lecturas_recientes.get("presion")
    if presion is not None and presion < 2.5:
        riesgo += min(30, (2.5 - presion) * 20)
        variables_relacionadas.append("Presión ↓")

    dp = lecturas_recientes.get("presion_diferencial")
    if dp is not None and dp > 1.3:
        riesgo += min(40, (dp - 1.3) * 30)
        variables_relacionadas.append("ΔP filtro ↑")

    riesgo = round(min(100.0, riesgo), 1)
    nivel = "ALTO" if riesgo >= 60 else "MEDIO" if riesgo >= 30 else "BAJO"
    return riesgo, nivel, variables_relacionadas


def recomendacion_por_nivel(nivel: str, equipo_nombre: str) -> str:
    if nivel == "ALTO":
        return f"Inspeccionar {equipo_nombre} a la brevedad: posible desalineación, desgaste o colmatación."
    elif nivel == "MEDIO":
        return f"Programar una revisión de {equipo_nombre} en los próximos días."
    return f"Sin acciones requeridas para {equipo_nombre}."
