"""Configuración central: constantes y acceso a secretos."""
from __future__ import annotations

import os

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


# Verifica el nombre vigente del modelo en la documentación de Gemini y cámbialo aquí
# o con el secreto GEMINI_MODEL sin tocar el código.
MODELO_GEMINI = secreto("GEMINI_MODEL", "gemini-2.5-flash")
