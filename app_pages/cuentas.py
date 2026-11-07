"""Resumen: patrimonio, disponible vs. invertido y detalle por cuenta."""
import datetime as dt

import altair as alt
import pandas as pd
import streamlit as st

import reports
from ui import MESES, fmt_money, load_data

config, diario = load_data()
saldos = reports.saldos_cuentas(diario, config["cuentas"])
cuentas_inversion = config.get("cuentas_inversion", [])
hoy = dt.date.today()

# (código, nombre, color del acento)
MONEDAS = (("ARS", "Pesos", "blue"), ("USD", "Dólares", "green"))

# --- Encabezado -------------------------------------------------------------
col_titulo, col_accion = st.columns([3, 1], vertical_alignment="center")
with col_titulo:
    st.title("Estado de cuenta")
    st.caption("Tu patrimonio, disponible e inversiones en un solo lugar.")
with col_accion:
    with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
        st.badge(f"{MESES[hoy.month - 1]} {hoy.year}", icon=":material/calendar_month:", color="gray")
        if st.button("Nuevo movimiento", type="primary", icon=":material/add:"):
            st.switch_page("app_pages/diario.py")

# --- Pendientes del mes -----------------------------------------------------
fijos = config.get("fijos", [])
pendientes = []
if fijos:
    fijos_df = reports.conceptos_fijos_mes(diario, fijos, "egreso", hoy.year, hoy.month)
    pendientes = fijos_df.loc[~fijos_df["pagado"], "concepto"].tolist()

ingresos_fijos = config.get("ingresos_fijos", [])
sin_cobrar = []
if ingresos_fijos:
    ing_fijos_df = reports.conceptos_fijos_mes(diario, ingresos_fijos, "ingreso", hoy.year, hoy.month)
    sin_cobrar = ing_fijos_df.loc[~ing_fijos_df["pagado"], "concepto"].tolist()

if pendientes or sin_cobrar:
    col_alerta, col_link = st.columns([5, 1], vertical_alignment="center")
    with col_alerta:
        partes = []
        if pendientes:
            partes.append(f"**{len(pendientes)} pagos pendientes**")
        if sin_cobrar:
            partes.append(f"**{len(sin_cobrar)} cobros pendientes**")
        st.warning("   |   ".join(partes), icon=":material/notifications_active:")
    with col_link:
        st.page_link("app_pages/movimientos.py", label="Ver pendientes", icon=":material/arrow_forward:")
    detalle_pend = []
    if pendientes:
        detalle_pend.append("Pagos: " + ", ".join(pendientes))
    if sin_cobrar:
        detalle_pend.append("Cobros: " + ", ".join(sin_cobrar))
    st.caption("  ·  ".join(detalle_pend))
elif fijos or ingresos_fijos:
    st.success("Todo al día este mes: no tenés pagos ni cobros pendientes.", icon=":material/check_circle:")

if saldos.empty:
    st.info("Todavía no hay movimientos cargados. Cargá el primero desde Diario.", icon=":material/info:")
    st.stop()


def totales(moneda: str):
    """(disponible, invertido, total) de una moneda."""
    s = saldos[saldos["moneda"] == moneda]
    inv = s.loc[s["cuenta"].isin(cuentas_inversion), "saldo"].sum()
    disp = s.loc[~s["cuenta"].isin(cuentas_inversion), "saldo"].sum()
    return disp, inv, disp + inv


# --- Patrimonio por moneda --------------------------------------------------
for col, (moneda, nombre, color) in zip(st.columns(2), MONEDAS):
    disp, inv, total = totales(moneda)
    evol = reports.patrimonio_evolucion(diario, moneda)
    delta = None
    if len(evol) >= 2:
        cambio = evol[-1] - evol[-2]
        delta = f"{'-' if cambio < 0 else '+'}{fmt_money(abs(cambio), moneda)}"
    with col:
        with st.container(border=True):
            st.markdown(f":{color}[**● Patrimonio en {nombre.lower()}**]")
            st.metric(
                f"Patrimonio en {nombre.lower()}", f"**{fmt_money(total, moneda)}**",
                delta=delta, delta_description="vs. mes anterior", label_visibility="collapsed",
            )
            c_disp, c_inv = st.columns(2)
            with c_disp:
                st.caption("Disponible")
                st.markdown(f"#### {fmt_money(disp, moneda)}")
            with c_inv:
                st.caption("Invertido")
                st.markdown(f"#### {fmt_money(inv, moneda)}")

# --- Mis cuentas ------------------------------------------------------------
base = saldos.copy()
base["cuenta_base"] = base["cuenta"].str.replace(r" (Disponible|Invertido)$", "", regex=True)
es_inv = base["cuenta"].isin(cuentas_inversion)
base["disponible"] = base["saldo"].where(~es_inv, 0.0)
base["invertido"] = base["saldo"].where(es_inv, 0.0)
tabla = (
    base.groupby(["cuenta_base", "moneda"], as_index=False)
    .agg(disponible=("disponible", "sum"), invertido=("invertido", "sum"), total=("saldo", "sum"), n_movs=("n_movs", "sum"))
    .sort_values(["n_movs", "total"], ascending=[False, False])
)

