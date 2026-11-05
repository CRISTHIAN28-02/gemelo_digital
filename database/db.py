# ==============================================================================
# CAPA DE DATOS — SQLite como sustituto de PostgreSQL/TimescaleDB para este MVP.
# ------------------------------------------------------------------------------
# La arquitectura modular (usuarios/roles, equipos/sensores/mediciones,
# alertas/predicciones/recomendaciones, mantenimientos, simulaciones, auditoría)
# es la misma que se usaría con PostgreSQL; solo cambia el motor de base de
# datos para que el MVP corra sin infraestructura adicional.
# ==============================================================================

import hashlib
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent / "gemelo_digital.db"

SALT_DEMO = "gemelo_digital_ptar_demo_salt"  # Solo para fines de demostración


# ------------------------------------------------------------------------------
# Conexión y helpers genéricos
# ------------------------------------------------------------------------------

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ejecutar(query: str, params: tuple = ()):
    conn = get_connection()
    cur = conn.execute(query, params)
    conn.commit()
    lastrowid = cur.lastrowid
    conn.close()
    return lastrowid


def ejecutar_muchos(query: str, lista_params: list):
    conn = get_connection()
    conn.executemany(query, lista_params)
    conn.commit()
    conn.close()


def fetch_df(query: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def fetch_uno(query: str, params: tuple = ()):
    conn = get_connection()
    cur = conn.execute(query, params)
    fila = cur.fetchone()
    conn.close()
    return fila


def hash_password(password: str) -> str:
    """
    Hash simple (SHA-256 + sal fija) SOLO para fines de demostración.
    En producción: usar bcrypt/argon2 con sal por usuario y gestión segura de secretos.
    """
    return hashlib.sha256((SALT_DEMO + password).encode("utf-8")).hexdigest()


def obtener_configuracion(clave: str, default=None):
    fila = fetch_uno("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
    return fila[0] if fila else default


def actualizar_configuracion(clave: str, valor):
    ejecutar(
        """INSERT INTO configuracion (clave, valor) VALUES (?, ?)
           ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor""",
        (clave, str(valor)),
    )


# ------------------------------------------------------------------------------
# Esquema de la base de datos
# ------------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol_id INTEGER NOT NULL REFERENCES roles(id),
    activo INTEGER NOT NULL DEFAULT 1,
    fecha_creacion TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plantas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    ubicacion TEXT
);

CREATE TABLE IF NOT EXISTS equipos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    planta_id INTEGER REFERENCES plantas(id),
    codigo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,
    ubicacion TEXT,
    estado TEXT NOT NULL DEFAULT 'operativo',
    fecha_instalacion TEXT,
    ultimo_mantenimiento TEXT,
    nivel_riesgo REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sensores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id INTEGER REFERENCES equipos(id),
    codigo TEXT UNIQUE NOT NULL,
    variable TEXT NOT NULL,
    unidad TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    umbral_min REAL NOT NULL,
    umbral_max REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS mediciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id INTEGER REFERENCES sensores(id),
    valor REAL NOT NULL,
    timestamp TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mediciones_sensor ON mediciones(sensor_id, timestamp);

CREATE TABLE IF NOT EXISTS alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id INTEGER REFERENCES equipos(id),
    sensor_id INTEGER REFERENCES sensores(id),
    tipo TEXT NOT NULL,
    severidad TEXT NOT NULL,
    valor_actual REAL,
    descripcion TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'nueva',
    fecha TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS predicciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id INTEGER REFERENCES equipos(id),
    riesgo_pct REAL NOT NULL,
    nivel TEXT NOT NULL,
    variables_relacionadas TEXT,
    recomendacion TEXT,
    fecha TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recomendaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuarios(id),
    turbidez REAL, ph REAL, caudal REAL, temperatura REAL,
    dosis_actual REAL, dosis_sugerida REAL,
    justificacion TEXT,
    fecha TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mantenimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id INTEGER REFERENCES equipos(id),
    tipo TEXT,
    descripcion TEXT,
    fecha TEXT NOT NULL,
    responsable TEXT
);

