"""Preparador del examen final · Introducción a Data Science.

Flujo: código de estudiante -> tema -> (dimensión / área / tipo de gráfico) -> pregunta -> práctica / tutor / progreso.
Temas: Clasificación y Regresión (por dimensión del razonamiento cuantitativo),
       Scikit-learn (código por área) y Reportes de datos (interpretación de gráficos): preguntas de respuesta escrita.

Ejecutar:  streamlit run app.py
"""
from __future__ import annotations

import random
import re
import time
import uuid

import altair as alt
import pandas as pd
import streamlit as st

import base_datos as bd
import tutor
from config import DIMENSIONES, MAX_CARACTERES_RESPUESTA, MAX_PISTAS, PUNTAJE_MAX, secreto
from problemas import Problema, obtener_problemas
from problemas_teoria import TEMA_REPORTES, TEMA_SKLEARN, dimensiones_teoria, obtener_teoria

st.set_page_config(page_title="Preparador EF · Intro a Data Science", page_icon="📊", layout="wide")

SECCIONES = ["📝 Práctica", "💬 Tutor", "📊 Mi progreso"]
CODIGO_RE = re.compile(r"^[A-Z0-9_-]{4,20}$")

TEMAS_CUANTI = ["Clasificación", "Regresión"]          # se practican por dimensión del razonamiento cuantitativo
TEMAS_TEORIA = [TEMA_SKLEARN, TEMA_REPORTES]            # preguntas de respuesta escrita
TODAS = "Todas"

FICHAS = {
    "Clasificación": ("🎯", "Clasificación binaria",
                      "Matriz de confusión, exactitud, precisión, recall y decisiones de negocio (Caso 1: banco)."),
    "Regresión": ("📈", "Regresión",
                  "Errores MAE, RMSE, MAPE, R² y su lectura en el negocio (Caso 2: inmobiliaria)."),
    TEMA_SKLEARN: ("🧰", "Scikit-learn",
                   "Escribe el código de modelamiento en clasificación y regresión: pipelines, métricas, validación cruzada e hiperparámetros."),
    TEMA_REPORTES: ("🗂️", "Presentación de reportes",
                    "Interpreta gráficos de barras simples y dobles, dispersión y cajas, y comunica resultados."),
}
TIPO_PREGUNTA = {
    "Clasificación": "Preguntas por dimensión", "Regresión": "Preguntas por dimensión",
    TEMA_SKLEARN: "Preguntas de código y teoría (por área)", TEMA_REPORTES: "Interpretación de gráficos (por tipo)",
}
ICONOS = {"Representación": "🧩", "Cálculo": "🧮", "Interpretación": "🔍", "Análisis": "⚖️", "Argumentación": "🗣️",
          "Clasificación": "🎯", "Regresión": "📈", "General": "🧭",
          "Barras simples": "📊", "Barras dobles": "📊", "Dispersión": "🔵", "Cajas (boxplot)": "📦",
          "Comunicación del reporte": "📝"}


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


def _nombre_modelo() -> str:
    """Nombre del modelo de IA que evalúa (para registrarlo en la base de datos)."""
    for nombre in ("MODELO", "MODELO_GEMINI", "MODEL", "MODEL_NAME", "GEMINI_MODEL"):
        valor = getattr(tutor, nombre, None)
        if isinstance(valor, str) and valor:
            return valor
    return str(secreto("GEMINI_MODEL") or "gemini")


def _elegir_al_azar(clave_widget: str, opciones: list) -> None:
    """Callback del botón 🎲 (los callbacks sí pueden modificar el estado de un widget ya creado)."""
    st.session_state[clave_widget] = random.choice(opciones)


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
        st.markdown("**Razonamiento cuantitativo**\n\n- 🎯 Clasificación binaria\n- 📈 Regresión\n\n"
                    "Elige la dimensión que quieres reforzar: interpretación, representación, cálculo, análisis o argumentación.")
    with c2:
        st.markdown("**Respuesta escrita**\n\n- 🧰 Scikit-learn: código en clasificación y regresión\n"
                    "- 🗂️ Reportes: interpretación de gráficos (barras, dispersión, cajas)\n\n"
                    "Escribe tu respuesta como en el examen.")
    st.info("Ingresa con tu código de estudiante en la barra lateral para comenzar.")


