"""Diezmo: cuánto corresponde cada mes, cuánto se debe y los pagos hechos."""
import streamlit as st

import config_store
import diezmo_calc
import ui_html
from ui import fmt_money, load_data

config, diario = load_data()
cfg = config["diezmo"]
est = diezmo_calc.estado(diario, cfg)

st.title("Diezmo")
st.caption(
    f"El {cfg['porcentaje']:g}% de los ingresos de cada mes, llevados a pesos al tipo de cambio de fin de mes."
)

# --- Resumen ------------------------------------------------------------------
c1, c2, c3 = st.columns(3)
with c1:
    st.html(ui_html.kpi_diezmo(
        "Deuda de diezmo", fmt_money(max(est["deuda"], 0.0), "ARS"),
        "Al día" if est["deuda"] <= 0.5 else "Meses cerrados pendientes de pago",
        negativo=est["deuda"] > 0.5,
    ))
with c2:
    f = est["en_curso"]
    st.html(ui_html.kpi_diezmo(
        f"{ui_html._nombre_mes(f['periodo'])} (en curso)" if f else "Mes en curso",
        fmt_money(f["diezmo"], "ARS") if f else "—",
        "Estimado: se suma a la deuda cuando cierre el mes", icono="hourglass_top", clase="ars",
    ))
with c3:
    st.html(ui_html.kpi_diezmo(
        "Pagado desde el 17/11", fmt_money(est["pagado_total"], "ARS"),
        f"{len(est['pagos'])} pago(s) con concepto Diezmo", icono="check_circle",
    ))

# --- Detalle por mes ----------------------------------------------------------
with st.container(key="card-diezmo-detalle"):
    st.html(ui_html.titulo_seccion("Detalle por mes", "Los pagos se aplican primero al mes más viejo."))
    st.html(ui_html.tabla_diezmo(est["filas"]))
    st.caption(
        "Confirmado = monto que cargaste a mano (julio a octubre). Estimado/Calculado = "
        "porcentaje × (ingresos en pesos + ingresos en USD × tipo de cambio). Manual = lo corregiste vos."
    )

# --- Pagos --------------------------------------------------------------------
with st.container(key="card-diezmo-pagos"):
    st.html(ui_html.titulo_seccion("Pagos de diezmo", "Cargalos en Diario con concepto Diezmo (egreso)."))
    if est["pagos"]:
        st.html(ui_html.tabla_pagos_diezmo(est["pagos"]))
    else:
        st.caption("Todavía no hay pagos desde el corte. Cuando pagues una parte, cargala en Diario y se descuenta sola.")
    st.page_link("app_pages/diario.py", label="Ir a Diario", icon=":material/arrow_forward:")

# --- Ajustes del cálculo ------------------------------------------------------
with st.container(key="card-diezmo-ajustes"):
    st.html(ui_html.titulo_seccion(
        "Ajustar el cálculo",
        "Corregí el tipo de cambio o el monto de un mes. Dejá en 0 para volver al valor automático.",
    ))
    periodos = [f["periodo"] for f in est["filas"]]
    with st.form("diezmo_ajustes", border=False):
        a, b, c = st.columns(3)
        periodo = a.selectbox("Mes", periodos, index=len(periodos) - 1, format_func=ui_html._nombre_mes)
        fila = next(f for f in est["filas"] if f["periodo"] == periodo)
        tc_nuevo = b.number_input(
            "Tipo de cambio de fin de mes ($ por US$)", min_value=0.0, step=1.0, format="%.2f",
            value=float(cfg["tc"].get(periodo, 0.0)),
            help=f"Automático: {fmt_money(fila['tc'], 'ARS') if fila['tc'] else 'sin dato'}",
        )
        manual_nuevo = c.number_input(
            "Diezmo del mes, a mano ($)", min_value=0.0, step=1000.0, format="%.2f",
            value=float(cfg["manual"].get(periodo, 0.0)),
            help="Si lo cargás, reemplaza el cálculo de ese mes.",
        )
        d, e = st.columns(2)
        pct = d.number_input("Porcentaje", min_value=0.0, max_value=100.0, step=0.5, value=float(cfg["porcentaje"]))
        conceptos = e.multiselect("Ingresos que cuentan", config["ingresos"], default=[c for c in cfg["conceptos"] if c in config["ingresos"]])
        if st.form_submit_button("Guardar ajustes", type="primary", icon=":material/save:"):
            if tc_nuevo > 0:
                cfg["tc"][periodo] = tc_nuevo
            else:
                cfg["tc"].pop(periodo, None)
            if manual_nuevo > 0:
                cfg["manual"][periodo] = manual_nuevo
            else:
                cfg["manual"].pop(periodo, None)
            cfg["porcentaje"] = pct
            cfg["conceptos"] = conceptos
            config_store.save(config)
            st.toast("Ajustes del diezmo guardados", icon=":material/check_circle:")
            st.rerun()
