"""Resumen: patrimonio, disponible vs. invertido y detalle por cuenta."""
import calendar
import datetime as dt

import streamlit as st

import reports
import ui_html
from ui import MESES, load_data, meses_disponibles

config, diario = load_data()
cuentas_inversion = config.get("cuentas_inversion", [])
hoy = dt.date.today()

# (código, nombre)
MONEDAS = (("ARS", "Pesos"), ("USD", "Dólares"))


def _etiqueta_mes(anio: int, mes: int) -> str:
    return f"{MESES[mes - 1]} {anio}"


meses = meses_disponibles(diario)
etiquetas = [_etiqueta_mes(*x) for x in meses]

# --- Encabezado -------------------------------------------------------------
col_titulo, col_mes, col_nuevo = st.columns([3.2, 1.3, 1.5], vertical_alignment="center")
with col_titulo:
    st.title("Estado de cuenta")
    st.caption("Tu patrimonio, disponible e inversiones en un solo lugar.")
with col_mes:
    elegida = st.selectbox("Mes", etiquetas, label_visibility="collapsed", key="resumen_mes")
with col_nuevo:
    if st.button("Nuevo movimiento", type="primary", icon=":material/add:", key="btn-nuevo", width="stretch"):
        st.switch_page("app_pages/diario.py")

anio, mes = meses[etiquetas.index(elegida)]
fin_mes = dt.date(anio, mes, calendar.monthrange(anio, mes)[1]).isoformat()
anterior = dt.date(anio, mes, 1) - dt.timedelta(days=1)

hasta = [e for e in diario if e["fecha"] <= fin_mes]
hasta_ant = [e for e in diario if e["fecha"] <= anterior.isoformat()]
saldos = reports.saldos_cuentas(hasta, config["cuentas"])

# --- Pendientes del mes -----------------------------------------------------
pendientes, sin_cobrar = [], []
if config.get("fijos"):
    df = reports.conceptos_fijos_mes(diario, config["fijos"], "egreso", anio, mes)
    pendientes = df.loc[~df["pagado"], "concepto"].tolist()
if config.get("ingresos_fijos"):
    df = reports.conceptos_fijos_mes(diario, config["ingresos_fijos"], "ingreso", anio, mes)
    sin_cobrar = df.loc[~df["pagado"], "concepto"].tolist()


def _lista(nombres: list, tope: int = 5) -> str:
    if len(nombres) <= tope:
        return ", ".join(nombres)
    return ", ".join(nombres[:tope]) + f" y {len(nombres) - tope} más"


if pendientes or sin_cobrar:
    with st.container(key="alerta"):
        c_texto, c_link = st.columns([5, 1.1], vertical_alignment="center")
        with c_texto:
            partes = []
            if pendientes:
                partes.append(f"**{len(pendientes)} pagos pendientes**")
            if sin_cobrar:
                partes.append(f"**{len(sin_cobrar)} cobros pendientes**")
            st.markdown(":material/notifications: " + "   |   ".join(partes))
            detalle = []
            if pendientes:
                detalle.append("Pagos: " + _lista(pendientes))
            if sin_cobrar:
                detalle.append("Cobros: " + _lista(sin_cobrar))
            st.html(f'<div class="fp-alerta-nombres">{" · ".join(detalle)}</div>')
        with c_link:
            st.page_link("app_pages/movimientos.py", label="Ver pendientes", icon=":material/arrow_forward:")
else:
    st.success(f"Todo al día en {elegida.lower()}: no hay pagos ni cobros pendientes.", icon=":material/check_circle:")

if saldos.empty:
    st.info("Todavía no hay movimientos cargados. Cargá el primero desde Diario.", icon=":material/info:")
    st.stop()


def totales(moneda: str, entradas=None):
    """(disponible, invertido, total) de una moneda."""
    s = saldos if entradas is None else reports.saldos_cuentas(entradas, config["cuentas"])
    s = s[s["moneda"] == moneda]
    inv = s.loc[s["cuenta"].isin(cuentas_inversion), "saldo"].sum()
    disp = s.loc[~s["cuenta"].isin(cuentas_inversion), "saldo"].sum()
    return disp, inv, disp + inv


# --- Patrimonio por moneda --------------------------------------------------
for col, (moneda, nombre) in zip(st.columns(2), MONEDAS):
    disp, inv, total = totales(moneda)
    delta = total - totales(moneda, hasta_ant)[2] if hasta_ant else None
    with col:
        st.html(ui_html.hero(moneda, nombre, total, disp, inv, delta))

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

with st.container(key="card-cuentas"):
    c_titulo, c_buscar, c_filtro = st.columns([3, 2.2, 1.8], vertical_alignment="center")
    with c_buscar:
        busqueda = st.text_input("Buscar cuenta", placeholder="Buscar cuenta", icon=":material/search:", label_visibility="collapsed")
    with c_filtro:
        filtro = st.selectbox("Moneda", ["Todas las monedas", "Pesos", "Dólares"], label_visibility="collapsed")

    vista = tabla
    if busqueda:
        vista = vista[vista["cuenta_base"].str.contains(busqueda, case=False, na=False)]
    if filtro != "Todas las monedas":
        vista = vista[vista["moneda"] == {"Pesos": "ARS", "Dólares": "USD"}[filtro]]

    with c_titulo:
        st.html(ui_html.titulo_seccion("Mis cuentas", f"{len(vista)} cuentas con saldo"))
    st.html(ui_html.tabla_cuentas(vista.to_dict("records")))

# --- Distribución del patrimonio -------------------------------------------
with st.container(key="card-dist"):
    items = []
    for moneda, nombre in MONEDAS:
        disp, inv, _ = totales(moneda)
        items.append((moneda, nombre, disp, inv))
    st.html(ui_html.distribucion(items))
