"""Preparador del examen final · Introducción a Data Science.

Flujo: código de estudiante -> tema -> (dimensión) -> pregunta -> práctica / tutor / progreso.
Temas: Clasificación y Regresión (por dimensión del razonamiento cuantitativo),
       Scikit-learn y Reportes de datos (preguntas teóricas de respuesta escrita).

Ejecutar:  streamlit run app.py
"""
from __future__ import annotations

import random
import re
import time
import uuid

import pandas as pd
import streamlit as st

import base_datos as bd
import tutor
from config import DIMENSIONES, MAX_CARACTERES_RESPUESTA, MAX_PISTAS, PUNTAJE_MAX, secreto
from problemas import Problema, obtener_problemas
from problemas_teoria import TEMA_REPORTES, TEMA_SKLEARN, obtener_teoria

st.set_page_config(page_title="Preparador EF · Intro a Data Science", page_icon="📊", layout="wide")

SECCIONES = ["📝 Práctica", "💬 Tutor", "📊 Mi progreso"]
CODIGO_RE = re.compile(r"^[A-Z0-9_-]{4,20}$")

TEMAS_CUANTI = ["Clasificación", "Regresión"]          # se practican por dimensión
TEMAS_TEORIA = [TEMA_SKLEARN, TEMA_REPORTES]            # preguntas teóricas escritas
TODAS = "Todas las dimensiones"

# Ficha de cada tema para la pantalla de selección
FICHAS = {
    "Clasificación": ("🎯", "Clasificación binaria",
                      "Matriz de confusión, exactitud, precisión, recall y decisiones de negocio (Caso 1: banco)."),
    "Regresión": ("📈", "Regresión",
                  "Errores MAE, RMSE, MAPE, R² y su lectura en el negocio (Caso 2: inmobiliaria)."),
    TEMA_SKLEARN: ("🧰", "Scikit-learn",
                   "Uso del código de modelamiento: particiones, pipelines, validación cruzada, métricas e hiperparámetros."),
    TEMA_REPORTES: ("🗂️", "Presentación de reportes",
                    "Estructura, gráficos, comunicación de métricas, limitaciones y recomendaciones."),
}
DIM_ICONO = {"Representación": "🧩", "Cálculo": "🧮", "Interpretación": "🔍",
             "Análisis": "⚖️", "Argumentación": "🗣️"}


# --------------------------------------------------------------------------- #
# Estado
# --------------------------------------------------------------------------- #
def init_estado() -> None:
    for clave, valor in {
        "codigo": None, "id_sesion": None, "n_registro": 0,
        "semilla": random.randint(1, 10**6), "tema": None,
        "chat": {}, "pistas": {}, "resultados": {}, "t0": {},
    }.items():
        st.session_state.setdefault(clave, valor)


def _es_teoria(tema: str) -> bool:
    return tema in TEMAS_TEORIA


def _resumen(texto: str, n: int = 70) -> str:
    texto = " ".join(texto.split())
    return texto if len(texto) <= n else texto[: n - 1].rstrip() + "…"


# --------------------------------------------------------------------------- #
# Ingreso por código
# --------------------------------------------------------------------------- #
def login_sidebar() -> None:
    with st.sidebar:
        st.title("📊 Preparador EF")
        st.caption("Introducción a Data Science")
        with st.form("login"):
            codigo = st.text_input("Código de estudiante")
            ingresar = st.form_submit_button("Ingresar", type="primary")
        if ingresar:
            codigo = codigo.strip().upper()
            if not CODIGO_RE.match(codigo):
                st.error("Ingresa un código válido (4 a 20 caracteres: letras, números, - o _).")
                return
            ok, mensaje = bd.verificar_codigo(codigo)
            if not ok:
                st.error(mensaje)
                return
            st.session_state.codigo = codigo
            st.session_state.id_sesion = str(uuid.uuid4())
            st.session_state.n_registro = 0
            st.session_state.tema = None
            st.rerun()


def pantalla_bienvenida() -> None:
    st.title("Preparador del examen final")
    st.write("Practica para tu examen final con retroalimentación inmediata basada en la rúbrica del curso.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Temas cuantitativos**\n\n- 🎯 Clasificación binaria\n- 📈 Regresión\n\n"
                    "Elige la dimensión del razonamiento cuantitativo que quieres reforzar: interpretación, "
                    "representación, cálculo, análisis o argumentación.")
    with c2:
        st.markdown("**Temas teóricos**\n\n- 🧰 Scikit-learn para modelamiento\n- 🗂️ Presentación de reportes\n\n"
                    "Responde por escrito preguntas conceptuales como las del examen.")
    st.info("Ingresa con tu código de estudiante en la barra lateral para comenzar.")


