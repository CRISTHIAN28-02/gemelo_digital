# ==============================================================================
# ASISTENTE DE IA (basado en reglas + consultas estructuradas a la base de
# datos). No inventa valores: siempre consulta el dato antes de responder e
# indica si es un dato real (simulado), una predicción, una simulación
# guardada, o si no está disponible con las herramientas actuales.
#
# Arquitectura:
#   Usuario → Asistente IA → Consultas SQL (API interna) → Base de datos
#             → sensores / alertas / predicciones / simulaciones
#
# Para una versión futura, este módulo podría reemplazarse por una llamada a
# un modelo de lenguaje (ej. API de Claude) que reciba estas mismas consultas
# como "herramientas", manteniendo la misma separación de capas.
# ==============================================================================

import re
from datetime import datetime, timedelta

from database import db


def _no_disponible() -> str:
    return "No dispongo de esa información con los datos y herramientas disponibles actualmente."


def responder(pregunta: str) -> str:
    p = pregunta.lower().strip()

    # ¿Cuál es el estado actual de la planta?
    if "estado" in p and "planta" in p:
        equipos = db.fetch_df("SELECT estado, COUNT(*) as n FROM equipos GROUP BY estado")
        alertas_activas = db.fetch_uno(
            "SELECT COUNT(*) FROM alertas WHERE estado IN ('nueva','en_revision')"
        )[0]
        total_equipos = int(equipos["n"].sum()) if not equipos.empty else 0
        resumen = ", ".join(f"{fila.n} en estado '{fila.estado}'" for fila in equipos.itertuples())
        return (f"📡 **Dato real (simulado):** de {total_equipos} equipos registrados: {resumen}. "
                f"Hay {alertas_activas} alerta(s) activa(s) en este momento.")

    # ¿Qué equipos presentan riesgo?
    if "riesgo" in p and "equipo" in p:
        df = db.fetch_df(
            "SELECT codigo, nombre, nivel_riesgo FROM equipos WHERE nivel_riesgo >= 30 "
            "ORDER BY nivel_riesgo DESC"
        )
        if df.empty:
            return "🔮 **Predicción (modelo demostrativo):** ningún equipo presenta riesgo relevante en este momento."
        detalle = "; ".join(f"{fila.codigo} ({fila.nivel_riesgo:.0f}%)" for fila in df.itertuples())
        return f"🔮 **Predicción (modelo demostrativo):** equipos con riesgo a vigilar: {detalle}."

    # ¿Por qué se generó esta alerta? / alertas recientes
    if "alerta" in p:
        df = db.fetch_df(
            """SELECT a.severidad, a.descripcion, e.nombre AS equipo, a.fecha
               FROM alertas a LEFT JOIN equipos e ON a.equipo_id = e.id
               ORDER BY a.fecha DESC LIMIT 3"""
        )
        if df.empty:
            return "📡 **Dato real (simulado):** no hay alertas registradas."
        detalle = " | ".join(f"[{f.severidad}] {f.equipo}: {f.descripcion}" for f in df.itertuples())
        return f"📡 **Dato real (simulado):** alertas más recientes → {detalle}"

    # ¿Qué variables están fuera de rango?
    if "fuera de rango" in p or ("variable" in p and "rango" in p):
        df = db.fetch_df(
            """SELECT s.codigo, s.variable, m.valor, s.umbral_min, s.umbral_max
               FROM mediciones m JOIN sensores s ON m.sensor_id = s.id
               WHERE m.id IN (SELECT MAX(id) FROM mediciones GROUP BY sensor_id)
                 AND (m.valor < s.umbral_min OR m.valor > s.umbral_max)"""
        )
        if df.empty:
            return "📡 **Dato real (simulado):** todas las variables están dentro de rango en este momento."
        detalle = "; ".join(f"{f.codigo} ({f.variable}) = {f.valor}" for f in df.itertuples())
        return f"📡 **Dato real (simulado):** variables fuera de rango → {detalle}"

    # ¿Cuál es la recomendación para la bomba P-01? (o cualquier otro código de equipo)
    coincidencia = re.search(r"\b([a-z]{1,3}-\d{1,3})\b", p)
    if "recomendaci" in p or coincidencia:
        codigo = coincidencia.group(1).upper() if coincidencia else None
        if codigo:
            df = db.fetch_df(
                """SELECT pr.recomendacion, pr.riesgo_pct, pr.nivel, pr.fecha
                   FROM predicciones pr JOIN equipos e ON pr.equipo_id = e.id
                   WHERE e.codigo = ? ORDER BY pr.fecha DESC LIMIT 1""",
                (codigo,),
            )
            if df.empty:
                return f"🔮 No hay todavía una predicción registrada para {codigo}."
            fila = df.iloc[0]
            return (f"🔮 **Predicción (modelo demostrativo)** para {codigo}: riesgo "
                    f"{fila['riesgo_pct']:.0f}% (nivel {fila['nivel']}). "
                    f"Recomendación: {fila['recomendacion']}")
        return _no_disponible()

    # ¿Qué ocurrió durante las últimas 24 horas?
    if "últimas 24" in p or "ultimas 24" in p:
        hace_24h = (datetime.now() - timedelta(hours=24)).isoformat(timespec="seconds")
        n_alertas = db.fetch_uno("SELECT COUNT(*) FROM alertas WHERE fecha >= ?", (hace_24h,))[0]
        n_mant = db.fetch_uno(
            "SELECT COUNT(*) FROM mantenimientos WHERE fecha >= ?", (hace_24h[:10],)
        )[0]
        return (f"📡 **Dato real (simulado):** en las últimas 24 horas se registraron "
                f"{n_alertas} alerta(s) y {n_mant} evento(s) de mantenimiento.")

    return (_no_disponible() + " Prueba preguntando por el estado de la planta, el riesgo de "
            "un equipo (ej. P-01), las alertas recientes o las variables fuera de rango.")
