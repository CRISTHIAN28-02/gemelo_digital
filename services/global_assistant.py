"""Asistente flotante disponible en todas las páginas autenticadas."""
import streamlit as st
from services.agente.orquestador import responder_agente
from services.voice_component import voice_component
from services.auditoria import registrar_evento
from services import auth


def render_global_assistant(contexto_pagina="la plataforma"):
    """Renderiza el asistente rápido global. No sustituye al asistente completo."""
    usuario = auth.usuario_actual()
    if not usuario:
        return
    st.markdown("""
    <style>
    .st-key-global_assistant_float{position:fixed!important;right:clamp(1rem,2.2vw,2rem)!important;bottom:1.1rem!important;z-index:99999!important;width:auto!important;max-width:min(94vw,390px)!important}
    .st-key-global_assistant_float [data-testid="stPopover"]>button{border-radius:999px!important;min-height:3.15rem!important;padding:.55rem 1.05rem!important;box-shadow:0 8px 28px rgba(20,50,80,.22)!important;font-weight:650!important}
    .st-key-global_assistant_float [data-testid="stPopoverBody"]{width:min(92vw,390px)!important;max-height:min(72vh,650px)!important;overflow-y:auto!important;border:1px solid var(--border-color,rgba(128,128,128,.25))!important;border-radius:16px!important;box-shadow:0 12px 40px rgba(0,0,0,.18)!important}
    .global-assistant-note{color:var(--text-color);opacity:.72;font-size:.78rem;margin-top:-.35rem}
    </style>""",unsafe_allow_html=True)
    defaults={"global_ai_history":[],"global_ai_voice_nonce":None,"global_ai_speak_id":0,"global_ai_speak_text":""}
    for key,value in defaults.items():
        if key not in st.session_state: st.session_state[key]=value
    with st.container(key="global_assistant_float"):
        with st.popover("Asistente",icon=":material/smart_toy:",use_container_width=False):
            st.markdown("#### Asistente rápido")
            st.caption(f"Consultas breves · Módulo: {contexto_pagina}")
            dictado=voice_component(speak_text=st.session_state.global_ai_speak_text,speak_id=st.session_state.global_ai_speak_id,key="global_assistant_voice_component",default=None)
            for item in st.session_state.global_ai_history[-4:]:
                with st.chat_message(item["role"],avatar=":material/person:" if item["role"]=="user" else ":material/smart_toy:"):
                    st.markdown(item["content"])
            pregunta_voz=None
            if isinstance(dictado,dict) and dictado.get("text"):
                nonce=dictado.get("nonce")
                if nonce!=st.session_state.global_ai_voice_nonce:
                    pregunta_voz=str(dictado["text"]).strip(); st.session_state.global_ai_voice_nonce=nonce
            with st.form("global_assistant_form",clear_on_submit=True):
                pregunta_texto=st.text_input("Consulta",placeholder="Escribe una consulta breve...",label_visibility="collapsed")
                enviar=st.form_submit_button("Enviar",use_container_width=True)
            pregunta=(pregunta_texto or "").strip() if enviar else (pregunta_voz or "")
            if pregunta:
                st.session_state.global_ai_history.append({"role":"user","content":pregunta})
                try:
                    with st.spinner("Consultando..."):
                        respuesta=responder_agente(st.session_state.global_ai_history,modo="rapido",contexto_pagina=contexto_pagina)
                    st.session_state.global_ai_history.append({"role":"assistant","content":respuesta})
                    st.session_state.global_ai_speak_text=respuesta; st.session_state.global_ai_speak_id+=1
                    registrar_evento(usuario["email"],"Consultó al asistente rápido","Asistente global","Éxito",pregunta[:500])
                except Exception as exc:
                    respuesta=f"No pude completar la consulta: {str(exc)[:240]}"
                    st.session_state.global_ai_history.append({"role":"assistant","content":respuesta})
                    st.session_state.global_ai_speak_text=respuesta; st.session_state.global_ai_speak_id+=1
                    registrar_evento(usuario["email"],"Error al consultar asistente rápido","Asistente global","Fallido",str(exc)[:500])
                st.rerun()
            st.markdown('<div class="global-assistant-note">Dicta con el micrófono. El envío ocurre tras 5 segundos de silencio. Las respuestas se leen automáticamente en el navegador.</div>',unsafe_allow_html=True)
            ca,cb=st.columns(2)
            with ca:
                if st.button("Detener voz",key="global_ai_stop_voice",use_container_width=True):
                    st.session_state.global_ai_speak_id+=1; st.session_state.global_ai_speak_text=""; st.rerun()
            with cb:
                if st.button("Limpiar",key="global_ai_clear",use_container_width=True):
                    st.session_state.global_ai_history=[]; st.session_state.global_ai_speak_id+=1; st.session_state.global_ai_speak_text=""; st.session_state.global_ai_voice_nonce=None; st.rerun()
