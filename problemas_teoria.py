"""Preguntas de respuesta escrita de los temas Scikit-learn y Presentación de reportes.

No requiere cambios en `problemas.py`: usa la misma dataclass `Problema`.
  - Scikit-learn  -> `dimension` = área de uso: "Clasificación", "Regresión" o "General".
  - Reportes      -> `dimension` = tipo de gráfico: "Barras simples", "Barras dobles",
                     "Dispersión", "Cajas (boxplot)" o "Comunicación del reporte".

Las preguntas de gráficos llevan los datos en `datos` (que `app.py` dibuja) y en `datos_texto`
(para que el evaluador de IA "vea" los mismos números). Todas las cifras de las soluciones modelo
se calculan aquí en Python; la IA nunca calcula.
"""
from __future__ import annotations

import statistics

from problemas import Problema

TEMA_SKLEARN = "Scikit-learn"
TEMA_REPORTES = "Reportes de datos"

DIMS_SKLEARN = ["Clasificación", "Regresión", "General"]
DIMS_REPORTES = ["Barras simples", "Barras dobles", "Dispersión", "Cajas (boxplot)", "Comunicación del reporte"]

CTX_SKLEARN = (
    "Curso de Introducción a Data Science · uso de scikit-learn. Caso 1 (clasificación): un banco predice si un "
    "cliente acepta un préstamo (Acepta = 1/0) con Edad, Nivel Educativo, Ingresos Anuales y Deuda Actual, usando "
    "Random Forest. Caso 2 (regresión): una inmobiliaria predice el Precio (miles de USD) con Metros Cuadrados, "
    "Habitaciones y Distrito (Norte, Sur, Centro), usando regresión lineal múltiple. Puedes escribir código y explicarlo."
)
CTX_BANCO = ("Caso 1 · Banco. Campaña telefónica de préstamos personales evaluada con 200 clientes "
             "(30 de ellos aceptan el préstamo).")
CTX_INMO = "Caso 2 · Inmobiliaria. Precios de venta de departamentos, en miles de USD."
CTX_REPORTE = "Curso de Introducción a Data Science · presentación de reportes de ciencia de datos (Casos 1 y 2)."


# --------------------------------------------------------------------------- #
# Utilidades numéricas
# --------------------------------------------------------------------------- #
def _fmt(x: float) -> str:
    return f"{x:.2f}".rstrip("0").rstrip(".")


def _cuartiles(x: list[float]) -> tuple[float, float, float]:
    q1, q2, q3 = statistics.quantiles(x, n=4, method="inclusive")  # interpolación lineal (como pandas/Vega)
    return q1, q2, q3


def _limites(x: list[float]) -> tuple[float, float, float]:
    q1, _, q3 = _cuartiles(x)
    iqr = q3 - q1
    return iqr, q1 - 1.5 * iqr, q3 + 1.5 * iqr


def _atipicos(x: list[float]) -> list[float]:
    _, lo, hi = _limites(x)
    return [v for v in x if v < lo or v > hi]


