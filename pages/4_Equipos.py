from datetime import date

import streamlit as st

from database import db
from services import auth
from services.auditoria import registrar_evento
from services.global_assistant import render_global_assistant

auth.requerir_login()
usuario = auth.usuario_actual()

st.title("️ Equipos")

df = db.fetch_df("SELECT * FROM equipos ORDER BY codigo")
st.dataframe(
    df[["codigo", "nombre", "tipo", "ubicacion", "estado", "fecha_instalacion",
        "ultimo_mantenimiento", "nivel_riesgo"]],
    use_container_width=True, hide_index=True,
)

if usuario["rol"] == "administrador":
    opciones = {f"{fila.codigo} — {fila.nombre}": fila.id for fila in df.itertuples()}

    st.divider()
    st.subheader("️ Actualizar estado de un equipo")
    seleccion = st.selectbox("Equipo", list(opciones.keys()), key="sel_estado")
    equipo_id = opciones[seleccion]
    nuevo_estado = st.selectbox(
        "Nuevo estado", ["operativo", "advertencia", "critico", "mantenimiento", "fuera_linea"]
    )
    if st.button("Guardar cambio de estado"):
        db.ejecutar("UPDATE equipos SET estado = ? WHERE id = ?", (nuevo_estado, equipo_id))
        registrar_evento(usuario["email"], "Actualizó estado de equipo", "Equipos", "Éxito",
                          f"Equipo id {equipo_id} -> {nuevo_estado}")
        st.success("Estado actualizado.")
        st.rerun()

    st.divider()
    st.subheader("️ Registrar mantenimiento")
    seleccion_mant = st.selectbox("Equipo", list(opciones.keys()), key="sel_mant")
    equipo_id_mant = opciones[seleccion_mant]
    tipo_mant = st.selectbox("Tipo", ["preventivo", "correctivo"])
    descripcion = st.text_area("Descripción")
    responsable = st.text_input("Responsable", value=usuario["nombre"])
    if st.button("Registrar mantenimiento"):
        db.ejecutar(
            "INSERT INTO mantenimientos (equipo_id, tipo, descripcion, fecha, responsable) "
            "VALUES (?,?,?,?,?)",
            (equipo_id_mant, tipo_mant, descripcion, date.today().isoformat(), responsable),
        )
        db.ejecutar("UPDATE equipos SET ultimo_mantenimiento = ? WHERE id = ?",
                    (date.today().isoformat(), equipo_id_mant))
        registrar_evento(usuario["email"], "Registró mantenimiento", "Equipos", "Éxito",
                          f"Equipo id {equipo_id_mant}")
        st.success("Mantenimiento registrado.")
        st.rerun()
else:
    st.caption("Como operador puedes consultar el estado de los equipos. "
               "La edición está reservada al administrador.")

# Asistente rápido global, disponible también en este módulo.
render_global_assistant("Equipos")
