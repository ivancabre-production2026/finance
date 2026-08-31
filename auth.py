"""Gate por contraseña. Si no hay APP_PASSWORD configurada (uso local), no pide nada.

Ademas de session_state (que se pierde en cada F5, porque un refresh completo abre una
sesion de navegador nueva), guarda una cookie en el browser para no tener que volver a
tipear la contrasena en cada recarga. La cookie no guarda la contrasena en texto plano,
sino un hash de la misma.
"""
import hashlib

import streamlit as st

_COOKIE_NAME = "finanzas_auth"
_COOKIE_DIAS = 90


def _token(app_password: str) -> str:
    return hashlib.sha256(f"finanzas-personales:{app_password}".encode()).hexdigest()


def _setear_cookie(token: str) -> None:
    st.html(
        f"""<script>
        document.cookie = "{_COOKIE_NAME}={token}; max-age={_COOKIE_DIAS * 86400}; path=/; SameSite=Lax";
        </script>""",
        unsafe_allow_javascript=True,
    )


def check_password() -> bool:
    try:
        app_password = st.secrets.get("APP_PASSWORD")
    except Exception:
        app_password = None
    if not app_password:
        return True  # local: sin contraseña configurada, no se pide login

    token_esperado = _token(app_password)

    # Si nos acabamos de autenticar (rerun disparado por el on_change de abajo), seteamos
    # la cookie ahora, antes de cortar camino, para que quede guardada para el proximo F5.
    if st.session_state.pop("_recien_autenticado", False):
        _setear_cookie(token_esperado)

    if st.session_state.get("authenticated"):
        return True

    # Cookie de una sesion anterior (sobrevive un F5, a diferencia de session_state).
    if st.context.cookies.get(_COOKIE_NAME) == token_esperado:
        st.session_state["authenticated"] = True
        return True

    def _validar():
        if st.session_state.get("password_input") == app_password:
            st.session_state["authenticated"] = True
            st.session_state["_recien_autenticado"] = True
        else:
            st.session_state["authenticated"] = False

    st.title("🔒 Finanzas personales")
    st.text_input("Contraseña", type="password", on_change=_validar, key="password_input")
    if st.session_state.get("authenticated") is False:
        st.error("Contraseña incorrecta.", icon=":material/error:")
    return False
