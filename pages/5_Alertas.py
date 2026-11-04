import streamlit as st

from database import db
from services import auth
from services.auditoria import registrar_evento

auth.requerir_login()
usuario = auth.usuario_actual()

st.title("🚨 Alertas")

col1, col2, col3 = st.columns(3)
severidad = col1.selectbox("Severidad", ["Todas", "informacion", "baja", "media", "alta", "critica"])
estado_f = col2.selectbox("Estado", ["Todos", "nueva", "en_revision", "atendida", "cerrada"])
equipos_df = db.fetch_df("SELECT id, codigo FROM equipos")
equipo_f = col3.selectbox("Equipo", ["Todos"] + equipos_df["codigo"].tolist())

query = """
    SELECT a.id, a.fecha, e.codigo AS equipo, a.tipo, a.severidad, a.valor_actual,
           a.descripcion, a.estado
    FROM alertas a LEFT JOIN equipos e ON a.equipo_id = e.id WHERE 1=1
"""
params = []
if severidad != "Todas":
    query += " AND a.severidad = ?"
    params.append(severidad)
if estado_f != "Todos":
    query += " AND a.estado = ?"
    params.append(estado_f)
if equipo_f != "Todos":
    query += " AND e.codigo = ?"
    params.append(equipo_f)
query += " ORDER BY a.fecha DESC"

df = db.fetch_df(query, tuple(params))
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Actualizar estado de una alerta")
if not df.empty:
    opciones = {f"#{fila.id} — {fila.descripcion[:50]}": fila.id for fila in df.itertuples()}
    seleccion = st.selectbox("Alerta", list(opciones.keys()))
    alerta_id = opciones[seleccion]
    nuevo_estado = st.selectbox("Nuevo estado", ["nueva", "en_revision", "atendida", "cerrada"])
    if st.button("Actualizar"):
        db.ejecutar("UPDATE alertas SET estado = ? WHERE id = ?", (nuevo_estado, alerta_id))
        registrar_evento(usuario["email"], "Actualizó estado de alerta", "Alertas", "Éxito",
                          f"Alerta #{alerta_id} -> {nuevo_estado}")
        st.success("Alerta actualizada.")
        st.rerun()
else:
    st.info("No hay alertas que coincidan con los filtros seleccionados.")
