"""
Finanzas personales — estado de cuenta, movimientos, diario y config.

Uso:
    cd finanzas-personales
    streamlit run app.py
"""
from pathlib import Path

import streamlit as st

from auth import check_password

st.set_page_config(
    page_title="Finanzas personales",
    page_icon=":material/account_balance_wallet:",
    layout="wide",
)

st.html(Path(__file__).parent / "assets" / "style.css")  # estilos propios (tarjetas, tabla, barras, login)

if not check_password():
    st.stop()

st.logo("assets/logo.svg", size="large", icon_image="assets/logo_icon.svg")

page = st.navigation(
    [
        st.Page("app_pages/cuentas.py", title="Resumen", icon=":material/home:", default=True),
        st.Page("app_pages/movimientos.py", title="Movimientos", icon=":material/swap_horiz:"),
        st.Page("app_pages/diario.py", title="Diario", icon=":material/edit_calendar:"),
        st.Page("app_pages/asistente.py", title="Asistente", icon=":material/auto_awesome:"),
        st.Page("app_pages/config.py", title="Configuración", icon=":material/settings:"),
    ],
    position="sidebar",
)

page.run()
