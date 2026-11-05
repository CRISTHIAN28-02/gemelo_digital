"""Orquestador DeepSeek con tool-calling y límites de consumo."""
import json
import os
import requests
import streamlit as st
from services.agente.herramientas import TOOL_DEFINITIONS, FUNCTIONS

SYSTEM_PROMPT = """Eres el agente inteligente de apoyo a la operación de una planta PTAP/PTAR.
Responde siempre en español, con claridad y sin inventar datos. Cuando la pregunta requiera datos de planta,
usa las herramientas disponibles. Distingue explícitamente: medición simulada, predicción demostrativa,
simulación matemática y fuente bibliográfica. No presentes datos simulados como datos reales de una planta.
Nunca inventes mediciones, alertas, equipos, artículos, DOI ni resultados. Para investigación, usa buscar_literatura
y aclara que OpenAlex devuelve metadatos, no necesariamente texto completo. Si una herramienta falla, dilo.
Las dosis son estimaciones de un modelo demostrativo y requieren pruebas de jarras y validación profesional.
No puedes ejecutar acciones físicas, cambiar estados ni modificar registros. Las simulaciones no se guardan.
Si la petición es ambigua, pregunta lo mínimo necesario. Cita título, año y DOI cuando estén disponibles."""

SYSTEM_PROMPT_RAPIDO = SYSTEM_PROMPT + """

MODO DE RESPUESTA RÁPIDA:
- Responde en 1 a 4 frases, idealmente menos de 70 palabras.
- Da primero el resultado o dato principal y después, solo si hace falta, una recomendación breve.
- Evita introducciones, saludos, explicaciones largas, listas extensas y repetir la pregunta.
- Si falta información, formula una sola pregunta concreta.
- No ocultes advertencias de seguridad ni la naturaleza simulada/demostrativa de los datos.
- Si la consulta requiere un análisis profundo, ofrece continuarlo en el apartado Asistente IA.
"""

def _api_key():
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    try:
        key = key or str(st.secrets.get("DEEPSEEK_API_KEY", "")).strip()
    except Exception:
        pass
    return key


def responder_agente(mensajes, max_tool_calls=4, modo="completo", contexto_pagina=None):
    key = _api_key()
    if not key:
        raise RuntimeError("Falta configurar DEEPSEEK_API_KEY en .streamlit/secrets.toml o como variable de entorno.")
    prompt = SYSTEM_PROMPT_RAPIDO if modo == "rapido" else SYSTEM_PROMPT
    if contexto_pagina:
        prompt += f"\n\nCONTEXTO DE INTERFAZ: el usuario está en el módulo {contexto_pagina}. Úsalo para interpretar referencias como 'aquí' o 'este módulo', pero no supongas datos que no se hayan consultado."
    base = [{"role": "system", "content": prompt}]
    base.extend(mensajes[-8:] if modo == "rapido" else mensajes[-10:])
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    url = "https://api.deepseek.com/chat/completions"
    for _ in range(max_tool_calls + 1):
        payload = {"model": "deepseek-flash", "messages": base, "tools": TOOL_DEFINITIONS,
                   "tool_choice": "auto", "temperature": 0.2, "max_tokens": 320 if modo == "rapido" else 1200}
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code >= 400:
            try:
                detail = response.json().get("error", {}).get("message", response.text)
            except Exception:
                detail = response.text
            raise RuntimeError(f"DeepSeek respondió {response.status_code}: {detail[:500]}")
        data = response.json()
        choice = data["choices"][0]["message"]
        base.append(choice)
        calls = choice.get("tool_calls") or []
        if not calls:
            return choice.get("content") or "No se obtuvo una respuesta de texto."
        for call in calls:
            name = call["function"]["name"]
            if name not in FUNCTIONS:
                result = {"error": "Herramienta no permitida."}
            else:
                try:
                    args = json.loads(call["function"].get("arguments") or "{}")
                    result = FUNCTIONS[name](**args)
                except Exception as exc:
                    result = {"error": f"No se pudo ejecutar {name}: {str(exc)[:300]}"}
            base.append({"role": "tool", "tool_call_id": call["id"],
                         "content": json.dumps(result, ensure_ascii=False, default=str)[:12000]})
    raise RuntimeError("Se alcanzó el límite de herramientas por consulta. Prueba dividiendo la solicitud.")
