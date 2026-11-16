"""Banco de problemas del examen final (Caso 1: clasificación, Caso 2: regresión).

Cada tema tiene 15 preguntas (3 por dimensión del razonamiento cuantitativo): las 5 del examen
modelo (P1-P10, marcadas con es_modelo) más 10 de práctica (P11-P30). Las del examen modelo son:
    P1/P6  Representación   (modelar el problema, tipo de variable, preprocesamiento)
    P2/P7  Cálculo          (métricas)
    P3/P8  Interpretación   (qué significa el valor en el contexto)
    P4/P9  Análisis         (trade-offs, límites de la métrica, alternativas)
    P5/P10 Argumentación    (comunicar y recomendar)

Los números NUNCA los calcula la IA: se calculan aquí en Python y se pasan a Gemini
como referencia verificada. Con `semilla=None` se usan los datos exactos del examen
modelo; con una semilla entera se genera una variante con otros números.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class Problema:
    id: str
    caso: int
    tema: str
    dimension: str
    numero: int
    contexto: str
    enunciado: str
    puntaje_max: float
    referencia: str
    criterios: list[str]
    datos: dict = field(default_factory=dict)
    datos_texto: str = ""
    es_modelo: bool = False  # True = pregunta del examen modelo


# --------------------------------------------------------------------------- #
# Datos del examen modelo
# --------------------------------------------------------------------------- #
DATOS_C1_MODELO = {"vp": 20, "fn": 10, "fp": 40, "vn": 130}
DATOS_C2_MODELO = {"real": [150, 200, 120, 300, 250], "pred": [145, 210, 118, 280, 255]}

CONTEXTO_C1 = (
    "Un banco realiza campañas telefónicas para ofrecer un préstamo personal. Se entrena un "
    "modelo de Random Forest para predecir si un cliente aceptará el préstamo (1) o no (0). "
    "Las variables incluyen Edad, Nivel Educativo (Primaria, Secundaria, Universitaria), "
    "Ingresos Anuales y Deuda Actual. Se evalúa con 200 clientes, obteniendo la siguiente matriz:"
)
CONTEXTO_C2 = (
    "Una inmobiliaria desea predecir el precio de venta de departamentos (en miles de USD). "
    "Utiliza un modelo de Regresión Lineal Múltiple con variables como Metros Cuadrados, "
    "Número de Habitaciones y Distrito (Norte, Sur, Centro). Se evalúa el modelo con 5 "
    "departamentos de prueba:"
)


# --------------------------------------------------------------------------- #
# Métricas (única fuente de verdad numérica)
# --------------------------------------------------------------------------- #
def metricas_clasificacion(vp: int, fn: int, fp: int, vn: int) -> dict:
    n = vp + fn + fp + vn
    precision = vp / (vp + fp) if (vp + fp) else 0.0
    recall = vp / (vp + fn) if (vp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "n": n,
        "exactitud": (vp + vn) / n,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "prevalencia": (vp + fn) / n,
        "base": max(vp + fn, fp + vn) / n,  # exactitud de predecir siempre la clase mayoritaria
    }


def metricas_regresion(real: list[float], pred: list[float]) -> dict:
    n = len(real)
    abs_err = [abs(r - p) for r, p in zip(real, pred)]
    mae = sum(abs_err) / n
    rmse = (sum((r - p) ** 2 for r, p in zip(real, pred)) / n) ** 0.5
    mape = sum(e / r for e, r in zip(abs_err, real)) / n
    media = sum(real) / n
    ss_res = sum((r - p) ** 2 for r, p in zip(real, pred))
    ss_tot = sum((r - media) ** 2 for r in real)
    return {
        "n": n,
        "abs_err": abs_err,
        "suma_err": sum(abs_err),
        "mae": mae,
        "rmse": rmse,
        "mse": ss_res / n,
        "ss_res": ss_res,
        "ss_tot": ss_tot,
        "mape": mape,
        "r2": 1 - ss_res / ss_tot if ss_tot else 0.0,
        "min_real": min(real),
        "max_real": max(real),
        "media_real": media,
    }


def _fmt(x: float) -> str:
    """Formatea sin ceros innecesarios (8.4, 20, 3.33)."""
    return f"{x:.2f}".rstrip("0").rstrip(".")


# --------------------------------------------------------------------------- #
# Generadores de variantes
# --------------------------------------------------------------------------- #
def datos_caso1(semilla: int | None) -> dict:
    if semilla is None:
        return dict(DATOS_C1_MODELO)
    rng = random.Random(f"c1-{semilla}")
    positivos = rng.randint(24, 50)
    vp = rng.randint(int(0.4 * positivos), int(0.85 * positivos))
    fn = positivos - vp
    fp = rng.randint(15, 60)
    vn = 200 - positivos - fp
    return {"vp": vp, "fn": fn, "fp": fp, "vn": vn}


def datos_caso2(semilla: int | None) -> dict:
    if semilla is None:
        return {k: list(v) for k, v in DATOS_C2_MODELO.items()}
    rng = random.Random(f"c2-{semilla}")
    for _ in range(100):
        real = [rng.randrange(120, 321, 10) for _ in range(5)]
        pred = [r + rng.choice([-1, 1]) * rng.randint(2, 25) for r in real]
        # Evita variantes degeneradas (precios muy parecidos o R² bajo con solo 5 casos)
        if max(real) - min(real) >= 120 and metricas_regresion(real, pred)["r2"] >= 0.85:
            break
    return {"real": real, "pred": pred}


# --------------------------------------------------------------------------- #
# Construcción de las preguntas
# --------------------------------------------------------------------------- #
def _problemas_caso1(semilla: int | None) -> list[Problema]:
    d = datos_caso1(semilla)
    vp, fn, fp, vn = d["vp"], d["fn"], d["fp"], d["vn"]
    m = metricas_clasificacion(**d)
    n = m["n"]
    datos = {"tipo": "matriz", **d}
    datos_texto = _texto_c1(d, n)
    comunes = dict(caso=1, tema="Clasificación", contexto=CONTEXTO_C1, datos=datos,
                   datos_texto=datos_texto, puntaje_max=2.0)

    exactitud, precision, recall = m["exactitud"], m["precision"], m["recall"]
    frase_base = (
        f"Además, la exactitud ({exactitud:.1%}) "
        f"{'es inferior a' if exactitud < m['base'] else 'supera a'} la línea base de predecir siempre "
        f"la clase mayoritaria ({m['base']:.1%}): con clases desbalanceadas la exactitud engaña."
    )

    return [
        Problema(
            id="P01", numero=1, dimension="Representación",
            enunciado=('Identifique la variable objetivo, el tipo de problema y qué técnica de '
                       'preprocesamiento aplicaría a la variable "Nivel Educativo". Justifique.'),
            referencia=(
                "Variable objetivo: aceptación del préstamo (1 = acepta, 0 = no acepta). "
                "Tipo de problema: clasificación binaria supervisada. "
                'Preprocesamiento de "Nivel Educativo": codificación ordinal (Primaria=0, Secundaria=1, '
                "Universitaria=2), porque es una variable categórica con orden natural y el modelo "
                "requiere entradas numéricas; la codificación ordinal conserva ese orden. One-hot también "
                "es aceptable si se justifica, aunque pierde la información de orden."),
            criterios=[
                "(0.5) Identifica correctamente la variable objetivo: aceptación del préstamo (0/1).",
                "(0.5) Identifica el tipo de problema: clasificación binaria supervisada.",
                "(0.5) Propone una técnica adecuada: codificación ordinal (o one-hot justificada).",
                "(0.5) Justifica: variable ordinal/categórica, el orden aporta información, el modelo necesita números.",
            ], **comunes),
        Problema(
            id="P02", numero=2, dimension="Cálculo",
            enunciado="Calcule la Exactitud, Precisión y Recall.",
            referencia=(
                f"Exactitud = (VP+VN)/N = ({vp}+{vn})/{n} = {exactitud:.3f} ({exactitud:.1%}). "
                f"Precisión = VP/(VP+FP) = {vp}/({vp}+{fp}) = {precision:.3f} ({precision:.1%}). "
                f"Recall = VP/(VP+FN) = {vp}/({vp}+{fn}) = {recall:.3f} ({recall:.1%})."),
            criterios=[
                "(0.5) Plantea correctamente las tres fórmulas con VP, VN, FP, FN.",
                f"(0.5) Exactitud correcta ({exactitud:.3f}).",
                f"(0.5) Precisión correcta ({precision:.3f}).",
                f"(0.5) Recall correcto ({recall:.3f}).",
            ], **comunes),
        Problema(
            id="P03", numero=3, dimension="Interpretación",
            enunciado=("Interprete el valor de la Precisión obtenida y qué significa en términos de "
                       "costos para el banco."),
            referencia=(
                f"La precisión de {precision:.1%} indica que, de los {vp + fp} clientes a los que el modelo "
                f"predice 'acepta', solo {vp} aceptan realmente; los otros {fp} son falsos positivos. "
                f"Es decir, de cada 100 llamadas guiadas por el modelo, unas {round(precision * 100)} terminan "
                f"en préstamo y {100 - round(precision * 100)} son llamadas improductivas. Costo para el banco: "
                "tiempo de asesores, costo operativo de llamadas y desgaste/molestia de clientes; una "
                "precisión baja encarece el costo por préstamo colocado."),
            criterios=[
                "(0.5) Lectura correcta: proporción de predicciones 'acepta' que realmente aceptan.",
                "(0.5) Usa los números del caso (de cada 100 llamadas..., o VP vs FP).",
                "(0.5) Vincula los falsos positivos con llamadas desperdiciadas / costo operativo.",
                "(0.5) Consecuencia de negocio explícita (tiempo de asesores, costo por préstamo, desgaste del cliente).",
            ], **comunes),
        Problema(
            id="P04", numero=4, dimension="Análisis",
            enunciado=("El gerente de marketing quiere maximizar la cantidad de préstamos otorgados "
                       "(Recall) sin importar cuántas llamadas haga. ¿Es este modelo el adecuado? Analice "
                       "el trade-off entre Precisión y Recall en este contexto."),
            referencia=(
                f"El recall actual es {recall:.1%}: el modelo deja de detectar {fn} de {vp + fn} clientes que sí "
                "aceptarían, así que no maximiza el recall tal como está. Precisión y recall se mueven en "
                "sentido contrario al variar el umbral de decisión: bajar el umbral (p. ej. de 0.5 a 0.3) "
                "aumenta el recall pero también los falsos positivos, reduciendo la precisión. En el extremo, "
                f"llamar a todos da recall = 100% y precisión = {m['prevalencia']:.1%} (la prevalencia). "
                "Como el gerente prioriza recall sin importar el número de llamadas, conviene ajustar el "
                "umbral (revisando la curva precisión-recall) y comparar el costo por llamada con la "
                "ganancia por préstamo. " + frase_base),
            criterios=[
                f"(0.5) Reconoce que el recall actual ({recall:.1%}) no es máximo y que hay {fn} falsos negativos (clientes perdidos).",
                "(0.5) Explica el trade-off: al bajar el umbral sube el recall y baja la precisión (más FP).",
                "(0.5) Relaciona con costos/beneficios: costo por llamada vs ganancia por préstamo (caso extremo: llamar a todos).",
                "(0.5) Concluye con una recomendación justificada sobre si el modelo es adecuado (p. ej. ajustando el umbral).",
            ], **comunes),
        Problema(
            id="P05", numero=5, dimension="Argumentación",
            enunciado=("Redacte un correo breve (3-4 líneas) al Gerente de Marketing explicando los "
                       "resultados y sugiriendo una acción."),
            referencia=(
                "Ejemplo de respuesta válida: «Estimado Gerente: el modelo identifica correctamente "
                f"{recall:.0%} de los clientes que sí aceptarían el préstamo, pero solo {precision:.0%} de las "
                f"llamadas que sugiere terminan en aceptación ({fp} llamadas improductivas de {vp + fp}). "
                "Recomiendo usar el modelo para priorizar la lista de llamadas y ajustar el umbral de decisión "
                "según el costo por llamada y la ganancia por préstamo. Puedo preparar una simulación con "
                "distintos umbrales para decidir.»"),
            criterios=[
                "(0.5) Formato de correo breve (3-4 líneas), tono ejecutivo y cordial.",
                "(0.5) Resume los resultados clave (recall y precisión) en lenguaje no técnico.",
                "(0.5) Explica la implicancia para el negocio (clientes perdidos / llamadas improductivas).",
                "(0.5) Sugiere una acción concreta y coherente con los resultados.",
            ], **comunes),
    ]


def _problemas_caso2(semilla: int | None) -> list[Problema]:
    d = datos_caso2(semilla)
    real, pred = d["real"], d["pred"]
    m = metricas_regresion(real, pred)
    datos = {"tipo": "tabla", **d}
    datos_texto = _texto_c2(real, pred)
    comunes = dict(caso=2, tema="Regresión", contexto=CONTEXTO_C2, datos=datos,
                   datos_texto=datos_texto, puntaje_max=2.0)

    mae = m["mae"]
    errores = ", ".join(_fmt(e) for e in m["abs_err"])
    sumandos = " + ".join(_fmt(e) for e in m["abs_err"])
    rel_media = mae / m["media_real"]
    i_max = max(range(len(real)), key=lambda i: m["abs_err"][i])
    err_max, real_max = m["abs_err"][i_max], real[i_max]

    return [
        Problema(
            id="P06", numero=6, dimension="Representación",
            enunciado=('Identifique la variable objetivo y el tipo de problema. ¿Qué técnica de '
                       'preprocesamiento aplicaría a la variable "Distrito"?'),
            referencia=(
                "Variable objetivo: precio de venta del departamento (miles de USD), variable numérica continua. "
                "Tipo de problema: regresión supervisada. 'Distrito' (Norte, Sur, Centro) es categórica nominal "
                "(sin orden), por lo que se aplica codificación one-hot / variables dummy (idealmente k-1 "
                "dummies para evitar multicolinealidad perfecta en la regresión lineal). Una codificación "
                "ordinal impondría un orden artificial entre distritos."),
            criterios=[
                "(0.5) Variable objetivo correcta: precio de venta.",
                "(0.5) Tipo de problema: regresión (objetivo continuo), supervisada.",
                "(0.5) Técnica adecuada: one-hot / variables dummy.",
                "(0.5) Justifica: variable nominal sin orden; ordinal impondría un orden falso; (bonus conceptual) k-1 dummies.",
            ], **comunes),
        Problema(
            id="P07", numero=7, dimension="Cálculo",
            enunciado="Calcule el MAE (Error Absoluto Medio) del modelo.",
            referencia=(
                f"MAE = (1/n)·Σ|y − ŷ|. Errores absolutos: {errores}. "
                f"Suma = {sumandos} = {_fmt(m['suma_err'])}. "
                f"MAE = {_fmt(m['suma_err'])}/{m['n']} = {_fmt(mae)} miles de USD."),
            criterios=[
                "(0.5) Plantea correctamente la fórmula del MAE (promedio de |y − ŷ|).",
                f"(0.5) Errores absolutos por departamento correctos ({errores}).",
                f"(0.5) Suma de errores correcta ({_fmt(m['suma_err'])}).",
                f"(0.5) MAE final correcto ({_fmt(mae)}) con unidades (miles de USD).",
            ], **comunes),
        Problema(
            id="P08", numero=8, dimension="Interpretación",
            enunciado=("Interprete el valor del MAE obtenido en el contexto del negocio inmobiliario, "
                       f"sabiendo que los precios reales oscilan entre {m['min_real']} y {m['max_real']} "
                       "miles de USD."),
            referencia=(
                f"El MAE de {_fmt(mae)} significa que, en promedio, la predicción se equivoca por "
                f"{_fmt(mae)} mil USD (≈ ${mae * 1000:,.0f}), sin importar si es por exceso o por defecto. "
                f"Frente a un precio medio de {_fmt(m['media_real'])} mil, equivale a ≈ {rel_media:.1%} de error "
                "relativo, lo que suele considerarse razonable para una estimación referencial. El juicio final "
                "depende de la tolerancia del negocio. El MAE trata todos los errores por igual y no indica la "
                "dirección del error."),
            criterios=[
                f"(0.5) Interpreta el MAE como error promedio de {_fmt(mae)} mil USD (en unidades del precio).",
                f"(0.5) Lo compara con el rango/precio típico (≈ {rel_media:.1%} del precio medio).",
                "(0.5) Emite un juicio de negocio justificado (aceptable o no según la tolerancia).",
                "(0.5) Usa la unidad correcta (miles de USD) y/o señala que el MAE no distingue sobre/subestimación.",
            ], **comunes),
        Problema(
            id="P09", numero=9, dimension="Análisis",
            enunciado=("¿Por qué no se utiliza la Exactitud (Accuracy) en este caso? ¿Qué otras métricas de "
                       "regresión podría revisar la inmobiliaria?"),
            referencia=(
                "La exactitud mide la proporción de clases acertadas y solo tiene sentido con variable objetivo "
                "categórica. Con un precio continuo, acertar el valor exacto es casi imposible y no mide qué "
                "tan cerca estuvo la predicción. Otras métricas: MSE y RMSE (penalizan más los errores "
                f"grandes; aquí RMSE = {_fmt(m['rmse'])}), R² (proporción de varianza explicada; aquí {m['r2']:.2f}), "
                f"MAPE (error porcentual; aquí {m['mape']:.1%}), y la mediana del error absoluto (robusta a atípicos)."),
            criterios=[
                "(0.5) Explica que la exactitud requiere clases discretas y el precio es una variable continua.",
                "(0.5) Argumenta que coincidir exactamente casi nunca ocurre / no mide cercanía del error.",
                "(0.5) Menciona al menos dos métricas de regresión (MSE, RMSE, R², MAPE, mediana del error...).",
                "(0.5) Explica qué aporta al menos una de ellas (p. ej. RMSE penaliza errores grandes, R² varianza explicada).",
            ], **comunes),
        Problema(
            id="P10", numero=10, dimension="Argumentación",
            enunciado=("Redacte una conclusión breve (2-3 líneas) para el Gerente de Ventas sobre la "
                       "utilidad del modelo."),
            referencia=(
                "Ejemplo de respuesta válida: «El modelo estima el precio con un error promedio de "
                f"{_fmt(mae)} mil USD (≈ {rel_media:.0%} del precio medio), por lo que es útil como referencia "
                "para fijar precios y priorizar propiedades. El mayor error se dio en el departamento de "
                f"{real_max} mil (error de {_fmt(err_max)}), y la evaluación usó solo {m['n']} casos; recomiendo "
                "validarlo con más datos antes de usarlo como única base de decisión.»"),
            criterios=[
                "(0.5) Redacción breve (2-3 líneas), en lenguaje para un gerente de ventas.",
                "(0.5) Cita el MAE y su magnitud relativa al precio.",
                "(0.5) Valora la utilidad del modelo (estimación referencial, apoyo a la decisión).",
                "(0.5) Incluye una limitación o cautela (pocos casos de prueba, errores mayores en ciertos precios, validar).",
            ], **comunes),
    ]


# --------------------------------------------------------------------------- #
# Preguntas de práctica adicionales (P11-P30): mismos casos y mismos datos
# --------------------------------------------------------------------------- #
COSTO_LLAMADA = 8          # S/ por llamada (preguntas P17)
GANANCIA_PRESTAMO = 150    # S/ de ganancia por préstamo aceptado (preguntas P17)
ORDEN_DIMENSIONES = ["Representación", "Cálculo", "Interpretación", "Análisis", "Argumentación"]
IDS_MODELO = {f"P{i:02d}" for i in range(1, 11)}


def _texto_c1(d: dict, n: int) -> str:
    return (
        f"Matriz de confusión (n={n}): VP={d['vp']}, FN={d['fn']}, FP={d['fp']}, VN={d['vn']}. "
        "Filas = valor real (Acepta/Rechaza); columnas = predicción (Acepta/Rechaza)."
    )


def _texto_c2(real: list, pred: list) -> str:
    return ("Departamentos de prueba (valor real y predicción, miles de USD): "
            + "; ".join(f"real={r}, predicción={p}" for r, p in zip(real, pred)) + ".")


def _sig(x: float) -> str:
    return f"{x:+g}"


def _extra_caso1(semilla: int | None) -> list[Problema]:
    d = datos_caso1(semilla)
    vp, fn, fp, vn = d["vp"], d["fn"], d["fp"], d["vn"]
    m = metricas_clasificacion(**d)
    n = m["n"]
    pos, neg = vp + fn, fp + vn
    precision, recall, exactitud, f1, prev = m["precision"], m["recall"], m["exactitud"], m["f1"], m["prevalencia"]
    esp, fpr = vn / neg, fp / neg
    triv = neg / n                           # exactitud de un clasificador que siempre predice "Rechaza"
    reduccion = 1 - (vp + fp) / n            # llamadas ahorradas al filtrar con el modelo
    c, g = COSTO_LLAMADA, GANANCIA_PRESTAMO
    ga = vp * g - (vp + fp) * c              # (a) llamar solo a los que el modelo predice "acepta"
    gb = pos * g - n * c                     # (b) llamar a todos
    equilibrio = c / g
    tasa_desc = fn / (fn + vn)               # tasa de aceptación entre los clientes que el modelo descarta

    if gb > ga:
        mejor = "llamar a todos (b)"
        decision = (f"Conviene llamar a todos (b): {gb:,.0f} > {ga:,.0f}. El modelo descarta {fn + vn} clientes y {fn} de ellos "
                    f"habrían aceptado: se pierden {fn * g:,.0f} de ingresos para ahorrar solo {(fn + vn) * c:,.0f} en llamadas.")
    elif ga > gb:
        mejor = "filtrar con el modelo (a)"
        decision = (f"Conviene filtrar con el modelo (a): {ga:,.0f} > {gb:,.0f}. Ahorra {(fn + vn) * c:,.0f} en llamadas a "
                    f"clientes descartados y solo renuncia a {fn * g:,.0f} de ingresos.")
    else:
        mejor = "cualquiera de las dos (empate)"
        decision = f"Ambas estrategias dejan la misma ganancia neta ({ga:,.0f})."
    texto_equilibrio = (
        f"Punto de equilibrio: una llamada es rentable si la probabilidad de aceptación supera costo/ganancia = {c}/{g} = "
        f"{equilibrio:.1%}. Entre los clientes que el modelo descarta la tasa de aceptación es {fn}/{fn + vn} = {tasa_desc:.1%}, "
        f"{'superior' if tasa_desc > equilibrio else 'inferior'} a ese umbral.")

    if fp > fn:
        mas_frec = f"los falsos positivos ({fp} frente a {fn})"
        sesgo = "El modelo tiende a ser optimista: prefiere llamar de más antes que dejar de llamar."
    elif fn > fp:
        mas_frec = f"los falsos negativos ({fn} frente a {fp})"
        sesgo = "El modelo tiende a ser conservador: deja de llamar a clientes que sí aceptarían."
    else:
        mas_frec = f"ambos errores por igual ({fp} cada uno)"
        sesgo = "El modelo no muestra un sesgo claro hacia un tipo de error."

    if exactitud <= triv:
        comp = f"Incluso es inferior a esa línea base ({exactitud:.1%} < {triv:.1%}): no mejora a un modelo que nunca llama a nadie."
    else:
        comp = (f"El modelo supera esa línea base ({exactitud:.1%} frente a {triv:.1%}), pero la exactitud sigue sin mostrar "
                "cuántos interesados se pierden ni cuántas llamadas se desperdician.")

    datos = {"tipo": "matriz", **d}
    comunes = dict(caso=1, tema="Clasificación", contexto=CONTEXTO_C1, datos=datos,
                   datos_texto=_texto_c1(d, n), puntaje_max=2.0)

    return [
        Problema(
            id="P11", numero=11, dimension="Representación",
            enunciado=("Clasifique cada variable predictora (Edad, Nivel Educativo, Ingresos Anuales y Deuda Actual) según su "
                       "tipo y señale cuáles requieren codificación antes de entrenar el modelo. Justifique."),
            referencia=(
                "Edad: numérica (discreta si se mide en años enteros; también se acepta continua). Nivel Educativo: categórica "
                "ordinal (Primaria < Secundaria < Universitaria). Ingresos Anuales y Deuda Actual: numéricas continuas. Solo Nivel "
                "Educativo requiere codificación (p. ej. ordinal 0/1/2) porque el modelo necesita entradas numéricas y las demás "
                "ya lo son. Random Forest se basa en divisiones de árboles, por lo que no necesita escalar las variables "
                "numéricas, a diferencia de modelos basados en distancias (k-NN) o en gradiente."),
            criterios=[
                "(0.5) Clasifica Edad como numérica (discreta o continua, ambas aceptables).",
                "(0.5) Clasifica Nivel Educativo como categórica ordinal.",
                "(0.5) Clasifica Ingresos Anuales y Deuda Actual como numéricas continuas.",
                "(0.5) Señala que solo Nivel Educativo requiere codificación y lo justifica (el modelo necesita números).",
            ], **comunes),
        Problema(
            id="P12", numero=12, dimension="Representación",
            enunciado=("Un cliente nuevo tiene 35 años, nivel educativo Universitaria, ingresos anuales de S/ 48000 y deuda actual "
                       "de S/ 5000. Represéntelo como el vector de entrada que recibiría el modelo (indique cómo codificó Nivel "
                       "Educativo) e indique en qué forma entrega su salida el modelo."),
            referencia=(
                "Con codificación ordinal (Primaria=0, Secundaria=1, Universitaria=2) y el orden Edad, Nivel Educativo, Ingresos, "
                "Deuda: x = [35, 2, 48000, 5000]. Con one-hot sería x = [35, 0, 0, 1, 48000, 5000] (dummies Primaria, Secundaria, "
                "Universitaria). La variable objetivo (acepta/no acepta) no forma parte del vector. La salida es la clase predicha "
                "ŷ ∈ {0, 1} (por votación de los árboles), o la probabilidad de aceptar en [0, 1] que se compara con un umbral."),
            criterios=[
                "(0.5) Construye un vector de entrada con las 4 variables en un orden consistente.",
                "(0.5) Codifica Nivel Educativo de forma coherente (ordinal Universitaria=2 o one-hot) y lo explicita.",
                "(0.5) Conserva los valores 35, 48000 y 5000 y no incluye la variable objetivo en el vector.",
                "(0.5) Indica la salida del modelo: clase 0/1 (o probabilidad entre 0 y 1 de aceptar).",
            ], **comunes),
        Problema(
            id="P13", numero=13, dimension="Cálculo",
            enunciado="Calcule la Especificidad y la Tasa de Falsos Positivos (FPR) del modelo e indique qué relación hay entre ambas.",
            referencia=(
                f"Especificidad = VN/(VN+FP) = {vn}/({vn}+{fp}) = {esp:.3f} ({esp:.1%}). "
                f"FPR = FP/(FP+VN) = {fp}/({fp}+{vn}) = {fpr:.3f} ({fpr:.1%}). "
                "Relación: FPR = 1 − Especificidad (ambas suman 1)."),
            criterios=[
                "(0.5) Plantea correctamente la fórmula de la Especificidad con VN y FP.",
                f"(0.5) Especificidad correcta ({esp:.3f}).",
                f"(0.5) FPR correcta ({fpr:.3f}).",
                "(0.5) Indica la relación FPR = 1 − Especificidad.",
            ], **comunes),
        Problema(
            id="P14", numero=14, dimension="Cálculo",
            enunciado=("Calcule el F1-score del modelo y la exactitud que tendría un clasificador que siempre predice "
                       "'Rechaza' (0)."),
            referencia=(
                f"F1 = 2·Precisión·Recall/(Precisión+Recall) = 2·{precision:.3f}·{recall:.3f}/({precision:.3f}+{recall:.3f}) "
                f"= {f1:.3f}. Un clasificador que siempre predice 'Rechaza' acierta solo a los negativos reales: "
                f"exactitud = {neg}/{n} = {triv:.3f} ({triv:.1%})."),
            criterios=[
                "(0.5) Plantea el F1 como media armónica de Precisión y Recall.",
                f"(0.5) F1 correcto ({f1:.3f}).",
                f"(0.5) Reconoce que el clasificador 'siempre Rechaza' solo acierta los {neg} negativos reales.",
                f"(0.5) Exactitud del clasificador trivial correcta ({triv:.3f}).",
            ], **comunes),
        Problema(
            id="P15", numero=15, dimension="Interpretación",
            enunciado=("Interprete el valor del Recall obtenido y explique qué significa, en términos de costos, un falso negativo "
                       "para el banco."),
            referencia=(
                f"El recall de {recall:.1%} indica que, de los {pos} clientes que sí aceptarían el préstamo, el modelo detecta "
                f"{vp} (unos {round(recall * 100)} de cada 100) y deja pasar {fn}. Un falso negativo es un cliente que habría "
                "aceptado pero a quien el modelo descarta: no se le llama y el banco pierde un préstamo que pudo colocar. Su costo "
                "es de oportunidad (ingreso no obtenido), no un gasto visible como la llamada."),
            criterios=[
                "(0.5) Lectura correcta: proporción de clientes que sí aceptarían que el modelo logra detectar.",
                f"(0.5) Usa los números del caso (detecta {vp} de {pos}, o 'de cada 100').",
                "(0.5) Define el falso negativo en el contexto: cliente que habría aceptado y no es contactado.",
                "(0.5) Explica la consecuencia de negocio: préstamo no colocado / costo de oportunidad.",
            ], **comunes),
        Problema(
            id="P16", numero=16, dimension="Interpretación",
            enunciado=("Interprete, en el contexto del banco, qué significan los falsos positivos y los falsos negativos de la "
                       "matriz e indique cuál de los dos errores ocurre con mayor frecuencia."),
            referencia=(
                f"Falsos positivos (FP = {fp}): clientes para quienes el modelo predice aceptación y rechazan; son llamadas "
                f"desperdiciadas. Falsos negativos (FN = {fn}): clientes que habrían aceptado y el modelo descarta; son "
                f"oportunidades perdidas. Ocurren con mayor frecuencia {mas_frec}. {sesgo}"),
            criterios=[
                "(0.5) Interpreta correctamente los falsos positivos en el contexto (llamadas a quienes no aceptan).",
                "(0.5) Interpreta correctamente los falsos negativos (clientes interesados no contactados).",
                "(0.5) Identifica con cifras cuál error es más frecuente.",
                "(0.5) Vincula el resultado con una consecuencia o tendencia del modelo (optimista/conservador, costo).",
            ], **comunes),
        Problema(
            id="P17", numero=17, dimension="Análisis",
            enunciado=(f"Cada llamada cuesta S/ {c} y cada préstamo aceptado deja una ganancia de S/ {g}. Compare la ganancia neta "
                       f"de (a) llamar solo a los clientes que el modelo predice 'acepta' y (b) llamar a los {n} clientes. "
                       "¿Qué estrategia conviene y por qué?"),
            referencia=(
                f"(a) Llamadas = VP+FP = {vp + fp}; ingresos = {vp}·{g} = {vp * g:,.0f}; costo = {vp + fp}·{c} = "
                f"{(vp + fp) * c:,.0f}; ganancia neta = {ga:,.0f}. (b) Llamadas = {n}; ingresos = {pos}·{g} = {pos * g:,.0f}; "
                f"costo = {n}·{c} = {n * c:,.0f}; ganancia neta = {gb:,.0f}. {decision} {texto_equilibrio}"),
            criterios=[
                f"(0.5) Ganancia neta de (a) correcta ({ga:,.0f}) con ingresos y costos planteados.",
                f"(0.5) Ganancia neta de (b) correcta ({gb:,.0f}).",
                f"(0.5) Decide correctamente la estrategia que conviene: {mejor}.",
                f"(0.5) Justifica con el punto de equilibrio ({equilibrio:.1%} = costo/ganancia) o con el costo de los {fn} falsos negativos frente al ahorro de llamadas.",
            ], **comunes),
        Problema(
            id="P18", numero=18, dimension="Análisis",
            enunciado=("Si el banco baja el umbral de decisión (de 0.5 a 0.3) para clasificar a un cliente como 'acepta', ¿cómo "
                       "esperaría que cambien VP, FP, FN, VN, la Precisión y el Recall? Justifique."),
            referencia=(
                f"Los positivos reales ({pos}) y los negativos reales ({neg}) no cambian. Al bajar el umbral el modelo declara "
                f"'acepta' a más clientes: VP sube (o se mantiene) y FN baja en la misma cantidad (VP+FN = {pos}); FP sube (o se "
                f"mantiene) y VN baja en la misma cantidad (FP+VN = {neg}). El Recall = VP/{pos} sube o se mantiene. La Precisión "
                "= VP/(VP+FP) tiende a bajar porque normalmente entran más falsos positivos que verdaderos positivos. Es el "
                "trade-off precisión-recall."),
            criterios=[
                f"(0.5) Indica que VP sube y FN baja, con suma constante igual a los positivos reales ({pos}).",
                f"(0.5) Indica que FP sube y VN baja, con suma constante igual a los negativos reales ({neg}).",
                "(0.5) Concluye que el Recall sube (o se mantiene) y explica por qué.",
                "(0.5) Concluye que la Precisión tiende a bajar y lo conecta con el trade-off precisión-recall.",
            ], **comunes),
        Problema(
            id="P19", numero=19, dimension="Argumentación",
            enunciado=("Redacte un párrafo (4-5 líneas) dirigido al Comité de Créditos en el que argumente si recomienda usar este "
                       "modelo en la próxima campaña. Sustente su postura con al menos dos métricas calculadas a partir de la "
                       "matriz."),
            referencia=(
                "Ejemplo de respuesta válida: «Recomiendo usar el modelo como filtro de apoyo, no como regla única. Reduce las "
                f"llamadas de {n} a {vp + fp} ({reduccion:.0%} menos) y contacta al {recall:.0%} de los clientes que aceptarían, "
                f"aunque solo el {precision:.0%} de las llamadas termina en préstamo y se pierden {fn} aceptantes. Sugiero ajustar "
                "el umbral y hacer una campaña piloto contra llamadas sin filtro para decidir con costos reales.»"),
            criterios=[
                "(0.5) Postura clara y coherente con las métricas (recomienda, no recomienda o condiciona).",
                "(0.5) Usa al menos dos métricas correctas (precisión, recall, exactitud, reducción de llamadas).",
                "(0.5) Reconoce una limitación o riesgo (falsos negativos perdidos o falsos positivos costosos).",
                "(0.5) Propone una condición o siguiente paso concreto y mantiene redacción formal y breve (4-5 líneas).",
            ], **comunes),
        Problema(
            id="P20", numero=20, dimension="Argumentación",
            enunciado=(f"Un directivo afirma: «El modelo acierta {round(exactitud * 100)} de cada 100 clientes, así que es "
                       "excelente». Redacte una respuesta (3-4 líneas) que sustente, con datos de la matriz, si esa conclusión es "
                       "válida."),
            referencia=(
                f"Ejemplo de respuesta válida: «La exactitud de {exactitud:.0%} es una medida incompleta: solo el {prev:.0%} de los "
                f"clientes acepta, y un modelo que siempre dijera 'rechaza' acertaría el {triv:.0%} sin detectar a ningún "
                f"interesado. {comp} Más informativo es que el modelo detecta el {recall:.0%} de los que aceptan (recall) pero solo "
                f"el {precision:.0%} de sus llamadas termina en préstamo (precisión); propongo evaluarlo con esas métricas y con "
                "el costo por llamada.»"),
            criterios=[
                "(0.5) Matiza o rechaza la afirmación con un argumento basado en el desbalance de clases.",
                f"(0.5) Usa como evidencia la línea base: predecir siempre 'rechaza' daría {triv:.0%} de exactitud.",
                "(0.5) Cita precisión y/o recall del modelo como métricas más informativas.",
                "(0.5) Redacción breve (3-4 líneas), clara y en tono profesional.",
            ], **comunes),
    ]


def _extra_caso2(semilla: int | None) -> list[Problema]:
    d = datos_caso2(semilla)
    real, pred = d["real"], d["pred"]
    m = metricas_regresion(real, pred)
    n = m["n"]
    mae, rmse, mse, mape, r2 = m["mae"], m["rmse"], m["mse"], m["mape"], m["r2"]
    media = m["media_real"]
    rel = mae / media
    cuadrados = [e ** 2 for e in m["abs_err"]]
    firmados = [r - p for r, p in zip(real, pred)]            # y − ŷ
    me = sum(firmados) / n
    n_sub = sum(e > 0 for e in firmados)                      # ŷ < y  (subestima)
    n_sob = sum(e < 0 for e in firmados)                      # ŷ > y  (sobreestima)
    i = max(range(n), key=lambda k: m["abs_err"][k])
    err_max, real_max, pred_max = m["abs_err"][i], real[i], pred[i]
    sentido = "subestimó" if real_max > pred_max else "sobreestimó"
    ratio = rmse / mae

    if me > 0:
        sesgo = f"ME > 0: en promedio el modelo subestima los precios en {_fmt(me)} mil USD ({n_sub} subestimaciones y {n_sob} sobreestimaciones)."
    elif me < 0:
        sesgo = f"ME < 0: en promedio el modelo sobreestima los precios en {_fmt(-me)} mil USD ({n_sob} sobreestimaciones y {n_sub} subestimaciones)."
    else:
        sesgo = f"ME = 0: no hay sesgo promedio ({n_sub} subestimaciones y {n_sob} sobreestimaciones que se compensan)."
    if ratio < 1.1:
        brecha = "La brecha es pequeña: los errores son bastante parejos."
    else:
        brecha = (f"La brecha (razón RMSE/MAE = {ratio:.2f}) indica que los errores son desiguales: hay algunos mayores que el "
                  f"resto, como el de {_fmt(err_max)} mil en el departamento de {real_max} mil.")

    datos = {"tipo": "tabla", **d}
    comunes = dict(caso=2, tema="Regresión", contexto=CONTEXTO_C2, datos=datos,
                   datos_texto=_texto_c2(real, pred), puntaje_max=2.0)

    return [
        Problema(
            id="P21", numero=21, dimension="Representación",
            enunciado=("Escriba la ecuación del modelo de Regresión Lineal Múltiple de este caso, representando la variable Distrito "
                       "con variables dummy (tome Centro como categoría de referencia), e indique qué mide cada coeficiente."),
            referencia=(
                "Precio = β0 + β1·MetrosCuadrados + β2·Habitaciones + β3·Norte + β4·Sur + ε, donde Norte y Sur son dummies (1 si "
                "el departamento está en ese distrito, 0 si no) y Centro es la referencia (Norte=0 y Sur=0). β0: precio esperado "
                "del departamento de referencia (Centro) con 0 m² y 0 habitaciones (intercepto, sin interpretación práctica por sí "
                "solo). β1: cambio esperado del precio (miles de USD) por cada m² adicional, manteniendo constantes las demás "
                "variables. β2: ídem por cada habitación adicional. β3 y β4: diferencia esperada de precio de Norte y de Sur "
                "respecto de Centro, a igual m² y número de habitaciones."),
            criterios=[
                "(0.5) Escribe una ecuación lineal con intercepto y las variables Metros Cuadrados y Habitaciones.",
                "(0.5) Representa Distrito con 2 dummies (Norte y Sur) y Centro como categoría de referencia.",
                "(0.5) Interpreta los coeficientes de m² y habitaciones como cambio esperado del precio por unidad, manteniendo constantes las demás.",
                "(0.5) Interpreta los coeficientes de las dummies como diferencia de precio respecto de Centro.",
            ], **comunes),
        Problema(
            id="P22", numero=22, dimension="Representación",
            enunciado=("Describa cómo representaría gráficamente el desempeño del modelo en los 5 departamentos de prueba: tipo de "
                       "gráfico, qué variable va en cada eje, qué línea de referencia incluiría y qué punto destacaría."),
            referencia=(
                "Gráfico de dispersión con el valor real (y) en el eje X y la predicción (ŷ) en el eje Y, ambos en miles de USD, "
                "con la recta de referencia ŷ = y (45°). Un modelo perfecto tendría los 5 puntos sobre la recta; la distancia "
                f"vertical de cada punto a la recta es su error. Se destacaría el departamento {i + 1} (real {real_max}, "
                f"predicción {pred_max}) por ser el más alejado de la recta (error {_fmt(err_max)}). También es válido un gráfico "
                "de residuos (error vs predicción) con una línea en cero."),
            criterios=[
                "(0.5) Elige un gráfico adecuado (dispersión real vs predicción, o gráfico de residuos).",
                "(0.5) Asigna y rotula bien los ejes, con unidades (miles de USD).",
                "(0.5) Incluye una línea de referencia (ŷ = y, o error = 0) y explica cómo se vería un modelo perfecto.",
                f"(0.5) Destaca el departamento de mayor error (real {real_max}, predicción {pred_max}).",
            ], **comunes),
        Problema(
            id="P23", numero=23, dimension="Cálculo",
            enunciado="Calcule el MSE (Error Cuadrático Medio) y el RMSE del modelo.",
            referencia=(
                "MSE = (1/n)·Σ(y − ŷ)². Errores al cuadrado: "
                f"{', '.join(_fmt(x) for x in cuadrados)}. Suma = {_fmt(m['ss_res'])}. MSE = {_fmt(m['ss_res'])}/{n} = "
                f"{_fmt(mse)} (miles de USD)². RMSE = √MSE = {_fmt(rmse)} miles de USD."),
            criterios=[
                "(0.5) Plantea correctamente las fórmulas de MSE y RMSE (RMSE = raíz del MSE).",
                f"(0.5) Errores al cuadrado correctos ({', '.join(_fmt(x) for x in cuadrados)}).",
                f"(0.5) MSE correcto ({_fmt(mse)}).",
                f"(0.5) RMSE correcto ({_fmt(rmse)}) y expresado en miles de USD.",
            ], **comunes),
        Problema(
            id="P24", numero=24, dimension="Cálculo",
            enunciado="Calcule el MAPE (Error Porcentual Absoluto Medio) y el R² del modelo.",
            referencia=(
                "MAPE = (1/n)·Σ|y − ŷ|/y. Errores relativos: "
                f"{', '.join(f'{e / r:.1%}' for e, r in zip(m['abs_err'], real))}. MAPE = {mape:.1%}. "
                f"R² = 1 − SS_res/SS_tot. Media real = {_fmt(media)}; SS_tot = Σ(y − ȳ)² = {_fmt(m['ss_tot'])}; "
                f"SS_res = Σ(y − ŷ)² = {_fmt(m['ss_res'])}. R² = 1 − {_fmt(m['ss_res'])}/{_fmt(m['ss_tot'])} = {r2:.3f}."),
            criterios=[
                "(0.5) Plantea el MAPE usando errores relativos |y − ŷ|/y.",
                f"(0.5) MAPE correcto ({mape:.1%}).",
                f"(0.5) Plantea el R² como 1 − SS_res/SS_tot usando la media real ({_fmt(media)}).",
                f"(0.5) R² correcto ({r2:.3f}).",
            ], **comunes),
        Problema(
            id="P25", numero=25, dimension="Interpretación",
            enunciado=(f"El modelo tiene MAE = {_fmt(mae)} y RMSE = {_fmt(rmse)} (miles de USD). Interprete ambos valores y explique "
                       "qué indica que el RMSE sea mayor que el MAE."),
            referencia=(
                f"MAE = {_fmt(mae)}: el error absoluto promedio es de {_fmt(mae)} mil USD. RMSE = {_fmt(rmse)}: raíz del error "
                "cuadrático medio, en las mismas unidades (miles de USD), pero eleva los errores al cuadrado y por eso pesa más los "
                "errores grandes. Siempre RMSE ≥ MAE; son iguales solo si todos los errores tienen la misma magnitud. "
                f"{brecha}"),
            criterios=[
                f"(0.5) Interpreta el MAE como error absoluto promedio ({_fmt(mae)} mil USD).",
                "(0.5) Interpreta el RMSE (mismas unidades) y explica que penaliza más los errores grandes.",
                "(0.5) Explica que RMSE ≥ MAE siempre y que la igualdad solo ocurre si los errores son iguales.",
                "(0.5) Concluye sobre la dispersión de los errores (parejos o con algunos grandes), apoyándose en los datos.",
            ], **comunes),
        Problema(
            id="P26", numero=26, dimension="Interpretación",
            enunciado=(f"El modelo obtuvo R² = {r2:.3f} en los 5 departamentos de prueba. Interprete este valor en el contexto del "
                       "negocio inmobiliario y mencione una precaución al usarlo."),
            referencia=(
                f"R² = {r2:.3f} significa que el modelo explica aproximadamente el {r2:.1%} de la variabilidad de los precios de los "
                f"departamentos de prueba; el {1 - r2:.1%} restante queda sin explicar (otras variables o error). Precauciones: solo "
                f"hay {n} departamentos, por lo que el R² es inestable; un R² alto no garantiza buenas predicciones con datos "
                "nuevos ni implica causalidad; conviene acompañarlo de MAE o RMSE, que están en las unidades del negocio."),
            criterios=[
                "(0.5) Interpreta el R² como proporción de la variabilidad del precio explicada por el modelo.",
                f"(0.5) Usa el valor (≈ {r2:.0%}) y menciona la parte no explicada.",
                "(0.5) Lo contextualiza en el negocio (precios de departamentos).",
                "(0.5) Menciona una precaución válida (pocos datos, no implica causalidad ni buen desempeño futuro, usar con MAE/RMSE).",
            ], **comunes),
        Problema(
            id="P27", numero=27, dimension="Análisis",
            enunciado=(f"El departamento con mayor error es el de {real_max} mil USD (predicción {pred_max} mil). Analice posibles "
                       "causas de ese error y proponga dos mejoras al modelo."),
            referencia=(
                f"El modelo {sentido} el precio en {_fmt(err_max)} mil USD. Causas posibles: variables omitidas (antigüedad, piso, "
                "vista, estado del inmueble), relación no lineal (el precio por m² no es constante en departamentos caros), "
                "pocos datos en ese rango de precios (el modelo extrapola) o un caso atípico. Mejoras: agregar variables relevantes, "
                "incluir términos no lineales o interacciones (p. ej. m² × Distrito), reunir más datos de ese segmento, "
                "transformar el precio (logaritmo) o probar modelos más flexibles. Se verificaría reevaluando MAE/RMSE con "
                "validación cruzada o con datos nuevos."),
            criterios=[
                f"(0.5) Identifica el error y su dirección (el modelo {sentido} en {_fmt(err_max)} mil USD).",
                "(0.5) Propone al menos una causa plausible (variables omitidas, no linealidad, pocos datos, atípico).",
                "(0.5) Propone dos mejoras concretas y coherentes con las causas.",
                "(0.5) Indica cómo verificaría la mejora (reevaluar MAE/RMSE, validación cruzada, más datos).",
            ], **comunes),
        Problema(
            id="P28", numero=28, dimension="Análisis",
            enunciado=("Calcule el error medio con signo (ME = promedio de y − ŷ) y analice si el modelo tiende a subestimar o a "
                       "sobreestimar los precios. ¿Por qué el ME no reemplaza al MAE?"),
            referencia=(
                f"Errores con signo (y − ŷ): {', '.join(_sig(e) for e in firmados)}. ME = {_sig(sum(firmados))}/{n} = "
                f"{_sig(me)}. {sesgo} El ME deja que errores positivos y negativos se compensen: aquí |ME| = {_fmt(abs(me))} es "
                f"menor que el MAE = {_fmt(mae)}. Por eso mide el sesgo, no la magnitud típica del error; el MAE sí."),
            criterios=[
                f"(0.5) Errores con signo correctos ({', '.join(_sig(e) for e in firmados)}).",
                f"(0.5) ME correcto ({_sig(me)}).",
                "(0.5) Interpreta el signo (ME > 0 subestima en promedio; ME < 0 sobreestima) apoyándose en los datos.",
                "(0.5) Explica que el ME compensa errores positivos con negativos y por eso no reemplaza al MAE.",
            ], **comunes),
        Problema(
            id="P29", numero=29, dimension="Argumentación",
            enunciado=("Un colega propone usar el modelo para fijar el precio de lista de todos los departamentos nuevos de la "
                       "inmobiliaria. Redacte un párrafo (3-4 líneas) a favor o en contra, usando el MAE y el tamaño de la muestra "
                       "de prueba."),
            referencia=(
                f"Ejemplo de respuesta válida: «Con un MAE de {_fmt(mae)} mil USD (≈ {rel:.1%} del precio medio) el modelo sirve como "
                f"referencia inicial para fijar precios, pero no recomiendo usarlo como única base: solo se probó con {n} "
                f"departamentos y el error llegó a {_fmt(err_max)} mil en uno de ellos. Propongo validarlo con una muestra mayor y "
                "usarlo junto con la tasación del agente, como un rango de precio y no como un valor único.»"),
            criterios=[
                "(0.5) Toma una postura clara (a favor, en contra o condicionada).",
                f"(0.5) Cita el MAE ({_fmt(mae)}) y su magnitud relativa al precio (≈ {rel:.1%}).",
                f"(0.5) Reconoce la limitación del tamaño de la muestra ({n} departamentos) y/o el error máximo.",
                "(0.5) Propone una acción coherente y mantiene una redacción breve (3-4 líneas).",
            ], **comunes),
        Problema(
            id="P30", numero=30, dimension="Argumentación",
            enunciado=(f"Un agente inmobiliario critica: «El modelo falla: en el departamento de {real_max} mil se equivocó por "
                       f"{_fmt(err_max)} mil». Redacte una respuesta (3-4 líneas) que sustente, con el error relativo y el MAE, si "
                       "esa crítica invalida el modelo."),
            referencia=(
                f"Ejemplo de respuesta válida: «Ese error equivale al {err_max / real_max:.1%} del precio de ese departamento y es el "
                f"mayor de los {n} casos, frente a un MAE de {_fmt(mae)} mil. Un solo caso no invalida el modelo: el error "
                f"promedio es de {rel:.1%} del precio medio. Sí conviene revisar por qué falla en ese tramo de precios y no usar el "
                "modelo sin supervisión en departamentos de ese rango.»"),
            criterios=[
                f"(0.5) Calcula el error relativo del caso criticado ({err_max / real_max:.1%}).",
                f"(0.5) Lo compara con el MAE o el error promedio ({_fmt(mae)}; ≈ {rel:.1%} del precio medio).",
                "(0.5) Argumenta con evidencia que un caso aislado no invalida el modelo (o matiza la conclusión con datos).",
                "(0.5) Propone una cautela o acción (revisar ese tramo) y mantiene una redacción breve (3-4 líneas).",
            ], **comunes),
    ]


# --------------------------------------------------------------------------- #
# API pública
# --------------------------------------------------------------------------- #
def obtener_problemas(semilla: int | None = None) -> list[Problema]:
    """Devuelve las 30 preguntas ordenadas por caso y dimensión.

    semilla=None -> datos exactos del examen modelo; con semilla entera, una variante con otros números.
    """
    todos = (_problemas_caso1(semilla) + _extra_caso1(semilla)
             + _problemas_caso2(semilla) + _extra_caso2(semilla))
    for p in todos:
        p.es_modelo = p.id in IDS_MODELO
    todos.sort(key=lambda p: (p.caso, ORDEN_DIMENSIONES.index(p.dimension), p.numero))
    return todos
