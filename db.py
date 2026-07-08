"""Almacenamiento en Postgres (Neon) para la versión desplegada.
Si no hay una conexión 'postgres' en secrets, is_configured() devuelve False
y config_store/diario_store siguen usando los archivos locales de siempre.
"""
import json

import streamlit as st
from sqlalchemy import text


def is_configured() -> bool:
    try:
        return "postgres" in st.secrets.get("connections", {})
    except Exception:
        return False


def _conn():
    return st.connection("postgres", type="sql")


def _ensure_table():
    conn = _conn()
    with conn.session as s:
        s.execute(text("CREATE TABLE IF NOT EXISTS app_data (key TEXT PRIMARY KEY, value JSONB NOT NULL)"))
        s.commit()


def load(key: str, default):
    _ensure_table()
    conn = _conn()
    df = conn.query("SELECT value FROM app_data WHERE key = :key", params={"key": key}, ttl=0)
    if df.empty:
        save(key, default)
        return json.loads(json.dumps(default))
    return df.iloc[0]["value"]


def save(key: str, value) -> None:
    _ensure_table()
    conn = _conn()
    with conn.session as s:
        s.execute(
            text(
                "INSERT INTO app_data (key, value) VALUES (:key, :value) "
                "ON CONFLICT (key) DO UPDATE SET value = :value"
            ),
            {"key": key, "value": json.dumps(value)},
        )
        s.commit()
