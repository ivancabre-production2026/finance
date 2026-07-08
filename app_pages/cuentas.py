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

with st.container(horizontal=True):
    st.metric("Patrimonio en pesos", fmt_money(total_ars, "ARS"), border=True)
    st.metric("Patrimonio en dólares", fmt_money(total_usd, "USD"), border=True)
    st.metric("Cuentas con saldo", str(n_cuentas), border=True)

if saldos.empty:
    st.info("Todavía no hay movimientos cargados. Cargá el primero desde Diario.", icon=":material/info:")
    st.stop()

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
    detalle = saldos.sort_values(["moneda", "saldo"], ascending=[True, False])
    detalle = fmt_df(detalle, ["saldo"])
    detalle = detalle.rename(columns={"cuenta": "Cuenta", "moneda": "Moneda", "saldo": "Saldo"})
    st.dataframe(detalle, hide_index=True, width="stretch")
