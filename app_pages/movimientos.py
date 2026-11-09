"""Ingresos y egresos del mes, por concepto."""
import streamlit as st

import reports
import ui_html
from ui import MESES, load_data, meses_disponibles

config, diario = load_data()

meses = meses_disponibles(diario)
etiquetas = [f"{MESES[m - 1]} {a}" for a, m in meses]

# --- Encabezado -------------------------------------------------------------
col_titulo, col_mes = st.columns([3.2, 1.4], vertical_alignment="center")
with col_titulo:
    st.title("Movimientos del mes")
    st.caption("Lo que entró y salió, y qué pagos fijos siguen pendientes.")
with col_mes:
    elegida = st.selectbox("Mes", etiquetas, label_visibility="collapsed", key="movimientos_mes")
anio, mes = meses[etiquetas.index(elegida)]

vista = reports.ing_egr_mes(diario, anio, mes)
ingresos = vista["ingresos"]
egresos = vista["egresos"]


def _total(df, moneda: str) -> float:
    return float(df[moneda].sum()) if not df.empty else 0.0


# --- Resumen por moneda -----------------------------------------------------
col_ars, col_usd = st.columns(2)
with col_ars:
    st.html(ui_html.kpi_movimientos("ARS", "Pesos", _total(ingresos, "ARS"), _total(egresos, "ARS")))
with col_usd:
    st.html(ui_html.kpi_movimientos("USD", "Dólares", _total(ingresos, "USD"), _total(egresos, "USD")))

# --- Pagos y cobros fijos ---------------------------------------------------
col_ing_fijos, col_egr_fijos = st.columns(2)
with col_ing_fijos:
    conceptos = config.get("ingresos_fijos", [])
    filas = reports.conceptos_fijos_mes(diario, conceptos, "ingreso", anio, mes).to_dict("records") if conceptos else []
    st.html(ui_html.tarjeta_fijos("Ingresos fijos del mes", filas, "Cobrado", "Pendiente"))
with col_egr_fijos:
    conceptos = config.get("fijos", [])
    filas = reports.conceptos_fijos_mes(diario, conceptos, "egreso", anio, mes).to_dict("records") if conceptos else []
    st.html(ui_html.tarjeta_fijos("Gastos fijos del mes", filas, "Pagado", "Pendiente"))

# --- Por concepto -----------------------------------------------------------
col_ing, col_egr = st.columns(2)
with col_ing:
    st.html(ui_html.tarjeta_conceptos("Ingresos por concepto", ingresos.to_dict("records"), "ing"))
with col_egr:
    st.html(ui_html.tarjeta_conceptos("Egresos por concepto", egresos.to_dict("records"), "egr"))

# --- Evolución mensual ------------------------------------------------------
with st.container(border=True, key="card-evolucion"):
    st.html(ui_html.titulo_seccion("Evolución mensual", "Ingresos y egresos reales de cada mes"))
    flujo = reports.flujo_mensual(diario)
    if flujo.empty:
        st.caption("Todavía no hay datos suficientes.")
    else:
        for moneda, nombre in (("ARS", "Pesos"), ("USD", "Dólares")):
            sub = flujo[flujo["moneda"] == moneda]
            if sub.empty:
                continue
            st.caption(f"**{nombre}**")
            pivot = sub.pivot(index="periodo", columns="tipo", values="monto").fillna(0)
            colores = [c for c, tipo in zip(["#DC2626", "#16A34A"], ["egreso", "ingreso"]) if tipo in pivot.columns]
            st.bar_chart(pivot, color=colores)
