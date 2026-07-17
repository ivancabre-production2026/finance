"""Configuración: conceptos y cuentas disponibles en el Diario."""
import streamlit as st

import config_store
from ui import load_data

st.title("Configuración")
st.caption("Conceptos y cuentas disponibles en el Diario")

config, _ = load_data()

c1, c2, c3 = st.columns(3)
with c1:
    with st.container(border=True):
        st.markdown("**:material/trending_up: Cuentas de ingreso**")
        ingresos_txt = st.text_area(
            "Cuentas de ingreso", "\n".join(config["ingresos"]), height=320,
            key="ingresos", label_visibility="collapsed",
        )
with c2:
    with st.container(border=True):
        st.markdown("**:material/trending_down: Cuentas de egreso**")
        egresos_txt = st.text_area(
            "Cuentas de egreso", "\n".join(config["egresos"]), height=320,
            key="egresos", label_visibility="collapsed",
        )
with c3:
    with st.container(border=True):
        st.markdown("**:material/account_balance: Cuentas banco/billeteras**")
        cuentas_txt = st.text_area(
            "Cuentas banco/billeteras", "\n".join(config["cuentas"]), height=320,
            key="cuentas", label_visibility="collapsed",
        )

c4, c5 = st.columns(2)
with c4:
    with st.container(border=True):
        st.markdown("**:material/notifications_active: Ingresos fijos / esperados**")
        st.caption("La app marca en rojo a los que todavía no cobraste este mes (ej: si Pretzel no pagó).")
        ingresos_fijos_seleccionados = st.multiselect(
            "Ingresos fijos", config["ingresos"],
            default=[f for f in config.get("ingresos_fijos", []) if f in config["ingresos"]],
            key="ingresos_fijos", label_visibility="collapsed",
        )
with c5:
    with st.container(border=True):
        st.markdown("**:material/notifications_active: Gastos fijos / recurrentes**")
        st.caption("La app marca en rojo a los que todavía no pagaste este mes.")
        fijos_seleccionados = st.multiselect(
            "Gastos fijos", config["egresos"], default=[f for f in config.get("fijos", []) if f in config["egresos"]],
            key="fijos", label_visibility="collapsed",
        )

with st.container(border=True):
    st.markdown("**:material/savings: Cuentas de inversión**")
    st.caption("En Cuentas, separan tu patrimonio en \"Disponible\" vs \"Invertido\" por moneda.")
    cuentas_inversion_seleccionadas = st.multiselect(
        "Cuentas de inversión", config["cuentas"],
        default=[c for c in config.get("cuentas_inversion", []) if c in config["cuentas"]],
        key="cuentas_inversion", label_visibility="collapsed",
    )

if st.button("Guardar config", type="primary", icon=":material/save:"):
    ingresos_lista = [l.strip() for l in ingresos_txt.splitlines() if l.strip()]
    egresos_lista = [l.strip() for l in egresos_txt.splitlines() if l.strip()]
    cuentas_lista = [l.strip() for l in cuentas_txt.splitlines() if l.strip()]
    nuevo_config = {
        "ingresos": ingresos_lista,
        "egresos": egresos_lista,
        "cuentas": cuentas_lista,
        "fijos": [f for f in fijos_seleccionados if f in egresos_lista],
        "ingresos_fijos": [f for f in ingresos_fijos_seleccionados if f in ingresos_lista],
        "cuentas_inversion": [c for c in cuentas_inversion_seleccionadas if c in cuentas_lista],
    }
    config_store.save(nuevo_config)
    st.toast("Config guardada", icon=":material/check_circle:")
    st.rerun()