# --------------------------------------------------------------------------- #
# Selección de tema (pantalla principal)
# --------------------------------------------------------------------------- #
def pantalla_temas() -> None:
    st.title("¿Qué quieres practicar hoy?")
    st.caption("Elige un tema. Luego podrás escoger la dimensión (en Clasificación y Regresión) y la pregunta.")
    orden = list(FICHAS)
    for fila in (orden[:2], orden[2:]):
        cols = st.columns(2)
        for col, tema in zip(cols, fila):
            icono, titulo, descripcion = FICHAS[tema]
            with col.container(border=True):
                st.markdown(f"### {icono} {titulo}")
                st.write(descripcion)
                kind = "Preguntas por dimensión" if tema in TEMAS_CUANTI else "Preguntas teóricas de desarrollo"
                st.caption(kind)
                if st.button(f"Practicar {titulo.lower()}", key=f"tema_{tema}", type="primary",
                             use_container_width=True):
                    st.session_state.tema = tema
                    st.rerun()


# --------------------------------------------------------------------------- #
# Barra lateral con sesión iniciada: tema, dimensión y pregunta
# --------------------------------------------------------------------------- #
def sidebar() -> tuple[Problema, str] | None:
    with st.sidebar:
        st.title("📊 Preparador EF")
        st.success(f"Código: `{st.session_state.codigo}`")
        c1, c2 = st.columns(2)
        if c1.button("Cerrar sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        if st.session_state.tema is not None and c2.button("↩ Cambiar tema", use_container_width=True):
            st.session_state.tema = None
            st.rerun()

        if not secreto("GEMINI_API_KEY"):
            st.error("Falta GEMINI_API_KEY en los secretos.")
        if not bd.disponible():
            st.warning("Supabase no está configurado: tu avance no se guardará.")
        elif st.session_state.get("db_error"):
            st.warning("No se pudo guardar algún dato en Supabase.")

        tema = st.session_state.tema
        if tema is None:
            return None

        icono, titulo, _ = FICHAS[tema]
        st.divider()
        st.markdown(f"**Tema:** {icono} {titulo}")

        if _es_teoria(tema):
            return _seleccion_teoria(tema)
        return _seleccion_cuantitativa(tema)


def _seleccion_cuantitativa(tema: str) -> tuple[Problema, str] | None:
    modo = st.radio("Datos del problema", ["Examen modelo", "Variante nueva"],
                    help="La variante cambia los números para que practiques el método, no la respuesta.")
    if modo == "Variante nueva":
        if st.button("🔄 Generar otra variante"):
            st.session_state.semilla = random.randint(1, 10**6)
            st.rerun()
        semilla = st.session_state.semilla
        etiqueta = f"var-{semilla}"
    else:
        semilla, etiqueta = None, "modelo"

    dimension = st.radio("Dimensión a practicar", [TODAS] + DIMENSIONES,
                         format_func=lambda d: d if d == TODAS else f"{DIM_ICONO.get(d, '•')} {d}")

    opciones = [p for p in obtener_problemas(semilla) if p.tema == tema]
    if dimension != TODAS:
        opciones = [p for p in opciones if p.dimension == dimension]
    if not opciones:
        st.warning("No hay preguntas para esta selección.")
        return None

    def fmt(p: Problema) -> str:
        base = f"P{p.numero}" + (" ★" if p.es_modelo else "")
        extra = f"{p.dimension}" if dimension == TODAS else _resumen(p.enunciado, 45)
        return f"{base} · {extra}"

    # clave del selectbox ligada a tema+dimensión para que no arrastre una pregunta que ya no existe
    p = st.selectbox(f"Pregunta ({len(opciones)})", opciones, format_func=fmt,
                     key=f"preg_{tema}_{dimension}_{etiqueta}")
    st.caption("★ = pregunta del examen modelo")
    if st.button("🎲 Pregunta al azar", use_container_width=True):
        st.session_state[f"preg_{tema}_{dimension}_{etiqueta}"] = random.choice(opciones)
        st.rerun()
    return p, f"{etiqueta}-{p.id}"


def _seleccion_teoria(tema: str) -> tuple[Problema, str] | None:
    opciones = obtener_teoria(tema)
    p = st.selectbox(f"Pregunta ({len(opciones)})", opciones,
                     format_func=lambda x: f"T{x.numero} · {getattr(x, 'subtema', '') or _resumen(x.enunciado, 40)}",
                     key=f"preg_{tema}")
    st.caption("Preguntas teóricas: responde por escrito, con tus palabras.")
    if st.button("🎲 Pregunta al azar", use_container_width=True):
        st.session_state[f"preg_{tema}"] = random.choice(opciones)
        st.rerun()
    return p, f"teo-{p.id}"


# --------------------------------------------------------------------------- #
# Presentación del problema
# --------------------------------------------------------------------------- #
def mostrar_datos(p: Problema) -> None:
    d = p.datos or {}
    if d.get("tipo") == "matriz":
        df = pd.DataFrame(
            [[f"VP = {d['vp']}", f"FN = {d['fn']}"], [f"FP = {d['fp']}", f"VN = {d['vn']}"]],
            index=["Real: Acepta (1)", "Real: Rechaza (0)"],
            columns=["Predicción: Acepta (1)", "Predicción: Rechaza (0)"],
        )
        st.table(df)
    elif d.get("tipo") == "tabla":
        df = pd.DataFrame({"Valor real (y)": d["real"], "Predicción (ŷ)": d["pred"]},
                          index=[f"Depto {i}" for i in range(1, len(d["real"]) + 1)])
        st.table(df)


def encabezado(p: Problema) -> None:
    if _es_teoria(p.tema):
        sub = getattr(p, "subtema", "")
        st.markdown(f"**{p.tema}**" + (f" · {sub}" if sub else ""))
        st.caption(p.contexto)
    else:
        st.markdown(f"**Caso {p.caso} · {p.tema}.** {p.contexto}")
        mostrar_datos(p)
    with st.container(border=True):
        st.markdown(f"#### Pregunta {p.numero} · {p.dimension}  ·  {p.puntaje_max:g} pts")
        st.write(p.enunciado)


# --------------------------------------------------------------------------- #
# Sección: práctica
# --------------------------------------------------------------------------- #
def _registrar_intento(p: Problema, respuesta: str, segundos: int, veredicto: str,
                       puntaje: float | None, error: str | None) -> None:
    st.session_state.n_registro += 1
    bd.guardar_intento(st.session_state.codigo, st.session_state.id_sesion, st.session_state.n_registro,
                       p, segundos, veredicto, puntaje, respuesta, error)


def seccion_practica(p: Problema, clave: str) -> None:
    encabezado(p)
    st.session_state.t0.setdefault(clave, time.time())

    teoria = _es_teoria(p.tema)
    placeholder = ("Redacta tu respuesta teórica con tus palabras; si ayuda, incluye un fragmento corto de código…"
                   if p.tema == TEMA_SKLEARN else
                   "Redacta tu respuesta como lo harías en el examen…" if teoria else
                   "Desarrolla tu respuesta como lo harías en el examen…")
    texto = st.text_area("Tu respuesta", key=f"resp_{clave}", height=300 if teoria else 220,
                         max_chars=MAX_CARACTERES_RESPUESTA, placeholder=placeholder)
    if st.button("✅ Evaluar mi respuesta", type="primary", key=f"eval_{clave}"):
        respuesta = texto.strip()
        if len(respuesta) < 3:
            st.warning("Escribe tu respuesta antes de evaluarla.")
        else:
            segundos = int(time.time() - st.session_state.t0[clave])  # solo el tiempo del estudiante
            try:
                with st.spinner("Evaluando con la rúbrica…"):
                    evaluacion = tutor.evaluar_respuesta(p, respuesta)
            except tutor.ErrorIA as e:
                _registrar_intento(p, respuesta, segundos, "Error técnico", None, str(e))
                st.error(str(e))
            else:
                _registrar_intento(p, respuesta, segundos, evaluacion["nivel"], evaluacion["puntaje"], None)
                st.session_state.resultados[clave] = evaluacion
            st.session_state.t0[clave] = time.time()

    evaluacion = st.session_state.resultados.get(clave)
    if evaluacion:
        st.divider()
        c1, c2 = st.columns([1, 3])
        c1.metric("Puntaje", f"{evaluacion['puntaje']:g} / {p.puntaje_max:g}", evaluacion["nivel"])
        with c2:
            if evaluacion["aciertos"]:
                st.markdown("**Lo que va bien**\n" + "\n".join(f"- {x}" for x in evaluacion["aciertos"]))
            if evaluacion["errores"]:
                st.markdown("**Para corregir**\n" + "\n".join(f"- {x}" for x in evaluacion["errores"]))
            if evaluacion["sugerencia"]:
                st.info(evaluacion["sugerencia"])
        with st.expander("Ver solución modelo"):
            st.write(p.referencia)
            msg = ("Revisa la solución solo después de intentarlo; vuelve a responder con otras palabras."
                   if teoria else
                   "Revisa la solución solo después de intentarlo; inténtalo de nuevo con una variante nueva.")
            st.caption(msg)


# --------------------------------------------------------------------------- #
# Sección: tutor
# --------------------------------------------------------------------------- #
def _enviar_al_tutor(p: Problema, clave: str, texto: str, nivel: int, es_pista: bool) -> None:
    codigo, id_sesion = st.session_state.codigo, st.session_state.id_sesion
    historial = st.session_state.chat.setdefault(clave, [])
    historial.append({"rol": "estudiante", "texto": texto})
    try:
        with st.spinner("Pensando…"):
            respuesta = tutor.responder_tutor(p, historial, nivel)
    except tutor.ErrorIA as e:
        historial.pop()
        st.error(str(e))
        return
    if es_pista:
        st.session_state.pistas[clave] = nivel
    historial.append({"rol": "tutor", "texto": respuesta})
    bd.guardar_mensaje(codigo, id_sesion, p, "estudiante", texto, nivel)
    bd.guardar_mensaje(codigo, id_sesion, p, "tutor", respuesta, nivel)
    st.rerun()


def seccion_tutor(p: Problema, clave: str) -> None:
    encabezado(p)
    st.divider()
    historial = st.session_state.chat.setdefault(clave, [])
    pistas = st.session_state.pistas.get(clave, 0)

    st.caption(f"Tutor socrático: te guía sin darte la respuesta. Pistas usadas: {pistas}/{MAX_PISTAS}.")
    if not historial:
        st.info("Cuéntame qué parte te cuesta o pide una pista.")
    for m in historial:
        with st.chat_message("user" if m["rol"] == "estudiante" else "assistant"):
            st.markdown(m["texto"])

    if st.button("💡 Dame una pista", disabled=pistas >= MAX_PISTAS, key=f"pista_{clave}"):
        nivel = pistas + 1
        _enviar_al_tutor(p, clave, f"Necesito una pista (nivel {nivel}).", nivel, True)

    mensaje = st.chat_input("Escribe tu duda o tu razonamiento…", key=f"chat_{clave}")
    if mensaje:
        _enviar_al_tutor(p, clave, mensaje, max(1, pistas), False)


# --------------------------------------------------------------------------- #
# Sección: progreso
# --------------------------------------------------------------------------- #
def seccion_progreso() -> None:
    st.subheader("Tu progreso")
    df = bd.cargar_intentos(st.session_state.codigo)
    if df.empty:
        st.info("Aún no hay intentos guardados. Evalúa una respuesta en la sección Práctica.")
        return

    df["logro"] = df["puntaje"] / PUNTAJE_MAX * 100
    validos = df.dropna(subset=["puntaje"])

    m1, m2, m3 = st.columns(3)
    m1.metric("Intentos evaluados", len(validos))
    m2.metric("Logro promedio", f"{validos['logro'].mean():.0f} %" if len(validos) else "—")
    m3.metric("Temas practicados", validos["tema"].nunique() if len(validos) else 0)

    st.markdown("**Logro (%) por tema**")
    por_tema = validos.groupby("tema")["logro"].mean().round(1)
    if len(por_tema):
        st.bar_chart(por_tema, y_label="Logro promedio (%)")

    cuanti = validos[validos["tema"].isin(TEMAS_CUANTI)]
    if not cuanti.empty:
        st.markdown("**Clasificación y Regresión · logro por dimensión**")
        por_dim = cuanti.groupby("dimension")["logro"].mean().reindex(DIMENSIONES).dropna()
        st.bar_chart(por_dim.round(1), y_label="Logro promedio (%)")
        cruce = (cuanti.pivot_table(index="tema", columns="dimension", values="logro", aggfunc="mean")
                 .reindex(columns=DIMENSIONES).round(0))
        st.dataframe(cruce, use_container_width=True)
        if len(por_dim) > 1:
            st.success(f"Dimensión a reforzar: **{por_dim.idxmin()}** ({por_dim.min():.0f} %).")

    teoria = validos[validos["tema"].isin(TEMAS_TEORIA)]
    if not teoria.empty:
        peor = teoria.groupby("tema")["logro"].mean().idxmin()
        st.info(f"Temas teóricos: el de menor logro es **{peor}**.")

    st.markdown("**Últimos intentos**")
    columnas = ["fecha_hora_lima", "tema", "dimension", "veredicto", "puntaje", "tiempo_resp_seg"]
    st.dataframe(df[columnas].head(10), use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    init_estado()

    if st.session_state.codigo is None:
        login_sidebar()
        pantalla_bienvenida()
        return

    seleccion = sidebar()

    # Sin tema elegido: pantalla de selección (el progreso también es accesible desde aquí)
    if st.session_state.tema is None:
        pestanas = st.tabs(["🧭 Elegir tema", "📊 Mi progreso"])
        with pestanas[0]:
            pantalla_temas()
        with pestanas[1]:
            seccion_progreso()
        return

    if seleccion is None:
        st.warning("No hay preguntas disponibles con esta selección.")
        return

    p, clave = seleccion
    seccion = st.radio("Sección", SECCIONES, horizontal=True, label_visibility="collapsed", key="seccion")
    if seccion == SECCIONES[0]:
        seccion_practica(p, clave)
    elif seccion == SECCIONES[1]:
        seccion_tutor(p, clave)
    else:
        seccion_progreso()


main()
