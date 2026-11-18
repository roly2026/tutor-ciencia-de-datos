"""Configuración central: constantes y acceso a secretos."""
from __future__ import annotations

import os
import re

import streamlit as st

DIMENSIONES = ["Interpretación", "Representación", "Cálculo", "Análisis", "Argumentación"]
TEMAS = ["Clasificación", "Regresión"]
MAX_PISTAS = 3
PUNTAJE_MAX = 2.0
MAX_CARACTERES_RESPUESTA = 3000


def secreto(nombre: str, defecto: str | None = None) -> str | None:
    """Lee un secreto de st.secrets (Streamlit Cloud / secrets.toml) o de variables de entorno."""
    try:
        valor = st.secrets[nombre]
        if valor:
            return str(valor)
    except Exception:
        pass
    return os.environ.get(nombre, defecto)


# GEMINI_MODEL admite uno o varios modelos separados por coma, p. ej. "gemini-2.5-flash-lite, gemini-2.5-flash":
# se prueban en orden y, si uno falla (cuota, sobrecarga), se usa el siguiente.


def _lista_modelos(texto: str | None) -> list[str]:
    """'modelo-a, modelo-b' -> ['modelo-a', 'modelo-b'] (el primero se prueba primero; los demás son respaldo)."""
    return [m.strip() for m in re.split(r"[,;\s]+", texto or "") if m.strip()]


MODELOS_GEMINI = _lista_modelos(secreto("GEMINI_MODEL", "gemini-2.5-flash")) or ["gemini-2.5-flash"]
MODELO_GEMINI = MODELOS_GEMINI[0]  # compatibilidad: modelo principal
