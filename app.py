# ==============================================================================
# GEMELO DIGITAL — PLANTA DE TRATAMIENTO DE AGUA (PTAP/PTAR)
# ------------------------------------------------------------------------------
# MVP funcional y navegable: monitoreo, gemelo digital, equipos, alertas,
# predicción de mantenimiento, dosificación, simulación What-If, reportes,
# asistente de IA y administración (usuarios/sensores/configuración/auditoría).
#
# Punto de entrada: maneja el login y construye el menú de navegación según
# el rol del usuario (administrador u operador).
# ==============================================================================

import streamlit as st

from database.db import asegurar_base_datos
from services import auth
from services.auditoria import registrar_evento

st.set_page_config(page_title="Gemelo Digital - PTAP/PTAR", page_icon="💧", layout="wide")

# Crea el esquema y siembra datos de demostración la primera vez que se ejecuta
asegurar_base_datos()


def pantalla_login():
    st.markdown(
        "<h2 style='text-align:center'>💧 Gemelo Digital — Planta de Tratamiento de Agua</h2>",
        unsafe_allow_html=True,
    )
    st.caption(
        "<p style='text-align:center'>MVP de monitoreo, análisis predictivo y apoyo a la toma "
        "de decisiones (PTAP/PTAR)</p>",
        unsafe_allow_html=True,
    )

    _, col_centro, _ = st.columns([1, 1.2, 1])
    with col_centro:
        with st.form("form_login"):
            email = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password")
            enviar = st.form_submit_button("Iniciar sesión", use_container_width=True)

        if enviar:
            usuario = auth.verificar_credenciales(email.strip().lower(), password)
            if usuario:
                st.session_state.usuario = usuario
                registrar_evento(usuario["email"], "Inicio de sesión", "Autenticación", "Éxito")
                st.rerun()
            else:
                st.error("Credenciales inválidas o usuario inactivo.")
                registrar_evento(email or "(vacío)", "Intento de inicio de sesión",
                                  "Autenticación", "Fallido")

        with st.expander("🔑 Credenciales de demostración"):
            st.markdown(
                "| Rol | Correo | Contraseña |\n"
                "|---|---|---|\n"
                "| Administrador | `admin@demo.com` | `admin123` |\n"
                "| Operador | `operador@demo.com` | `operador123` |\n\n"
                "*Credenciales de prueba — cámbialas antes de usar este sistema en un entorno real.*"
            )


usuario_actual = auth.usuario_actual()

if usuario_actual is None:
    pantalla_login()
else:
    # --- Páginas comunes a ambos roles ---
    paginas = [
        st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊", default=True),
        st.Page("pages/2_Monitoreo.py", title="Monitoreo", icon="📡"),
        st.Page("pages/3_Gemelo_Digital.py", title="Gemelo Digital", icon="🏭"),
        st.Page("pages/4_Equipos.py", title="Equipos", icon="⚙️"),
        st.Page("pages/5_Alertas.py", title="Alertas", icon="🚨"),
        st.Page("pages/6_Predicciones.py", title="Predicciones", icon="🔮"),
        st.Page("pages/7_Dosificacion.py", title="Dosificación", icon="🧪"),
        st.Page("pages/8_Simulacion_WhatIf.py", title="Simulación What-If", icon="🧭"),
        st.Page("pages/9_Reportes.py", title="Reportes", icon="📄"),
        st.Page("pages/10_Asistente_IA.py", title="Asistente IA", icon="🤖"),
    ]

    # --- Páginas exclusivas del administrador ---
    if usuario_actual["rol"] == "administrador":
        paginas += [
            st.Page("pages/12_Usuarios.py", title="Usuarios", icon="👥"),
            st.Page("pages/13_Sensores.py", title="Sensores", icon="📶"),
            st.Page("pages/14_Configuracion.py", title="Configuración", icon="🛠️"),
            st.Page("pages/15_Auditoria.py", title="Auditoría", icon="🗂️"),
        ]

    paginas.append(st.Page("pages/11_Mi_Perfil.py", title="Mi Perfil", icon="👤"))

    with st.sidebar:
        st.markdown(f"**👤 {usuario_actual['nombre']}**")
        st.caption(f"Rol: {usuario_actual['rol'].capitalize()}")
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            auth.cerrar_sesion()
            st.rerun()
        st.divider()

    navegacion = st.navigation(paginas)
    navegacion.run()
