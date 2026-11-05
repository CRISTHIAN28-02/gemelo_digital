import os
import streamlit as st

from services import auth
from services.auditoria import registrar_evento
from services.agente.orquestador import responder_agente
from services.voice_component import voice_component
from services.global_assistant import render_global_assistant


# La interfaz conserva el login y los permisos existentes.
auth.requerir_login()
usuario = auth.usuario_actual()
st.title("Agente inteligente | Gemelo Digital")
st.caption("Escribe o dicta una instrucción. También puedes escuchar las respuestas del agente.")

with st.expander("Ejemplos de instrucciones", expanded=False):
    st.markdown("""
    - Analiza el estado actual de la planta.
    - ¿Qué equipos tienen mayor riesgo?
    - Revisa el histórico del sensor DP-001.
    - Simula turbidez 100 NTU, caudal 120 L/s y saturación 65%.
    - Busca investigaciones sobre eliminación de metales pesados mediante nanomateriales.
    """)

if "agente_historial" not in st.session_state:
    st.session_state.agente_historial = []
if "voz_nonce_procesado" not in st.session_state:
    st.session_state.voz_nonce_procesado = None
if "agente_respuesta_id" not in st.session_state:
    st.session_state.agente_respuesta_id = 0
if "agente_ultima_respuesta" not in st.session_state:
    st.session_state.agente_ultima_respuesta = ""

# Componente: dictado con envío tras 5 s de silencio + lectura de respuestas.
dictado = voice_component(
    speak_text=st.session_state.agente_ultima_respuesta,
    speak_id=st.session_state.agente_respuesta_id,
    key="agente_voice_component",
    default=None,
)

for item in st.session_state.agente_historial:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

col_voice, col_help = st.columns([1, 3])
with col_voice:
    st.caption("Usa el botón de micrófono del componente para dictar.")
with col_help:
    st.caption("El dictado se envía automáticamente después de 5 segundos sin nuevas palabras. La lectura utiliza la voz disponible en tu navegador.")

pregunta_texto = st.chat_input("Escribe una instrucción para el agente…")
pregunta_voz = None
if isinstance(dictado, dict) and dictado.get("text"):
    nonce = dictado.get("nonce")
    if nonce != st.session_state.voz_nonce_procesado:
        pregunta_voz = str(dictado["text"]).strip()
        st.session_state.voz_nonce_procesado = nonce

pregunta = pregunta_texto or pregunta_voz
if pregunta:
    st.session_state.agente_historial.append({"role": "user", "content": pregunta})
    try:
        with st.spinner("Analizando tu instrucción…"):
            respuesta = responder_agente(st.session_state.agente_historial)
        st.session_state.agente_historial.append({"role": "assistant", "content": respuesta})
        st.session_state.agente_ultima_respuesta = respuesta
        st.session_state.agente_respuesta_id += 1
        registrar_evento(usuario["email"], "Consultó al agente inteligente", "Agente IA", "Éxito", pregunta[:500])
    except Exception as exc:
        mensaje_error = f"No pude completar la solicitud: {exc}"
        st.session_state.agente_historial.append({"role": "assistant", "content": mensaje_error})
        st.session_state.agente_ultima_respuesta = mensaje_error
        st.session_state.agente_respuesta_id += 1
        registrar_evento(usuario["email"], "Error al consultar agente inteligente", "Agente IA", "Fallido", str(exc)[:500])
    st.rerun()

with st.sidebar:
    st.subheader("Agente inteligente")
    try:
        tiene_key = bool(os.getenv("DEEPSEEK_API_KEY", "").strip() or st.secrets.get("DEEPSEEK_API_KEY", "").strip())
    except Exception:
        tiene_key = bool(os.getenv("DEEPSEEK_API_KEY", "").strip())
    st.success("DeepSeek configurado") if tiene_key else st.warning("Falta configurar la API key")
    st.caption("Las consultas a DeepSeek consumen saldo. La voz se procesa mediante las funciones del navegador.")
    st.caption("Los datos de la planta de este MVP son simulados; predicciones y dosis son demostrativas.")
    if st.button("Detener lectura", use_container_width=True):
        st.session_state.agente_respuesta_id += 1
        st.session_state.agente_ultima_respuesta = ""
        st.rerun()
    if st.button("Limpiar conversación", use_container_width=True):
        st.session_state.agente_historial = []
        st.session_state.voz_nonce_procesado = None
        st.session_state.agente_ultima_respuesta = ""
        st.session_state.agente_respuesta_id += 1
        st.rerun()

# Asistente rápido global, disponible también en este módulo.
render_global_assistant("Asistente IA")
