"""Vistas calculadas a partir del Diario: Ing.-Egr. del mes, saldos de cuentas y flujo mensual.
Nada de esto se persiste: se recalcula siempre desde diario_store.load().
"""
import pandas as pd


def _df(entries: list) -> pd.DataFrame:
    if not entries:
        return pd.DataFrame(columns=["id", "fecha", "tipo", "concepto", "cuenta", "moneda", "monto", "nota"])
    df = pd.DataFrame(entries)
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df


def _sin_saldo_inicial(df: pd.DataFrame) -> pd.DataFrame:
    """'Saldo Inicial' es un asiento de arranque, no un movimiento real: se excluye de los reportes de actividad."""
    if df.empty:
        return df
    return df[df["concepto"] != "Saldo Inicial"]


def ing_egr_mes(entries: list, anio: int, mes: int) -> dict:
    """Egresos e ingresos reales del mes (sin contar el saldo inicial), agrupados por concepto y moneda."""
    df = _sin_saldo_inicial(_df(entries))
    if df.empty:
        return {"egresos": pd.DataFrame(), "ingresos": pd.DataFrame()}
    df_mes = df[(df["fecha"].dt.year == anio) & (df["fecha"].dt.month == mes)]

    def agrupar(tipo: str) -> pd.DataFrame:
        sub = df_mes[df_mes["tipo"] == tipo]
        if sub.empty:
            return pd.DataFrame(columns=["concepto", "ARS", "USD"])
        pivot = sub.pivot_table(index="concepto", columns="moneda", values="monto", aggfunc="sum", fill_value=0)
        for moneda in ("ARS", "USD"):
            if moneda not in pivot.columns:
                pivot[moneda] = 0
        return pivot[["ARS", "USD"]].reset_index()

    return {"egresos": agrupar("egreso"), "ingresos": agrupar("ingreso")}


def saldos_cuentas(entries: list, cuentas: list) -> pd.DataFrame:
    """Saldo real de cada cuenta (ingresos - egresos acumulados), por moneda."""
    df = _df(entries)
    filas = []
    for cuenta in cuentas:
        sub = df[df["cuenta"] == cuenta] if not df.empty else df
        for moneda in ("ARS", "USD"):
            sub_moneda = sub[sub["moneda"] == moneda] if not sub.empty else sub
            ingresos = sub_moneda[sub_moneda["tipo"] == "ingreso"]["monto"].sum() if not sub_moneda.empty else 0
            egresos = sub_moneda[sub_moneda["tipo"] == "egreso"]["monto"].sum() if not sub_moneda.empty else 0
            saldo = ingresos - egresos
            if saldo != 0:
                filas.append({"cuenta": cuenta, "moneda": moneda, "saldo": saldo})
    return pd.DataFrame(filas, columns=["cuenta", "moneda", "saldo"])


def conceptos_fijos_mes(entries: list, conceptos: list, tipo: str, anio: int, mes: int) -> pd.DataFrame:
    """Para cada concepto fijo/recurrente (ingreso o egreso), si ya tuvo movimiento este mes o sigue pendiente."""
    df = _df(entries)
    if not df.empty:
        df_mes = df[(df["fecha"].dt.year == anio) & (df["fecha"].dt.month == mes) & (df["tipo"] == tipo)]
    else:
        df_mes = df

    filas = []
    for concepto in conceptos:
        sub = df_mes[df_mes["concepto"] == concepto] if not df_mes.empty else df_mes
        ars = sub[sub["moneda"] == "ARS"]["monto"].sum() if not sub.empty else 0.0
        usd = sub[sub["moneda"] == "USD"]["monto"].sum() if not sub.empty else 0.0
        filas.append({"concepto": concepto, "ARS": ars, "USD": usd, "pagado": bool(ars) or bool(usd)})
    return pd.DataFrame(filas, columns=["concepto", "ARS", "USD", "pagado"])


def patrimonio_evolucion(entries: list, moneda: str) -> list[float]:
    """Patrimonio total (todas las cuentas) al cierre de cada mes, para una moneda. Para sparklines."""
    df = _df(entries)
    if df.empty:
        return []
    df = df[df["moneda"] == moneda]
    if df.empty:
        return []
    signo = df["tipo"].map({"ingreso": 1, "egreso": -1})
    df = df.assign(monto_signed=df["monto"] * signo, periodo=df["fecha"].dt.to_period("M"))
    por_mes = df.groupby("periodo")["monto_signed"].sum().sort_index()
    return por_mes.cumsum().tolist()


def flujo_mensual(entries: list) -> pd.DataFrame:
    """Ingresos vs egresos reales totales por mes y moneda (sin saldo inicial), para ver la evolución."""
    df = _sin_saldo_inicial(_df(entries))
    if df.empty:
        return pd.DataFrame(columns=["periodo", "moneda", "tipo", "monto"])
    df["periodo"] = df["fecha"].dt.to_period("M").astype(str)
    resumen = df.groupby(["periodo", "moneda", "tipo"])["monto"].sum().reset_index()
    return resumen.sort_values("periodo")
