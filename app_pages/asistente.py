"""Asistente por chat: cargar movimientos o consultar el Diario en lenguaje natural."""
import datetime as dt

import streamlit as st

import diario_store
import reports
from ui import fmt, load_data

st.title("Asistente")
st.caption("Cargá movimientos o preguntá por tus finanzas escribiendo como si le hablaras a alguien")

try:
    api_key = st.secrets.get("ANTHROPIC_API_KEY")
except Exception:
    api_key = None

if not api_key:
    st.info(
        "Para usar el asistente necesitás una API key de Anthropic. "
        "Creá una en [console.anthropic.com](https://console.anthropic.com/settings/keys) "
        "y agregala a `.streamlit/secrets.toml` (local) o a los Secrets de Streamlit Cloud como "
        "`ANTHROPIC_API_KEY = \"...\"`.",
        icon=":material/info:",
    )
    st.stop()

import anthropic  # noqa: E402  (después del st.stop si falta la key)

MODEL = "claude-opus-4-8"

config, diario = load_data()
client = anthropic.Anthropic(api_key=api_key)

conceptos = config["ingresos"] + config["egresos"]

TOOLS = [
    {
        "name": "registrar_movimiento",
        "description": "Carga un movimiento nuevo (ingreso o egreso) en el Diario.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fecha": {
                    "type": "string",
                    "description": "Fecha en formato YYYY-MM-DD. Si el usuario dice 'hoy', 'ayer', etc., calculá la fecha real.",
                },
                "tipo": {"type": "string", "enum": ["ingreso", "egreso"]},
                "concepto": {"type": "string", "enum": conceptos},
                "cuenta": {"type": "string", "enum": config["cuentas"]},
                "moneda": {"type": "string", "enum": ["ARS", "USD"]},
                "monto": {"type": "number", "description": "Monto positivo."},
                "nota": {"type": "string", "description": "Opcional."},
            },
            "required": ["fecha", "tipo", "concepto", "cuenta", "moneda", "monto"],
            "additionalProperties": False,
        },
    },
    {
        "name": "consultar_resumen_mes",
        "description": "Devuelve ingresos y egresos agrupados por concepto para un mes/año dado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "anio": {"type": "integer"},
                "mes": {"type": "integer", "description": "1 a 12"},
            },
            "required": ["anio", "mes"],
            "additionalProperties": False,
        },
    },
    {
        "name": "consultar_saldos",
        "description": "Devuelve el saldo actual de cada cuenta, en ARS y USD.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]

SYSTEM_PROMPT = f"""Sos el asistente de la app de finanzas personales de Iván. Hoy es {dt.date.today().isoformat()}.

Tu trabajo es cargar movimientos en el Diario y responder consultas sobre plata, usando exclusivamente las tools disponibles.
No inventes conceptos ni cuentas que no existan en las listas de las tools (son las únicas válidas).
Si falta un dato imprescindible (por ejemplo el monto), preguntalo antes de llamar a la tool.
Después de cargar un movimiento, confirmá en una frase corta qué quedó registrado.
Respondé siempre en español, corto y directo."""


def _registrar_movimiento(fecha, tipo, concepto, cuenta, moneda, monto, nota=""):
    entry = diario_store.add({
        "fecha": fecha,
        "tipo": tipo,
        "concepto": concepto,
        "cuenta": cuenta,
        "moneda": moneda,
        "monto": float(monto),
        "nota": nota,
    })
    simbolo = "US$" if moneda == "USD" else "$"
    return f"Cargado: {tipo} de {simbolo} {fmt(entry['monto'])} en {concepto} ({cuenta}), {fecha}."


def _consultar_resumen_mes(anio, mes):
    vista = reports.ing_egr_mes(diario_store.load(), int(anio), int(mes))
    partes = []
    for etiqueta, df in (("Ingresos", vista["ingresos"]), ("Egresos", vista["egresos"])):
        if df.empty:
            partes.append(f"{etiqueta}: sin movimientos.")
            continue
        filas = [f"{r.concepto}: $ {fmt(r.ARS)} / US$ {fmt(r.USD)}" for r in df.itertuples()]
        partes.append(f"{etiqueta}:\n" + "\n".join(filas))
    return "\n\n".join(partes)


def _consultar_saldos():
    saldos = reports.saldos_cuentas(diario_store.load(), config["cuentas"])
    if saldos.empty:
        return "No hay saldos cargados todavía."
    filas = [f"{r.cuenta} ({r.moneda}): {fmt(r.saldo)}" for r in saldos.itertuples()]
    return "\n".join(filas)


def _ejecutar_tool(nombre: str, entrada: dict) -> str:
    if nombre == "registrar_movimiento":
        return _registrar_movimiento(**entrada)
    if nombre == "consultar_resumen_mes":
        return _consultar_resumen_mes(**entrada)
    if nombre == "consultar_saldos":
        return _consultar_saldos()
    return f"Tool desconocida: {nombre}"


if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

for msg in st.session_state.chat_messages:
    if msg["role"] not in ("user", "assistant") or not isinstance(msg["content"], str):
        continue
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ej: cargué $5000 en Super hoy, o ¿cuánto tengo en Fiwind Pesos?"):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            messages = list(st.session_state.chat_messages)
            respuesta_final = ""
            for _ in range(6):  # límite de vueltas por seguridad
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=messages,
                )
                textos = [b.text for b in response.content if b.type == "text"]
                if textos:
                    respuesta_final = "\n".join(textos)

                if response.stop_reason != "tool_use":
                    break

                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        resultado = _ejecutar_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": resultado,
                        })
                messages.append({"role": "user", "content": tool_results})

        st.write(respuesta_final or "(sin respuesta)")

    st.session_state.chat_messages.append({"role": "assistant", "content": respuesta_final})
