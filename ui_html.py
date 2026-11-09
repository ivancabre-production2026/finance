"""Componentes HTML del Resumen. Los estilos viven en assets/style.css (clases .fp-*)."""
from html import escape

from ui import fmt_money

# (fondo, texto) para el avatar de cada cuenta
_AVATARES = [
    ("#FDE8D3", "#B45309"),
    ("#DDF3E4", "#15803D"),
    ("#DBE8FC", "#1D4ED8"),
    ("#EADFFB", "#6D28D9"),
    ("#FCE1E7", "#BE123C"),
    ("#D8F0F4", "#0E7490"),
]


def hero(moneda: str, nombre: str, total: float, disponible: float, invertido: float, delta: float | None) -> str:
    icono = "paid" if moneda == "ARS" else "account_balance_wallet"
    clase = "ars" if moneda == "ARS" else "usd"
    if delta is None:
        linea_delta = ""
    else:
        signo = "▲ +" if delta >= 0 else "▼ −"
        css = "up" if delta >= 0 else "down"
        linea_delta = (
            f'<div class="fp-delta"><span class="{css}">{signo}{escape(fmt_money(abs(delta), moneda))}</span>'
            f" vs. mes anterior</div>"
        )
    return f"""
<div class="fp-hero">
  <div class="fp-hero-top">
    <div class="fp-ico {clase}"><span>{icono}</span></div>
    <div>
      <div class="fp-hero-label">Patrimonio en {escape(nombre.lower())}</div>
      <div class="fp-hero-value">{escape(fmt_money(total, moneda))}</div>
      {linea_delta}
    </div>
  </div>
  <div class="fp-sep"></div>
  <div class="fp-split">
    <div><div class="fp-k">Disponible</div><div class="fp-v">{escape(fmt_money(disponible, moneda))}</div></div>
    <div class="fp-vsep"></div>
    <div><div class="fp-k">Invertido</div><div class="fp-v">{escape(fmt_money(invertido, moneda))}</div></div>
  </div>
</div>
"""


def titulo_seccion(titulo: str, subtitulo: str = "") -> str:
    sub = f'<div class="fp-sec-sub">{escape(subtitulo)}</div>' if subtitulo else ""
    return f'<div class="fp-sec-title">{escape(titulo)}</div>{sub}'


def _celda_monto(valor: float, moneda: str, total: bool = False) -> str:
    clases = "r"
    if total:
        clases += " tot"
    elif valor == 0:
        clases += " zero"
    return f'<td class="{clases}">{escape(fmt_money(valor, moneda))}</td>'


def tabla_cuentas(filas: list) -> str:
    """filas: lista de dicts con cuenta_base, moneda, disponible, invertido, total."""
    if not filas:
        return '<div class="fp-vacio">Ninguna cuenta coincide con la búsqueda.</div>'
    cuerpo = []
    for f in filas:
        nombre = f["cuenta_base"]
        bg, fg = _AVATARES[sum(map(ord, nombre)) % len(_AVATARES)]
        pill = "ars" if f["moneda"] == "ARS" else "usd"
        cuerpo.append(
            "<tr>"
            f'<td><div class="fp-acc"><span class="fp-av" style="background:{bg};color:{fg}">{escape(nombre[:1].upper())}</span>'
            f"{escape(nombre)}</div></td>"
            f'<td><span class="fp-pill {pill}">{escape(f["moneda"])}</span></td>'
            + _celda_monto(f["disponible"], f["moneda"])
            + _celda_monto(f["invertido"], f["moneda"])
            + _celda_monto(f["total"], f["moneda"], total=True)
            + "</tr>"
        )
    return (
        '<table class="fp-table"><thead><tr>'
        '<th>Cuenta</th><th>Moneda</th><th class="r">Disponible</th><th class="r">Invertido</th><th class="r">Saldo total</th>'
        "</tr></thead><tbody>" + "".join(cuerpo) + "</tbody></table>"
    )


