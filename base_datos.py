"""Conexión a Supabase (PostgreSQL) para guardar el avance de cada estudiante.

Las credenciales NO van en el código (el repositorio es público/compartido): se leen de los secretos de Streamlit
(Settings > Secrets en Streamlit Cloud, o .streamlit/secrets.toml en local):

    db_host = "aws-1-us-east-1.pooler.supabase.com"
    db_port = 6543
    db_user = "postgres.<id-del-proyecto>"
    db_password = "<tu-contraseña>"
    db_name = "postgres"

Requiere `psycopg2-binary` en requirements.txt.
Funciones públicas (las usa app.py): disponible, verificar_codigo, guardar_intento, guardar_mensaje, cargar_intentos.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import streamlit as st

from config import secreto

try:  # la app debe seguir funcionando (sin guardar) si falta la librería
    import psycopg2
    import psycopg2.extras
except ImportError:  # pragma: no cover
    psycopg2 = None

COLUMNAS_INTENTOS = ["id", "fecha_hora_lima", "codigo", "id_sesion", "n_registro_sesion", "tema", "dimension",
                     "tiempo_resp_seg", "veredicto", "puntaje", "long_respuesta", "modelo", "error_tecnico",
                     "enunciado", "pedido", "respuesta", "clave"]
_ESQUEMA = Path(__file__).with_name("supabase_esquema.sql")
_esquema_ok = False  # se activa tras crear/verificar las tablas una vez por proceso


# --------------------------------------------------------------------------- #
# Conexión
# --------------------------------------------------------------------------- #
def _credenciales() -> dict | None:
    host, usuario, clave = secreto("db_host"), secreto("db_user"), secreto("db_password")
    if not (host and usuario and clave):
        return None
    return {
        "host": str(host),
        "port": int(secreto("db_port") or 6543),
        "user": str(usuario),
        "password": str(clave),
        "dbname": str(secreto("db_name") or "postgres"),
        "sslmode": "require",
        "connect_timeout": 8,
    }


def disponible() -> bool:
    """True si hay librería y credenciales para intentar guardar."""
    return psycopg2 is not None and _credenciales() is not None


def _marcar_error(e: Exception) -> None:
    # Solo el tipo y la primera línea: nunca se expone la contraseña ni la cadena de conexión.
    st.session_state["db_error"] = f"{type(e).__name__}: {str(e).splitlines()[0][:160] if str(e) else ''}"


def _ejecutar(sql: str, params: tuple | None = None, *, leer: bool = False):
    """Abre una conexión corta (adecuada para el pooler de Supabase), ejecuta y confirma.

    Devuelve las filas (lista de dicts) si leer=True, True si escribió bien y None si hubo un error.
    """
    credenciales = _credenciales()
    if psycopg2 is None or credenciales is None:
        return None
    conexion = None
    try:
        conexion = psycopg2.connect(**credenciales)
        with conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            filas = [dict(f) for f in cur.fetchall()] if leer else True
        conexion.commit()
        return filas
    except Exception as e:  # noqa: BLE001 - cualquier fallo de red/SQL no debe tumbar la app
        if conexion is not None:
            try:
                conexion.rollback()
            except Exception:  # noqa: BLE001
                pass
        _marcar_error(e)
        return None
    finally:
        if conexion is not None:
            conexion.close()


def _asegurar_esquema() -> None:
    """Crea las tablas si no existen (una vez por proceso). Idempotente."""
    global _esquema_ok
    if _esquema_ok or not disponible():
        return
    if _ESQUEMA.exists() and _ejecutar(_ESQUEMA.read_text(encoding="utf-8")):
        _esquema_ok = True


# --------------------------------------------------------------------------- #
# Acceso por código
# --------------------------------------------------------------------------- #
def _codigos_secretos() -> set[str]:
    """Códigos autorizados definidos en los secretos (`codigos = [...]`). Vacío si no hay lista."""
    bruto = secreto("codigos")
    if not bruto:
        return set()
    if isinstance(bruto, str):          # por si se pegó como texto: "1001,1002" o con saltos de línea
        bruto = re.split(r"[\s,;]+", bruto)
    return {str(c).strip().upper() for c in bruto if str(c).strip()}


def verificar_codigo(codigo: str) -> tuple[bool, str]:
    """Valida el código de estudiante.

    1. Si los secretos traen la lista `codigos`, solo ingresan esos códigos (no depende de la base de datos).
    2. Si no hay lista: usa la tabla codigos_acceso (vacía = cualquier código con formato válido).
    3. Sin lista ni conexión: deja ingresar (el avance simplemente no se guarda).
    """
    autorizados = _codigos_secretos()
    if autorizados:
        if codigo in autorizados:
            return True, ""
        return False, "Código no autorizado. Verifica que esté bien escrito o consulta con tu docente."
    if not disponible():
        return True, ""
    _asegurar_esquema()
    filas = _ejecutar(
        "select (select count(*) from public.codigos_acceso) as total, "
        "(select activo from public.codigos_acceso where codigo = %s) as activo",
        (codigo,), leer=True)
    if not filas:          # error de conexión: no bloquear al estudiante
        return True, ""
    total, activo = filas[0]["total"], filas[0]["activo"]
    if total == 0 or activo:
        return True, ""
    if activo is False:
        return False, "Tu código está desactivado. Consulta con tu docente."
    return False, "Código no autorizado. Verifica que esté bien escrito o consulta con tu docente."


def probar_conexion() -> tuple[bool, str]:
    """Diagnóstico para la barra lateral: intenta conectar, crear las tablas y contar los intentos guardados."""
    global _esquema_ok
    if psycopg2 is None:
        return False, "Falta la librería psycopg2-binary en requirements.txt."
    cred = _credenciales()
    if cred is None:
        return False, "Faltan db_host, db_user o db_password en los secretos."
    st.session_state.pop("db_error", None)
    _esquema_ok = False
    _asegurar_esquema()
    if st.session_state.get("db_error"):
        return False, st.session_state["db_error"]
    filas = _ejecutar("select count(*) as n from public.intentos", leer=True)
    if filas is None:
        return False, st.session_state.get("db_error", "No se pudo leer public.intentos.")
    return True, f"Conectado a {cred['host']} (usuario {cred['user']}). Intentos guardados: {filas[0]['n']}."


# --------------------------------------------------------------------------- #
# Escritura
# --------------------------------------------------------------------------- #
def guardar_intento(codigo: str, id_sesion: str, n_registro: int, p, segundos: int, veredicto: str,
                    puntaje: float | None, respuesta: str, error: str | None,
                    clave: str = "", modelo: str = "") -> None:
    """Guarda una fila en public.intentos (fecha_hora_lima y id los asigna la base de datos)."""
    if not disponible():
        return
    _asegurar_esquema()
    enunciado = "\n".join(x for x in (p.contexto, p.datos_texto) if x)
    ok = _ejecutar(
        "insert into public.intentos (codigo, id_sesion, n_registro_sesion, tema, dimension, tiempo_resp_seg, "
        "veredicto, puntaje, long_respuesta, modelo, error_tecnico, enunciado, pedido, respuesta, clave) "
        "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (codigo, id_sesion, n_registro, p.tema, p.dimension, int(segundos), veredicto, puntaje, len(respuesta),
         modelo or None, error, enunciado, p.enunciado, respuesta, clave))
    if ok:
        st.session_state.pop("db_error", None)


def guardar_mensaje(codigo: str, id_sesion: str, p, rol: str, texto: str, nivel: int) -> None:
    """Guarda un mensaje del chat con el tutor en public.mensajes_tutor."""
    if not disponible():
        return
    _asegurar_esquema()
    _ejecutar(
        "insert into public.mensajes_tutor (codigo, id_sesion, tema, dimension, id_pregunta, rol, texto, nivel_pista) "
        "values (%s,%s,%s,%s,%s,%s,%s,%s)",
        (codigo, id_sesion, p.tema, p.dimension, p.id, rol, texto, int(nivel)))


# --------------------------------------------------------------------------- #
# Lectura (progreso del estudiante)
# --------------------------------------------------------------------------- #
def cargar_intentos(codigo: str) -> pd.DataFrame:
    """Intentos del estudiante, del más reciente al más antiguo (DataFrame vacío si no hay conexión o datos)."""
    vacio = pd.DataFrame(columns=COLUMNAS_INTENTOS)
    if not disponible():
        return vacio
    _asegurar_esquema()
    filas = _ejecutar(
        "select id, fecha_hora_lima, codigo, id_sesion, n_registro_sesion, tema, dimension, tiempo_resp_seg, "
        "veredicto, puntaje::float8 as puntaje, long_respuesta, modelo, error_tecnico, clave "
        "from public.intentos where codigo = %s order by fecha_hora_lima desc, id desc limit 500",
        (codigo,), leer=True)
    if not filas:
        return vacio
    return pd.DataFrame(filas)
