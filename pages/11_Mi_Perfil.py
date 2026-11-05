import streamlit as st

from services import auth
from services.global_assistant import render_global_assistant

auth.requerir_login()
usuario = auth.usuario_actual()

st.title(" Mi Perfil")
st.write(f"**Nombre:** {usuario['nombre']}")
st.write(f"**Correo:** {usuario['email']}")
st.write(f"**Rol:** {usuario['rol'].capitalize()}")
st.caption("La edición de contraseña y datos personales no está incluida en este MVP.")

# Asistente rápido global, disponible también en este módulo.
render_global_assistant("Mi Perfil")
