"""Persistencia en Supabase. Si falla o no está configurada, la app sigue funcionando sin guardar."""
from __future__ import annotations

import logging

import pandas as pd
import streamlit as st

from config import MODELO_GEMINI, secreto
from problemas import Problema

log = logging.getLogger(__name__)


@st.cache_resource(show_spinner=False)
def _cliente():
    url, clave = secreto("SUPABASE_URL"), secreto("SUPABASE_KEY")
    if not url or not clave:
        return None
    try:
        from supabase import create_client

        return create_client(url, clave)
    except Exception as e:
        log.warning("No se pudo crear el cliente de Supabase: %s", e)
        return None


def disponible() -> bool:
    return _cliente() is not None


def _registrar_error(e: Exception) -> None:
    log.warning("Error de Supabase: %s", e)
    st.session_state["db_error"] = str(e)


def verificar_codigo(codigo: str) -> tuple[bool, str]:
    """Si `codigos_habilitados` tiene filas, solo deja ingresar a esos códigos; si está vacía, acepta cualquiera."""
    cl = _cliente()
    if cl is None:
        return True, ""
    try:
        total = cl.table("codigos_habilitados").select("codigo", count="exact").limit(1).execute()
        if not total.count:
            return True, ""
        r = cl.table("codigos_habilitados").select("codigo").eq("codigo", codigo).limit(1).execute()
        if r.data:
            return True, ""
        return False, "Código no habilitado. Revisa que esté bien escrito o consulta con tu docente."
    except Exception as e:  # p. ej. la tabla aún no existe: no bloquear el ingreso
        _registrar_error(e)
        return True, ""


def guardar_intento(codigo: str, id_sesion: str, n_registro: int, p: Problema, tiempo_seg: int,
                    veredicto: str, puntaje: float | None, respuesta: str,
                    error_tecnico: str | None = None) -> bool:
    """Inserta una fila en `intentos`. `fecha_hora_lima` la fija la base de datos (America/Lima)."""
    cl = _cliente()
    if cl is None:
        return False
    try:
        cl.table("intentos").insert({
            "codigo": codigo,
            "id_sesion": id_sesion,
            "n_registro_sesion": n_registro,
            "tema": p.tema,
            "dimension": p.dimension,
            "tiempo_resp_seg": tiempo_seg,
            "veredicto": veredicto,
            "puntaje": puntaje,
            "long_respuesta": len(respuesta),
            "modelo": MODELO_GEMINI,
            "error_tecnico": error_tecnico[:1000] if error_tecnico else None,
            "enunciado": f"{p.contexto}\n{p.datos_texto}",
            "pedido": p.enunciado,
            "respuesta": respuesta,
            "clave": p.referencia,
        }).execute()
        return True
    except Exception as e:
        _registrar_error(e)
        return False


def guardar_mensaje(codigo: str, id_sesion: str, p: Problema, rol: str, contenido: str, nivel_pista: int) -> bool:
    cl = _cliente()
    if cl is None:
        return False
    try:
        cl.table("mensajes").insert({
            "codigo": codigo,
            "id_sesion": id_sesion,
            "tema": p.tema,
            "dimension": p.dimension,
            "rol": rol,
            "contenido": contenido,
            "nivel_pista": nivel_pista,
        }).execute()
        return True
    except Exception as e:
        _registrar_error(e)
        return False


def cargar_intentos(codigo: str) -> pd.DataFrame:
    """Intentos evaluados del estudiante (excluye los que fallaron por error técnico)."""
    cl = _cliente()
    if cl is None:
        return pd.DataFrame()
    try:
        r = (cl.table("intentos").select("*").eq("codigo", codigo)
             .order("id", desc=True).limit(500).execute())
        df = pd.DataFrame(r.data)
    except Exception as e:
        _registrar_error(e)
        return pd.DataFrame()
    if df.empty:
        return df
    df["puntaje"] = pd.to_numeric(df["puntaje"], errors="coerce")
    return df.dropna(subset=["puntaje"])
