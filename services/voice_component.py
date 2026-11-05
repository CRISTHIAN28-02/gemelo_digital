from pathlib import Path
import streamlit.components.v1 as components

_COMPONENT_DIR = Path(__file__).resolve().parents[1] / "components" / "voice_input"
if not _COMPONENT_DIR.is_dir():
    raise FileNotFoundError(f"No se encontró el componente de voz: {_COMPONENT_DIR}")

voice_component = components.declare_component(
    "gemelo_voice_input",
    path=str(_COMPONENT_DIR),
)
