"""Sube tus datos locales (data/config.json y data/diario.json) a la base Postgres
configurada en .streamlit/secrets.toml. Corré esto UNA sola vez, después de crear
tu base en Neon y antes de desplegar en Streamlit Community Cloud.

Uso:
    cd finanzas-personales
    streamlit run migrate_to_db.py
"""
import json
from pathlib import Path

import streamlit as st

import db

st.title("Migración a Postgres")

if not db.is_configured():
    st.error(
        "No encontré una conexión 'postgres' en .streamlit/secrets.toml. "
        "Agregala primero (ver .streamlit/secrets.toml.example) y volvé a correr esto.",
        icon=":material/error:",
    )
    st.stop()

config_path = Path(__file__).parent / "data" / "config.json"
diario_path = Path(__file__).parent / "data" / "diario.json"

if not config_path.exists() or not diario_path.exists():
    st.error("No encontré data/config.json o data/diario.json en esta carpeta.", icon=":material/error:")
    st.stop()

config = json.loads(config_path.read_text(encoding="utf-8"))
diario = json.loads(diario_path.read_text(encoding="utf-8"))

st.write(f"Config: {len(config.get('cuentas', []))} cuentas, {len(config.get('egresos', []))} conceptos de egreso.")
st.write(f"Diario: {len(diario)} movimientos.")

if st.button("Subir a Postgres", type="primary", icon=":material/cloud_upload:"):
    db.save("config", config)
    db.save("diario", diario)
    st.success("Listo. Tu base en la nube ya tiene tus datos reales.", icon=":material/check_circle:")
