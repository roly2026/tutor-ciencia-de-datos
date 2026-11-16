"""Preparador del examen final · Introducción a Data Science (Clasificación y Regresión).

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

st.set_page_config(page_title="Preparador EF · Intro a Data Science", page_icon="📊", layout="wide")

SECCIONES = ["📝 Práctica", "💬 Tutor", "📊 Mi progreso"]
CODIGO_RE = re.compile(r"^[A-Z0-9_-]{4,20}$")


# --------------------------------------------------------------------------- #
# Estado
# --------------------------------------------------------------------------- #
def init_estado() -> None:
    for clave, valor in {
        "codigo": None, "id_sesion": None, "n_registro": 0,
        "semilla": random.randint(1, 10**6),
        "chat": {}, "pistas": {}, "resultados": {}, "t0": {},
    }.items():
        st.session_state.setdefault(clave, valor)


# --------------------------------------------------------------------------- #
# Barra lateral: ingreso por código, variante y selección de pregunta
# --------------------------------------------------------------------------- #
def sidebar() -> tuple[Problema, str] | None:
    with st.sidebar:
        st.title("📊 Preparador EF")
        st.caption("Introducción a Data Science · Clasificación y Regresión")

        if st.session_state.codigo is None:
            with st.form("login"):
                codigo = st.text_input("Código de estudiante")
                ingresar = st.form_submit_button("Ingresar", type="primary")
            if ingresar:
                codigo = codigo.strip().upper()
                if not CODIGO_RE.match(codigo):
                    st.error("Ingresa un código válido (4 a 20 caracteres: letras, números, - o _).")
                else:
                    ok, mensaje = bd.verificar_codigo(codigo)
                    if not ok:
                        st.error(mensaje)
                    else:
                        st.session_state.codigo = codigo
                        st.session_state.id_sesion = str(uuid.uuid4())
                        st.session_state.n_registro = 0
                        st.rerun()
            return None

        st.success(f"Código: `{st.session_state.codigo}`")
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.rerun()

        if not secreto("GEMINI_API_KEY"):
            st.error("Falta GEMINI_API_KEY en los secretos.")
        if not bd.disponible():
            st.warning("Supabase no está configurado: tu avance no se guardará.")
        elif st.session_state.get("db_error"):
            st.warning("No se pudo guardar algún dato en Supabase.")

        st.divider()
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

        problemas = obtener_problemas(semilla)
        tema = st.radio("Tema", ["Clasificación", "Regresión"], horizontal=True)
        opciones = [p for p in problemas if p.tema == tema]
        p = st.selectbox("Pregunta", opciones,
                         format_func=lambda x: f"P{x.numero} · {x.dimension}" + (" ★" if x.es_modelo else ""))
        st.caption("★ = pregunta del examen modelo")
        return p, f"{etiqueta}-{p.id}"


# --------------------------------------------------------------------------- #
# Presentación del problema
# --------------------------------------------------------------------------- #
def mostrar_datos(p: Problema) -> None:
    d = p.datos
    if d["tipo"] == "matriz":
        df = pd.DataFrame(
            [[f"VP = {d['vp']}", f"FN = {d['fn']}"], [f"FP = {d['fp']}", f"VN = {d['vn']}"]],
            index=["Real: Acepta (1)", "Real: Rechaza (0)"],
            columns=["Predicción: Acepta (1)", "Predicción: Rechaza (0)"],
        )
    else:
        df = pd.DataFrame({"Valor real (y)": d["real"], "Predicción (ŷ)": d["pred"]},
                          index=[f"Depto {i}" for i in range(1, len(d["real"]) + 1)])
    st.table(df)


def encabezado(p: Problema) -> None:
    st.markdown(f"**Caso {p.caso} · {p.tema}.** {p.contexto}")
    mostrar_datos(p)
    st.subheader(f"Pregunta {p.numero} · {p.dimension}  [{p.puntaje_max:g} pts]")
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

    texto = st.text_area("Tu respuesta", key=f"resp_{clave}", height=220, max_chars=MAX_CARACTERES_RESPUESTA,
                         placeholder="Desarrolla tu respuesta como lo harías en el examen…")
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
            st.caption("Revisa la solución solo después de intentarlo; inténtalo de nuevo con una variante nueva.")


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
    st.subheader("Tu progreso por dimensión")
    df = bd.cargar_intentos(st.session_state.codigo)
    if df.empty:
        st.info("Aún no hay intentos guardados. Evalúa una respuesta en la sección Práctica.")
        return

    df["logro"] = df["puntaje"] / PUNTAJE_MAX * 100
    por_dim = df.groupby("dimension")["logro"].mean().reindex(DIMENSIONES).dropna()
    st.bar_chart(por_dim.round(1), y_label="Logro promedio (%)")

    cruce = (df.pivot_table(index="tema", columns="dimension", values="logro", aggfunc="mean")
             .reindex(columns=DIMENSIONES).round(0))
    st.markdown("**Logro (%) por tema y dimensión**")
    st.dataframe(cruce, use_container_width=True)

    if len(por_dim) > 1:
        st.success(f"Dimensión a reforzar: **{por_dim.idxmin()}** ({por_dim.min():.0f} %).")

    st.markdown("**Últimos intentos**")
    ultimos = df[["fecha_hora_lima", "tema", "dimension", "veredicto", "puntaje", "tiempo_resp_seg"]].head(10)
    st.dataframe(ultimos, use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    init_estado()
    seleccion = sidebar()
    if seleccion is None:
        st.title("Preparador del examen final")
        st.write("Practica **clasificación** y **regresión** en las cinco dimensiones del razonamiento "
                 "cuantitativo: interpretación, representación, cálculo, análisis y argumentación. "
                 "Ingresa con tu código de estudiante para comenzar.")
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
