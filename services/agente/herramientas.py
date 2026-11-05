"""Herramientas controladas que el agente puede ejecutar sobre el MVP."""
from __future__ import annotations
import json
from datetime import datetime, timedelta
from database import db
from services import motor_predictivo as mp


def estado_planta():
    equipos = db.fetch_df("SELECT estado, COUNT(*) AS cantidad FROM equipos GROUP BY estado")
    alertas = db.fetch_uno("SELECT COUNT(*) FROM alertas WHERE estado IN ('nueva','en_revision')")[0]
    sensores = db.fetch_uno("SELECT COUNT(*) FROM sensores WHERE activo=1")[0]
    lecturas = db.fetch_uno("SELECT COUNT(*) FROM mediciones")[0]
    return {"tipo_dato": "datos simulados del MVP", "equipos": equipos.to_dict("records"),
            "alertas_activas": int(alertas), "sensores_activos": int(sensores),
            "mediciones_historicas": int(lecturas)}


def alertas_recientes(limite=5):
    limite = max(1, min(int(limite), 20))
    df = db.fetch_df("""SELECT a.fecha,a.severidad,a.estado,a.descripcion,e.codigo AS equipo
        FROM alertas a LEFT JOIN equipos e ON e.id=a.equipo_id ORDER BY a.fecha DESC LIMIT ?""", (limite,))
    return {"tipo_dato": "alertas registradas en la base simulada", "resultados": df.to_dict("records")}


def equipos_en_riesgo():
    df = db.fetch_df("""SELECT codigo,nombre,estado,nivel_riesgo FROM equipos
        WHERE nivel_riesgo >= 30 ORDER BY nivel_riesgo DESC""")
    return {"tipo_dato": "riesgo demostrativo calculado/almacenado en el MVP", "equipos": df.to_dict("records")}


def ultimas_mediciones(variable=None, limite=20):
    limite = max(1, min(int(limite), 100))
    if variable:
        df = db.fetch_df("""SELECT s.codigo,s.variable,s.unidad,m.valor,m.timestamp
            FROM mediciones m JOIN sensores s ON s.id=m.sensor_id
            WHERE lower(s.variable)=lower(?) ORDER BY m.timestamp DESC LIMIT ?""", (variable, limite))
    else:
        df = db.fetch_df("""SELECT s.codigo,s.variable,s.unidad,m.valor,m.timestamp
            FROM mediciones m JOIN sensores s ON s.id=m.sensor_id
            WHERE m.id IN (SELECT MAX(id) FROM mediciones GROUP BY sensor_id)
            ORDER BY s.variable""")
    return {"tipo_dato": "mediciones simuladas", "resultados": df.to_dict("records")}


def historial_sensor(codigo, horas=24):
    horas = max(1, min(int(horas), 168))
    desde = (datetime.now() - timedelta(hours=horas)).isoformat(timespec="seconds")
    df = db.fetch_df("""SELECT s.codigo,s.variable,s.unidad,m.valor,m.timestamp
        FROM sensores s JOIN mediciones m ON m.sensor_id=s.id
        WHERE s.codigo=? AND m.timestamp>=? ORDER BY m.timestamp""", (codigo.upper(), desde))
    return {"sensor": codigo.upper(), "periodo_horas": horas,
            "tipo_dato": "histórico simulado", "cantidad": len(df),
            "lecturas": df.to_dict("records")[-100:]}


def calcular_dosis(turbidez, ph=7.2, caudal=120, temperatura=20):
    valores = [float(turbidez), float(ph), float(caudal), float(temperatura)]
    if not (0 <= valores[0] <= 1000 and 0 <= valores[1] <= 14 and 0 < valores[2] <= 10000 and -5 <= valores[3] <= 60):
        raise ValueError("Parámetros fuera de los límites admitidos para esta simulación.")
    dosis = mp.calcular_dosis_sugerida(*valores)
    return {"tipo_dato": "estimación de modelo demostrativo; no es una consigna operativa",
            "dosis_sugerida_mg_l": dosis, "entradas": {"turbidez_ntu": valores[0], "ph": valores[1],
            "caudal_l_s": valores[2], "temperatura_c": valores[3]},
            "advertencia": "Validar mediante pruebas de jarras y criterio del operador antes de cualquier uso real."}


