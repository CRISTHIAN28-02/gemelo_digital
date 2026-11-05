import streamlit as st

from database import db
from services import auth
from services import motor_predictivo as mp
from services.auditoria import registrar_evento
from services.global_assistant import render_global_assistant

auth.requerir_login()
usuario = auth.usuario_actual()

st.title(" Recomendación de Dosificación")
st.caption("Apoyo a la decisión del operador. La dosis NO se aplica automáticamente en la planta física.")


def ultima_lectura(variable, valor_por_defecto):
    fila = db.fetch_uno(
        """SELECT m.valor FROM mediciones m JOIN sensores s ON m.sensor_id = s.id
           WHERE s.variable = ? ORDER BY m.timestamp DESC LIMIT 1""",
        (variable,),
    )
    return float(fila[0]) if fila else valor_por_defecto


col1, col2 = st.columns(2)
turbidez = col1.number_input("Turbidez (NTU)", 0.0, 500.0, ultima_lectura("turbidez", 20.0))
ph = col2.number_input("pH", 0.0, 14.0, ultima_lectura("ph", 7.2))
caudal = col1.number_input("Caudal (L/s)", 0.0, 500.0, ultima_lectura("caudal", 120.0))
dosis_actual = col2.number_input("Dosis actual (mg/L)", 0.0, 100.0, ultima_lectura("dosis", 38.0))
temperatura = col1.number_input("Temperatura (°C)", 0.0, 50.0, ultima_lectura("temperatura", 21.0))

if st.button("Calcular recomendación", use_container_width=True):
    dosis_sugerida = mp.calcular_dosis_sugerida(turbidez, ph, caudal, temperatura)
    diferencia = dosis_sugerida - dosis_actual
    if diferencia > 0.5:
        tendencia_txt = "exigen una dosis mayor"
    elif diferencia < -0.5:
        tendencia_txt = "permiten reducir la dosis"
    else:
        tendencia_txt = "ya están cerca del óptimo"
    justificacion = (
        f"Con una turbidez de {turbidez:.0f} NTU, pH {ph:.1f} y caudal de {caudal:.0f} L/s, "
        f"el modelo estima que las condiciones actuales {tendencia_txt} respecto al escenario "
        f"de operación configurado."
    )

    st.subheader("DATOS ACTUALES")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Turbidez", f"{turbidez:.0f} NTU")
    c2.metric("pH", f"{ph:.1f}")
    c3.metric("Caudal", f"{caudal:.0f} L/s")
    c4.metric("Dosis actual", f"{dosis_actual:.1f} mg/L")

    st.subheader("RECOMENDACIÓN")
    st.metric("Dosis sugerida", f"{dosis_sugerida:.1f} mg/L", delta=f"{diferencia:+.1f} mg/L")
    st.write(f"**Justificación:** {justificacion}")

    db.ejecutar(
        """INSERT INTO recomendaciones (usuario_id, turbidez, ph, caudal, temperatura, dosis_actual,
           dosis_sugerida, justificacion, fecha) VALUES (?,?,?,?,?,?,?,?, datetime('now'))""",
        (usuario["id"], turbidez, ph, caudal, temperatura, dosis_actual, dosis_sugerida, justificacion),
    )
    registrar_evento(usuario["email"], "Generó recomendación de dosificación", "Dosificación", "Éxito")

st.divider()
st.subheader(" Historial de recomendaciones")
df_hist = db.fetch_df(
    """SELECT r.fecha, u.nombre AS usuario, r.turbidez, r.ph, r.caudal, r.dosis_actual, r.dosis_sugerida
       FROM recomendaciones r LEFT JOIN usuarios u ON r.usuario_id = u.id
       ORDER BY r.fecha DESC LIMIT 20"""
)
st.dataframe(df_hist, use_container_width=True, hide_index=True)

# Asistente rápido global, disponible también en este módulo.
render_global_assistant("Dosificación")