# --------------------------------------------------------------------------- #
# Selección de tema (pantalla principal)
# --------------------------------------------------------------------------- #
def pantalla_temas() -> None:
    st.title("¿Qué quieres practicar hoy?")
    st.caption("Elige un tema; luego filtra por dimensión, área o tipo de gráfico y escoge la pregunta.")
    orden = list(FICHAS)
    for fila in (orden[:2], orden[2:]):
        cols = st.columns(2)
        for col, tema in zip(cols, fila):
            icono, titulo, descripcion = FICHAS[tema]
            with col.container(border=True):
                st.markdown(f"### {icono} {titulo}")
                st.write(descripcion)
                st.caption(TIPO_PREGUNTA[tema])
                if st.button(f"Practicar {titulo.lower()}", key=f"tema_{tema}", type="primary", use_container_width=True):
                    st.session_state.tema = tema
                    st.rerun()


# --------------------------------------------------------------------------- #
# Barra lateral con sesión iniciada
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
            with st.expander("Detalle técnico"):
                st.code(st.session_state["db_error"])

        tema = st.session_state.tema
        if tema is None:
            return None

        icono, titulo, _ = FICHAS[tema]
        st.divider()
        st.markdown(f"**Tema:** {icono} {titulo}")
        return _seleccion_teoria(tema) if _es_teoria(tema) else _seleccion_cuantitativa(tema)


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
                         format_func=lambda d: d if d == TODAS else f"{ICONOS.get(d, '•')} {d}")
    opciones = [p for p in obtener_problemas(semilla) if p.tema == tema]
    if dimension != TODAS:
        opciones = [p for p in opciones if p.dimension == dimension]
    if not opciones:
        st.warning("No hay preguntas para esta selección.")
        return None

    def fmt(p: Problema) -> str:
        base = f"P{p.numero}" + (" ★" if p.es_modelo else "")
        return f"{base} · {p.dimension if dimension == TODAS else _resumen(p.enunciado, 45)}"

    clave_w = f"preg_{tema}_{dimension}_{etiqueta}"   # ligada a tema+dimensión+variante
    p = st.selectbox(f"Pregunta ({len(opciones)})", opciones, format_func=fmt, key=clave_w)
    st.caption("★ = pregunta del examen modelo")
    st.button("🎲 Pregunta al azar", use_container_width=True, on_click=_elegir_al_azar, args=(clave_w, opciones))
    return p, f"{etiqueta}-{p.id}"


def _seleccion_teoria(tema: str) -> tuple[Problema, str] | None:
    etiqueta_filtro = "Área de uso" if tema == TEMA_SKLEARN else "Tipo de gráfico / contenido"
    dimension = st.radio(etiqueta_filtro, [TODAS] + dimensiones_teoria(tema),
                         format_func=lambda d: d if d == TODAS else f"{ICONOS.get(d, '•')} {d}")
    opciones = obtener_teoria(tema)
    if dimension != TODAS:
        opciones = [p for p in opciones if p.dimension == dimension]
    if not opciones:
        st.warning("No hay preguntas para esta selección.")
        return None

    def fmt(p: Problema) -> str:
        return f"{p.id} · {p.dimension if dimension == TODAS else _resumen(p.enunciado, 45)}"

    clave_w = f"preg_{tema}_{dimension}"
    p = st.selectbox(f"Pregunta ({len(opciones)})", opciones, format_func=fmt, key=clave_w)
    st.caption("Respuesta escrita: desarróllala con tus palabras.")
    st.button("🎲 Pregunta al azar", use_container_width=True, on_click=_elegir_al_azar, args=(clave_w, opciones))
    return p, f"teo-{p.id}"


