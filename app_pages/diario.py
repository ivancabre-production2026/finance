"""Diario: carga de movimientos y últimos registros."""
import datetime as dt

import streamlit as st

import diario_store
import ui_html
from ui import load_data

st.title("Diario")
st.caption("Registrá cada movimiento apenas suceda.")

config, diario = load_data()

# --- Nuevo movimiento -------------------------------------------------------
with st.container(key="card-form"):
    st.html(ui_html.titulo_seccion("Nuevo movimiento", "Completá los datos y cargalo al diario."))
    with st.form("nuevo_movimiento", clear_on_submit=True, border=False):
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
        sin_saldo = st.checkbox(
            "Devengado: cuenta como pagado del mes, pero todavía no descontar del saldo",
            help="Para algo que se cobra después, por ejemplo en el resumen de la tarjeta del mes que viene.",
        )
        if st.form_submit_button("Cargar movimiento", type="primary", icon=":material/add_circle:"):
            if monto <= 0:
                st.error("El monto tiene que ser mayor a 0.")
            else:
                entrada = {
                    "fecha": fecha.isoformat(),
                    "tipo": tipo,
                    "concepto": concepto,
                    "cuenta": cuenta,
                    "moneda": moneda,
                    "monto": monto,
                    "nota": nota,
                }
                if sin_saldo:
                    entrada["sin_saldo"] = True
                diario_store.add(entrada)
                st.toast("Movimiento cargado", icon=":material/check_circle:")
                st.rerun()

# --- Últimos movimientos ----------------------------------------------------
diario = diario_store.load()
with st.container(key="card-movs"):
    c_titulo, c_buscar, c_cant = st.columns([2.4, 2.2, 1.2], vertical_alignment="center")
    with c_buscar:
        busqueda = st.text_input("Buscar", placeholder="Buscar concepto, cuenta o nota", icon=":material/search:", label_visibility="collapsed")
    with c_cant:
        cantidad = st.selectbox("Mostrar", ["25", "50", "100", "Todos"], label_visibility="collapsed")

    filas = sorted(diario, key=lambda e: (e["fecha"], e["id"]), reverse=True)
    if busqueda:
        q = busqueda.lower()
        filas = [e for e in filas if q in e["concepto"].lower() or q in e["cuenta"].lower() or q in (e.get("nota") or "").lower()]
    total = len(filas)
    if cantidad != "Todos":
        filas = filas[: int(cantidad)]

    with c_titulo:
        st.html(ui_html.titulo_seccion("Últimos movimientos", f"Mostrando {len(filas)} de {total}"))

    if not diario:
        st.info("Todavía no cargaste movimientos.", icon=":material/info:")
    else:
        st.html(ui_html.tabla_movimientos(filas))

        with st.expander("Borrar un movimiento", icon=":material/delete:"):
            id_borrar = st.number_input("ID a borrar", min_value=1, step=1)
            if st.button("Borrar", icon=":material/delete_forever:"):
                diario_store.delete(int(id_borrar))
                st.toast("Movimiento borrado", icon=":material/check_circle:")
                st.rerun()
