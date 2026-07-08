"""Ingresos y egresos del mes, por concepto."""
import datetime as dt

import streamlit as st

import reports
from ui import MESES, fmt, fmt_df, load_data

st.title("Movimientos del mes")

config, diario = load_data()

hoy = dt.date.today()
with st.container(horizontal=True):
    anio = st.selectbox("Año", list(range(hoy.year - 2, hoy.year + 1)), index=2)
    mes = st.selectbox("Mes", list(range(1, 13)), index=hoy.month - 1, format_func=lambda m: MESES[m - 1])

st.caption(f"{MESES[mes - 1]} {anio}")

vista = reports.ing_egr_mes(diario, anio, mes)
ingresos = vista["ingresos"]
egresos = vista["egresos"]

total_ing_ars = ingresos["ARS"].sum() if not ingresos.empty else 0.0
total_ing_usd = ingresos["USD"].sum() if not ingresos.empty else 0.0
total_egr_ars = egresos["ARS"].sum() if not egresos.empty else 0.0
total_egr_usd = egresos["USD"].sum() if not egresos.empty else 0.0

with st.container(horizontal=True):
    st.metric("Ingresos ARS", f"$ {fmt(total_ing_ars)}", border=True)
    st.metric("Ingresos USD", f"US$ {fmt(total_ing_usd)}", border=True)
    st.metric("Egresos ARS", f"$ {fmt(total_egr_ars)}", border=True)
    st.metric("Egresos USD", f"US$ {fmt(total_egr_usd)}", border=True)

def _color_estado(row):
    if row["pagado"]:
        estilo = "background-color: #0F2E23; color: #6EE7B7"
    else:
        estilo = "background-color: #3A1518; color: #FCA5A5"
    return [estilo] * len(row)


def _tarjeta_pendientes(titulo: str, conceptos: list, tipo: str, verbo: str):
    with st.container(border=True):
        st.markdown(f"**:material/notifications_active: {titulo}**")
        if not conceptos:
            st.caption("No configuraste ninguno todavía (se hace desde Config).")
            return
        df = reports.conceptos_fijos_mes(diario, conceptos, tipo, anio, mes)
        pendientes = df.loc[~df["pagado"], "concepto"].tolist()
        if pendientes:
            st.warning(f"{len(pendientes)} sin {verbo}: {', '.join(pendientes)}", icon=":material/warning:")
        else:
            st.success(f"Todos están al día este mes.", icon=":material/check_circle:")

        tabla = df.copy()
        tabla["Estado"] = tabla["pagado"].map({True: "OK", False: "Pendiente"})
        tabla["ARS"] = tabla["ARS"].apply(fmt)
        tabla["USD"] = tabla["USD"].apply(fmt)
        tabla = tabla.rename(columns={"concepto": "Concepto"})[["Concepto", "ARS", "USD", "Estado", "pagado"]]
        styled = tabla.style.apply(_color_estado, axis=1)
        st.dataframe(styled, column_config={"pagado": None}, hide_index=True, width="stretch")


col_ing_fijos, col_egr_fijos = st.columns(2)
with col_ing_fijos:
    _tarjeta_pendientes("Ingresos fijos del mes", config.get("ingresos_fijos", []), "ingreso", "cobrar")
with col_egr_fijos:
    _tarjeta_pendientes("Gastos fijos del mes", config.get("fijos", []), "egreso", "pagar")


def _seccion(titulo: str, icono: str, df, color: str):
    with st.container(border=True):
        st.markdown(f"**:material/{icono}: {titulo}**")
        if df.empty:
            st.caption(f"Sin {titulo.lower()} este mes.")
            return
        col_tabla, col_grafico = st.columns([1, 1])
        with col_tabla:
            tabla = fmt_df(df, ["ARS", "USD"]).rename(columns={"concepto": "Concepto"})
            st.dataframe(tabla, hide_index=True, width="stretch")
        with col_grafico:
            ars_df = df[df["ARS"] != 0].sort_values("ARS", ascending=False)
            if not ars_df.empty:
                st.bar_chart(ars_df.set_index("concepto")["ARS"], horizontal=True, color=color)
            else:
                st.caption("Sin montos en pesos para graficar.")


_seccion("Ingresos por concepto", "trending_up", ingresos, "#34D399")
_seccion("Egresos por concepto", "trending_down", egresos, "#F87171")

with st.container(border=True):
    st.markdown("**:material/insights: Evolución mensual**")
    flujo = reports.flujo_mensual(diario)
    if flujo.empty:
        st.caption("Todavía no hay datos suficientes.")
    else:
        for moneda in ("ARS", "USD"):
            sub = flujo[flujo["moneda"] == moneda]
            if sub.empty:
                continue
            st.caption(f"En {moneda}")
            pivot = sub.pivot(index="periodo", columns="tipo", values="monto").fillna(0)
            colores = [c for c, tipo in zip(["#F87171", "#34D399"], ["egreso", "ingreso"]) if tipo in pivot.columns]
            st.bar_chart(pivot, color=colores)
