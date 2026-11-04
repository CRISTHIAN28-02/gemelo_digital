import streamlit as st

from database import db
from services import auth
from services.simulador import ejecutar_ciclo_ingesta

auth.requerir_login()

st.title("📊 Dashboard General")
st.caption("Estado general de la planta — datos simulados como sustituto de sensores físicos.")

if st.button("🔄 Simular ciclo IoT (nueva ronda de lecturas)"):
    n = ejecutar_ciclo_ingesta()
    st.toast(f"Se generaron {n} nuevas lecturas simuladas.")


def ultima_lectura(variable):
    fila = db.fetch_uno(
        """SELECT m.valor FROM mediciones m JOIN sensores s ON m.sensor_id = s.id
           WHERE s.variable = ? ORDER BY m.timestamp DESC LIMIT 1""",
        (variable,),
    )
    return fila[0] if fila else None


ph = ultima_lectura("ph")
turbidez = ultima_lectura("turbidez")
caudal = ultima_lectura("caudal")
temperatura = ultima_lectura("temperatura")

equipos_df = db.fetch_df("SELECT estado FROM equipos")
total_equipos = len(equipos_df)
activos = len(equipos_df[equipos_df["estado"].isin(["operativo", "advertencia"])])
alertas_activas = db.fetch_uno("SELECT COUNT(*) FROM alertas WHERE estado IN ('nueva','en_revision')")[0]
criticos = len(equipos_df[equipos_df["estado"] == "critico"])
anomalias_altas = db.fetch_uno("SELECT COUNT(*) FROM predicciones WHERE nivel = 'ALTO'")[0]

if criticos > 0 or alertas_activas >= 3:
    estado_general = "🔴 ATENCIÓN REQUERIDA"
elif alertas_activas > 0:
    estado_general = "🟡 OPERACIÓN CON ADVERTENCIAS"
else:
    estado_general = "🟢 OPERACIÓN NORMAL"

st.subheader(f"Estado de planta: {estado_general}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("pH", f"{ph:.2f}" if ph is not None else "N/D")
c2.metric("Turbidez", f"{turbidez:.1f} NTU" if turbidez is not None else "N/D")
c3.metric("Caudal", f"{caudal:.0f} L/s" if caudal is not None else "N/D")
c4.metric("Temperatura", f"{temperatura:.1f} °C" if temperatura is not None else "N/D")

c5, c6, c7 = st.columns(3)
c5.metric("Equipos activos", f"{activos}/{total_equipos}")
c6.metric("Alertas activas", int(alertas_activas))
c7.metric("Equipos con riesgo alto", int(anomalias_altas))

st.divider()

st.subheader("🚨 Últimas alertas")
df_alertas = db.fetch_df(
    """SELECT a.fecha, e.nombre AS equipo, a.severidad, a.descripcion, a.estado
       FROM alertas a LEFT JOIN equipos e ON a.equipo_id = e.id
       ORDER BY a.fecha DESC LIMIT 5"""
)
st.dataframe(df_alertas, use_container_width=True, hide_index=True)

st.subheader("⚙️ Estado de equipos")
df_equipos = db.fetch_df(
    "SELECT codigo, nombre, tipo, estado, nivel_riesgo FROM equipos ORDER BY nivel_riesgo DESC"
)
st.dataframe(df_equipos, use_container_width=True, hide_index=True)
