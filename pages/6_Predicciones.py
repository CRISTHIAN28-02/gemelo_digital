import streamlit as st

from database import db
from services import auth
from services import motor_predictivo as mp
from services.auditoria import registrar_evento

auth.requerir_login()
usuario = auth.usuario_actual()

st.title("🔮 Predicciones de Mantenimiento")
st.info(
    "⚠️ Modelo demostrativo basado en reglas sobre lecturas recientes. Aún no corresponde a un "
    "modelo de Machine Learning entrenado con datos históricos reales de la planta."
)

equipos = db.fetch_df("SELECT * FROM equipos ORDER BY nivel_riesgo DESC")

if st.button("🔁 Recalcular predicciones con las lecturas más recientes"):
    for _, eq in equipos.iterrows():
        lecturas = db.fetch_df(
            """SELECT s.variable, m.valor FROM sensores s
               LEFT JOIN mediciones m
                 ON m.id = (SELECT id FROM mediciones WHERE sensor_id = s.id ORDER BY timestamp DESC LIMIT 1)
               WHERE s.equipo_id = ?""",
            (int(eq["id"]),),
        )
        dict_lecturas = dict(zip(lecturas["variable"], lecturas["valor"]))
        riesgo, nivel, vars_rel = mp.calcular_riesgo_anomalia_equipo(dict_lecturas)
        recomendacion = mp.recomendacion_por_nivel(nivel, eq["nombre"])
        db.ejecutar(
            "INSERT INTO predicciones (equipo_id, riesgo_pct, nivel, variables_relacionadas, "
            "recomendacion, fecha) VALUES (?,?,?,?,?, datetime('now'))",
            (int(eq["id"]), riesgo, nivel,
             ", ".join(vars_rel) if vars_rel else "Sin variables fuera de rango", recomendacion),
        )
        db.ejecutar("UPDATE equipos SET nivel_riesgo = ? WHERE id = ?", (riesgo, int(eq["id"])))
    registrar_evento(usuario["email"], "Recalculó predicciones", "Predicciones", "Éxito")
    st.success("Predicciones recalculadas.")
    st.rerun()

for _, eq in equipos.iterrows():
    pred = db.fetch_df(
        "SELECT * FROM predicciones WHERE equipo_id = ? ORDER BY fecha DESC LIMIT 1", (int(eq["id"]),)
    )
    with st.expander(f"{eq['codigo']} — {eq['nombre']}  |  Riesgo: {eq['nivel_riesgo']:.0f}%"):
        if pred.empty:
            st.caption("Sin predicción registrada todavía.")
        else:
            p = pred.iloc[0]
            st.metric("Riesgo de anomalía", f"{p['riesgo_pct']:.0f} %", help=f"Nivel: {p['nivel']}")
            st.write(f"**Variables relacionadas:** {p['variables_relacionadas']}")
            st.write(f"**Fecha:** {p['fecha']}")
            st.write(f"**Recomendación:** {p['recomendacion']}")