def _pearson(x: list[float], y: list[float]) -> float:
    mx, my = sum(x) / len(x), sum(y) / len(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / (sxx * syy) ** 0.5


def _pendiente(x: list[float], y: list[float]) -> float:
    mx, my = sum(x) / len(x), sum(y) / len(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / sum((a - mx) ** 2 for a in x)


def _p(id_: str, n: int, tema: str, caso: int, contexto: str, dimension: str, enunciado: str,
       referencia: str, criterios: list[str], datos: dict | None = None, datos_texto: str = "") -> Problema:
    return Problema(
        id=id_, caso=caso, tema=tema, dimension=dimension, numero=n, contexto=contexto,
        enunciado=enunciado, puntaje_max=2.0, referencia=referencia,
        criterios=[f"(0.5) {c}" for c in criterios], datos=datos or {}, datos_texto=datos_texto,
    )


# --------------------------------------------------------------------------- #
# Scikit-learn (11 preguntas)
# --------------------------------------------------------------------------- #
def _sklearn() -> list[Problema]:
    t, c, x = TEMA_SKLEARN, 3, CTX_SKLEARN
    return [
        _p("S01", 1, t, c, x, "Clasificación",
           "Escriba el código en Python (scikit-learn) que, a partir de un DataFrame df con las columnas Edad, Nivel Educativo, "
           "Ingresos Anuales, Deuda Actual y Acepta: (a) divida los datos 80/20 de forma estratificada, (b) codifique Nivel "
           "Educativo como variable ordinal, (c) entrene un RandomForestClassifier dentro de un Pipeline y (d) genere las "
           "predicciones sobre el conjunto de prueba.",
           "from sklearn.model_selection import train_test_split\n"
           "from sklearn.compose import ColumnTransformer\n"
           "from sklearn.preprocessing import OrdinalEncoder\n"
           "from sklearn.ensemble import RandomForestClassifier\n"
           "from sklearn.pipeline import Pipeline\n\n"
           "X = df[['Edad', 'Nivel Educativo', 'Ingresos Anuales', 'Deuda Actual']]   # sin la variable objetivo\n"
           "y = df['Acepta']\n"
           "X_train, X_test, y_train, y_test = train_test_split(\n"
           "    X, y, test_size=0.2, stratify=y, random_state=42)\n\n"
           "prep = ColumnTransformer(\n"
           "    [('nivel', OrdinalEncoder(categories=[['Primaria', 'Secundaria', 'Universitaria']]), ['Nivel Educativo'])],\n"
           "    remainder='passthrough')          # las columnas numéricas pasan sin cambios\n"
           "modelo = Pipeline([('prep', prep), ('rf', RandomForestClassifier(n_estimators=200, random_state=42))])\n"
           "modelo.fit(X_train, y_train)           # solo con entrenamiento\n"
           "y_pred = modelo.predict(X_test)\n\n"
           "Se pasa categories=[[...]] para que el orden sea Primaria<Secundaria<Universitaria (por defecto sería alfabético). "
           "Random Forest no requiere escalar las variables numéricas.",
           ["Separa X (sin la variable objetivo) e y y usa train_test_split con test_size=0.2, stratify=y y random_state.",
            "Codifica Nivel Educativo con OrdinalEncoder indicando el orden correcto de las categorías, dentro de un ColumnTransformer (remainder='passthrough' para las numéricas).",
            "Arma un Pipeline que encadena el preprocesamiento y RandomForestClassifier.",
            "Ajusta (fit) solo con entrenamiento y obtiene y_pred con predict sobre X_test."]),
        _p("S02", 2, t, c, x, "Regresión",
           "Escriba el código en Python (scikit-learn) que, a partir de un DataFrame df con las columnas Metros Cuadrados, "
           "Habitaciones, Distrito y Precio, divida los datos 80/20, represente Distrito con variables dummy (evitando la "
           "colinealidad perfecta), entrene una LinearRegression dentro de un Pipeline y prediga sobre el conjunto de prueba. "
           "Indique cuál distrito queda como categoría de referencia.",
           "X = df[['Metros Cuadrados', 'Habitaciones', 'Distrito']]\n"
           "y = df['Precio']\n"
           "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)   # sin stratify: y es continua\n\n"
           "prep = ColumnTransformer([('dist', OneHotEncoder(drop='first'), ['Distrito'])], remainder='passthrough')\n"
           "modelo = Pipeline([('prep', prep), ('lr', LinearRegression())])\n"
           "modelo.fit(X_train, y_train)\n"
           "y_pred = modelo.predict(X_test)\n\n"
           "drop='first' elimina la primera categoría en orden alfabético: Centro (Centro, Norte, Sur), que queda como referencia, "
           "y se crean las dummies Norte y Sur (k−1). Así se evita la colinealidad perfecta (trampa de las variables dummy).",
           ["Separa X e y y divide con train_test_split (test_size=0.2, random_state) sin usar stratify porque y es continua.",
            "Usa OneHotEncoder(drop='first') (o equivalente k−1) sobre Distrito dentro de un ColumnTransformer.",
            "Encadena el preprocesamiento y LinearRegression en un Pipeline y hace fit con entrenamiento y predict con prueba.",
            "Identifica Centro como categoría de referencia (primera en orden alfabético) y explica que drop evita la colinealidad perfecta."]),
        _p("S03", 3, t, c, x, "General",
           "Explique para qué se usa train_test_split, qué hacen los parámetros test_size, random_state y stratify, y en cuál de los dos "
           "casos tiene sentido usar stratify=y.",
           "train_test_split separa los datos en entrenamiento (para ajustar el modelo) y prueba (para evaluarlo con datos que no vio y "
           "estimar su desempeño real). test_size fija la proporción de prueba (p. ej. 0.2). random_state fija la semilla para que la "
           "partición sea reproducible. stratify=y conserva en ambos conjuntos la misma proporción de clases; tiene sentido en el Caso 1 "
           "(clasificación con la clase 'acepta' minoritaria) y no en el Caso 2, porque el precio es continuo y no tiene clases.",
           ["Explica el propósito: evaluar con datos no vistos / evitar evaluar donde se entrenó.",
            "Describe test_size y random_state (proporción y reproducibilidad).",
            "Explica qué hace stratify (mantiene la proporción de clases en ambos conjuntos).",
            "Indica que se usa en clasificación (Caso 1, desbalanceado) y no en regresión (Caso 2, objetivo continuo)."]),
        _p("S04", 4, t, c, x, "General",
           "Diferencie fit, transform y fit_transform. ¿Por qué es un error ajustar (fit) un codificador o escalador con todos los datos "
           "antes de dividir en entrenamiento y prueba? ¿Cómo ayuda un Pipeline?",
           "fit aprende parámetros a partir de los datos (categorías, media y desviación, coeficientes); transform los aplica; fit_transform "
           "hace ambos pasos sobre el mismo conjunto. Se usa fit_transform solo con entrenamiento y solo transform con prueba. Ajustar con "
           "todos los datos produce fuga de datos (data leakage): la información de prueba influye en el preprocesamiento y las métricas "
           "salen optimistas. El Pipeline aplica automáticamente fit solo con lo que recibe en fit y transform en predict, y dentro de la "
           "validación cruzada reajusta el preprocesamiento en cada partición.",
           ["Define fit (aprende parámetros) y transform (los aplica) y explica fit_transform.",
            "Indica en qué conjunto se usa cada método (fit_transform en entrenamiento, transform en prueba).",
            "Identifica el problema como fuga de datos y su consecuencia (métricas optimistas).",
            "Explica cómo el Pipeline evita el error (preprocesamiento aprendido solo con entrenamiento, también en validación cruzada)."]),
        _p("S05", 5, t, c, x, "Clasificación",
           "Dados y_test e y_pred del modelo del Caso 1, escriba el código para obtener la matriz de confusión, la exactitud, la precisión, "
           "el recall y el F1. Explique cómo ordena confusion_matrix sus celdas y en qué se diferencia de la matriz tal como se presenta en "
           "el examen (VP y FN en la primera fila).",
           "from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score\n\n"
           "cm = confusion_matrix(y_test, y_pred)          # [[VN, FP], [FN, VP]]\n"
           "vn, fp, fn, vp = cm.ravel()\n"
           "exactitud = accuracy_score(y_test, y_pred)\n"
           "precision = precision_score(y_test, y_pred)    # pos_label=1 por defecto\n"
           "recall = recall_score(y_test, y_pred)\n"
           "f1 = f1_score(y_test, y_pred)\n\n"
           "Todas reciben primero el valor real y luego la predicción. En confusion_matrix las filas son lo real y las columnas lo predicho, "
           "con las clases en orden ascendente (0, 1): arriba a la izquierda queda VN y abajo a la derecha VP. En el examen la matriz "
           "empieza por 'Acepta' (VP, FN / FP, VN), por lo que hay que reordenar al compararlas.",
           ["Usa las funciones correctas de sklearn.metrics con los argumentos en el orden (y_real, y_pred).",
            "Explica el orden de confusion_matrix: filas = real, columnas = predicción, [[VN, FP], [FN, VP]].",
            "Extrae VN, FP, FN y VP (p. ej. con ravel()) y/o calcula precisión, recall y F1 con las funciones respectivas.",
            "Señala la diferencia con la matriz del examen (el orden de clases está invertido) o menciona pos_label=1."]),
        _p("S06", 6, t, c, x, "Regresión",
           "Escriba el código para calcular el MAE, RMSE, MAPE y R² del modelo del Caso 2 con sklearn.metrics y explique cómo obtendría el "
           "RMSE según la versión instalada de scikit-learn. ¿En qué forma devuelve el MAPE?",
           "from sklearn.metrics import (mean_absolute_error, mean_squared_error,\n"
           "                             mean_absolute_percentage_error, r2_score)\n"
           "import numpy as np\n\n"
           "mae = mean_absolute_error(y_test, y_pred)                    # miles de USD\n"
           "rmse = np.sqrt(mean_squared_error(y_test, y_pred))           # o root_mean_squared_error (scikit-learn >= 1.4)\n"
           "mape = mean_absolute_percentage_error(y_test, y_pred)        # fracción: 0.05 = 5 %\n"
           "r2 = r2_score(y_test, y_pred)\n\n"
           "El argumento squared=False de mean_squared_error quedó obsoleto y se retiró en versiones recientes; por eso se usa np.sqrt o "
           "root_mean_squared_error. El MAPE se devuelve como proporción, no como porcentaje.",
           ["Usa mean_absolute_error y r2_score de sklearn.metrics con (y_real, y_pred).",
            "Obtiene el RMSE como raíz del MSE (np.sqrt o root_mean_squared_error).",
            "Usa mean_absolute_percentage_error e indica que devuelve una proporción (0.05 = 5 %).",
            "Menciona la dependencia de la versión (squared=False obsoleto) o interpreta las unidades (MAE y RMSE en miles de USD)."]),
        _p("S07", 7, t, c, x, "Clasificación",
           "Con el Pipeline del Caso 1 ya entrenado, escriba el código para obtener las probabilidades de aceptar y clasificar con un umbral "
           "de 0.3 en lugar de 0.5. Explique qué efecto esperaría en precisión y recall.",
           "proba = modelo.predict_proba(X_test)[:, 1]        # columna de la clase 1 (acepta)\n"
           "y_pred_03 = (proba >= 0.3).astype(int)\n\n"
           "predict equivale a umbral 0.5; predict_proba devuelve una columna por clase (en el orden de modelo.classes_), por eso se toma "
           "la columna 1. Al bajar el umbral se declara 'acepta' a más clientes: el recall sube (o se mantiene) y la precisión tiende a "
           "bajar porque entran más falsos positivos (trade-off precisión-recall).",
           ["Usa predict_proba y selecciona la columna de la clase positiva ([:, 1]).",
            "Aplica el umbral con una comparación (proba >= 0.3) y convierte a 0/1.",
            "Explica que predict usa implícitamente 0.5 / diferencia predict de predict_proba.",
            "Predice recall sube y precisión tiende a bajar, y lo explica (más falsos positivos)."]),
        _p("S08", 8, t, c, x, "General",
           "Escriba el código para evaluar con validación cruzada de 5 particiones el modelo del Caso 1 (métrica: recall) y el del Caso 2 "
           "(métrica: MAE). Indique qué tipo de partición usaría en cada caso y cómo interpretaría el signo del MAE que devuelve scikit-learn.",
           "from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold\n\n"
           "cv_clf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)\n"
           "recall_cv = cross_val_score(modelo_clf, X, y, cv=cv_clf, scoring='recall')\n"
           "cv_reg = KFold(n_splits=5, shuffle=True, random_state=42)\n"
           "mae_cv = -cross_val_score(modelo_reg, X, y, cv=cv_reg, scoring='neg_mean_absolute_error')\n"
           "print(recall_cv.mean(), recall_cv.std(), mae_cv.mean())\n\n"
           "En clasificación conviene StratifiedKFold (mantiene la proporción de clases); en regresión KFold. scikit-learn maximiza el score, "
           "por eso las métricas de error se devuelven negativas ('neg_mean_absolute_error') y se multiplican por −1 para leer el MAE. Se "
           "pasa el Pipeline completo para que el preprocesamiento se reajuste en cada partición, y se reporta la media y la desviación.",
           ["Usa cross_val_score con cv=5 (o un objeto KFold/StratifiedKFold) y scoring correcto: 'recall' y 'neg_mean_absolute_error'.",
            "Elige StratifiedKFold para clasificación (clases desbalanceadas) y KFold para regresión.",
            "Explica el signo negativo del MAE y lo corrige (−1 × resultado).",
            "Reporta media y desviación de los k resultados y/o pasa el Pipeline completo para evitar fuga de datos."]),
        _p("S09", 9, t, c, x, "Clasificación",
           "Escriba el código para buscar con GridSearchCV los mejores hiperparámetros del Pipeline con RandomForest del Caso 1, "
           "optimizando el recall. Indique cómo nombraría los parámetros de un paso del Pipeline y cómo evaluaría el resultado final.",
           "param_grid = {\n"
           "    'rf__n_estimators': [100, 300],\n"
           "    'rf__max_depth': [None, 5, 10],\n"
           "    'rf__min_samples_leaf': [1, 5],\n"
           "    'rf__class_weight': [None, 'balanced'],\n"
           "}\n"
           "gs = GridSearchCV(modelo, param_grid, cv=5, scoring='recall', n_jobs=-1)\n"
           "gs.fit(X_train, y_train)\n"
           "print(gs.best_params_, gs.best_score_)\n"
           "y_pred = gs.best_estimator_.predict(X_test)     # evaluación final con datos que no participaron en la búsqueda\n\n"
           "En un Pipeline los parámetros se nombran paso__parametro (doble guion bajo). El best_score_ es optimista porque se eligió "
           "mirando la validación; la evaluación honesta es sobre el conjunto de prueba.",
           ["Crea GridSearchCV con el estimador (Pipeline), param_grid, cv y scoring coherente con el objetivo (recall).",
            "Nombra los hiperparámetros del Pipeline con el formato paso__parametro (p. ej. rf__max_depth).",
            "Ajusta (fit) solo con entrenamiento y recupera best_params_ / best_estimator_.",
            "Evalúa el mejor modelo en el conjunto de prueba y explica por qué (best_score_ es optimista)."]),
        _p("S10", 10, t, c, x, "Regresión",
           "Tras ajustar el Pipeline del Caso 2, escriba el código para mostrar cada coeficiente con el nombre de su variable y el "
           "intercepto. Interprete el coeficiente de Metros Cuadrados y el de la dummy Norte.",
           "import pandas as pd\n"
           "nombres = modelo.named_steps['prep'].get_feature_names_out()\n"
           "coefs = pd.Series(modelo.named_steps['lr'].coef_, index=nombres)\n"
           "intercepto = modelo.named_steps['lr'].intercept_\n\n"
           "El coeficiente de Metros Cuadrados es el cambio esperado del precio (miles de USD) por cada m² adicional, manteniendo constantes "
           "habitaciones y distrito. El de la dummy Norte es la diferencia esperada de precio de Norte respecto de Centro (referencia) a "
           "igual m² y habitaciones. El intercepto es el precio esperado del caso base (Centro, 0 m², 0 habitaciones), sin interpretación "
           "práctica por sí solo.",
           ["Accede a los pasos con named_steps y usa coef_ e intercept_.",
            "Obtiene los nombres de las variables transformadas (get_feature_names_out) y los asocia a los coeficientes.",
            "Interpreta el coeficiente de Metros Cuadrados con unidades (miles de USD por m²) y 'manteniendo constantes las demás'.",
            "Interpreta la dummy Norte como diferencia respecto de la categoría de referencia (Centro)."]),
        _p("S11", 11, t, c, x, "Regresión",
           "Un departamento nuevo tiene 85 m², 3 habitaciones y está en el distrito Sur. Escriba el código para estimar su precio con el "
           "Pipeline ya entrenado y explique por qué conviene pasar un DataFrame con los mismos nombres de columnas y no solo una lista "
           "de números.",
           "nuevo = pd.DataFrame([{'Metros Cuadrados': 85, 'Habitaciones': 3, 'Distrito': 'Sur'}])\n"
           "precio = modelo.predict(nuevo)[0]      # miles de USD, las mismas unidades que y_train\n\n"
           "El ColumnTransformer selecciona las columnas por nombre y aplica el OneHotEncoder a 'Distrito'; si se pasara una lista de números "
           "no habría nombres ni la categoría 'Sur' podría codificarse. Se usa el Pipeline completo (no el LinearRegression suelto) para que "
           "se repita exactamente el mismo preprocesamiento y orden de columnas del entrenamiento.",
           ["Construye un DataFrame con una fila y los mismos nombres de columnas que en el entrenamiento.",
            "Llama a predict sobre el Pipeline completo (no sobre el modelo interno sin preprocesar).",
            "Explica la razón: mismos nombres/orden y mismo preprocesamiento (Distrito categórico debe codificarse).",
            "Interpreta la salida (valor en miles de USD) o extrae el escalar con [0]."]),
    ]


# --------------------------------------------------------------------------- #
# Reportes de datos: interpretación de gráficos (16 preguntas)
# --------------------------------------------------------------------------- #
def _reportes() -> list[Problema]:
    t, rep = TEMA_REPORTES, CTX_REPORTE
    out: list[Problema] = []

    # ------------------------- Barras simples (Caso 1) ------------------------- #
    niveles = ["Primaria", "Secundaria", "Universitaria"]
    clientes = [50, 80, 70]
    aceptan = [4, 11, 15]
    tasas = [round(a / n * 100, 2) for a, n in zip(aceptan, clientes)]
    tasa_global = sum(aceptan) / sum(clientes) * 100
    d_barras = {"tipo": "grafico", "grafico": "barras", "titulo": "Tasa de aceptación del préstamo por nivel educativo",
                "categorias": niveles, "valores": tasas, "x_titulo": "Nivel educativo", "y_titulo": "Tasa de aceptación (%)",
                "referencia_y": round(tasa_global, 2)}
    t_barras = ("Gráfico de barras simples: tasa de aceptación (%) por nivel educativo. "
                + "; ".join(f"{n}: {tasa:.1f} % ({a} de {c} clientes)" for n, tasa, a, c in zip(niveles, tasas, aceptan, clientes))
                + f". Tasa global: {tasa_global:.1f} % (30 de 200).")
    i_max, i_min = tasas.index(max(tasas)), tasas.index(min(tasas))
    veces = tasas[i_max] / tasas[i_min]

    out.append(_p(
        "R01", 1, t, 1, f"{CTX_BANCO} {rep}", "Barras simples",
        "El gráfico muestra la tasa de aceptación del préstamo según el nivel educativo del cliente. Interprételo: ¿qué nivel acepta más y "
        "cuál menos?, ¿qué tan grande es la diferencia?, ¿cómo se compara cada nivel con la tasa global? ¿Qué implicancia tiene para la campaña?",
        f"La tasa más alta es la de {niveles[i_max]} ({tasas[i_max]:.1f} %, {aceptan[i_max]} de {clientes[i_max]}) y la más baja la de "
        f"{niveles[i_min]} ({tasas[i_min]:.1f} %, {aceptan[i_min]} de {clientes[i_min]}); la diferencia es de {tasas[i_max] - tasas[i_min]:.1f} "
        f"puntos porcentuales, es decir, {veces:.1f} veces. Secundaria ({tasas[1]:.1f} %) queda en el medio. La tasa aumenta con el nivel "
        f"educativo. Frente a la tasa global de {tasa_global:.0f} %, Universitaria está por encima y Primaria y Secundaria por debajo. "
        "Implicancia: conviene priorizar las llamadas a clientes con mayor nivel educativo o diseñar un mensaje distinto para Primaria. "
        "Cautela: son diferencias descriptivas (no prueban causalidad) y los grupos tienen tamaños distintos (50, 80 y 70 clientes).",
        [f"Identifica el nivel con mayor tasa ({niveles[i_max]}, {tasas[i_max]:.1f} %) y el de menor tasa ({niveles[i_min]}, {tasas[i_min]:.1f} %).",
         f"Cuantifica la diferencia (≈ {tasas[i_max] - tasas[i_min]:.0f} puntos porcentuales o ≈ {veces:.1f} veces).",
         f"Describe el patrón creciente con el nivel educativo y/o compara con la tasa global ({tasa_global:.0f} %).",
         "Señala una implicancia de negocio (a quién priorizar) y/o una cautela (diferencias descriptivas, tamaños de grupo distintos)."],
        d_barras, t_barras))

    out.append(_p(
        "R02", 2, t, 1, f"{CTX_BANCO} {rep}", "Barras simples",
        "Explique por qué un gráfico de barras simples es adecuado para representar estos datos y por qué no usaría uno de líneas. Indique "
        "qué variable va en cada eje, qué escala usaría en el eje vertical, cómo ordenaría las categorías y qué elementos agregaría "
        "(título, etiquetas, referencia) para que el reporte sea claro.",
        "Las barras se usan para comparar valores entre categorías: el nivel educativo es una variable categórica ordinal (eje horizontal) y "
        "la tasa de aceptación es numérica (eje vertical, en %). Un gráfico de líneas sugiere continuidad entre puntos, lo que no corresponde "
        "a categorías. El eje vertical debe empezar en 0 porque la longitud de la barra codifica el valor y truncarlo exagera las diferencias. "
        "Las categorías se ordenan por su orden natural (Primaria, Secundaria, Universitaria). Se agregan un título que exprese el hallazgo, "
        "etiquetas de datos con unidades (%), el número de clientes por categoría y, opcionalmente, una línea con la tasa global.",
        ["Asigna correctamente las variables: categoría en el eje horizontal y tasa (%) en el vertical.",
         "Justifica barras frente a líneas (categorías discretas, comparación entre grupos).",
         "Indica que el eje vertical debe iniciar en 0 y explica por qué (la longitud codifica el valor).",
         "Menciona orden lógico de categorías y elementos de claridad (título, etiquetas con unidades, n o línea de referencia)."],
        d_barras, t_barras))

    out.append(_p(
        "R03", 3, t, 1, f"{CTX_BANCO} {rep}", "Barras simples",
        "Con base en el gráfico, redacte un mensaje breve (3 líneas) para el Gerente de Marketing que incluya el hallazgo principal con "
        "cifras, una acción concreta y una cautela.",
        f"Ejemplo de respuesta válida: «La tasa de aceptación sube con el nivel educativo: {tasas[0]:.0f} % en Primaria, {tasas[1]:.0f} % en "
        f"Secundaria y {tasas[2]:.0f} % en Universitaria, frente a {tasa_global:.0f} % en promedio. Recomiendo priorizar las llamadas a clientes "
        "universitarios y probar un mensaje distinto para Primaria. Son diferencias observadas en 200 clientes, así que conviene confirmarlas "
        "con un piloto antes de reasignar todo el presupuesto.»",
        ["Redacción breve (3 líneas), clara y en tono ejecutivo.",
         "Cita cifras del gráfico (tasas por nivel y/o la tasa global).",
         "Propone una acción concreta coherente con el hallazgo (priorizar, segmentar, probar mensajes).",
         "Incluye una cautela o paso de validación (muestra, piloto, no causalidad)."],
        d_barras, t_barras))

    # ------------------------- Barras dobles ------------------------- #
    real = [150, 200, 120, 300, 250]
    pred = [145, 210, 118, 280, 255]
    deptos = [f"Depto {i}" for i in range(1, 6)]
    dif = [p - r for r, p in zip(real, pred)]              # ŷ − y
    sub = [deptos[i] for i, e in enumerate(dif) if e < 0]
    sob = [deptos[i] for i, e in enumerate(dif) if e > 0]
    i_err = max(range(5), key=lambda i: abs(dif[i]))
    mae = sum(abs(e) for e in dif) / 5
    d_dobles1 = {"tipo": "grafico", "grafico": "barras_dobles", "titulo": "Precio real vs precio predicho por departamento",
                 "categorias": deptos, "series": {"Real": real, "Predicho": pred}, "x_titulo": "Departamento de prueba",
                 "y_titulo": "Precio (miles de USD)"}
    t_dobles1 = ("Gráfico de barras dobles (precio real vs predicho, miles de USD): "
                 + "; ".join(f"{d}: real={r}, predicho={p}" for d, r, p in zip(deptos, real, pred)) + ".")

    out.append(_p(
        "R04", 4, t, 2, f"{CTX_INMO} {rep}", "Barras dobles",
        "El gráfico compara el precio real y el precio predicho por el modelo en 5 departamentos de prueba. Interprételo: ¿en cuáles "
        "departamentos el modelo subestima y en cuáles sobreestima?, ¿dónde es mayor la diferencia y cuánto vale?, ¿qué tan bueno parece "
        "el ajuste global?",
        f"Subestima (barra predicha menor que la real): {', '.join(sub)}. Sobreestima (predicha mayor): {', '.join(sob)}. La mayor diferencia "
        f"está en {deptos[i_err]}: real {real[i_err]} y predicho {pred[i_err]}, una diferencia de {abs(dif[i_err])} mil USD "
        f"({abs(dif[i_err]) / real[i_err]:.1%} de su precio). En los demás las barras son casi iguales (diferencias de 2 a 10 mil USD). El "
        f"error absoluto promedio es de {_fmt(mae)} mil USD, un ajuste bueno para un uso referencial. Limitación: solo hay 5 casos y el gráfico "
        "no resume el error en una métrica ni distingue por sí solo el signo del error.",
        [f"Identifica correctamente dónde subestima ({', '.join(sub)}) y dónde sobreestima ({', '.join(sob)}).",
         f"Señala la mayor diferencia con cifras ({deptos[i_err]}, {abs(dif[i_err])} mil USD).",
         f"Valora el ajuste global con evidencia (barras muy cercanas; error promedio ≈ {_fmt(mae)} mil USD).",
         "Menciona una limitación (pocos casos, el gráfico no cuantifica el error ni resume en una métrica)."],
        d_dobles1, t_dobles1))

    modelos = ["Regresión logística", "Random Forest", "Árbol de decisión"]
    prec = [45.0, 33.3, 28.0]
    rec = [40.0, 66.7, 80.0]
    f1 = [2 * p * r / (p + r) for p, r in zip(prec, rec)]
    d_dobles2 = {"tipo": "grafico", "grafico": "barras_dobles", "titulo": "Precisión y recall por modelo (Caso 1)",
                 "categorias": modelos, "series": {"Precisión": prec, "Recall": rec}, "x_titulo": "Modelo",
                 "y_titulo": "Valor (%)"}
    t_dobles2 = ("Gráfico de barras dobles (precisión y recall en %, conjunto de prueba de 200 clientes): "
                 + "; ".join(f"{m}: precisión={p}, recall={r}" for m, p, r in zip(modelos, prec, rec)) + ".")

    out.append(_p(
        "R05", 5, t, 1, f"{CTX_BANCO} {rep}", "Barras dobles",
        "El gráfico compara la precisión y el recall de tres modelos entrenados con los mismos datos. El gerente quiere maximizar la cantidad "
        "de préstamos colocados sin importar cuántas llamadas se hagan. ¿Qué modelo elegiría y qué trade-off observa en el gráfico? ¿Qué "
        "información adicional pediría antes de decidir?",
        f"Con el objetivo de maximizar el recall, el mejor es el Árbol de decisión (recall {rec[2]:.0f} %: detecta 8 de cada 10 aceptantes), pero "
        f"con la menor precisión ({prec[2]:.0f} %: unas 72 de cada 100 llamadas serían improductivas). Entre los tres modelos se ve el trade-off: "
        f"al subir el recall (Regresión logística {rec[0]:.0f} % → Random Forest {rec[1]:.1f} % → Árbol {rec[2]:.0f} %) baja la precisión "
        f"({prec[0]:.0f} % → {prec[1]:.1f} % → {prec[2]:.0f} %). El Random Forest es el más equilibrado (F1 ≈ {f1[1]:.1f} %, frente a "
        f"{f1[0]:.1f} % de la regresión logística y {f1[2]:.1f} % del árbol). Antes de decidir pediría el costo por llamada y la ganancia por "
        "préstamo (para ver si compensan las llamadas extra), la posibilidad de ajustar el umbral de cada modelo y una validación con más "
        "datos o validación cruzada.",
        [f"Elige un modelo coherente con el objetivo (Árbol de decisión por su recall de {rec[2]:.0f} %) citando valores del gráfico.",
         "Describe el trade-off precisión-recall observado entre los modelos (donde sube uno, baja el otro).",
         "Vincula la baja precisión con llamadas improductivas / costo para el banco.",
         "Propone información o criterio adicional (costo por llamada vs ganancia, F1, ajuste de umbral, validación con más datos)."],
        d_dobles2, t_dobles2))

    out.append(_p(
        "R06", 6, t, 1, f"{CTX_BANCO} {rep}", "Barras dobles",
        "Explique cuándo usaría un gráfico de barras dobles (agrupadas) en lugar de barras simples o apiladas, y qué elementos incluiría "
        "para que el gráfico de precisión y recall por modelo sea legible para un público no técnico.",
        "Las barras dobles (agrupadas) se usan para comparar dos series (aquí dos métricas) sobre las mismas categorías (modelos): al estar "
        "juntas, permiten comparar directamente la precisión con el recall de cada modelo y también entre modelos. Las barras simples "
        "muestran una sola serie; las apiladas solo tienen sentido cuando la suma de las partes tiene significado (precisión + recall no "
        "lo tiene). Elementos: leyenda clara, colores distinguibles (también para daltonismo), mismo eje con unidades (%) que inicie en 0, "
        "categorías en un orden con criterio, etiquetas de valor y un título que enuncie el hallazgo.",
        ["Explica que las barras dobles comparan dos series sobre las mismas categorías.",
         "Diferencia el uso frente a barras simples (una serie) y apiladas (partes de un total).",
         "Menciona leyenda y colores distinguibles para las dos series.",
         "Incluye otros elementos de claridad: eje desde 0 con unidades, orden de categorías, etiquetas de valor, título informativo."],
        d_dobles2, t_dobles2))

    # ------------------------- Dispersión ------------------------- #
    m2 = [45, 52, 58, 62, 65, 70, 75, 80, 90, 95, 110, 120, 140]
    precio = [104, 100, 131, 210, 122, 152, 140, 176, 170, 205, 214, 252, 262]
    r_all = _pearson(m2, precio)
    b_all = _pendiente(m2, precio)
    idx = [i for i in range(len(m2)) if i != 3]
    r_sin = _pearson([m2[i] for i in idx], [precio[i] for i in idx])
    b_sin = _pendiente([m2[i] for i in idx], [precio[i] for i in idx])
    d_disp1 = {"tipo": "grafico", "grafico": "dispersion", "titulo": "Metros cuadrados vs precio de venta (13 departamentos)",
               "x": m2, "y": precio, "x_titulo": "Metros cuadrados (m²)", "y_titulo": "Precio (miles de USD)", "diagonal": False}
    t_disp1 = ("Diagrama de dispersión (X = metros cuadrados, Y = precio en miles de USD) de 13 departamentos: "
               + "; ".join(f"({a}, {b})" for a, b in zip(m2, precio))
               + f". Correlación de Pearson r = {r_all:.2f}. El punto (62, 210) se aleja de la tendencia del resto.")

    out.append(_p(
        "R07", 7, t, 2, f"{CTX_INMO} {rep}", "Dispersión",
        f"El diagrama muestra los metros cuadrados (eje X) y el precio de venta (eje Y) de 13 departamentos; la correlación es r = {r_all:.2f}. "
        "Interprételo: dirección, forma y fuerza de la relación, el cambio aproximado del precio por cada m² adicional y cualquier punto "
        "atípico (indique cuál y cómo afecta la lectura).",
        f"La relación es positiva (a más m², mayor precio), aproximadamente lineal y fuerte (r = {r_all:.2f}). La pendiente es de unos "
        f"{b_all:.1f} mil USD por m² adicional (≈ {b_sin:.1f} si se excluye el atípico). El punto atípico es el de 62 m² y 210 mil USD: los "
        f"departamentos de tamaño parecido (58 y 65 m²) cuestan 131 y 122 mil, así que es mucho más caro de lo esperado (puede deberse a ubicación, acabados o un "
        f"error de registro). Ese punto debilita la correlación: sin él r = {r_sin:.2f}. Se recomienda revisarlo antes de modelar.",
        ["Describe la dirección positiva y la forma aproximadamente lineal de la relación.",
         f"Valora la fuerza con el coeficiente (r = {r_all:.2f}, fuerte) y/o la dispersión de los puntos.",
         f"Interpreta la pendiente en unidades de negocio (≈ {b_all:.1f} mil USD por m² adicional; se acepta un rango razonable por lectura visual).",
         f"Identifica el punto atípico (62 m², 210 mil USD) y explica su efecto o qué haría con él (r sin el atípico ≈ {r_sin:.2f})."],
        d_disp1, t_disp1))

    real2 = [150, 200, 120, 300, 250, 180, 220, 140, 260, 190, 170, 280]
    pred2 = [145, 210, 118, 280, 255, 176, 214, 138, 255, 188, 230, 276]
    err2 = [p - r for r, p in zip(real2, pred2)]
    j = max(range(len(err2)), key=lambda k: abs(err2[k]))
    mae2 = sum(abs(e) for e in err2) / len(err2)
    mae2_sin = sum(abs(e) for k, e in enumerate(err2) if k != j) / (len(err2) - 1)
    max_resto = max(abs(e) for k, e in enumerate(err2) if k != j)
    d_disp2 = {"tipo": "grafico", "grafico": "dispersion", "titulo": "Precio real vs precio predicho (12 departamentos)",
               "x": real2, "y": pred2, "x_titulo": "Precio real (miles de USD)", "y_titulo": "Precio predicho (miles de USD)",
               "diagonal": True}
    t_disp2 = ("Diagrama de dispersión de precio real (X) vs predicho (Y), miles de USD, con la recta diagonal ŷ = y, para 12 departamentos: "
               + "; ".join(f"Depto {k + 1}: ({r}, {p})" for k, (r, p) in enumerate(zip(real2, pred2)))
               + f". El Depto {j + 1} queda muy por encima de la recta.")

    out.append(_p(
        "R08", 8, t, 2, f"{CTX_INMO} {rep}", "Dispersión",
        "Cada punto del gráfico es un departamento de prueba y la recta diagonal representa ŷ = y (predicción perfecta). Analice el "
        "desempeño del modelo: ¿qué significa que un punto quede sobre o bajo la recta?, ¿qué punto destaca y cuál es su error?, ¿cómo "
        "afecta ese punto al MAE y qué causas revisaría?",
        f"Un punto en la diagonal tiene error cero; por encima de ella el modelo sobreestima (predicción mayor que el valor real) y por "
        f"debajo subestima. Casi todos los puntos están pegados a la diagonal (errores de hasta {max_resto} mil USD), salvo el Depto {j + 1} "
        f"(real {real2[j]}, predicho {pred2[j]}): sobreestima en {abs(err2[j])} mil USD ({abs(err2[j]) / real2[j]:.0%} de su precio). Ese caso "
        f"eleva el MAE de {_fmt(mae2_sin)} mil USD (sin él) a {_fmt(mae2)} mil USD. Causas a revisar: error de registro del precio o de las "
        "variables, característica no considerada (vista, antigüedad, estado), o un caso atípico que el modelo lineal no captura.",
        ["Explica el significado de estar sobre (sobreestima) o bajo (subestima) la diagonal ŷ = y.",
         f"Identifica el punto que destaca (Depto {j + 1}: real {real2[j]}, predicho {pred2[j]}) y su error (≈ {abs(err2[j])} mil USD).",
         f"Indica que el resto está cerca de la diagonal y/o cómo ese punto eleva el MAE (de ≈ {_fmt(mae2_sin)} a ≈ {_fmt(mae2)}).",
         "Propone causas plausibles o acciones (revisar datos, variables omitidas, atípico, no linealidad)."],
        d_disp2, t_disp2))

    out.append(_p(
        "R09", 9, t, 2, f"{CTX_INMO} {rep}", "Dispersión",
        f"Con base en el diagrama de metros cuadrados y precio (r = {r_all:.2f}), redacte 3-4 líneas para el Gerente de Ventas con una conclusión "
        "sobre la relación, una limitación (por ejemplo, correlación no implica causalidad o el punto atípico) y una acción.",
        f"Ejemplo de respuesta válida: «Los departamentos más grandes tienen precios más altos de forma clara (r = {r_all:.2f}; unos "
        f"{b_all:.1f} mil USD por m² adicional). Esto no significa que ampliar un departamento garantice ese aumento, porque otros factores como "
        "el distrito también influyen, y un caso (62 m², 210 mil USD) se sale del patrón. Recomiendo usar los m² como referencia inicial del "
        "precio de lista, revisar ese caso y completar el análisis con distrito y habitaciones.»",
        ["Redacción breve (3-4 líneas) y en lenguaje para un gerente.",
         f"Formula la conclusión con evidencia del gráfico (relación positiva y fuerte, r = {r_all:.2f}, pendiente aproximada).",
         "Incluye una limitación válida (correlación no es causalidad, otras variables, punto atípico, pocos datos).",
         "Propone una acción concreta y coherente (usar como referencia, revisar el atípico, incorporar otras variables)."],
        d_disp1, t_disp1))

    # ------------------------- Cajas ------------------------- #
    grupos_precio = {
        "Norte": [120, 135, 140, 150, 155, 160, 170, 185, 210],
        "Sur": [100, 110, 115, 120, 125, 130, 135, 140, 260],
        "Centro": [180, 200, 220, 240, 250, 260, 280, 300, 320],
    }
    est = {k: (*_cuartiles(v), _limites(v)[0], _atipicos(v)) for k, v in grupos_precio.items()}   # q1,q2,q3,iqr,atip
    d_cajas1 = {"tipo": "grafico", "grafico": "cajas", "titulo": "Precio de venta por distrito (9 departamentos por distrito)",
                "grupos": grupos_precio, "x_titulo": "Distrito", "y_titulo": "Precio (miles de USD)"}
    t_cajas1 = ("Diagrama de cajas del precio (miles de USD) por distrito. "
                + "; ".join(f"{k}: Q1={_fmt(v[0])}, mediana={_fmt(v[1])}, Q3={_fmt(v[2])}, RIC={_fmt(v[3])}, atípicos={v[4] or 'ninguno'}"
                            for k, v in est.items()) + ".")
    caro = max(est, key=lambda k: est[k][1]); barato = min(est, key=lambda k: est[k][1])
    var_alta = max(est, key=lambda k: est[k][3]); var_baja = min(est, key=lambda k: est[k][3])

    out.append(_p(
        "R10", 10, t, 2, f"{CTX_INMO} {rep}", "Cajas (boxplot)",
        "El diagrama de cajas resume el precio de venta de departamentos en tres distritos. Interprételo: compare las medianas, compare la "
        "dispersión (tamaño de las cajas), identifique valores atípicos y concluya qué distrito es más caro y cuál es más homogéneo.",
        f"Medianas: {', '.join(f'{k} {_fmt(v[1])}' for k, v in est.items())} (miles de USD); {caro} es el distrito más caro y {barato} el más "
        f"barato (la caja de {caro} está casi totalmente por encima de las otras). Dispersión (RIC = Q3 − Q1): "
        f"{', '.join(f'{k} {_fmt(v[3])}' for k, v in est.items())}; {var_alta} es el más variable y {var_baja} el más homogéneo. Hay un valor "
        f"atípico en {', '.join(k for k, v in est.items() if v[4])} ({', '.join(_fmt(a) for k, v in est.items() for a in v[4])} mil USD), muy por "
        "encima del resto de su distrito: conviene revisarlo (¿propiedad especial o error?). La mediana y la caja no se distorsionan por él. "
        "Cautela: son solo 9 departamentos por distrito.",
        [f"Compara las medianas (más alta: {caro} ≈ {_fmt(est[caro][1])}; más baja: {barato} ≈ {_fmt(est[barato][1])}).",
         f"Compara la dispersión por el tamaño de la caja (más variable: {var_alta}; más homogéneo: {var_baja}).",
         "Identifica el valor atípico (distrito Sur, 260 mil USD) como punto fuera de los bigotes y propone revisarlo.",
         "Concluye con una lectura de negocio o cautela (distrito más caro, pocos datos por grupo, la mediana es robusta al atípico)."],
        d_cajas1, t_cajas1))

    ing_acepta = [28, 32, 35, 38, 40, 42, 45, 48, 52, 60, 95]
    ing_no = [18, 22, 25, 27, 30, 32, 34, 36, 40, 44, 48]
    qa, qn = _cuartiles(ing_acepta), _cuartiles(ing_no)
    solapan = qa[0] < qn[2]
    atip_a, atip_n = _atipicos(ing_acepta), _atipicos(ing_no)
    d_cajas2 = {"tipo": "grafico", "grafico": "cajas", "titulo": "Ingresos anuales según aceptación del préstamo",
                "grupos": {"Acepta": ing_acepta, "No acepta": ing_no}, "x_titulo": "Respuesta del cliente",
                "y_titulo": "Ingresos anuales (miles de S/)"}
    t_cajas2 = (f"Diagrama de cajas de ingresos anuales (miles de S/) por respuesta del cliente. Acepta (n=11): Q1={_fmt(qa[0])}, "
                f"mediana={_fmt(qa[1])}, Q3={_fmt(qa[2])}, atípicos={atip_a or 'ninguno'}. No acepta (n=11): Q1={_fmt(qn[0])}, "
                f"mediana={_fmt(qn[1])}, Q3={_fmt(qn[2])}, atípicos={atip_n or 'ninguno'}.")

    out.append(_p(
        "R11", 11, t, 1, f"{CTX_BANCO} {rep}", "Cajas (boxplot)",
        "El diagrama compara los ingresos anuales de los clientes que aceptaron y que no aceptaron el préstamo. Analice si Ingresos Anuales "
        "sirve para distinguir entre ambos grupos: compare medianas, evalúe si las cajas se solapan, interprete los atípicos y concluya "
        "qué implica para usar esta variable en el modelo.",
        f"La mediana de ingresos de quienes aceptan ({_fmt(qa[1])}) es mayor que la de quienes no aceptan ({_fmt(qn[1])}), y toda la caja de "
        f"'Acepta' está desplazada hacia arriba. Sin embargo, {'las cajas se solapan: el Q1 de Acepta (' + _fmt(qa[0]) + ') es menor que el Q3 de No acepta (' + _fmt(qn[2]) + ')' if solapan else 'las cajas no se solapan'}, "
        f"por lo que ingresos separa parcialmente los grupos pero no los distingue por sí solo. Hay un valor atípico alto en 'Acepta' "
        f"({', '.join(_fmt(a) for a in atip_a)} mil S/); es un cliente de ingresos muy altos que no representa al grupo. Implicancia: Ingresos "
        "Anuales aporta información útil y conviene incluirla en el modelo, junto con otras variables (Deuda, Edad, Nivel Educativo), "
        "pues sola no basta para clasificar.",
        [f"Compara las medianas (Acepta ≈ {_fmt(qa[1])} vs No acepta ≈ {_fmt(qn[1])}) e indica que los aceptantes tienen ingresos mayores.",
         "Evalúa el solapamiento de las cajas y concluye que la separación es parcial (no basta por sí sola).",
         f"Identifica e interpreta el atípico alto en 'Acepta' ({', '.join(_fmt(a) for a in atip_a)} mil S/).",
         "Concluye sobre su uso en el modelo (variable informativa pero insuficiente; combinar con otras)."],
        d_cajas2, t_cajas2))

    s = grupos_precio["Sur"]
    q1s, _, q3s = _cuartiles(s)
    iqr_s, lo_s, hi_s = _limites(s)
    out.append(_p(
        "R12", 12, t, 2, f"{CTX_INMO} {rep}", "Cajas (boxplot)",
        "Explique qué representan la caja, la línea central, los bigotes y los puntos de un diagrama de cajas. Luego, para el distrito Sur "
        "(precios: 100, 110, 115, 120, 125, 130, 135, 140, 260), calcule Q1, Q3, el rango intercuartílico (RIC) y el límite superior del "
        "bigote (Q3 + 1.5·RIC) para verificar si 260 es un valor atípico. ¿Cuándo preferiría cajas a barras con promedios?",
        f"La caja va de Q1 a Q3 (contiene el 50 % central de los datos); la línea central es la mediana; los bigotes se extienden hasta el "
        f"dato más lejano dentro de 1.5·RIC desde la caja; los puntos fuera de los bigotes son valores atípicos. Para Sur: Q1 = {_fmt(q1s)}, "
        f"Q3 = {_fmt(q3s)}, RIC = {_fmt(iqr_s)}; límite superior = {_fmt(q3s)} + 1.5·{_fmt(iqr_s)} = {_fmt(hi_s)}. Como 260 > {_fmt(hi_s)}, es atípico. "
        "Se prefieren cajas a barras de promedios cuando interesa ver la distribución (mediana, dispersión, asimetría y atípicos): el promedio "
        "oculta la dispersión y se distorsiona con valores extremos (aquí 260 eleva la media de Sur).",
        ["Describe los elementos: caja (Q1-Q3), línea central (mediana), bigotes y puntos atípicos.",
         f"Calcula correctamente Q1 ({_fmt(q1s)}), Q3 ({_fmt(q3s)}) y RIC ({_fmt(iqr_s)}).",
         f"Calcula el límite superior ({_fmt(hi_s)}) y concluye que 260 es atípico.",
         "Justifica cajas frente a barras de promedios (muestran dispersión y atípicos; el promedio los oculta o se distorsiona)."],
        d_cajas1, t_cajas1))

    # ------------------------- Comunicación del reporte (sin gráfico) ------------------------- #
    cm = "Comunicación del reporte"
    out.append(_p(
        "R13", 13, t, 1, rep, cm,
        "Describa la estructura que debería tener un reporte de un proyecto de ciencia de datos dirigido a la gerencia y qué iría en cada sección.",
        "Estructura típica: (1) resumen ejecutivo con el hallazgo principal y la recomendación; (2) contexto y objetivo del negocio; (3) datos y "
        "metodología resumidos; (4) resultados con métricas y gráficos clave; (5) interpretación y limitaciones; (6) conclusiones y "
        "recomendaciones con próximos pasos; (7) anexos técnicos para quien quiera el detalle.",
        ["Incluye un resumen ejecutivo al inicio con hallazgo y recomendación.",
         "Incluye contexto/objetivo y una descripción de datos y metodología.",
         "Incluye resultados (métricas, gráficos) e interpretación o limitaciones.",
         "Incluye conclusiones/recomendaciones y propone anexos técnicos para el detalle."]))
    out.append(_p(
        "R14", 14, t, 1, rep, cm,
        "Compare cómo presentaría los resultados del Caso 1 (banco) a un comité técnico y al Gerente de Marketing. Ilustre con un ejemplo de "
        "cómo reformularía una métrica.",
        "Al comité técnico: matriz de confusión, precisión, recall, F1, umbral, validación y limitaciones, con detalle metodológico. Al gerente: "
        "lenguaje de negocio, pocas cifras, impacto en costos y decisiones, y una recomendación clara. Ejemplo: en vez de 'precisión = 33 %', "
        "decir 'de cada 100 llamadas sugeridas por el modelo, 33 terminan en préstamo y 67 son improductivas'.",
        ["Describe el enfoque técnico (métricas, método, limitaciones).",
         "Describe el enfoque gerencial (lenguaje de negocio, impacto, decisión).",
         "Da un ejemplo concreto de reformulación de una métrica en términos de negocio.",
         "Argumenta que el nivel de detalle depende de lo que la audiencia necesita decidir."]))
    out.append(_p(
        "R15", 15, t, 2, rep, cm,
        "¿Qué limitaciones y riesgos incluiría en el reporte del modelo inmobiliario (Caso 2) y por qué es importante declararlas?",
        "Muestra de prueba muy pequeña (5 departamentos) que vuelve inestables el MAE y el R²; posible sesgo si los datos no representan todos "
        "los distritos o épocas; variables omitidas; riesgo de extrapolar fuera del rango de precios observado; errores mayores en ciertos "
        "segmentos; posible fuga de datos si hubo mala partición. Declararlas evita decisiones sobreconfiadas, protege la credibilidad del "
        "análisis y orienta mejoras (más datos, validación cruzada).",
        ["Menciona la limitación del tamaño de la muestra de prueba.",
         "Menciona al menos otra limitación (representatividad, variables omitidas, extrapolación, errores por segmento).",
         "Explica por qué declararlas importa (evitar sobreconfianza, credibilidad).",
         "Vincula las limitaciones con acciones de mejora o validación."]))
    out.append(_p(
        "R16", 16, t, 1, rep, cm,
        "¿Cómo redactaría las recomendaciones de un reporte para que sean accionables y estén respaldadas por la evidencia? Dé un ejemplo para el Caso 1.",
        "Cada recomendación debe ser concreta, estar ligada a un resultado (métrica o hallazgo), indicar el beneficio o costo esperado y proponer "
        "un siguiente paso verificable, con responsable o plazo cuando sea posible. Ejemplo: 'Usar el modelo para priorizar la lista de llamadas "
        "y hacer un piloto de 4 semanas comparando umbrales 0.5 y 0.3, porque bajar el umbral aumenta el recall y se evaluará si la ganancia por "
        "préstamo compensa el costo por llamada'.",
        ["Indica que la recomendación debe ser concreta y accionable.",
         "Indica que debe apoyarse en un resultado o métrica del análisis.",
         "Incluye beneficio/costo esperado o criterio de decisión.",
         "Da un ejemplo coherente para el Caso 1 con un siguiente paso verificable (piloto, umbral, costos)."]))
    return out


def dimensiones_teoria(tema: str) -> list[str]:
    return DIMS_SKLEARN if tema == TEMA_SKLEARN else DIMS_REPORTES


def obtener_teoria(tema: str) -> list[Problema]:
    """Devuelve las preguntas escritas del tema ('Scikit-learn' o 'Reportes de datos')."""
    return _sklearn() if tema == TEMA_SKLEARN else _reportes()
