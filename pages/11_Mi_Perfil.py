import streamlit as st

from services import auth

auth.requerir_login()
usuario = auth.usuario_actual()

st.title("👤 Mi Perfil")
st.write(f"**Nombre:** {usuario['nombre']}")
st.write(f"**Correo:** {usuario['email']}")
st.write(f"**Rol:** {usuario['rol'].capitalize()}")
st.caption("La edición de contraseña y datos personales no está incluida en este MVP.")
