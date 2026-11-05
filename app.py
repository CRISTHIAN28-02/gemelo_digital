
"""Entrada principal de Gemelo Digital PTAP/PTAR."""

import streamlit as st

from database.db import asegurar_base_datos
from services import auth
from services.auditoria import registrar_evento


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Gemelo Digital | PTAP / PTAR",
    page_icon="G",
    layout="wide",
    initial_sidebar_state="expanded",
)

asegurar_base_datos()


# ============================================================
# ESTILOS CORPORATIVOS
# Compatible con temas Light y Dark de Streamlit
# ============================================================

st.markdown(
    """
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --gd-blue: #3478A8;
    --gd-navy: #173B5E;
}

html,
body,
[class*="css"] {
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.stApp {
    background: var(--background-color);
    color: var(--text-color);
}

[data-testid="stHeader"] {
    background: color-mix(in srgb, var(--background-color) 88%, transparent);
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background: var(--secondary-background-color);
    border-right: 1px solid var(--border-color, rgba(128,128,128,.2));
}

[data-testid="stSidebar"] > div {
    padding-top: 1.2rem;
}

[data-testid="stSidebarNav"] {
    padding-top: .35rem;
}

[data-testid="stSidebarNav"] a {
    border-radius: 9px;
    margin: 2px 7px;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: color-mix(
        in srgb,
        var(--primary-color) 13%,
        var(--secondary-background-color)
    );
    font-weight: 650;
}

/* TIPOGRAFÍA */

h1,
h2,
h3 {
    letter-spacing: -.025em;
    font-weight: 700 !important;
}

h1 {
    font-size: clamp(1.65rem, 2.5vw, 2.15rem) !important;
}

h2 {
    font-size: 1.35rem !important;
}

h3 {
    font-size: 1.08rem !important;
}

/* MÉTRICAS */

[data-testid="stMetric"] {
    background: var(--secondary-background-color);
    border: 1px solid var(--border-color, rgba(128,128,128,.2));
    border-radius: 13px;
    padding: 14px 16px;
}

[data-testid="stMetricLabel"] {
    font-weight: 600;
}

/* TABLAS */

[data-testid="stDataFrame"],
[data-testid="stTable"] {
    border: 1px solid var(--border-color, rgba(128,128,128,.2));
    border-radius: 12px;
    overflow: hidden;
}

/* FORMULARIOS */

[data-testid="stForm"],
[data-testid="stExpander"] {
    border-color: var(--border-color, rgba(128,128,128,.2)) !important;
    border-radius: 12px !important;
}

/* BOTONES */

.stButton > button,
.stFormSubmitButton > button,
.stDownloadButton > button {
    border-radius: 9px;
    font-weight: 600;
    transition: all .15s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    transform: translateY(-1px);
}

/* CAMPOS */

input,
textarea,
[data-baseweb="select"] > div {
    border-radius: 9px !important;
}

hr {
    border-color: var(--border-color, rgba(128,128,128,.2));
}

/* IDENTIDAD CORPORATIVA */

.gd-brand {
    display: flex;
    align-items: center;
    gap: .75rem;
    padding: .25rem 0 1.15rem;
    border-bottom: 1px solid var(--border-color, rgba(128,128,128,.2));
    margin-bottom: 1rem;
}

.gd-brand-mark {
    width: 42px;
    height: 42px;
    display: grid;
    place-items: center;
    border-radius: 12px;
    background: var(--primary-color);
    color: white;
    font-size: 20px;
    font-weight: 800;
    flex-shrink: 0;
}

.gd-brand-name {
    font-size: 1rem;
    font-weight: 750;
    line-height: 1.2;
}

.gd-brand-sub {
    font-size: .72rem;
    opacity: .68;
    margin-top: 3px;
}


/* ============================================================
   LOGIN - TARJETA UNIFICADA
   ============================================================ */

.st-key-login_shell {
    width: 100%;
    max-width: 480px;
    margin: 5vh auto 0;
    padding: 2.2rem 2.3rem 1.8rem;
    border: 1px solid var(--border-color, rgba(128,128,128,.2));
    border-radius: 20px;
    background: var(--secondary-background-color);
    box-shadow: 0 18px 55px rgba(20, 40, 60, .09);
    overflow: hidden;
}

/* ENCABEZADO */

.login-brand {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    margin-bottom: 1.5rem;
}

.login-brand-mark {
    width: 66px;
    height: 66px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 19px;
    background: var(--primary-color);
    color: white;
    font-size: 29px;
    font-weight: 800;
    margin-bottom: 1rem;
    box-shadow: 0 8px 20px rgba(52, 120, 168, .22);
}

.login-brand h1 {
    font-size: 1.65rem !important;
    margin: 0 !important;
    letter-spacing: -.04em;
}

.login-brand p {
    font-size: .68rem;
    letter-spacing: .10em;
    font-weight: 650;
    opacity: .65;
    margin: .45rem 0 0;
}

/* DESCRIPCIÓN */

.login-description {
    text-align: center;
    font-size: .88rem;
    line-height: 1.6;
    opacity: .72;
    margin: 0 0 1.5rem;
}

/* CAMPOS DEL LOGIN */

.st-key-login_shell [data-testid="stTextInput"] label {
    font-weight: 600;
    font-size: .84rem;
}

.st-key-login_shell [data-testid="stTextInput"] input {
    min-height: 45px;
    border-radius: 10px !important;
}

/* BOTÓN */

.st-key-login_shell [data-testid="stFormSubmitButton"] button {
    min-height: 46px;
    border-radius: 10px;
    font-weight: 700;
    margin-top: .5rem;
}

/* EXPANDER */

.st-key-login_shell [data-testid="stExpander"] {
    margin-top: 1rem;
}

/* PIE */

.login-footer {
    text-align: center;
    font-size: .68rem;
    letter-spacing: .035em;
    opacity: .5;
    margin-top: 1.5rem;
    line-height: 1.5;
}

/* RESPONSIVE */

@media (max-width: 700px) {

    [data-testid="stMainBlockContainer"] {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .st-key-login_shell {
        margin-top: 2vh;
        padding: 1.5rem 1.2rem;
        border-radius: 15px;
    }

    .login-brand-mark {
        width: 58px;
        height: 58px;
        font-size: 25px;
    }

    .login-brand h1 {
        font-size: 1.45rem !important;
    }

    .login-brand p {
        font-size: .62rem;
    }

    .login-description {
        font-size: .82rem;
    }

    .st-key-global_assistant_float {
        right: .65rem !important;
        bottom: .65rem !important;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# PANTALLA DE LOGIN
# ============================================================

def pantalla_login():

    # Centrado horizontal
    espacio_izquierdo, centro, espacio_derecho = st.columns(
        [1, 1.2, 1]
    )

    with centro:

        # Una sola tarjeta para todo el contenido
        with st.container(
            key="login_shell",
            border=True,
        ):

            # ------------------------------------------------
            # IDENTIDAD DE LA PLATAFORMA
            # ------------------------------------------------

            st.markdown(
                """
<div class="login-brand">
    <div class="login-brand-mark">G</div>
    <h1>Gemelo Digital</h1>
    <p>PTAP / PTAR · CONTROL OPERACIONAL</p>
</div>

<div class="login-description">
    Plataforma inteligente de monitoreo,
    análisis predictivo y gestión de plantas
    de tratamiento de agua.
</div>
""",
                unsafe_allow_html=True,
            )

            # ------------------------------------------------
            # FORMULARIO
            # ------------------------------------------------

            with st.form("form_login"):

                email = st.text_input(
                    "Correo electrónico",
                    placeholder="usuario@empresa.com",
                )

                password = st.text_input(
                    "Contraseña",
                    type="password",
                    placeholder="Ingresa tu contraseña",
                )

                enviar = st.form_submit_button(
                    "Iniciar sesión",
                    use_container_width=True,
                    type="primary",
                )

            # ------------------------------------------------
            # VALIDACIÓN DE CREDENCIALES
            # ------------------------------------------------

            if enviar:

                usuario = auth.verificar_credenciales(
                    email.strip().lower(),
                    password,
                )

                if usuario:

                    st.session_state.usuario = usuario

                    registrar_evento(
                        usuario["email"],
                        "Inicio de sesión",
                        "Autenticación",
                        "Éxito",
                    )

                    st.rerun()

                else:

                    st.error(
                        "Credenciales inválidas o usuario inactivo."
                    )

                    registrar_evento(
                        email or "(vacío)",
                        "Intento de inicio de sesión",
                        "Autenticación",
                        "Fallido",
                    )

            # ------------------------------------------------
            # CREDENCIALES DE DEMOSTRACIÓN
            # ------------------------------------------------

            with st.expander("Credenciales de demostración"):

                st.markdown(
                    """
| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@demo.com` | `admin123` |
| Operador | `operador@demo.com` | `operador123` |

*Credenciales de prueba. Cámbialas antes de usar el sistema en un entorno real.*
"""
                )

            # ------------------------------------------------
            # PIE DE TARJETA
            # ------------------------------------------------

            st.markdown(
                """
<div class="login-footer">
    GEMELO DIGITAL · SISTEMA DE GESTIÓN Y MONITOREO
</div>
""",
                unsafe_allow_html=True,
            )


# ============================================================
# SESIÓN Y NAVEGACIÓN
# ============================================================

usuario_actual = auth.usuario_actual()

if usuario_actual is None:

    pantalla_login()

else:

    # --------------------------------------------------------
    # PÁGINAS GENERALES
    # --------------------------------------------------------

    paginas = [

        st.Page(
            "pages/1_Dashboard.py",
            title="Dashboard",
            icon=":material/dashboard:",
            default=True,
        ),

        st.Page(
            "pages/2_Monitoreo.py",
            title="Monitoreo",
            icon=":material/monitor_heart:",
        ),

        st.Page(
            "pages/3_Gemelo_Digital.py",
            title="Gemelo Digital",
            icon=":material/account_tree:",
        ),

        st.Page(
            "pages/4_Equipos.py",
            title="Equipos",
            icon=":material/precision_manufacturing:",
        ),

        st.Page(
            "pages/5_Alertas.py",
            title="Alertas",
            icon=":material/notifications_active:",
        ),

        st.Page(
            "pages/6_Predicciones.py",
            title="Predicciones",
            icon=":material/analytics:",
        ),

        st.Page(
            "pages/7_Dosificacion.py",
            title="Dosificación",
            icon=":material/science:",
        ),

        st.Page(
            "pages/8_Simulacion_WhatIf.py",
            title="Simulación What-If",
            icon=":material/tune:",
        ),

        st.Page(
            "pages/9_Reportes.py",
            title="Reportes",
            icon=":material/description:",
        ),

        st.Page(
            "pages/10_Asistente_IA.py",
            title="Asistente IA",
            icon=":material/smart_toy:",
        ),

    ]

    # --------------------------------------------------------
    # MÓDULOS EXCLUSIVOS DEL ADMINISTRADOR
    # --------------------------------------------------------

    if usuario_actual["rol"] == "administrador":

        paginas.extend([

            st.Page(
                "pages/12_Usuarios.py",
                title="Usuarios",
                icon=":material/group:",
            ),

            st.Page(
                "pages/13_Sensores.py",
                title="Sensores",
                icon=":material/sensors:",
            ),

            st.Page(
                "pages/14_Configuracion.py",
                title="Configuración",
                icon=":material/settings:",
            ),

            st.Page(
                "pages/15_Auditoria.py",
                title="Auditoría",
                icon=":material/history:",
            ),

        ])

    # --------------------------------------------------------
    # PERFIL
    # --------------------------------------------------------

    paginas.append(
        st.Page(
            "pages/11_Mi_Perfil.py",
            title="Mi Perfil",
            icon=":material/account_circle:",
        )
    )

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    with st.sidebar:

        st.markdown(
            """
<div class="gd-brand">
    <div class="gd-brand-mark">G</div>
    <div>
        <div class="gd-brand-name">Gemelo Digital</div>
        <div class="gd-brand-sub">
            PTAP / PTAR · CONTROL OPERACIONAL
        </div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"**{usuario_actual['nombre']}**"
        )

        st.caption(
            f"Rol: {usuario_actual['rol'].capitalize()}"
        )

        if st.button(
            "Cerrar sesión",
            icon=":material/logout:",
            use_container_width=True,
        ):

            auth.cerrar_sesion()
            st.rerun()

    # --------------------------------------------------------
    # EJECUCIÓN DE NAVEGACIÓN
    # --------------------------------------------------------

    st.navigation(paginas).run()
