from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from database import db
from services import auth
from services.simulador import ejecutar_ciclo_ingesta

auth.requerir_login()

st.title("📡 Monitoreo de Sensores")
st.caption("Lecturas simuladas de variables de proceso (sustituyen a un flujo MQTT real en este MVP).")

if st.button("🔄 Simular ciclo IoT"):
    n = ejecutar_ciclo_ingesta()
    st.toast(f"{n} lecturas nuevas generadas.")

sensores = db.fetch_df(
    """SELECT s.id, s.codigo, s.variable, s.unidad, e.nombre AS equipo, e.codigo AS equipo_codigo
       FROM sensores s JOIN equipos e ON s.equipo_id = e.id
       WHERE s.activo = 1 ORDER BY e.codigo, s.codigo"""
)

opciones = {f"{fila.codigo} — {fila.variable} ({fila.equipo})": fila.id for fila in sensores.itertuples()}
seleccion = st.selectbox("Selecciona un sensor", list(opciones.keys()))
sensor_id = opciones[seleccion]

rango = st.radio(
    "Rango histórico",
    ["Últimos 15 min", "Última hora", "Últimas 24 horas", "Últimos 7 días"],
    horizontal=True, index=2,
)
rango_delta = {
    "Últimos 15 min": timedelta(minutes=15),
    "Última hora": timedelta(hours=1),
    "Últimas 24 horas": timedelta(hours=24),
    "Últimos 7 días": timedelta(days=7),
}[rango]
desde = (datetime.now() - rango_delta).isoformat(timespec="seconds")

df_hist = db.fetch_df(
    "SELECT timestamp, valor FROM mediciones WHERE sensor_id = ? AND timestamp >= ? ORDER BY timestamp",
    (sensor_id, desde),
)
info_sensor = db.fetch_df("SELECT * FROM sensores WHERE id = ?", (sensor_id,)).iloc[0]

if not df_hist.empty:
    ultimo_valor = df_hist.iloc[-1]["valor"]
    ultimo_ts = df_hist.iloc[-1]["timestamp"]
    fuera_rango = ultimo_valor < info_sensor["umbral_min"] or ultimo_valor > info_sensor["umbral_max"]
    estado_txt = "🔴 Fuera de rango" if fuera_rango else "🟢 Normal"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Valor actual", f"{ultimo_valor:.2f} {info_sensor['unidad']}")
    c2.metric("Estado", estado_txt)
    c3.metric("Última lectura", ultimo_ts)
    c4.metric("Rango normal", f"{info_sensor['umbral_min']} – {info_sensor['umbral_max']}")

    df_hist_plot = df_hist.copy()
    df_hist_plot["timestamp"] = pd.to_datetime(df_hist_plot["timestamp"])
    st.line_chart(df_hist_plot.set_index("timestamp")["valor"])

    if len(df_hist) >= 2:
        tendencia = df_hist.iloc[-1]["valor"] - df_hist.iloc[0]["valor"]
        flecha = "↑" if tendencia > 0 else "↓" if tendencia < 0 else "→"
        st.caption(f"Tendencia en el periodo seleccionado: {flecha} {tendencia:+.2f} {info_sensor['unidad']}")
else:
    st.info("No hay mediciones en el rango seleccionado todavía. Genera un ciclo IoT o elige un rango mayor.")