CREATE TABLE IF NOT EXISTS simulaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuarios(id),
    nombre TEXT,
    parametros TEXT NOT NULL,
    resultado TEXT NOT NULL,
    fecha TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    fecha TEXT NOT NULL,
    accion TEXT NOT NULL,
    modulo TEXT NOT NULL,
    descripcion TEXT,
    resultado TEXT
);

CREATE TABLE IF NOT EXISTS configuracion (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);
"""


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def esta_vacia() -> bool:
    fila = fetch_uno("SELECT COUNT(*) FROM usuarios")
    return fila[0] == 0


# ------------------------------------------------------------------------------
# Generación de series históricas simuladas (para que los gráficos no empiecen
# vacíos) — una caminata aleatoria con una posible tendencia de degradación.
# ------------------------------------------------------------------------------

def _generar_serie(base, variabilidad, minimo, maximo, puntos, tendencia):
    valores = []
    v = base
    for _ in range(puntos):
        v += random.gauss(0, variabilidad * 0.12)
        v = max(minimo, min(maximo, v))
        valores.append(v)
    if tendencia != 0:
        ventana = min(24, puntos)
        for i in range(1, ventana + 1):
            idx = puntos - i
            incremento = (ventana - i + 1) / ventana * variabilidad * 1.8 * tendencia
            valores[idx] = max(minimo, min(maximo, valores[idx] + incremento))
    return [round(x, 2) for x in valores]


def seed_data():
    """Puebla la base de datos con una planta, equipos, sensores, historial de
    mediciones (7 días), alertas, predicciones, recomendaciones, mantenimientos,
    configuración inicial y los dos usuarios de demostración."""
    random.seed(42)
    ahora = datetime.now()

    # --- Roles y usuarios demo ---
    ejecutar("INSERT INTO roles (nombre) VALUES ('administrador')")
    ejecutar("INSERT INTO roles (nombre) VALUES ('operador')")
    rol_admin = fetch_uno("SELECT id FROM roles WHERE nombre='administrador'")[0]
    rol_operador = fetch_uno("SELECT id FROM roles WHERE nombre='operador'")[0]

    ejecutar(
        "INSERT INTO usuarios (nombre, email, password_hash, rol_id, activo, fecha_creacion) "
        "VALUES (?,?,?,?,1,?)",
        ("Administrador Demo", "admin@demo.com", hash_password("admin123"), rol_admin,
         ahora.isoformat(timespec="seconds")),
    )
    ejecutar(
        "INSERT INTO usuarios (nombre, email, password_hash, rol_id, activo, fecha_creacion) "
        "VALUES (?,?,?,?,1,?)",
        ("Operador Demo", "operador@demo.com", hash_password("operador123"), rol_operador,
         ahora.isoformat(timespec="seconds")),
    )

    # --- Planta ---
    planta_id = ejecutar(
        "INSERT INTO plantas (nombre, ubicacion) VALUES (?,?)",
        ("Planta de Tratamiento de Agua - Sede Demo", "Zona Industrial Demo"),
    )

    # --- Equipos ---
    equipos_spec = [
        ("P-01", "Bomba de Impulsión P-01", "bomba", "Sala de bombeo", "advertencia"),
        ("P-02", "Bomba de Impulsión P-02", "bomba", "Sala de bombeo", "operativo"),
        ("F-01", "Filtro de Arena F-01", "filtro", "Área de filtración", "advertencia"),
        ("F-02", "Filtro de Arena F-02", "filtro", "Área de filtración", "operativo"),
        ("T-01", "Tanque de Mezcla T-01", "tanque", "Área de mezcla rápida", "operativo"),
        ("T-02", "Tanque de Almacenamiento T-02", "tanque", "Área de salida", "operativo"),
        ("D-01", "Sistema de Dosificación D-01", "dosificador", "Área de mezcla rápida", "operativo"),
        ("V-01", "Válvula de Control V-01", "valvula", "Línea de salida", "operativo"),
    ]
    equipo_ids = {}
    for i, (codigo, nombre, tipo, ubicacion, estado) in enumerate(equipos_spec):
        fecha_inst = (ahora - timedelta(days=400 + i * 30)).date().isoformat()
        fecha_mant = (ahora - timedelta(days=15 + i * 5)).date().isoformat()
        eid = ejecutar(
            """INSERT INTO equipos (planta_id, codigo, nombre, tipo, ubicacion, estado,
               fecha_instalacion, ultimo_mantenimiento, nivel_riesgo)
               VALUES (?,?,?,?,?,?,?,?,0)""",
            (planta_id, codigo, nombre, tipo, ubicacion, estado, fecha_inst, fecha_mant),
        )
        equipo_ids[codigo] = eid

    # --- Sensores ---
    # (codigo, variable, unidad, equipo, base, variabilidad, min, max, tendencia)
    # tendencia: 0 estable | 1 ascendente (degradación) | -1 descendente (degradación)
    sensores_spec = [
        ("PH-001", "ph", "pH", "T-01", 7.2, 0.15, 6.0, 9.0, 0),
        ("TURB-001", "turbidez", "NTU", "T-01", 18, 6, 0, 60, 0),
        ("CAU-001", "caudal", "L/s", "T-01", 120, 8, 60, 180, 0),
        ("NIV-001", "nivel", "%", "T-01", 68, 6, 5, 100, 0),
        ("TEMP-001", "temperatura", "°C", "T-01", 21, 1.5, 5, 40, 0),
        ("PRES-001", "presion", "bar", "P-01", 3.2, 0.25, 0.5, 5.0, -1),
        ("VIB-001", "vibracion", "mm/s", "P-01", 2.0, 0.4, 0, 6.0, 1),
        ("TEMP-002", "temperatura", "°C", "P-01", 26, 1.5, 5, 60, 1),
        ("PRES-002", "presion", "bar", "P-02", 3.1, 0.2, 0.5, 5.0, 0),
        ("VIB-002", "vibracion", "mm/s", "P-02", 1.6, 0.3, 0, 6.0, 0),
        ("DP-001", "presion_diferencial", "bar", "F-01", 0.9, 0.15, 0.1, 2.2, 1),
        ("TURB-002", "turbidez", "NTU", "F-01", 3.0, 1.0, 0, 15, 0),
        ("DP-002", "presion_diferencial", "bar", "F-02", 0.4, 0.1, 0.1, 2.2, 0),
        ("TURB-003", "turbidez", "NTU", "F-02", 2.2, 0.8, 0, 15, 0),
        ("NIV-002", "nivel", "%", "T-02", 74, 6, 5, 100, 0),
        ("DOS-001", "dosis", "mg/L", "D-01", 38, 4, 0, 80, 0),
        ("CAU-002", "caudal", "L/s", "V-01", 118, 8, 60, 180, 0),
    ]

    sensor_ids = {}
    for codigo, variable, unidad, eq_cod, base, var, mn, mx, tendencia in sensores_spec:
        sid = ejecutar(
            """INSERT INTO sensores (equipo_id, codigo, variable, unidad, activo, umbral_min, umbral_max)
               VALUES (?,?,?,?,1,?,?)""",
            (equipo_ids[eq_cod], codigo, variable, unidad, mn, mx),
        )
        sensor_ids[codigo] = sid

    # --- Historial de mediciones: cada 30 min durante los últimos 7 días ---
    puntos = 7 * 24 * 2  # 336 lecturas por sensor
    filas_mediciones = []
    for codigo, variable, unidad, eq_cod, base, var, mn, mx, tendencia in sensores_spec:
        valores = _generar_serie(base, var, mn, mx, puntos, tendencia)
        for i, valor in enumerate(valores):
            ts = (ahora - timedelta(minutes=30 * (puntos - i))).isoformat(timespec="seconds")
            filas_mediciones.append((sensor_ids[codigo], valor, ts))
    ejecutar_muchos(
        "INSERT INTO mediciones (sensor_id, valor, timestamp) VALUES (?,?,?)", filas_mediciones
    )

    # --- Alertas demo ---
    alertas_demo = [
        (equipo_ids["P-01"], sensor_ids["VIB-001"], "tendencia", "alta", 3.4,
         "Vibración de la bomba P-01 muestra tendencia ascendente sostenida.", "nueva"),
        (equipo_ids["F-01"], sensor_ids["DP-001"], "umbral", "media", 1.3,
         "Presión diferencial del filtro F-01 se aproxima al umbral de colmatación.", "en_revision"),
        (equipo_ids["T-01"], sensor_ids["TURB-001"], "umbral", "baja", 22.0,
         "Turbidez de entrada por encima del rango habitual de operación.", "atendida"),
        (equipo_ids["P-02"], sensor_ids["VIB-002"], "informacion", "informacion", 1.6,
         "Lectura de referencia registrada correctamente.", "cerrada"),
    ]
    for eq, sen, tipo, sev, valor, desc, estado in alertas_demo:
        fecha = (ahora - timedelta(hours=random.randint(1, 48))).isoformat(timespec="seconds")
        ejecutar(
            """INSERT INTO alertas (equipo_id, sensor_id, tipo, severidad, valor_actual,
               descripcion, estado, fecha) VALUES (?,?,?,?,?,?,?,?)""",
            (eq, sen, tipo, sev, valor, desc, estado, fecha),
        )

    # --- Predicciones demo ---
    predicciones_demo = [
        (equipo_ids["P-01"], 78.0, "ALTO", "Vibración ↑, Temperatura ↑, Presión ↓",
         "Inspeccionar la bomba P-01: posible desalineación o desgaste de rodamientos."),
        (equipo_ids["F-01"], 55.0, "MEDIO", "ΔP filtro ↑",
         "Programar retrolavado del filtro F-01 en las próximas 24-48 horas."),
        (equipo_ids["P-02"], 12.0, "BAJO", "Sin variables fuera de rango",
         "Sin acciones requeridas."),
    ]
    for eq, riesgo, nivel, vars_rel, reco in predicciones_demo:
        ejecutar(
            """INSERT INTO predicciones (equipo_id, riesgo_pct, nivel, variables_relacionadas,
               recomendacion, fecha) VALUES (?,?,?,?,?,?)""",
            (eq, riesgo, nivel, vars_rel, reco, ahora.isoformat(timespec="seconds")),
        )
    ejecutar("UPDATE equipos SET nivel_riesgo = 78.0 WHERE id = ?", (equipo_ids["P-01"],))
    ejecutar("UPDATE equipos SET nivel_riesgo = 55.0 WHERE id = ?", (equipo_ids["F-01"],))

    # --- Recomendación de dosificación demo ---
    admin_id = fetch_uno("SELECT id FROM usuarios WHERE email='admin@demo.com'")[0]
    ejecutar(
        """INSERT INTO recomendaciones (usuario_id, turbidez, ph, caudal, temperatura,
           dosis_actual, dosis_sugerida, justificacion, fecha) VALUES (?,?,?,?,?,?,?,?,?)""",
        (admin_id, 85, 7.2, 120, 21, 40, 47.3,
         "Turbidez elevada respecto al escenario de operación configurado.",
         (ahora - timedelta(hours=6)).isoformat(timespec="seconds")),
    )

    # --- Mantenimientos demo ---
    for codigo, eid in equipo_ids.items():
        ejecutar(
            "INSERT INTO mantenimientos (equipo_id, tipo, descripcion, fecha, responsable) "
            "VALUES (?,?,?,?,?)",
            (eid, "preventivo", f"Mantenimiento preventivo programado de {codigo}.",
             (ahora - timedelta(days=random.randint(10, 60))).date().isoformat(),
             "Equipo de Mantenimiento"),
        )

    # --- Configuración inicial ---
    config_inicial = {
        "mqtt_conectado": "1",
        "intervalo_simulacion_seg": "10",
        "umbral_turbidez_salida": "5",
        "umbral_saturacion_filtro": "80",
        "umbral_riesgo_bomba": "70",
        "costo_quimico_usd_kg": "1.8",
    }
    for clave, valor in config_inicial.items():
        ejecutar("INSERT INTO configuracion (clave, valor) VALUES (?,?)", (clave, valor))

    # --- Auditoría inicial ---
    ejecutar(
        "INSERT INTO auditoria (usuario, fecha, accion, modulo, descripcion, resultado) "
        "VALUES (?,?,?,?,?,?)",
        ("sistema", ahora.isoformat(timespec="seconds"), "Inicialización", "Sistema",
         "Base de datos creada y poblada con datos de demostración.", "Éxito"),
    )


def asegurar_base_datos():
    """Crea el esquema si no existe y siembra datos demo si la BD está vacía."""
    init_db()
    if esta_vacia():
        seed_data()
