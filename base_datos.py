"""Persistencia en Supabase (PostgreSQL) por conexión directa al pooler.

Secretos que lee (Streamlit > Settings > Secrets):
    db_host, db_port, db_user, db_password, db_name   (también acepta DB_HOST, DB_PORT, ...)
    codigos   lista de códigos de estudiante con acceso (solo ellos pueden ingresar; también se acepta el nombre codigos_habilitados)
Si falta alguno o la conexión falla, la app sigue funcionando sin guardar y muestra el motivo.
"""
from __future__ import annotations

import logging
import os
import re
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
            cur.execute("select to_regclass('public.evaluaciones'), to_regclass('public.guias_tutor')")
            faltan = [n for n, r in zip(("evaluaciones", "guias_tutor"), cur.fetchone()) if r is None]
            if faltan:
                return ("Faltan las tablas " + " y ".join(faltan)
                        + ": ejecuta supabase_schema.sql en el SQL Editor de Supabase.")
        return ""
    except Exception as e:
        return _explicar(e)


# --------------------------------------------------------------------------- #
# Operaciones
# --------------------------------------------------------------------------- #
def _modelo_actual() -> str | None:
    """Modelo que respondió por última vez en esta sesión (lo expone tutor.MODELO_GEMINI)."""
    try:
        import tutor

        return str(getattr(tutor, "MODELO_GEMINI", "") or "") or None
    except Exception:
        return None


def _variante_de(clave: str | None, p: Problema) -> str | None:
    """La app identifica cada pregunta como '<variante>-<id>' (p. ej. 'var-123-P17' o 'modelo-P04')."""
    if not clave:
        return None
    sufijo = f"-{p.id}"
    return (clave[: -len(sufijo)] if clave.endswith(sufijo) else clave) or "modelo"


def _codigos_habilitados() -> set[str]:
    """Códigos con acceso, desde el secreto `codigos` (o `codigos_habilitados`): lista TOML o texto separado por comas/saltos de línea."""
    valor = None
    for nombre in ("codigos", "codigos_habilitados", "CODIGOS", "CODIGOS_HABILITADOS"):
        try:
            valor = st.secrets[nombre]
        except Exception:
            valor = os.environ.get(nombre)
        if valor:
            break
    if not valor:
        return set()
    if isinstance(valor, str):
        items = re.split(r"[,;\s]+", valor)
    else:
        try:
            items = [str(x) for x in valor]
        except TypeError:
            items = [str(valor)]
    return {i.strip().strip("\"'").upper() for i in items if i and i.strip()}


def verificar_codigo(codigo: str) -> tuple[bool, str]:
    """Solo deja ingresar a los códigos listados en el secreto `codigos`.

    Si el secreto no existe o está vacío, nadie ingresa (así un error de configuración no abre el acceso).
    """
    habilitados = _codigos_habilitados()
    if not habilitados:
        return False, "El acceso aún no está configurado (faltan los códigos habilitados). Avisa a tu docente."
    if codigo.strip().upper() in habilitados:
        return True, ""
    return False, "Código no habilitado. Revisa que esté bien escrito o consulta con tu docente."


# ---- Tabla 1: evaluaciones (respuestas del estudiante) ---------------------- #
def guardar_intento(codigo: str, id_sesion: str, n_registro: int, p: Problema, tiempo_seg: int,
                    veredicto: str, puntaje: float | None, respuesta: str,
                    error_tecnico: str | None = None, clave: str | None = None,
                    modelo: str | None = None) -> bool:
    """Inserta una fila en `evaluaciones`. `fecha_hora_lima` la fija la base de datos (America/Lima).

    `clave` es la etiqueta interna de la pregunta en la app ('<variante>-<id>'): de ahí sale `variante`.
    La columna `clave` de la tabla guarda, en cambio, la solución de referencia.
    """
    if not disponible():
        return False
    try:
        with _conexion() as con, con.cursor() as cur:
            cur.execute(
                """insert into evaluaciones
                   (codigo, id_sesion, n_registro_sesion, id_pregunta, variante, tema, dimension,
                    tiempo_resp_seg, veredicto, puntaje, puntaje_max, long_respuesta, modelo, error_tecnico,
                    enunciado, pedido, respuesta, clave)
                   values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (codigo, id_sesion, n_registro, p.id, _variante_de(clave, p) or "modelo", p.tema, p.dimension,
                 tiempo_seg, veredicto, puntaje, p.puntaje_max, len(respuesta), modelo or _modelo_actual(),
                 error_tecnico[:1000] if error_tecnico else None,
                 f"{p.contexto}\n{getattr(p, 'datos_texto', '')}".strip(), p.enunciado, respuesta, p.referencia),
            )
        return True
    except Exception as e:
        _registrar_error(e)
        return False


# ---- Tabla 2: guias_tutor (ayuda que recibe el estudiante) ------------------ #
def guardar_mensaje(codigo: str, id_sesion: str, p: Problema, rol: str, contenido: str, nivel_pista: int,
                    clave: str | None = None, modelo: str | None = None) -> bool:
    """Registra UNA fila por interacción con el tutor.

    La app llama primero con rol='estudiante' (se guarda en memoria) y luego con rol='tutor':
    en ese momento se inserta la fila completa en `guias_tutor` con la consulta y la guía.
    """
    if not disponible():
        return False
    if rol == "estudiante":
        st.session_state["_consulta_pendiente"] = {"texto": contenido, "nivel": nivel_pista, "clave": clave}
        return True

    pendiente = st.session_state.pop("_consulta_pendiente", None) or {}
    consulta = pendiente.get("texto") or ""
    tipo = "pista" if consulta.lower().startswith("necesito una pista") else "consulta"
    variante = _variante_de(clave or pendiente.get("clave"), p)
    try:
        with _conexion() as con, con.cursor() as cur:
            cur.execute(
                """insert into guias_tutor
                   (codigo, id_sesion, n_registro_sesion, id_pregunta, variante, tema, dimension,
                    tipo, nivel_pista, modelo, long_guia, consulta_estudiante, guia_tutor)
                   values (%s, %s,
                           (select coalesce(max(n_registro_sesion), 0) + 1 from guias_tutor where id_sesion = %s),
                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (codigo, id_sesion, id_sesion, p.id, variante, p.tema, p.dimension,
                 tipo, pendiente.get("nivel", nivel_pista), modelo or _modelo_actual(),
                 len(contenido), consulta, contenido),
            )
        return True
    except Exception as e:
        _registrar_error(e)
        return False


# ---- Lectura para "Mi progreso" ---------------------------------------------- #
def cargar_intentos(codigo: str) -> pd.DataFrame:
    """Evaluaciones del estudiante (excluye las que fallaron por error técnico)."""
    if not disponible():
        return pd.DataFrame()
    try:
        import psycopg2.extras

        with _conexion() as con, con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("select * from evaluaciones where codigo = %s order by id desc limit 500", (codigo,))
            df = pd.DataFrame(cur.fetchall())
    except Exception as e:
        _registrar_error(e)
        return pd.DataFrame()
    if df.empty:
        return df
    df["puntaje"] = pd.to_numeric(df["puntaje"], errors="coerce")
    return df.dropna(subset=["puntaje"])
