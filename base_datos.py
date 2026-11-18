"""Persistencia en Supabase (PostgreSQL) por conexión directa al pooler.

Secretos que lee (Streamlit > Settings > Secrets):
    db_host, db_port, db_user, db_password, db_name   (también acepta DB_HOST, DB_PORT, ...)
Si falta alguno o la conexión falla, la app sigue funcionando sin guardar y muestra el motivo.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager

import pandas as pd
import streamlit as st

from config import secreto
from problemas import Problema

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Conexión
# --------------------------------------------------------------------------- #
def _param(*nombres: str, defecto: str | None = None) -> str | None:
    for n in nombres:
        valor = secreto(n)
        if valor:
            return str(valor).strip()
    return defecto


def _credenciales() -> dict | None:
    host = _param("db_host", "DB_HOST")
    user = _param("db_user", "DB_USER")
    password = _param("db_password", "DB_PASSWORD")
    if not (host and user and password):
        return None
    return {
        "host": host,
        "port": int(_param("db_port", "DB_PORT", defecto="6543")),
        "user": user,
        "password": password,
        "dbname": _param("db_name", "DB_NAME", defecto="postgres"),
        "sslmode": _param("db_sslmode", "DB_SSLMODE", defecto="require"),
        "connect_timeout": 8,
    }


def disponible() -> bool:
    """True si los secretos de conexión están configurados (no prueba la red)."""
    return _credenciales() is not None


@contextmanager
def _conexion():
    """Conexión corta: commit al salir bien, rollback si hay error, y siempre se cierra."""
    import psycopg2

    cred = _credenciales()
    if cred is None:
        raise RuntimeError("Faltan los secretos db_host, db_user y db_password.")
    con = psycopg2.connect(**cred)
    try:
        with con:
            yield con
    finally:
        con.close()


def _registrar_error(e: Exception) -> None:
    log.warning("Error de base de datos: %s", e)
    st.session_state["db_error"] = _explicar(e)


def _explicar(e: Exception) -> str:
    """Traduce los errores típicos a una indicación concreta."""
    msg = str(e)
    bajo = msg.lower()
    if isinstance(e, ModuleNotFoundError) or "psycopg2" in bajo and "no module" in bajo:
        return "Falta la librería psycopg2: agrega `psycopg2-binary` a requirements.txt."
    if "tenant or user not found" in bajo:
        return "El pooler no reconoce el usuario: db_user debe ser 'postgres.<ref-del-proyecto>'."
    if "password authentication failed" in bajo:
        return "Usuario o contraseña incorrectos (db_user / db_password)."
    if "timeout" in bajo or "could not translate host" in bajo or "connection refused" in bajo:
        return "No se pudo alcanzar el servidor: revisa db_host y db_port (pooler: puerto 6543)."
    if "does not exist" in bajo and "relation" in bajo:
        return "Falta crear las tablas: ejecuta supabase_schema.sql en el SQL Editor de Supabase."
    return msg.strip()[:300]


@st.cache_data(ttl=120, show_spinner=False)
def verificar_conexion() -> str:
    """'' si todo funciona; si no, el motivo en español (para mostrarlo en la barra lateral)."""
    if not disponible():
        return "Faltan los secretos db_host, db_user y db_password."
    try:
        with _conexion() as con, con.cursor() as cur:
            cur.execute("select to_regclass('public.intentos')")
            if cur.fetchone()[0] is None:
                return "Falta crear las tablas: ejecuta supabase_schema.sql en el SQL Editor de Supabase."
        return ""
    except Exception as e:
        return _explicar(e)


# --------------------------------------------------------------------------- #
# Operaciones
# --------------------------------------------------------------------------- #
def verificar_codigo(codigo: str) -> tuple[bool, str]:
    """Si `codigos_habilitados` tiene filas, solo deja ingresar a esos códigos; si está vacía, acepta cualquiera."""
    if not disponible():
        return True, ""
    try:
        with _conexion() as con, con.cursor() as cur:
            cur.execute("select count(*) from codigos_habilitados")
            if cur.fetchone()[0] == 0:
                return True, ""
            cur.execute("select 1 from codigos_habilitados where codigo = %s", (codigo,))
            if cur.fetchone():
                return True, ""
        return False, "Código no habilitado. Revisa que esté bien escrito o consulta con tu docente."
    except Exception as e:  # p. ej. la tabla aún no existe: no bloquear el ingreso
        _registrar_error(e)
        return True, ""


def guardar_intento(codigo: str, id_sesion: str, n_registro: int, p: Problema, tiempo_seg: int,
                    veredicto: str, puntaje: float | None, respuesta: str,
                    error_tecnico: str | None = None, clave: str | None = None,
                    modelo: str | None = None) -> bool:
    """Inserta una fila en `intentos`. `fecha_hora_lima` la fija la base de datos (America/Lima).

    La columna `clave` guarda la solución de referencia de la pregunta; el argumento `clave`
    (la etiqueta interna de la app) se acepta por compatibilidad pero no se almacena.
    """
    if not disponible():
        return False
    try:
        with _conexion() as con, con.cursor() as cur:
            cur.execute(
                """insert into intentos
                   (codigo, id_sesion, n_registro_sesion, tema, dimension, tiempo_resp_seg, veredicto,
                    puntaje, long_respuesta, modelo, error_tecnico, enunciado, pedido, respuesta, clave)
                   values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (codigo, id_sesion, n_registro, p.tema, p.dimension, tiempo_seg, veredicto,
                 puntaje, len(respuesta), modelo, error_tecnico[:1000] if error_tecnico else None,
                 f"{p.contexto}\n{getattr(p, 'datos_texto', '')}".strip(), p.enunciado, respuesta, p.referencia),
            )
        return True
    except Exception as e:
        _registrar_error(e)
        return False


def guardar_mensaje(codigo: str, id_sesion: str, p: Problema, rol: str, contenido: str, nivel_pista: int) -> bool:
    if not disponible():
        return False
    try:
        with _conexion() as con, con.cursor() as cur:
            cur.execute(
                """insert into mensajes (codigo, id_sesion, tema, dimension, rol, contenido, nivel_pista)
                   values (%s, %s, %s, %s, %s, %s, %s)""",
                (codigo, id_sesion, p.tema, p.dimension, rol, contenido, nivel_pista),
            )
        return True
    except Exception as e:
        _registrar_error(e)
        return False


def cargar_intentos(codigo: str) -> pd.DataFrame:
    """Intentos evaluados del estudiante (excluye los que fallaron por error técnico)."""
    if not disponible():
        return pd.DataFrame()
    try:
        import psycopg2.extras

        with _conexion() as con, con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("select * from intentos where codigo = %s order by id desc limit 500", (codigo,))
            df = pd.DataFrame(cur.fetchall())
    except Exception as e:
        _registrar_error(e)
        return pd.DataFrame()
    if df.empty:
        return df
    df["puntaje"] = pd.to_numeric(df["puntaje"], errors="coerce")
    return df.dropna(subset=["puntaje"])
