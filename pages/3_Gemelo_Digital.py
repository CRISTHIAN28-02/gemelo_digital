import plotly.graph_objects as go
import streamlit as st

from database import db
from services import auth

auth.requerir_login()

st.title("🏭 Gemelo Digital de la Planta")
st.caption(
    "Representación simplificada del proceso. Selecciona un equipo debajo del esquema para ver su "
    "detalle (la selección sustituye al clic directo sobre el diagrama en este MVP)."
)

COLOR_ESTADO = {
    "operativo": ("#2ecc71", "🟢"),
    "advertencia": ("#f1c40f", "🟡"),
    "critico": ("#e74c3c", "🔴"),
    "mantenimiento": ("#3498db", "🔵"),
    "fuera_linea": ("#95a5a6", "⚪"),
}

equipos = db.fetch_df("SELECT * FROM equipos ORDER BY id")


def dibujar_esquema(df):
    fig = go.Figure()
    box_w, box_h = 2.2, 1.5
    cols = 4
    for i, fila in df.reset_index(drop=True).iterrows():
        renglon, columna = divmod(i, cols)
        x = columna * (box_w + 0.6)
        y = -renglon * (box_h + 0.8)
        hex_c, emoji = COLOR_ESTADO.get(fila["estado"], ("#7f8c8d", "⚪"))
        fig.add_shape(
            type="rect", x0=x, x1=x + box_w, y0=y, y1=y + box_h,
            line=dict(color=hex_c, width=3), fillcolor=hex_c, opacity=0.25,
        )
        fig.add_annotation(x=x + box_w / 2, y=y + box_h * 0.65, showarrow=False,
                            text=f"{fila['codigo']}<br>{fila['nombre']}", font=dict(size=11, color="#eaeaea"))
        fig.add_annotation(x=x + box_w / 2, y=y + box_h * 0.2, showarrow=False,
                            text=f"{emoji} {fila['estado'].capitalize()}", font=dict(size=11, color="#eaeaea"))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10),
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


st.plotly_chart(dibujar_esquema(equipos), use_container_width=True)

opciones = {
    f"{COLOR_ESTADO.get(fila.estado, ('', '⚪'))[1]} {fila.codigo} — {fila.nombre}": fila.id
    for fila in equipos.itertuples()
}
seleccion = st.selectbox("Seleccionar equipo", list(opciones.keys()))
equipo_id = opciones[seleccion]
equipo = equipos[equipos["id"] == equipo_id].iloc[0]

st.divider()
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"{equipo['nombre']} ({equipo['codigo']})")
    st.write(f"**Tipo:** {equipo['tipo'].capitalize()}  |  **Ubicación:** {equipo['ubicacion']}")
    hex_c, emoji = COLOR_ESTADO.get(equipo["estado"], ("", "⚪"))
    st.write(f"**Estado:** {emoji} {equipo['estado'].capitalize()}")
    st.write(f"**Instalado:** {equipo['fecha_instalacion']}  |  "
             f"**Último mantenimiento:** {equipo['ultimo_mantenimiento']}")

    st.markdown("**Variables asociadas (última medición):**")
    df_vars = db.fetch_df(
        """SELECT s.variable, s.unidad, m.valor, m.timestamp
           FROM sensores s
           LEFT JOIN mediciones m
             ON m.id = (SELECT id FROM mediciones WHERE sensor_id = s.id ORDER BY timestamp DESC LIMIT 1)
           WHERE s.equipo_id = ?""",
        (int(equipo_id),),
    )
    st.dataframe(df_vars, use_container_width=True, hide_index=True)

with col2:
    st.markdown("**🚨 Alertas relacionadas**")
    df_al = db.fetch_df(
        "SELECT fecha, severidad, descripcion FROM alertas WHERE equipo_id = ? ORDER BY fecha DESC LIMIT 3",
        (int(equipo_id),),
    )
    if df_al.empty:
        st.caption("Sin alertas registradas.")
    else:
        st.dataframe(df_al, use_container_width=True, hide_index=True)

    st.markdown("**🔮 Predicción más reciente**")
    df_pred = db.fetch_df(
        "SELECT riesgo_pct, nivel, recomendacion, fecha FROM predicciones "
        "WHERE equipo_id = ? ORDER BY fecha DESC LIMIT 1",
        (int(equipo_id),),
    )
    if df_pred.empty:
        st.caption("Aún no hay predicción para este equipo.")
    else:
        p = df_pred.iloc[0]
        st.write(f"Riesgo: **{p['riesgo_pct']:.0f}%** ({p['nivel']})")
        st.caption(p["recomendacion"])

st.markdown("**🛠️ Historial de mantenimiento**")
df_mant = db.fetch_df(
    "SELECT fecha, tipo, descripcion, responsable FROM mantenimientos "
    "WHERE equipo_id = ? ORDER BY fecha DESC",
    (int(equipo_id),),
)
st.dataframe(df_mant, use_container_width=True, hide_index=True)