with st.container(border=True):
    c_titulo, c_buscar, c_filtro = st.columns([3, 2, 2], vertical_alignment="center")
    with c_buscar:
        busqueda = st.text_input("Buscar cuenta", placeholder="Buscar cuenta", icon=":material/search:", label_visibility="collapsed")
    with c_filtro:
        filtro = st.selectbox("Moneda", ["Todas las monedas", "Pesos", "Dólares"], label_visibility="collapsed")

    vista = tabla
    if busqueda:
        vista = vista[vista["cuenta_base"].str.contains(busqueda, case=False, na=False)]
    if filtro != "Todas las monedas":
        vista = vista[vista["moneda"] == {"Pesos": "ARS", "Dólares": "USD"}[filtro]]
    vista = vista.reset_index(drop=True)

    with c_titulo:
        st.subheader("Mis cuentas")
        st.caption("Las de más movimiento van primero  ·  %d cuentas con saldo" % len(vista))

    if vista.empty:
        st.caption("Ninguna cuenta coincide con la búsqueda.")
    else:
        mostrar = pd.DataFrame({
            "Cuenta": vista["cuenta_base"],
            "Moneda": vista["moneda"],
            "Disponible": [fmt_money(v, m) for v, m in zip(vista["disponible"], vista["moneda"])],
            "Invertido": [fmt_money(v, m) for v, m in zip(vista["invertido"], vista["moneda"])],
            "Saldo total": [fmt_money(v, m) for v, m in zip(vista["total"], vista["moneda"])],
        })

        def _estilo(row):
            r = vista.loc[row.name]
            if r["moneda"] == "ARS":
                pill = "background-color: #DBEAFE; color: #1E40AF; font-weight: 700"
            else:
                pill = "background-color: #DCFCE7; color: #166534; font-weight: 700"
            apagado = "color: #9CA3AF"
            return [
                "font-weight: 700",
                pill,
                apagado if r["disponible"] == 0 else "",
                apagado if r["invertido"] == 0 else "",
                "font-weight: 700",
            ]

        styled = mostrar.style.apply(_estilo, axis=1).set_properties(**{"font-size": "16px"})
        st.dataframe(
            styled, hide_index=True, width="stretch", height="content", row_height=46,
            column_config={
                "Cuenta": st.column_config.TextColumn("Cuenta", width="medium"),
                "Moneda": st.column_config.TextColumn("Moneda", width="small", alignment="center"),
                "Disponible": st.column_config.TextColumn("Disponible", alignment="right"),
                "Invertido": st.column_config.TextColumn("Invertido", alignment="right"),
                "Saldo total": st.column_config.TextColumn("Saldo total", alignment="right"),
            },
        )

# --- Distribución del patrimonio -------------------------------------------
filas = []
for moneda, nombre, _ in MONEDAS:
    disp, inv, _total = totales(moneda)
    d, i = max(disp, 0.0), max(inv, 0.0)
    t = d + i
    if t <= 0:
        continue
    etiqueta = f"{nombre}  {fmt_money(disp + inv, moneda)}"
    filas.append(dict(Moneda=etiqueta, Tipo="Disponible", ini=0.0, fin=d / t, mid=d / t / 2, ancho=d / t, Monto=fmt_money(disp, moneda)))
    filas.append(dict(Moneda=etiqueta, Tipo="Invertido", ini=d / t, fin=1.0, mid=(d / t + 1) / 2, ancho=i / t, Monto=fmt_money(inv, moneda)))

with st.container(border=True):
    st.subheader("Distribución del patrimonio")
    if not filas:
        st.caption("Sin saldo para mostrar.")
    else:
        df_dist = pd.DataFrame(filas)
        orden = list(dict.fromkeys(df_dist["Moneda"]))
        eje_y = alt.Y(
            "Moneda:N", sort=orden, title=None,
            axis=alt.Axis(labelFontSize=15, labelFontWeight="bold", labelLimit=320, ticks=False, domain=False),
        )
        escala_x = alt.Scale(domain=[0, 1])
        barras = (
            alt.Chart(df_dist)
            .mark_bar(cornerRadius=6, size=36)
            .encode(
                y=eje_y,
                x=alt.X("ini:Q", axis=None, scale=escala_x),
                x2="fin:Q",
                color=alt.Color(
                    "Tipo:N",
                    scale=alt.Scale(domain=["Disponible", "Invertido"], range=["#A9D9B5", "#0B5D3B"]),
                    legend=alt.Legend(orient="top", direction="horizontal", title=None, labelFontSize=14, symbolType="square", symbolSize=180),
                ),
                tooltip=["Moneda", "Tipo", "Monto"],
            )
        )
        textos = (
            alt.Chart(df_dist[df_dist["ancho"] >= 0.14])
            .mark_text(fontSize=14, fontWeight="bold")
            .encode(
                y=eje_y,
                x=alt.X("mid:Q", axis=None, scale=escala_x),
                text="Monto:N",
                color=alt.condition(alt.datum.Tipo == "Invertido", alt.value("#FFFFFF"), alt.value("#0B3D2B")),
            )
        )
        st.altair_chart((barras + textos).properties(height=74 * len(orden) + 20), width="stretch")
