"""Helpers compartidos entre páginas: formato de números y acceso a datos."""
import datetime as dt

import pandas as pd

import config_store
import diario_store

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def fmt(monto: float) -> str:
    """Formatea un número al estilo argentino: 2.355.289,68"""
    return f"{monto:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_money(monto: float, moneda: str) -> str:
    simbolo = "US$" if moneda == "USD" else "$"
    return f"{simbolo} {fmt(monto)}"


def fmt_df(df: pd.DataFrame, columnas: list) -> pd.DataFrame:
    """Copia de df con las columnas numéricas indicadas formateadas como texto (estilo argentino)."""
    df = df.copy()
    for col in columnas:
        df[col] = df[col].apply(fmt)
    return df


def load_data():
    return config_store.load(), diario_store.load()


def meses_disponibles(diario: list) -> list:
    """Meses (año, mes) desde el primer movimiento hasta el actual, el más reciente primero."""
    hoy = dt.date.today()
    primero = min((e["fecha"][:7] for e in diario), default=hoy.strftime("%Y-%m"))
    a, m = int(primero[:4]), int(primero[5:7])
    meses = []
    while (a, m) <= (hoy.year, hoy.month):
        meses.append((a, m))
        m += 1
        if m == 13:
            a, m = a + 1, 1
    meses.reverse()
    return meses
