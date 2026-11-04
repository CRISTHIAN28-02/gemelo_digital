import streamlit as st

from database import db
from services import auth

auth.requerir_login()

st.title("📄 Reportes")

tabs = st.tabs(["Estado de planta", "Alertas", "Predicciones", "Mantenimientos", "Dosificación", "Simulaciones"])

with tabs[0]:
    df = db.fetch_df("SELECT codigo, nombre, tipo, estado, nivel_riesgo FROM equipos")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Descargar CSV", df.to_csv(index=False).encode("utf-8"),
                        "estado_planta.csv", "text/csv")

with tabs[1]:
    col1, col2 = st.columns(2)
    fecha_desde = col1.date_input("Desde", key="al_desde")
    fecha_hasta = col2.date_input("Hasta", key="al_hasta")
    df = db.fetch_df(
        """SELECT a.fecha, e.codigo AS equipo, a.tipo, a.severidad, a.descripcion, a.estado
           FROM alertas a LEFT JOIN equipos e ON a.equipo_id = e.id
           WHERE date(a.fecha) BETWEEN ? AND ? ORDER BY a.fecha DESC""",
        (fecha_desde.isoformat(), fecha_hasta.isoformat()),
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Descargar CSV", df.to_csv(index=False).encode("utf-8"),
                        "alertas.csv", "text/csv")

with tabs[2]:
    df = db.fetch_df(
        """SELECT p.fecha, e.codigo AS equipo, p.riesgo_pct, p.nivel, p.recomendacion
           FROM predicciones p LEFT JOIN equipos e ON p.equipo_id = e.id ORDER BY p.fecha DESC"""
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Descargar CSV", df.to_csv(index=False).encode("utf-8"),
                        "predicciones.csv", "text/csv")

with tabs[3]:
    df = db.fetch_df(
        """SELECT m.fecha, e.codigo AS equipo, m.tipo, m.descripcion, m.responsable
           FROM mantenimientos m LEFT JOIN equipos e ON m.equipo_id = e.id ORDER BY m.fecha DESC"""
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Descargar CSV", df.to_csv(index=False).encode("utf-8"),
                        "mantenimientos.csv", "text/csv")

with tabs[4]:
    df = db.fetch_df(
        """SELECT r.fecha, u.nombre AS usuario, r.turbidez, r.ph, r.caudal, r.dosis_actual, r.dosis_sugerida
           FROM recomendaciones r LEFT JOIN usuarios u ON r.usuario_id = u.id ORDER BY r.fecha DESC"""
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Descargar CSV", df.to_csv(index=False).encode("utf-8"),
                        "dosificacion.csv", "text/csv")

with tabs[5]:
    df = db.fetch_df(
        """SELECT s.fecha, u.nombre AS usuario, s.nombre AS escenario, s.parametros, s.resultado
           FROM simulaciones s LEFT JOIN usuarios u ON s.usuario_id = u.id ORDER BY s.fecha DESC"""
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Descargar CSV", df.to_csv(index=False).encode("utf-8"),
                        "simulaciones.csv", "text/csv")