def distribucion(items: list) -> str:
    """items: lista de (moneda, nombre, disponible, invertido)."""
    filas = []
    for moneda, nombre, disp, inv in items:
        d, i = max(disp, 0.0), max(inv, 0.0)
        t = d + i
        if t <= 0:
            continue
        pd_, pi_ = d / t * 100, i / t * 100
        etiqueta_d = escape(fmt_money(disp, moneda)) if pd_ >= 16 else ""
        etiqueta_i = escape(fmt_money(inv, moneda)) if pi_ >= 16 else ""
        filas.append(
            '<div class="fp-dist-row">'
            f'<div class="fp-dist-name"><b>{escape(nombre)}</b><span>{escape(fmt_money(disp + inv, moneda))}</span></div>'
            '<div class="fp-bar">'
            f'<div class="fp-seg disp" style="width:{pd_:.2f}%" title="Disponible {escape(fmt_money(disp, moneda))}">{etiqueta_d}</div>'
            f'<div class="fp-seg inv" style="width:{pi_:.2f}%" title="Invertido {escape(fmt_money(inv, moneda))}">{etiqueta_i}</div>'
            "</div></div>"
        )
    leyenda = (
        '<div class="fp-legend"><span><i style="background:#A9D9B5"></i>Disponible</span>'
        '<span><i style="background:#0B5D3B"></i>Invertido</span></div>'
    )
    cabecera = f'<div class="fp-dist-head"><div class="fp-sec-title">Distribución del patrimonio</div>{leyenda}</div>'
    return cabecera + "".join(filas)


# ---------------------------------------------------------------- Movimientos
def kpi_movimientos(moneda: str, nombre: str, ingresos: float, egresos: float) -> str:
    icono = "paid" if moneda == "ARS" else "account_balance_wallet"
    clase = "ars" if moneda == "ARS" else "usd"
    return f"""
<div class="fp-hero">
  <div class="fp-hero-top">
    <div class="fp-ico {clase}"><span>{icono}</span></div>
    <div>
      <div class="fp-hero-label">{escape(nombre)} ({moneda})</div>
      <div class="fp-delta">Movimientos del mes</div>
    </div>
  </div>
  <div class="fp-sep"></div>
  <div class="fp-split">
    <div><div class="fp-k">Ingresos</div><div class="fp-big pos">{escape(fmt_money(ingresos, moneda))}</div></div>
    <div class="fp-vsep"></div>
    <div><div class="fp-k">Egresos</div><div class="fp-big neg">{escape(fmt_money(egresos, moneda))}</div></div>
  </div>
</div>
"""


def tarjeta_fijos(titulo: str, filas: list, palabra_ok: str, palabra_pend: str) -> str:
    """filas: dicts con concepto, ARS, USD, pagado. Pendientes primero."""
    pend = [f for f in filas if not f["pagado"]]
    ok = [f for f in filas if f["pagado"]]
    if not filas:
        cuerpo = '<div class="fp-vacio">No configuraste ninguno todavía (se hace desde Configuración).</div>'
        resumen = ""
    else:
        def celda_monto(f: dict) -> str:
            partes = []
            if f["ARS"] > 0:
                partes.append(escape(fmt_money(f["ARS"], "ARS")))
            if f["USD"] > 0:
                partes.append(escape(fmt_money(f["USD"], "USD")))
            if not partes:
                return '<td class="r zero nw">—</td>'
            return '<td class="r nw">' + "<br>".join(partes) + "</td>"

        trs = []
        for f in pend + ok:
            pill = (
                f'<span class="fp-pill ok">{escape(palabra_ok)}</span>' if f["pagado"]
                else f'<span class="fp-pill pend">{escape(palabra_pend)}</span>'
            )
            trs.append(
                f'<tr><td class="b">{escape(f["concepto"])}</td>{celda_monto(f)}<td class="nw">{pill}</td></tr>'
            )
        cuerpo = (
            '<table class="fp-table"><thead><tr><th>Concepto</th><th class="r">Monto</th><th>Estado</th></tr></thead>'
            "<tbody>" + "".join(trs) + "</tbody></table>"
        )
        resumen = (
            f'<span class="fp-pill pend">{len(pend)} {escape(palabra_pend.lower())}{"s" if len(pend) != 1 else ""}</span>'
            if pend else '<span class="fp-pill ok">Todo al día</span>'
        )
    return (
        f'<div class="fp-card"><div class="fp-card-head"><div class="fp-sec-title">{escape(titulo)}</div>{resumen}</div>{cuerpo}</div>'
    )


