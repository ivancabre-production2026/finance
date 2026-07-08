"""
Finanzas personales — estado de cuenta, movimientos, diario y config.

Uso:
    cd finanzas-personales
    streamlit run app.py
"""
import streamlit as st

from auth import check_password

st.set_page_config(
    page_title="Finanzas personales",
    page_icon=":material/account_balance_wallet:",
    layout="wide",
)

if not check_password():
    st.stop()

page = st.navigation(
    [
        st.Page("app_pages/cuentas.py", title="Cuentas", icon=":material/account_balance_wallet:", default=True),
        st.Page("app_pages/movimientos.py", title="Movimientos", icon=":material/receipt_long:"),
        st.Page("app_pages/diario.py", title="Diario", icon=":material/edit_note:"),
        st.Page("app_pages/config.py", title="Config", icon=":material/settings:"),
    ],
    position="sidebar",
)

page.run()
