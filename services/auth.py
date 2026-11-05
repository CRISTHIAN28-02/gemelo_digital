# ==============================================================================
# AUTENTICACIÓN Y CONTROL DE ACCESO POR ROL
# ==============================================================================

import streamlit as st

from database import db


def verificar_credenciales(email: str, password: str):
    """Valida email/contraseña contra la tabla usuarios y devuelve un dict con
    los datos de sesión, o None si las credenciales son inválidas."""
    df = db.fetch_df(
        """SELECT u.id, u.nombre, u.email, u.password_hash, u.activo, r.nombre AS rol
           FROM usuarios u JOIN roles r ON u.rol_id = r.id
           WHERE u.email = ?""",
        (email,),
    )
    if df.empty:
        return None
    fila = df.iloc[0]
    if not bool(fila["activo"]):
        return None
    if fila["password_hash"] != db.hash_password(password):
        return None
    return {"id": int(fila["id"]), "nombre": fila["nombre"], "email": fila["email"], "rol": fila["rol"]}


def usuario_actual():
    return st.session_state.get("usuario")


def requerir_login():
    """Detiene la ejecución de la página si no hay una sesión iniciada."""
    if usuario_actual() is None:
        st.warning("Debes iniciar sesión para acceder a esta sección.")
        st.stop()


def requerir_rol(roles_permitidos: list):
    """Detiene la ejecución si el usuario no está logueado o su rol no está
    en la lista de roles permitidos para este módulo."""
    requerir_login()
    usuario = usuario_actual()
    if usuario["rol"] not in roles_permitidos:
        st.error("⛔ No tienes permisos para acceder a este módulo.")
        st.stop()


def cerrar_sesion():
    from services.auditoria import registrar_evento

    usuario = usuario_actual()
    if usuario:
        registrar_evento(usuario["email"], "Cierre de sesión", "Autenticación", "Éxito")
    if "usuario" in st.session_state:
        del st.session_state["usuario"]
