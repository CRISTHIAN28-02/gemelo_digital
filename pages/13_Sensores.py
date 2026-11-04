import streamlit as st

from database import db
from services import auth
from services.auditoria import registrar_evento

auth.requerir_rol(["administrador"])
usuario = auth.usuario_actual()

st.title("📶 Gestión de Sensores")

df = db.fetch_df(
    """SELECT s.id, s.codigo, s.variable, s.unidad, e.codigo AS equipo, s.activo,
              s.umbral_min, s.umbral_max
       FROM sensores s JOIN equipos e ON s.equipo_id = e.id ORDER BY s.codigo"""
)
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("➕ Registrar sensor")
equipos = db.fetch_df("SELECT id, codigo, nombre FROM equipos")
equipo_opciones = {f"{fila.codigo} — {fila.nombre}": fila.id for fila in equipos.itertuples()}

with st.form("crear_sensor"):
    codigo = st.text_input("Código del sensor (ej. PH-002)")
    variable = st.selectbox(
        "Variable",
        ["ph", "turbidez", "caudal", "presion", "presion_diferencial", "nivel",
         "temperatura", "vibracion", "dosis"],
    )
    unidad = st.text_input("Unidad (ej. NTU, bar, °C)")
    equipo_sel = st.selectbox("Equipo asociado", list(equipo_opciones.keys()))
    umbral_min = st.number_input("Umbral mínimo", value=0.0)
    umbral_max = st.number_input("Umbral máximo", value=100.0)
    crear = st.form_submit_button("Registrar sensor")

if crear:
    if not codigo:
        st.error("El código del sensor es obligatorio.")
    else:
        equipo_id = equipo_opciones[equipo_sel]
        try:
            db.ejecutar(
                "INSERT INTO sensores (equipo_id, codigo, variable, unidad, activo, umbral_min, umbral_max) "
                "VALUES (?,?,?,?,1,?,?)",
                (equipo_id, codigo, variable, unidad, umbral_min, umbral_max),
            )
            registrar_evento(usuario["email"], "Registró sensor", "Sensores", "Éxito", codigo)
            st.success("Sensor registrado.")
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo registrar el sensor (¿código duplicado?): {e}")

st.divider()
st.subheader("✏️ Activar / desactivar sensor")
if not df.empty:
    opciones_sensor = {f"{fila.codigo} ({fila.equipo})": fila.id for fila in df.itertuples()}
    seleccion = st.selectbox("Sensor", list(opciones_sensor.keys()))
    sid = opciones_sensor[seleccion]
    activo_actual = bool(df[df["id"] == sid].iloc[0]["activo"])
    nuevo_estado = st.checkbox("Sensor activo", value=activo_actual)
    if st.button("Guardar"):
        db.ejecutar("UPDATE sensores SET activo = ? WHERE id = ?", (int(nuevo_estado), int(sid)))
        registrar_evento(usuario["email"], "Actualizó sensor", "Sensores", "Éxito", f"id {sid}")
        st.success("Sensor actualizado.")
        st.rerun()
