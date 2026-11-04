from datetime import datetime

import streamlit as st

from database import db
from services import auth
from services.auditoria import registrar_evento

auth.requerir_rol(["administrador"])
usuario = auth.usuario_actual()

st.title("👥 Gestión de Usuarios")

df = db.fetch_df(
    """SELECT u.id, u.nombre, u.email, r.nombre AS rol, u.activo, u.fecha_creacion
       FROM usuarios u JOIN roles r ON u.rol_id = r.id ORDER BY u.id"""
)

filtro = st.text_input("🔍 Buscar por nombre o correo")
df_vista = df
if filtro:
    df_vista = df[
        df["nombre"].str.contains(filtro, case=False) | df["email"].str.contains(filtro, case=False)
    ]
st.dataframe(df_vista, use_container_width=True, hide_index=True)

st.divider()
st.subheader("➕ Crear usuario")
with st.form("crear_usuario"):
    nombre = st.text_input("Nombre completo")
    email = st.text_input("Correo electrónico")
    password = st.text_input("Contraseña temporal", type="password")
    rol_nombre = st.selectbox("Rol", ["operador", "administrador"])
    crear = st.form_submit_button("Crear usuario")

if crear:
    if not nombre or not email or not password:
        st.error("Todos los campos son obligatorios.")
    else:
        email_norm = email.strip().lower()
        existe = db.fetch_uno("SELECT id FROM usuarios WHERE email = ?", (email_norm,))
        if existe:
            st.error("Ya existe un usuario con ese correo.")
        else:
            rol_id = db.fetch_uno("SELECT id FROM roles WHERE nombre = ?", (rol_nombre,))[0]
            db.ejecutar(
                "INSERT INTO usuarios (nombre, email, password_hash, rol_id, activo, fecha_creacion) "
                "VALUES (?,?,?,?,1,?)",
                (nombre, email_norm, db.hash_password(password), rol_id,
                 datetime.now().isoformat(timespec="seconds")),
            )
            registrar_evento(usuario["email"], "Creó usuario", "Usuarios", "Éxito", email_norm)
            st.success("Usuario creado correctamente.")
            st.rerun()

st.divider()
st.subheader("✏️ Editar / desactivar usuario")
opciones = {f"{fila.nombre} ({fila.email})": fila.id for fila in df.itertuples()}
if opciones:
    seleccion = st.selectbox("Usuario", list(opciones.keys()))
    uid = opciones[seleccion]
    fila_sel = df[df["id"] == uid].iloc[0]
    nuevo_rol = st.selectbox("Rol", ["operador", "administrador"],
                              index=0 if fila_sel["rol"] == "operador" else 1)
    nuevo_activo = st.checkbox("Usuario activo", value=bool(fila_sel["activo"]))
    if st.button("Guardar cambios"):
        if uid == usuario["id"] and not nuevo_activo:
            st.error("No puedes desactivar tu propia cuenta.")
        else:
            rol_id = db.fetch_uno("SELECT id FROM roles WHERE nombre = ?", (nuevo_rol,))[0]
            db.ejecutar("UPDATE usuarios SET rol_id = ?, activo = ? WHERE id = ?",
                        (rol_id, int(nuevo_activo), int(uid)))
            registrar_evento(usuario["email"], "Editó usuario", "Usuarios", "Éxito", f"id {uid}")
            st.success("Usuario actualizado.")
            st.rerun()
