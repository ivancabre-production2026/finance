"""Gate por contraseña. Si no hay APP_PASSWORD configurada (uso local), no pide nada."""
import streamlit as st


def check_password() -> bool:
    try:
        app_password = st.secrets.get("APP_PASSWORD")
    except Exception:
        app_password = None
    if not app_password:
        return True  # local: sin contraseña configurada, no se pide login

    if st.session_state.get("authenticated"):
        return True

    def _validar():
        if st.session_state.get("password_input") == app_password:
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False

    st.title("🔒 Finanzas personales")
    st.text_input("Contraseña", type="password", on_change=_validar, key="password_input")
    if st.session_state.get("authenticated") is False:
        st.error("Contraseña incorrecta.", icon=":material/error:")
    return False
