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