def simular_escenario(turbidez, caudal, dosis_actual, saturacion_filtro, ph=7.2, temperatura=20):
    vals = [float(turbidez), float(caudal), float(dosis_actual), float(saturacion_filtro), float(ph), float(temperatura)]
    if not (0 <= vals[0] <= 1000 and 0 < vals[1] <= 10000 and 0 <= vals[2] <= 100 and 0 <= vals[3] <= 100 and 0 <= vals[4] <= 14 and -5 <= vals[5] <= 60):
        raise ValueError("Uno o más parámetros están fuera de los límites admitidos.")
    dosis = mp.calcular_dosis_sugerida(vals[0], vals[4], vals[1], vals[5])
    turb_actual = mp.calcular_turbidez_estimada(vals[0], vals[2], dosis, vals[3])
    turb_prop = mp.calcular_turbidez_estimada(vals[0], dosis, dosis, vals[3])
    costo_actual = mp.calcular_costo_dosificacion(vals[2], vals[1])
    costo_prop = mp.calcular_costo_dosificacion(dosis, vals[1])
    return {"tipo_dato": "simulación matemática demostrativa; no modifica la planta ni la base de datos",
            "dosis_sugerida_mg_l": dosis, "turbidez_estimada_escenario_actual_ntu": turb_actual,
            "turbidez_estimada_escenario_propuesto_ntu": turb_prop,
            "costo_actual_usd_h": costo_actual, "costo_propuesto_usd_h": costo_prop,
            "diferencia_costo_usd_h": round(costo_prop-costo_actual, 3),
            "advertencia": "Modelo ilustrativo. No sustituye pruebas de jarras, calibración ni validación del operador."}


def buscar_literatura(consulta):
    """Búsqueda gratuita de literatura vía OpenAlex; no usa API key."""
    import requests
    q = str(consulta).strip()[:250]
    if not q:
        return {"resultados": []}
    url = "https://api.openalex.org/works"
    resp = requests.get(url, params={"search": q, "per-page": 5,
        "select": "title,publication_year,doi,authorships,primary_location"}, timeout=15)
    resp.raise_for_status()
    items = []
    for item in resp.json().get("results", []):
        authors = [a.get("author", {}).get("display_name") for a in item.get("authorships", [])[:3]]
        loc = item.get("primary_location") or {}
        source = (loc.get("source") or {}).get("display_name")
        items.append({"titulo": item.get("title"), "año": item.get("publication_year"),
                      "autores": authors, "revista_o_fuente": source, "doi": item.get("doi")})
    return {"fuente": "OpenAlex", "resultados": items,
            "nota": "Metadatos bibliográficos. Verificar el texto completo y la pertinencia técnica antes de aplicar conclusiones."}


TOOL_DEFINITIONS = [
 {"type":"function","function":{"name":"estado_planta","description":"Consulta el resumen de equipos, sensores y alertas activas de la planta demo.","parameters":{"type":"object","properties":{},"additionalProperties":False}}},
 {"type":"function","function":{"name":"alertas_recientes","description":"Consulta alertas recientes registradas.","parameters":{"type":"object","properties":{"limite":{"type":"integer","minimum":1,"maximum":20}},"additionalProperties":False}}},
 {"type":"function","function":{"name":"equipos_en_riesgo","description":"Consulta equipos con riesgo demostrativo igual o mayor a 30 por ciento.","parameters":{"type":"object","properties":{},"additionalProperties":False}}},
 {"type":"function","function":{"name":"ultimas_mediciones","description":"Consulta las últimas mediciones por variable o la última lectura de cada sensor.","parameters":{"type":"object","properties":{"variable":{"type":"string"},"limite":{"type":"integer","minimum":1,"maximum":100}},"additionalProperties":False}}},
 {"type":"function","function":{"name":"historial_sensor","description":"Consulta el histórico de un sensor por código, por ejemplo DP-001 o TURB-001.","parameters":{"type":"object","properties":{"codigo":{"type":"string"},"horas":{"type":"integer","minimum":1,"maximum":168}},"required":["codigo"],"additionalProperties":False}}},
 {"type":"function","function":{"name":"calcular_dosis","description":"Calcula una dosis estimada con el motor matemático demostrativo existente. Nunca es una consigna real.","parameters":{"type":"object","properties":{"turbidez":{"type":"number"},"ph":{"type":"number"},"caudal":{"type":"number"},"temperatura":{"type":"number"}},"required":["turbidez"],"additionalProperties":False}}},
 {"type":"function","function":{"name":"simular_escenario","description":"Ejecuta una simulación What-If sin guardar ni modificar datos reales.","parameters":{"type":"object","properties":{"turbidez":{"type":"number"},"caudal":{"type":"number"},"dosis_actual":{"type":"number"},"saturacion_filtro":{"type":"number"},"ph":{"type":"number"},"temperatura":{"type":"number"}},"required":["turbidez","caudal","dosis_actual","saturacion_filtro"],"additionalProperties":False}}},
 {"type":"function","function":{"name":"buscar_literatura","description":"Busca publicaciones científicas sobre tratamiento de agua en OpenAlex, servicio bibliográfico gratuito.","parameters":{"type":"object","properties":{"consulta":{"type":"string"}},"required":["consulta"],"additionalProperties":False}}}
]

FUNCTIONS = {"estado_planta": estado_planta, "alertas_recientes": alertas_recientes,
 "equipos_en_riesgo": equipos_en_riesgo, "ultimas_mediciones": ultimas_mediciones,
 "historial_sensor": historial_sensor, "calcular_dosis": calcular_dosis,
 "simular_escenario": simular_escenario, "buscar_literatura": buscar_literatura}
