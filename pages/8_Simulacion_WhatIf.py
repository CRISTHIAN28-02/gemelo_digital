import json

import streamlit as st

from database import db
from services import auth
from services import motor_predictivo as mp
from services.auditoria import registrar_evento

auth.requerir_login()
usuario = auth.usuario_actual()

st.title("🧭 Simulación What-If")
st.caption("Compara un escenario propuesto contra el escenario actual, sin afectar la operación real de la planta.")

st.subheader("ESCENARIO")
col1, col2, col3 = st.columns(3)
turbidez = col1.slider("Turbidez (NTU)", 5, 300, 85)
caudal = col2.slider("Caudal (L/s)", 20, 300, 120)
dosis_actual = col3.slider("Dosis actual (mg/L)", 0, 100, 40)
saturacion_filtro = st.slider("Saturación estimada del filtro (%)", 0, 100, 20)

if st.button("▶️ SIMULAR", use_container_width=True):
    dosis_sugerida = mp.calcular_dosis_sugerida(turbidez, caudal=caudal)
    turbidez_actual_est = mp.calcular_turbidez_estimada(turbidez, dosis_actual, dosis_sugerida, saturacion_filtro)
    turbidez_propuesta_est = mp.calcular_turbidez_estimada(turbidez, dosis_sugerida, dosis_sugerida, saturacion_filtro)
    costo_actual = mp.calcular_costo_dosificacion(dosis_actual, caudal)
    costo_propuesto = mp.calcular_costo_dosificacion(dosis_sugerida, caudal)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### ESCENARIO ACTUAL")
        st.metric("Dosis", f"{dosis_actual} mg/L")
        st.metric("Turbidez estimada", f"{turbidez_actual_est:.1f} NTU")
        st.metric("Costo estimado", f"${costo_actual:.2f}/h")
    with col_b:
        st.markdown("### ESCENARIO PROPUESTO")
        st.metric("Dosis", f"{dosis_sugerida} mg/L")
        st.metric("Turbidez estimada", f"{turbidez_propuesta_est:.1f} NTU")
        st.metric("Costo estimado", f"${costo_propuesto:.2f}/h")

    st.info(
        f"Diferencia de dosis: {dosis_sugerida - dosis_actual:+.1f} mg/L  |  "
        f"Diferencia de costo: ${costo_propuesto - costo_actual:+.2f}/h"
    )
    st.caption("⚠️ Resultados de un modelo demostrativo — no representan mediciones físicas exactas de la planta.")

    st.session_state["ultimo_resultado_whatif"] = {
        "parametros": {"turbidez": turbidez, "caudal": caudal, "dosis_actual": dosis_actual,
                       "saturacion_filtro": saturacion_filtro},
        "resultado": {"dosis_sugerida": dosis_sugerida, "turbidez_actual_est": turbidez_actual_est,
                      "turbidez_propuesta_est": turbidez_propuesta_est,
                      "costo_actual": costo_actual, "costo_propuesto": costo_propuesto},
    }

st.divider()
if "ultimo_resultado_whatif" in st.session_state:
    nombre = st.text_input("Nombre del escenario a guardar", value="Escenario sin nombre")
    if st.button("💾 Guardar simulación"):
        r = st.session_state["ultimo_resultado_whatif"]
        db.ejecutar(
            "INSERT INTO simulaciones (usuario_id, nombre, parametros, resultado, fecha) "
            "VALUES (?,?,?,?, datetime('now'))",
            (usuario["id"], nombre, json.dumps(r["parametros"]), json.dumps(r["resultado"])),
        )
        registrar_evento(usuario["email"], "Guardó simulación What-If", "Simulación", "Éxito", nombre)
        st.success("Simulación guardada.")

st.subheader("📜 Simulaciones guardadas")
df_sim = db.fetch_df(
    """SELECT s.fecha, u.nombre AS usuario, s.nombre AS escenario, s.parametros, s.resultado
       FROM simulaciones s LEFT JOIN usuarios u ON s.usuario_id = u.id
       ORDER BY s.fecha DESC LIMIT 20"""
)
st.dataframe(df_sim, use_container_width=True, hide_index=True)
