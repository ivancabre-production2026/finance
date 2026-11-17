"""Ingresos y egresos del mes, por concepto."""
import altair as alt
import pandas as pd
import streamlit as st

import reports
import ui_html
from ui import MESES, fmt_money, load_data, meses_disponibles

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

# --- Ingresos y distribución de gastos --------------------------------------
PALETA = ["#0B5D3B", "#2FA66B", "#7CC8A0", "#2563EB", "#F59E0B", "#E5605A", "#7C3AED", "#0891B2"]
GRIS_OTROS = "#94A3B8"
CAMBIOS = "Cambio USD a ARS"
col_ing, col_gastos = st.columns([1, 1.7])
with col_ing:
    st.html(ui_html.tarjeta_conceptos("Ingresos por concepto", ingresos.to_dict("records"), "ing"))

with col_gastos:
    with st.container(key="card-dist-gastos"):
        st.html(ui_html.titulo_seccion("¿En qué se va el gasto?", f"Distribución porcentual de los egresos de {elegida.lower()}"))
        c_moneda, c_cambios = st.columns([1, 1.4], vertical_alignment="center")
        with c_moneda:
            nombre_moneda = st.segmented_control("Moneda", ["Pesos", "Dólares"], default="Pesos", key="dist_moneda", label_visibility="collapsed") or "Pesos"
        with c_cambios:
            incluir_cambios = st.toggle("Incluir cambios USD→ARS", value=False, key="dist_cambios",
                                        help="Los cambios a pesos no son un gasto: la plata se gasta después, en pesos. Por eso empiezan apagados.")
        moneda = "ARS" if nombre_moneda == "Pesos" else "USD"

        datos = egresos[["concepto", moneda]].rename(columns={moneda: "monto"}) if not egresos.empty else pd.DataFrame(columns=["concepto", "monto"])
        datos = datos[datos["monto"] > 0]
        if not incluir_cambios:
            datos = datos[datos["concepto"] != CAMBIOS]
        datos = datos.sort_values("monto", ascending=False)
        total_gasto = float(datos["monto"].sum())

        if datos.empty or total_gasto <= 0:
            st.caption("Sin gastos en este mes para esa moneda.")
        else:
            top = datos.head(7)
            resto = datos.iloc[7:]
            filas = [(r.concepto, float(r.monto)) for r in top.itertuples()]
            if not resto.empty:
                filas.append((f"Otros ({len(resto)})", float(resto["monto"].sum())))
            items = []
            for i, (concepto, monto) in enumerate(filas):
                color = GRIS_OTROS if concepto.startswith("Otros (") else PALETA[i % len(PALETA)]
                items.append((concepto, monto, monto / total_gasto * 100, color))

            df_torta = pd.DataFrame(
                [{"Concepto": c, "Monto": m, "Porcentaje": f"{p:.1f}%", "Importe": fmt_money(m, moneda)} for c, m, p, _ in items]
            )
            escala = alt.Scale(domain=[i[0] for i in items], range=[i[3] for i in items])
            torta = (
                alt.Chart(df_torta)
                .mark_arc(innerRadius=62, outerRadius=118, cornerRadius=4, stroke="#FFFFFF", strokeWidth=2)
                .encode(
                    theta=alt.Theta("Monto:Q", stack=True),
                    color=alt.Color("Concepto:N", scale=escala, legend=None),
                    tooltip=["Concepto", "Importe", "Porcentaje"],
                )
            )
            centro = (
                alt.Chart(pd.DataFrame({"t": [fmt_money(total_gasto, moneda)], "s": ["total"]}))
                .mark_text(fontSize=15, fontWeight="bold", dy=-2)
                .encode(text="t:N")
            )
            c_torta, c_lista = st.columns([0.9, 1.35], vertical_alignment="center")
            with c_torta:
                st.altair_chart((torta + centro).properties(height=250).configure(background="#FFFFFF").configure_view(strokeWidth=0), width="stretch")
            with c_lista:
                st.html(ui_html.lista_distribucion(items, moneda))

# --- Evolución mensual ------------------------------------------------------
with st.container(key="card-evolucion"):
    st.html(ui_html.titulo_seccion("Evolución mensual", "Ingresos y egresos reales de cada mes, lado a lado"))
    c_m, c_c = st.columns([1, 1.4], vertical_alignment="center")
    with c_m:
        nombre_ev = st.segmented_control("Moneda", ["Pesos", "Dólares"], default="Pesos", key="evo_moneda", label_visibility="collapsed") or "Pesos"
    with c_c:
        cambios_ev = st.toggle("Incluir cambios USD→ARS", value=False, key="evo_cambios",
                               help="Para dólares conviene dejarlo apagado: los cambios a pesos inflan los egresos sin ser un gasto.")
    moneda_ev = "ARS" if nombre_ev == "Pesos" else "USD"
    flujo = reports.flujo_mensual(diario, excluir_conceptos=() if cambios_ev else (CAMBIOS,))
    sub = flujo[flujo["moneda"] == moneda_ev].copy() if not flujo.empty else flujo
    if sub.empty:
        st.caption("Todavía no hay datos suficientes.")
    else:
        sub["Mes"] = sub["periodo"].map(lambda p: f"{MESES[int(p[5:7]) - 1][:3]} {p[2:4]}")
        sub["Tipo"] = sub["tipo"].map({"ingreso": "Ingresos", "egreso": "Egresos"})
        sub["Importe"] = sub["monto"].map(lambda v: fmt_money(v, moneda_ev))
        orden = list(dict.fromkeys(sub.sort_values("periodo")["Mes"]))
        barras = (
            alt.Chart(sub)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("Mes:N", sort=orden, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=14)),
                xOffset=alt.XOffset("Tipo:N", sort=["Ingresos", "Egresos"]),
                y=alt.Y("monto:Q", title=None, axis=alt.Axis(format="~s", labelFontSize=13)),
                color=alt.Color(
                    "Tipo:N",
                    scale=alt.Scale(domain=["Ingresos", "Egresos"], range=["#16A34A", "#E5605A"]),
                    legend=alt.Legend(orient="top", direction="horizontal", title=None, labelFontSize=14, symbolType="square"),
                ),
                tooltip=["Mes", "Tipo", "Importe"],
            )
            .properties(height=300)
        )
        st.altair_chart(barras.properties(autosize=alt.AutoSizeParams(type="fit", contains="padding")).configure(background="#FFFFFF", padding={"left": 6, "right": 14, "top": 6, "bottom": 6}).configure_view(strokeWidth=0), width="stretch")
