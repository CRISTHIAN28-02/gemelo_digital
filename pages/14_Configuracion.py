import streamlit as st

from database import db
from services import auth
from services.auditoria import registrar_evento

auth.requerir_rol(["administrador"])
usuario = auth.usuario_actual()

st.title("🛠️ Configuración del Sistema")

st.subheader("Estado de las integraciones")
mqtt_ok = db.obtener_configuracion("mqtt_conectado", "1") == "1"
col1, col2 = st.columns(2)
col1.metric("MQTT (simulado)", "🟢 CONECTADO" if mqtt_ok else "🔴 DESCONECTADO")
col2.metric("Base de datos", "🟢 SQLite operativa")
st.caption(
    "Este MVP sustituye un broker MQTT real y PostgreSQL/TimescaleDB por un simulador interno "
    "y una base de datos SQLite local, manteniendo la misma arquitectura modular."
)

if st.button("Alternar estado simulado de MQTT"):
    db.actualizar_configuracion("mqtt_conectado", "0" if mqtt_ok else "1")
    registrar_evento(usuario["email"], "Alternó estado MQTT simulado", "Configuración", "Éxito")
    st.rerun()

st.divider()
st.subheader("Parámetros de simulación y umbrales")
with st.form("form_config"):
    intervalo = st.number_input(
        "Intervalo de simulación (segundos)", 1, 300,
        int(float(db.obtener_configuracion("intervalo_simulacion_seg", 10))),
    )
    umbral_turbidez = st.number_input(
        "Umbral de turbidez de salida (NTU)", 0.0, 50.0,
        float(db.obtener_configuracion("umbral_turbidez_salida", 5)),
    )
    umbral_saturacion = st.number_input(
        "Umbral de saturación de filtro (%)", 0, 100,
        int(float(db.obtener_configuracion("umbral_saturacion_filtro", 80))),
    )
    umbral_riesgo_bomba = st.number_input(
        "Umbral de riesgo de bomba (%)", 0, 100,
        int(float(db.obtener_configuracion("umbral_riesgo_bomba", 70))),
    )
    costo_quimico = st.number_input(
        "Costo del químico (USD/kg)", 0.0, 100.0,
        float(db.obtener_configuracion("costo_quimico_usd_kg", 1.8)),
    )
    guardar = st.form_submit_button("Guardar configuración")

if guardar:
    db.actualizar_configuracion("intervalo_simulacion_seg", intervalo)
    db.actualizar_configuracion("umbral_turbidez_salida", umbral_turbidez)
    db.actualizar_configuracion("umbral_saturacion_filtro", umbral_saturacion)
    db.actualizar_configuracion("umbral_riesgo_bomba", umbral_riesgo_bomba)
    db.actualizar_configuracion("costo_quimico_usd_kg", costo_quimico)
    registrar_evento(usuario["email"], "Actualizó configuración del sistema", "Configuración", "Éxito")
    st.success("Configuración guardada.")