def tarjeta_conceptos(titulo: str, filas: list, tipo: str) -> str:
    """filas: dicts con concepto, ARS, USD. tipo: 'ing' o 'egr' (color de la barra)."""
    if not filas:
        return f'<div class="fp-card"><div class="fp-sec-title">{escape(titulo)}</div><div class="fp-vacio">Sin movimientos este mes.</div></div>'
    filas = sorted(filas, key=lambda f: (f["ARS"], f["USD"]), reverse=True)
    max_ars = max((f["ARS"] for f in filas), default=0.0)
    max_usd = max((f["USD"] for f in filas), default=0.0)
    items = []
    for f in filas:
        if f["ARS"] > 0 and max_ars > 0:
            frac = f["ARS"] / max_ars
        elif max_usd > 0:
            frac = f["USD"] / max_usd
        else:
            frac = 0.0
        montos = ""
        if f["ARS"] > 0:
            montos += escape(fmt_money(f["ARS"], "ARS"))
        if f["USD"] > 0:
            linea = escape(fmt_money(f["USD"], "USD"))
            montos += f"<small>{linea}</small>" if f["ARS"] > 0 else linea
        items.append(
            '<div class="fp-row">'
            f'<div class="fp-row-name">{escape(f["concepto"])}</div>'
            f'<div class="fp-row-bar {tipo}"><i style="width:{max(frac * 100, 2):.1f}%"></i></div>'
            f'<div class="fp-row-amt">{montos}</div></div>'
        )
    return f'<div class="fp-card"><div class="fp-card-head"><div class="fp-sec-title">{escape(titulo)}</div></div>{"".join(items)}</div>'


# --------------------------------------------------------------------- Diario
def tabla_movimientos(rows: list) -> str:
    """rows: dicts con id, fecha (AAAA-MM-DD), tipo, concepto, cuenta, moneda, monto, nota."""
    if not rows:
        return '<div class="fp-vacio">No hay movimientos que coincidan.</div>'
    trs = []
    for r in rows:
        f = r["fecha"]
        fecha = f"{f[8:10]}/{f[5:7]}/{f[:4]}"
        es_ing = r["tipo"] == "ingreso"
        signo = "+" if es_ing else "−"
        monto = f'{signo} {fmt_money(r["monto"], r["moneda"])}'
        pill = '<span class="fp-pill ok">Ingreso</span>' if es_ing else '<span class="fp-pill egr">Egreso</span>'
        if r.get("sin_saldo"):
            pill += ' <span class="fp-pill pend" title="Cuenta como gasto del mes, pero todavía no descontó saldo">Devengado</span>'
        nota_completa = (r.get("nota") or "").strip()
        trs.append(
            "<tr>"
            f'<td class="muted">{fecha}</td>'
            f'<td class="b">{escape(r["concepto"])}</td>'
            f'<td>{escape(r["cuenta"])}</td>'
            f"<td>{pill}</td>"
            f'<td class="r tot {"pos" if es_ing else "neg"}">{escape(monto)}</td>'
            f'<td class="muted nota"><div title="{escape(nota_completa)}">{escape(nota_completa)}</div></td>'
            f'<td class="muted r">#{r["id"]}</td>'
            "</tr>"
        )
    return (
        '<div class="fp-scroll"><table class="fp-table fp-mov"><thead><tr>'
        '<th>Fecha</th><th>Concepto</th><th>Cuenta</th><th>Tipo</th><th class="r">Monto</th><th>Nota</th><th class="r">ID</th>'
        "</tr></thead><tbody>" + "".join(trs) + "</tbody></table></div>"
    )
