"""Diario de movimientos: cada carga (ingreso o egreso) queda como una fila acá.
Equivalente a la pestaña 'Diario' de la planilla. Ing.-Egr. y saldos de cuentas
se calculan a partir de esta lista, no se guardan por separado.
"""
import json
from pathlib import Path

import db

DIARIO_FILE = Path(__file__).parent / "data" / "diario.json"

# Saldos reales al 01/07/2026, tomados de la tabla "Cuentas" de la planilla.
_SEED = [
    {"id": 1, "fecha": "2026-07-01", "tipo": "ingreso", "concepto": "Saldo Inicial", "cuenta": "Efectivo", "moneda": "ARS", "monto": 101387.71, "nota": "Saldo real al 01/07/2026 (tabla Cuentas)"},
    {"id": 2, "fecha": "2026-07-01", "tipo": "ingreso", "concepto": "Saldo Inicial", "cuenta": "Efectivo", "moneda": "USD", "monto": 200.00, "nota": "Saldo real al 01/07/2026 (tabla Cuentas)"},
    {"id": 3, "fecha": "2026-07-01", "tipo": "ingreso", "concepto": "Saldo Inicial", "cuenta": "Naranja X", "moneda": "ARS", "monto": 1932.90, "nota": "Saldo real al 01/07/2026 (tabla Cuentas)"},
    {"id": 4, "fecha": "2026-07-01", "tipo": "ingreso", "concepto": "Saldo Inicial", "cuenta": "Fiwind Pesos", "moneda": "ARS", "monto": 817880.00, "nota": "Saldo real al 01/07/2026 (tabla Cuentas)"},
    {"id": 5, "fecha": "2026-07-01", "tipo": "ingreso", "concepto": "Saldo Inicial", "cuenta": "Fiwind Dólares", "moneda": "USD", "monto": 1.05, "nota": "Saldo real al 01/07/2026 (tabla Cuentas)"},
    {"id": 6, "fecha": "2026-07-01", "tipo": "ingreso", "concepto": "Saldo Inicial", "cuenta": "DolarApp", "moneda": "USD", "monto": 9155.78, "nota": "Saldo real al 01/07/2026 (tabla Cuentas)"},
    {"id": 7, "fecha": "2026-07-01", "tipo": "ingreso", "concepto": "Saldo Inicial", "cuenta": "Mercado Pago", "moneda": "ARS", "monto": 16238.19, "nota": "Saldo real al 01/07/2026 (tabla Cuentas)"},
    {"id": 8, "fecha": "2026-07-01", "tipo": "ingreso", "concepto": "Saldo Inicial", "cuenta": "Balanz", "moneda": "USD", "monto": 8450.00, "nota": "Saldo real al 01/07/2026 (tabla Cuentas)"},
    {"id": 9, "fecha": "2026-07-01", "tipo": "ingreso", "concepto": "Saldo Inicial", "cuenta": "Galicia", "moneda": "ARS", "monto": 2355289.68, "nota": "Saldo real al 01/07/2026 (tabla Cuentas)"},
]


def load() -> list:
    if db.is_configured():
        return db.load("diario", _SEED)
    if DIARIO_FILE.exists():
        return json.loads(DIARIO_FILE.read_text(encoding="utf-8"))
    save(_SEED)
    return list(_SEED)


def save(entries: list) -> None:
    if db.is_configured():
        db.save("diario", entries)
        return
    DIARIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    DIARIO_FILE.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


def add(entry: dict) -> dict:
    entries = load()
    next_id = max((e["id"] for e in entries), default=0) + 1
    entry = {"id": next_id, **entry}
    entries.append(entry)
    save(entries)
    return entry


def update(entry_id: int, changes: dict) -> None:
    entries = load()
    for e in entries:
        if e["id"] == entry_id:
            e.update(changes)
            break
    save(entries)


def delete(entry_id: int) -> None:
    entries = load()
    entries = [e for e in entries if e["id"] != entry_id]
    save(entries)
