import streamlit as st

from database import db
from services import auth

auth.requerir_rol(["administrador"])

st.title("🗂️ Auditoría del Sistema")

col1, col2 = st.columns(2)
usuario_f = col1.text_input("Filtrar por usuario (correo)")
modulo_f = col2.text_input("Filtrar por módulo")

query = "SELECT fecha, usuario, accion, modulo, descripcion, resultado FROM auditoria WHERE 1=1"
params = []
if usuario_f:
    query += " AND usuario LIKE ?"
    params.append(f"%{usuario_f}%")
if modulo_f:
    query += " AND modulo LIKE ?"
    params.append(f"%{modulo_f}%")
query += " ORDER BY fecha DESC LIMIT 300"

df = db.fetch_df(query, tuple(params))
st.dataframe(df, use_container_width=True, hide_index=True)
st.download_button("⬇️ Descargar CSV", df.to_csv(index=False).encode("utf-8"), "auditoria.csv", "text/csv")
