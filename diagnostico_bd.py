"""Diagnóstico temporal de la conexión a Supabase (usa los mismos secretos y el mismo código que la app).

Cómo usarlo en Streamlit Cloud:
  1) Sube este archivo a la raíz del repositorio (junto a app.py).
  2) App > Settings > General > Main file path = diagnostico_bd.py  y reinicia la app.
  3) Lee el resultado y vuelve a poner  app.py  como archivo principal.
No compartas el enlace mientras esté activo: muestra datos técnicos de la conexión (nunca la contraseña).
"""
from __future__ import annotations

import time

import streamlit as st

st.set_page_config(page_title="Diagnóstico de Supabase", page_icon="🔧")
st.title("Diagnóstico de la conexión a Supabase")
st.caption("Uso temporal. Al terminar, vuelve a poner app.py como archivo principal.")

problemas: list[str] = []


def ok(txt: str) -> None:
    st.success(txt)


def aviso(txt: str) -> None:
    st.warning(txt)
    problemas.append(txt)


def error(txt: str) -> None:
    st.error(txt)
    problemas.append(txt)


# ------------------------------------------------------------------ 1. Secretos
st.subheader("1. Secretos")
try:
    nombres = list(st.secrets.keys())
    ok("Streamlit leyó los secretos. Nombres encontrados: " + ", ".join(sorted(nombres)))
except FileNotFoundError:
    nombres = []
    aviso("No hay archivo de secretos (normal en pruebas locales). En Streamlit Cloud se definen en Settings > Secrets.")
except Exception as e:  # TOML mal escrito
    nombres = []
    error("Streamlit NO pudo leer los secretos, casi seguro por un error de sintaxis TOML "
          "(comillas sin cerrar, o una contraseña con \\ o \" sin escapar). Detalle: " + str(e)[:200])

from config import secreto  # noqa: E402  (después de configurar la página)
import base_datos as bd  # noqa: E402

cred = bd._credenciales()
faltan = [n for n in ("db_host", "db_port", "db_user", "db_password", "db_name") if not secreto(n)]
if faltan:
    error("Faltan estos secretos: " + ", ".join(faltan) + " (se escriben exactamente así, en minúsculas).")
if cred:
    host, user, port, pwd = cred["host"], cred["user"], cred["port"], cred["password"]
    if host.endswith(".pooler.supabase.com"):
        ok("db_host es el pooler de Supabase.")
    elif host.startswith("db.") and host.endswith(".supabase.co"):
        error("db_host es la conexión directa (solo IPv6) y Streamlit Cloud no la alcanza. "
              "Usa el Transaction pooler: Supabase > Connect > Transaction pooler.")
    else:
        aviso("db_host no parece un host de Supabase. Revísalo en Supabase > Connect.")
    if "." in user and user.startswith("postgres."):
        ok("db_user tiene el formato del pooler (postgres.<ref-del-proyecto>).")
    else:
        error("db_user debe ser postgres.<ref-del-proyecto> cuando se usa el pooler.")
    if port == 6543:
        ok("db_port = 6543 (Transaction pooler).")
    else:
        aviso(f"db_port = {port}. Para el Transaction pooler se usa 6543.")
    if pwd != pwd.strip():
        error("db_password tiene espacios al inicio o al final.")
    ok(f"db_password configurada ({len(pwd)} caracteres).")
st.write(f"Códigos habilitados leídos: **{len(bd._codigos_habilitados())}**")

# ------------------------------------------------------------------ 2. Librería
st.subheader("2. Librería psycopg2")
try:
    import psycopg2

    ok("psycopg2 instalado: " + psycopg2.__version__.split(" ")[0])
except Exception as e:
    error("Falta psycopg2: agrega psycopg2-binary a requirements.txt y reinicia. Detalle: " + str(e)[:150])
    psycopg2 = None  # type: ignore

# ------------------------------------------------------------------ 3. Conexión
st.subheader("3. Conexión")
con = None
if cred and psycopg2 is not None:
    t0 = time.time()
    try:
        con = psycopg2.connect(**cred)
        con.autocommit = False
        with con.cursor() as cur:
            cur.execute("select current_user, now() at time zone 'America/Lima'")
            usuario, ahora = cur.fetchone()
        ok(f"Conexión correcta en {time.time() - t0:.1f} s. Usuario: {usuario}. Hora de Lima en el servidor: {ahora:%Y-%m-%d %H:%M}.")
    except Exception as e:
        error("No se pudo conectar: " + bd._explicar(e))
        with st.expander("Mensaje técnico completo"):
            st.code(str(e))
        st.info("Si Supabase muestra el proyecto como pausado, restáuralo desde el panel: los proyectos del plan "
                "gratuito se pausan tras una semana sin uso.")

# ------------------------------------------------------------------ 4. Tablas
st.subheader("4. Tablas y permisos")
if con is not None:
    try:
        with con.cursor() as cur:
            for tabla in ("evaluaciones", "guias_tutor"):
                cur.execute("select to_regclass(%s)", (f"public.{tabla}",))
                if cur.fetchone()[0] is None:
                    error(f"No existe la tabla {tabla}: ejecuta supabase_borrar_y_crear.sql en el SQL Editor de Supabase.")
                else:
                    cur.execute(f"select count(*) from {tabla}")
                    ok(f"Tabla {tabla}: existe y tiene {cur.fetchone()[0]} filas.")
        with con.cursor() as cur:  # prueba de escritura que se revierte
            cur.execute(
                """insert into evaluaciones (codigo, id_sesion, n_registro_sesion, id_pregunta, tema, dimension,
                   veredicto, long_respuesta, enunciado, pedido, respuesta, clave)
                   values ('DIAG', gen_random_uuid(), 1, 'DIAG', 't', 'd', 'Logrado', 0, '-', '-', '-', '-')""")
        ok("Escritura en evaluaciones: correcta (la prueba se revirtió y no dejó ninguna fila).")
    except Exception as e:
        error("Falló la prueba de tablas o de escritura: " + bd._explicar(e))
        with st.expander("Mensaje técnico completo"):
            st.code(str(e))
    finally:
        con.rollback()
        con.close()
else:
    st.write("Se omite porque no hay conexión.")

# ------------------------------------------------------------------ Resultado
st.divider()
if problemas:
    st.error("Se encontraron %d punto(s) por corregir; revisa los avisos en rojo y amarillo de arriba." % len(problemas))
else:
    st.success("Todo correcto: la conexión, las tablas y la escritura funcionan. Vuelve a poner app.py como archivo principal.")