# --------------------------------------------------------------------------- #
# Presentación del problema
# --------------------------------------------------------------------------- #
def _grafico(d: dict) -> alt.Chart:
    """Dibuja los gráficos de las preguntas de reportes (barras, barras dobles, dispersión y cajas)."""
    tipo, titulo = d["grafico"], d.get("titulo", "")
    xt, yt = d.get("x_titulo", ""), d.get("y_titulo", "")
    if tipo == "barras":
        df = pd.DataFrame({"categoria": d["categorias"], "valor": d["valores"]})
        base = alt.Chart(df).encode(x=alt.X("categoria:N", sort=None, title=xt, axis=alt.Axis(labelAngle=0)),
                                    y=alt.Y("valor:Q", title=yt, scale=alt.Scale(domainMin=0)))
        capas = base.mark_bar() + base.mark_text(dy=-8).encode(text=alt.Text("valor:Q", format=".1f"))
        if d.get("referencia_y") is not None:
            capas += alt.Chart(pd.DataFrame({"y": [d["referencia_y"]]})).mark_rule(strokeDash=[5, 4]).encode(y="y:Q")
        return capas.properties(title=titulo, height=320)
    if tipo == "barras_dobles":
        filas = [{"categoria": c, "serie": s, "valor": v}
                 for s, vals in d["series"].items() for c, v in zip(d["categorias"], vals)]
        df = pd.DataFrame(filas)
        return (alt.Chart(df).mark_bar()
                .encode(x=alt.X("categoria:N", sort=None, title=xt, axis=alt.Axis(labelAngle=0)),
                        xOffset="serie:N",
                        y=alt.Y("valor:Q", title=yt, scale=alt.Scale(domainMin=0)),
                        color=alt.Color("serie:N", title=None),
                        tooltip=["categoria", "serie", "valor"])
                .properties(title=titulo, height=320))
    if tipo == "dispersion":
        df = pd.DataFrame({"x": d["x"], "y": d["y"]})
        capas = (alt.Chart(df).mark_circle(size=90, opacity=0.8)
                 .encode(x=alt.X("x:Q", title=xt, scale=alt.Scale(zero=False)),
                         y=alt.Y("y:Q", title=yt, scale=alt.Scale(zero=False)), tooltip=["x", "y"]))
        if d.get("diagonal"):
            lo, hi = min(min(d["x"]), min(d["y"])), max(max(d["x"]), max(d["y"]))
            capas += (alt.Chart(pd.DataFrame({"x": [lo, hi], "y": [lo, hi]}))
                      .mark_line(strokeDash=[6, 4]).encode(x="x:Q", y="y:Q"))
        return capas.properties(title=titulo, height=340)
    # cajas
    filas = [{"grupo": g, "valor": v} for g, vals in d["grupos"].items() for v in vals]
    df = pd.DataFrame(filas)
    return (alt.Chart(df).mark_boxplot(extent=1.5, size=60)
            .encode(x=alt.X("grupo:N", sort=None, title=xt, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("valor:Q", title=yt, scale=alt.Scale(zero=False)),
                    color=alt.Color("grupo:N", legend=None))
            .properties(title=titulo, height=340))


def mostrar_datos(p: Problema) -> None:
    d = p.datos or {}
    tipo = d.get("tipo")
    if tipo == "matriz":
        df = pd.DataFrame(
            [[f"VP = {d['vp']}", f"FN = {d['fn']}"], [f"FP = {d['fp']}", f"VN = {d['vn']}"]],
            index=["Real: Acepta (1)", "Real: Rechaza (0)"],
            columns=["Predicción: Acepta (1)", "Predicción: Rechaza (0)"],
        )
        st.table(df)
    elif tipo == "tabla":
        df = pd.DataFrame({"Valor real (y)": d["real"], "Predicción (ŷ)": d["pred"]},
                          index=[f"Depto {i}" for i in range(1, len(d["real"]) + 1)])
        st.table(df)
    elif tipo == "grafico":
        st.altair_chart(_grafico(d), use_container_width=True)


def encabezado(p: Problema) -> None:
    if _es_teoria(p.tema):
        st.markdown(f"**{p.tema} · {p.dimension}**")
        st.caption(p.contexto)
        mostrar_datos(p)
    else:
        st.markdown(f"**Caso {p.caso} · {p.tema}.** {p.contexto}")
        mostrar_datos(p)
    with st.container(border=True):
        st.markdown(f"#### Pregunta {p.numero} · {p.dimension}  ·  {p.puntaje_max:g} pts")
        st.write(p.enunciado)


# --------------------------------------------------------------------------- #
# Sección: práctica
# --------------------------------------------------------------------------- #
def _registrar_intento(p: Problema, clave: str, respuesta: str, segundos: int, veredicto: str,
                       puntaje: float | None, error: str | None) -> None:
    st.session_state.n_registro += 1
    bd.guardar_intento(st.session_state.codigo, st.session_state.id_sesion, st.session_state.n_registro,
                       p, segundos, veredicto, puntaje, respuesta, error, clave=clave, modelo=_nombre_modelo())


def seccion_practica(p: Problema, clave: str) -> None:
    encabezado(p)
    st.session_state.t0.setdefault(clave, time.time())

    teoria = _es_teoria(p.tema)
    if p.tema == TEMA_SKLEARN:
        placeholder = "Escribe tu código y/o tu explicación. Puedes usar bloques de código con ``` …"
    elif p.tema == TEMA_REPORTES:
        placeholder = "Interpreta el gráfico con cifras y redacta tu conclusión como en el examen…"
    else:
        placeholder = "Desarrolla tu respuesta como lo harías en el examen…"
    texto = st.text_area("Tu respuesta", key=f"resp_{clave}", height=320 if teoria else 220,
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
                _registrar_intento(p, clave, respuesta, segundos, "Error técnico", None, str(e))
                st.error(str(e))
            else:
                _registrar_intento(p, clave, respuesta, segundos, evaluacion["nivel"], evaluacion["puntaje"], None)
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
            if p.tema == TEMA_SKLEARN and "\n\n" in p.referencia:
                codigo, explicacion = p.referencia.rsplit("\n\n", 1)   # código + párrafo final de explicación
                st.code(codigo, language="python")
                st.write(explicacion)
            else:
                st.write(p.referencia)
            st.caption("Revisa la solución solo después de intentarlo; "
                       + ("vuelve a responder con otras palabras." if teoria
                          else "inténtalo de nuevo con una variante nueva."))


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

    df["logro"] = pd.to_numeric(df["puntaje"], errors="coerce") / PUNTAJE_MAX * 100
    validos = df.dropna(subset=["puntaje"])

    m1, m2, m3 = st.columns(3)
    m1.metric("Intentos evaluados", len(validos))
    m2.metric("Logro promedio", f"{validos['logro'].mean():.0f} %" if len(validos) else "—")
    m3.metric("Temas practicados", validos["tema"].nunique() if len(validos) else 0)

    if len(validos):
        st.markdown("**Logro (%) por tema**")
        st.bar_chart(validos.groupby("tema")["logro"].mean().round(1), y_label="Logro promedio (%)")

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
        st.markdown("**Scikit-learn y Reportes · logro (%) por área o tipo de gráfico**")
        tabla = teoria.pivot_table(index="dimension", columns="tema", values="logro", aggfunc="mean").round(0)
        st.dataframe(tabla, use_container_width=True)

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

    if st.session_state.tema is None:   # sin tema elegido: selección de tema (y progreso)
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
