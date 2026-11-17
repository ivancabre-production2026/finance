"""Diezmo: 10% de los ingresos del mes, llevados a pesos al tipo de cambio de fin de mes.

Meses con deuda confirmada (config['diezmo']['deuda_inicial']) usan ese monto. Desde el primer mes
sin deuda confirmada, el diezmo se calcula solo: porcentaje x (ingresos en pesos + ingresos en USD x TC).
Los pagos son movimientos del Diario con concepto 'Diezmo' (egreso) desde la fecha de corte, y se
aplican al mes mas viejo primero.
"""
import datetime as dt
import re

_RE_ARS = re.compile(r"(?:\(|-> )([\d\.]+) ARS")  # "(65.200 ARS" o "-> 500.000 ARS"


def _mes_siguiente(periodo: str) -> str:
    a, m = int(periodo[:4]), int(periodo[5:7])
    return f"{a + 1}-01" if m == 12 else f"{a}-{m + 1:02d}"


def periodos(cfg: dict, hoy: dt.date | None = None) -> list:
    """Meses desde el primero con deuda confirmada hasta el mes actual."""
    hoy = hoy or dt.date.today()
    actual = hoy.strftime("%Y-%m")
    primero = min(cfg["deuda_inicial"]) if cfg["deuda_inicial"] else actual
    out, p = [], primero
    while p <= actual:
        out.append(p)
        p = _mes_siguiente(p)
    return out


def tc_estimado(entries: list, periodo: str):
    """TC de la ultima conversion USD->ARS del mes (sale de la nota '(N ARS)'); si no hay, el del mes
    anterior mas cercano. Devuelve (tc, de_que_mes) o (None, None)."""
    por_mes = {}
    for e in sorted(entries, key=lambda x: (x["fecha"], x["id"])):
        if e["concepto"] == "Cambio USD a ARS" and e["moneda"] == "USD" and e["monto"] > 5 and not e.get("sin_saldo"):
            m = _RE_ARS.search(e.get("nota") or "")
            if m:
                ars = float(m.group(1).replace(".", ""))
                por_mes[e["fecha"][:7]] = ars / e["monto"]
    candidatos = [p for p in por_mes if p <= periodo]
    if not candidatos:
        return None, None
    mejor = max(candidatos)
    return por_mes[mejor], mejor


def tc_mes(entries: list, cfg: dict, periodo: str):
    """(tc, origen): origen 'Manual', 'Estimado' o 'Sin dato'."""
    manual = cfg["tc"].get(periodo)
    if manual:
        return float(manual), "Manual"
    tc, _ = tc_estimado(entries, periodo)
    return (tc, "Estimado") if tc else (None, "Sin dato")


def ingresos_mes(entries: list, cfg: dict, periodo: str):
    usd = sum(e["monto"] for e in entries if e["fecha"][:7] == periodo and e["tipo"] == "ingreso"
              and e["concepto"] in cfg["conceptos"] and e["moneda"] == "USD")
    ars = sum(e["monto"] for e in entries if e["fecha"][:7] == periodo and e["tipo"] == "ingreso"
              and e["concepto"] in cfg["conceptos"] and e["moneda"] == "ARS")
    return usd, ars


def estado(entries: list, cfg: dict, hoy: dt.date | None = None) -> dict:
    """Devuelve filas por mes, pagos y los totales de deuda."""
    hoy = hoy or dt.date.today()
    actual = hoy.strftime("%Y-%m")
    pct = float(cfg["porcentaje"]) / 100.0

    filas = []
    for p in periodos(cfg, hoy):
        usd, ars = ingresos_mes(entries, cfg, p)
        tc, tc_origen = tc_mes(entries, cfg, p)
        base = ars + (usd * tc if tc else 0.0)
        if p in cfg["manual"]:
            diezmo, origen = float(cfg["manual"][p]), "Manual"
        elif p in cfg["deuda_inicial"]:
            diezmo, origen = float(cfg["deuda_inicial"][p]), "Confirmado"
        else:
            diezmo, origen = base * pct, ("Estimado" if p == actual else "Calculado")
        filas.append(dict(periodo=p, usd=usd, ars=ars, tc=tc, tc_origen=tc_origen, base=base,
                          diezmo=diezmo, origen=origen, cerrado=p < actual, pagado=0.0, pendiente=diezmo))

    # Pagos desde el corte (ARS directo; USD al TC estimado del mes del pago)
    pagos = []
    for e in sorted(entries, key=lambda x: (x["fecha"], x["id"])):
        if e["concepto"] == "Diezmo" and e["tipo"] == "egreso" and e["fecha"] >= cfg["corte"]:
            if e["moneda"] == "ARS":
                ars_eq, tc_pago = e["monto"], None
            else:
                tc_pago, _ = tc_estimado(entries, e["fecha"][:7])
                ars_eq = e["monto"] * tc_pago if tc_pago else 0.0
            pagos.append(dict(id=e["id"], fecha=e["fecha"], cuenta=e["cuenta"], monto=e["monto"], moneda=e["moneda"],
                              ars_eq=ars_eq, tc=tc_pago, nota=e.get("nota") or ""))
    restante = sum(p["ars_eq"] for p in pagos)
    for f in filas:  # del mes mas viejo al mas nuevo
        aplicado = min(restante, f["diezmo"])
        f["pagado"], f["pendiente"] = aplicado, f["diezmo"] - aplicado
        restante -= aplicado

    cerradas = [f for f in filas if f["cerrado"]]
    en_curso = next((f for f in filas if not f["cerrado"]), None)
    return dict(
        filas=filas, pagos=pagos, pagado_total=sum(p["ars_eq"] for p in pagos),
        deuda=sum(f["pendiente"] for f in cerradas),                      # meses cerrados, ya adeudados
        deuda_confirmada=sum(f["diezmo"] for f in cerradas),
        en_curso=en_curso, actual=actual,
    )
