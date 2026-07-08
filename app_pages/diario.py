"""Diario: carga de movimientos y últimos registros."""
import datetime as dt

import pandas as pd
import streamlit as st

import diario_store
from ui import fmt_df, load_data

st.title("Diario")
st.caption("Registrá cada movimiento apenas suceda")

config, diario = load_data()

with st.container(border=True):
    with st.form("nuevo_movimiento", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        fecha = c1.date_input("Fecha", value=dt.date.today())
        tipo = c2.selectbox("Tipo", ["egreso", "ingreso"])
        moneda = c3.selectbox("Moneda", ["ARS", "USD"])

        c4, c5, c6 = st.columns(3)
        conceptos = config["ingresos"] + config["egresos"]
        concepto = c4.selectbox("Concepto", conceptos)
        cuenta = c5.selectbox("Cuenta", config["cuentas"])
        monto = c6.number_input("Monto", min_value=0.0, step=100.0, format="%.2f")

        nota = st.text_input("Nota (opcional)")
        if st.form_submit_button("Cargar movimiento", type="primary", icon=":material/add_circle:"):
            if monto <= 0:
                st.error("El monto tiene que ser mayor a 0.")
            else:
                diario_store.add({
                    "fecha": fecha.isoformat(),
                    "tipo": tipo,
                    "concepto": concepto,
                    "cuenta": cuenta,
                    "moneda": moneda,
                    "monto": monto,
                    "nota": nota,
                })
                st.toast("Movimiento cargado", icon=":material/check_circle:")
                st.rerun()

st.subheader("Últimos movimientos")
diario = diario_store.load()
if diario:
    df = pd.DataFrame(diario).sort_values(["fecha", "id"], ascending=[False, False])
    df_view = df[["id", "fecha", "tipo", "concepto", "cuenta", "moneda", "monto", "nota"]]
    df_view = fmt_df(df_view, ["monto"])
    df_view = df_view.rename(columns={
        "id": "ID", "fecha": "Fecha", "tipo": "Tipo", "concepto": "Concepto",
        "cuenta": "Cuenta", "moneda": "Moneda", "monto": "Monto", "nota": "Nota",
    })
    st.dataframe(df_view, hide_index=True, width="stretch")

    with st.expander("Borrar un movimiento", icon=":material/delete:"):
        id_borrar = st.number_input("ID a borrar", min_value=1, step=1)
        if st.button("Borrar", icon=":material/delete_forever:"):
            diario_store.delete(int(id_borrar))
            st.toast("Movimiento borrado", icon=":material/check_circle:")
            st.rerun()
else:
    st.info("Todavía no cargaste movimientos.", icon=":material/info:")
