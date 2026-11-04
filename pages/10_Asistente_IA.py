import streamlit as st

from services import auth
from services.asistente_ia import responder
from services.auditoria import registrar_evento

auth.requerir_login()
usuario = auth.usuario_actual()

st.title("🤖 Asistente IA de la Planta")
st.caption(
    "Asistente basado en reglas que consulta la base de datos antes de responder. No inventa "
    "valores: indica cuándo un dato es real (simulado), una predicción, una simulación, o si "
    "no está disponible."
)

with st.expander("💡 Preguntas de ejemplo"):
    st.markdown(
        "- ¿Cuál es el estado actual de la planta?\n"
        "- ¿Qué equipos presentan riesgo?\n"
        "- ¿Por qué se generó esta alerta?\n"
        "- ¿Qué variables están fuera de rango?\n"
        "- ¿Cuál es la recomendación para la bomba P-01?\n"
        "- ¿Qué ocurrió durante las últimas 24 horas?"
    )

if "historial_chat" not in st.session_state:
    st.session_state.historial_chat = []

for rol, mensaje in st.session_state.historial_chat:
    with st.chat_message(rol):
        st.markdown(mensaje)

pregunta = st.chat_input("Escribe tu pregunta sobre la planta...")
if pregunta:
    st.session_state.historial_chat.append(("user", pregunta))
    respuesta = responder(pregunta)
    st.session_state.historial_chat.append(("assistant", respuesta))
    registrar_evento(usuario["email"], "Consultó al asistente IA", "Asistente IA", "Éxito", pregunta)
    st.rerun()
