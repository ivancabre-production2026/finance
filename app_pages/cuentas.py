"""Estado de cuenta: patrimonio actual por cuenta y por moneda."""
import datetime as dt

import streamlit as st

import reports
from ui import fmt_df, fmt_money, load_data

st.title("Estado de cuenta")
st.caption("Tu patrimonio actual, por cuenta y por moneda")

config, diario = load_data()
saldos = reports.saldos_cuentas(diario, config["cuentas"])

hoy = dt.date.today()
fijos = config.get("fijos", [])
if fijos:
    fijos_df = reports.conceptos_fijos_mes(diario, fijos, "egreso", hoy.year, hoy.month)
    pendientes = fijos_df.loc[~fijos_df["pagado"], "concepto"].tolist()
    if pendientes:
        st.warning(
            f"{len(pendientes)} gasto(s) fijo(s) pendiente(s) de pago este mes: {', '.join(pendientes)}",
            icon=":material/warning:",
        )

ingresos_fijos = config.get("ingresos_fijos", [])
if ingresos_fijos:
    ing_fijos_df = reports.conceptos_fijos_mes(diario, ingresos_fijos, "ingreso", hoy.year, hoy.month)
    sin_cobrar = ing_fijos_df.loc[~ing_fijos_df["pagado"], "concepto"].tolist()
    if sin_cobrar:
        st.warning(
            f"{len(sin_cobrar)} ingreso(s) fijo(s) sin cobrar este mes: {', '.join(sin_cobrar)}",
            icon=":material/notifications_active:",
        )

total_ars = saldos.loc[saldos["moneda"] == "ARS", "saldo"].sum() if not saldos.empty else 0.0
total_usd = saldos.loc[saldos["moneda"] == "USD", "saldo"].sum() if not saldos.empty else 0.0
n_cuentas = saldos["cuenta"].nunique() if not saldos.empty else 0

evol_ars = reports.patrimonio_evolucion(diario, "ARS")
evol_usd = reports.patrimonio_evolucion(diario, "USD")
delta_ars = evol_ars[-1] - evol_ars[-2] if len(evol_ars) >= 2 else None
delta_usd = evol_usd[-1] - evol_usd[-2] if len(evol_usd) >= 2 else None

col_p_ars, col_p_usd, col_p_n = st.columns([2, 2, 1])
with col_p_ars:
    with st.container(border=True):
        st.caption(":blue[**● Patrimonio en pesos**]")
        st.metric(
            "Patrimonio en pesos", fmt_money(total_ars, "ARS"), label_visibility="collapsed",
            delta=fmt_money(delta_ars, "ARS") if delta_ars is not None else None,
            delta_description="vs. mes anterior",
            chart_data=evol_ars if len(evol_ars) > 1 else None, chart_type="area",
        )
with col_p_usd:
    with st.container(border=True):
        st.caption(":green[**● Patrimonio en dólares**]")
        st.metric(
            "Patrimonio en dólares", fmt_money(total_usd, "USD"), label_visibility="collapsed",
            delta=fmt_money(delta_usd, "USD") if delta_usd is not None else None,
            delta_description="vs. mes anterior",
            chart_data=evol_usd if len(evol_usd) > 1 else None, chart_type="area",
        )
with col_p_n:
    with st.container(border=True):
        st.caption("&nbsp;")
        st.metric(":material/account_balance_wallet: Cuentas con saldo", str(n_cuentas))

if saldos.empty:
    st.info("Todavía no hay movimientos cargados. Cargá el primero desde Diario.", icon=":material/info:")
    st.stop()

cuentas_inversion = config.get("cuentas_inversion", [])
es_inversion = saldos["cuenta"].isin(cuentas_inversion)

col_d_ars, col_d_usd = st.columns(2)
for col, moneda, color in ((col_d_ars, "ARS", "blue"), (col_d_usd, "USD", "green")):
    with col:
        with st.container(border=True):
            st.caption(f":{color}[**● {'Pesos' if moneda == 'ARS' else 'Dólares'} — disponible vs. invertido**]")
            en_moneda = saldos["moneda"] == moneda
            disponible = saldos.loc[en_moneda & ~es_inversion, "saldo"].sum()
            invertido = saldos.loc[en_moneda & es_inversion, "saldo"].sum()
            with st.container(horizontal=True):
                st.metric(":material/savings: Disponible", fmt_money(disponible, moneda))
                st.metric(":material/trending_up: Invertido", fmt_money(invertido, moneda))

col_ars, col_usd = st.columns(2)
with col_ars:
    with st.container(border=True):
        st.markdown("**:material/payments: Pesos por cuenta (ARS)**")
        ars = saldos[saldos["moneda"] == "ARS"].sort_values("saldo", ascending=False)
        if ars.empty:
            st.caption("Sin saldo en pesos.")
        else:
            st.bar_chart(ars.set_index("cuenta")["saldo"], horizontal=True, color="#3B82F6")

with col_usd:
    with st.container(border=True):
        st.markdown("**:material/attach_money: Dólares por cuenta (USD)**")
        usd = saldos[saldos["moneda"] == "USD"].sort_values("saldo", ascending=False)
        if usd.empty:
            st.caption("Sin saldo en dólares.")
        else:
            st.bar_chart(usd.set_index("cuenta")["saldo"], horizontal=True, color="#34D399")

with st.container(border=True):
    st.markdown("**:material/table_chart: Detalle por cuenta**")
    st.caption("Las cuentas con más movimiento aparecen primero.")
    detalle = saldos.sort_values(["n_movs", "saldo"], ascending=[False, False]).copy()
    detalle["tipo"] = detalle["cuenta"].isin(cuentas_inversion).map({True: "Invertido", False: "Disponible"})
    detalle = fmt_df(detalle, ["saldo"])
    detalle = detalle.rename(columns={"cuenta": "Cuenta", "moneda": "Moneda", "saldo": "Saldo", "tipo": "Tipo"})
    detalle = detalle[["Cuenta", "Moneda", "Saldo", "Tipo"]]

    def _estilo_detalle(row):
        es_ars = row["Moneda"] == "ARS"
        color_moneda = "#60A5FA" if es_ars else "#34D399"
        if row["Tipo"] == "Invertido":
            bg_tipo, color_tipo = "#241B4A", "#C4B5FD"
        else:
            bg_tipo, color_tipo = "#0F2E23", "#6EE7B7"
        return [
            "",
            f"color: {color_moneda}; font-weight: 600",
            f"color: {color_moneda}; font-weight: 600",
            f"background-color: {bg_tipo}; color: {color_tipo}; font-weight: 600; border-radius: 6px",
        ]

    styled = detalle.style.apply(_estilo_detalle, axis=1).set_properties(**{"font-size": "15px", "padding": "8px 12px"})
    st.dataframe(styled, hide_index=True, width="stretch")
