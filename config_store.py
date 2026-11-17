"""Listas de conceptos y cuentas (equivalente a la pestaña 'config' de la planilla)."""
import json
from pathlib import Path

import db

CONFIG_FILE = Path(__file__).parent / "data" / "config.json"

_SEED = {
    "ingresos": [
        "Ingreso ilatin/Iron Rod",
        "Ingreso Pretzel",
        "Ingreso Jaime",
        "Ingreso Alquiler Frías",
        "Ingreso Otros",
        "Intereses Plazo Fijo Bco.+Billeteras",
        "Saldo Inicial",
        "Ingreso a Balanz",
    ],
    "egresos": [
        "Alquiler",
        "Expensas",
        "Luz Edet",
        "SAT",
        "Gas",
        "CISI",
        "Monot Iván",
        "Master BNA Iván",
        "Master y Visa+prefer",
        "Master y Visa",
        "Naranja+Gcia Euni",
        "Naranja Iván",
        "Salidas/Pedidos",
        "Super",
        "Farmacia/Medicina",
        "Celu",
        "Diezmo",
        "Ajuste",
        "Inversión",
        "Doméstico",
        "AUTO+Cochera",
        "Obra Social OSPE",
        "Internet",
        "Ropa+Corte, etc",
        "Pichis + Otros",
        "Alquiler Cochera",
        "Euni Inversión",
        "Viaje",
        "Deporte",
        "Cambio USD a ARS",
        "Transferencia",
        "Asistencia Nahuel",
    ],
    "cuentas": [
        "Efectivo",
        "Naranja X",
        "Fiwind Pesos",
        "Fiwind Dólares",
        "DolarApp",
        "Ualá",
        "Mercado Pago",
        "Balanz",
        "Galicia",
        "Plazo Fijo Galicia",
        "HiGlobe",
    ],
    # Conceptos de egreso que son gastos fijos/recurrentes (para la alerta de pendientes de pago).
    "fijos": [
        "Alquiler",
        "Expensas",
        "Luz Edet",
        "SAT",
        "Gas",
        "CISI",
        "Monot Iván",
        "Master BNA Iván",
        "Master y Visa+prefer",
        "Master y Visa",
        "Naranja+Gcia Euni",
        "Naranja Iván",
        "Celu",
        "Diezmo",
        "Obra Social OSPE",
        "Internet",
        "Alquiler Cochera",
    ],
    # Conceptos de ingreso que son cobros fijos/esperados cada mes (para detectar quién no pagó aún).
    "ingresos_fijos": [
        "Ingreso ilatin/Iron Rod",
        "Ingreso Pretzel",
        "Ingreso Jaime",
        "Ingreso Alquiler Frías",
    ],
    # Cuentas que son inversión (no liquidez disponible), para separar el patrimonio en Cuentas.
    "cuentas_inversion": [
        "Balanz",
        "DolarApp Invertido",
        "Galicia",
        "Plazo Fijo Galicia",
    ],
}


DIEZMO_DEFAULT = {
    "porcentaje": 10.0,
    # Conceptos de ingreso sobre los que se calcula el diezmo.
    "conceptos": ["Ingreso ilatin/Iron Rod", "Ingreso Pretzel", "Ingreso Jaime"],
    # Diezmo adeudado por mes, tal como figuraba al 17/11/2026 (ARS).
    "deuda_inicial": {"2026-07": 848000.0, "2026-08": 877120.0, "2026-09": 840800.0, "2026-10": 873920.0},
    # Fecha desde la cual los pagos con concepto Diezmo reducen esa deuda.
    "corte": "2026-11-17",
    # Tipo de cambio de fin de mes ingresado a mano, {"2026-11": 1650.0}. Si falta, se estima.
    "tc": {},
    # Monto del diezmo de un mes ingresado a mano (pisa el calculo), {"2026-11": 780000.0}.
    "manual": {},
}


def _load_raw() -> dict:
    if db.is_configured():
        return db.load("config", _SEED)
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    save(_SEED)
    return json.loads(json.dumps(_SEED))


def load() -> dict:
    config = _load_raw()
    dirty = False
    if "fijos" not in config:
        config["fijos"] = [c for c in _SEED["fijos"] if c in config.get("egresos", [])]
        dirty = True
    if "ingresos_fijos" not in config:
        config["ingresos_fijos"] = [c for c in _SEED["ingresos_fijos"] if c in config.get("ingresos", [])]
        dirty = True
    if "cuentas_inversion" not in config:
        config["cuentas_inversion"] = [c for c in _SEED["cuentas_inversion"] if c in config.get("cuentas", [])]
        dirty = True
    # Diezmo: deuda al 17/11/2026 (jul-oct) y reglas de calculo. Los pagos desde el corte la reducen.
    diezmo = config.setdefault("diezmo", {})
    for clave, valor in DIEZMO_DEFAULT.items():
        if clave not in diezmo:
            diezmo[clave] = json.loads(json.dumps(valor))
            dirty = True
    if dirty:
        save(config)
    return config


def save(config: dict) -> None:
    if db.is_configured():
        db.save("config", config)
        return
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
