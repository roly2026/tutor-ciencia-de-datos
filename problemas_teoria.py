"""Preguntas teóricas (respuesta escrita) de los temas Scikit-learn y Reportes de ciencia de datos.

Cada tema tiene 8 preguntas. No llevan datos numéricos: se evalúan con la misma rúbrica
de 4 criterios x 0.5 pts que las demás, así que `tutor.evaluar_respuesta` funciona igual.

Requiere que la dataclass `Problema` tenga el campo `subtema: str = ""` (ver instrucciones).
"""
from __future__ import annotations

from problemas import Problema

TEMA_SKLEARN = "Scikit-learn"
TEMA_REPORTES = "Reportes de datos"

CONTEXTO_SKLEARN = (
    "Curso de Introducción a Data Science · uso de scikit-learn en el modelamiento (Caso 1: clasificación "
    "de aceptación de préstamo con Random Forest; Caso 2: precio de departamentos con regresión lineal "
    "múltiple). Responde con tus palabras; puedes incluir fragmentos cortos de código."
)
CONTEXTO_REPORTES = (
    "Curso de Introducción a Data Science · presentación de reportes de ciencia de datos "
    "(Caso 1: banco que prioriza llamadas; Caso 2: inmobiliaria que estima precios). "
    "Responde en prosa clara, como lo harías en el examen."
)


def _p(id_: str, n: int, tema: str, caso: int, contexto: str, sub: str,
       enunciado: str, referencia: str, criterios: list[str]) -> Problema:
    return Problema(
        id=id_, caso=caso, tema=tema, dimension="Teoría", numero=n, contexto=contexto,
        enunciado=enunciado, puntaje_max=2.0, referencia=referencia,
        criterios=[f"(0.5) {c}" for c in criterios], subtema=sub,
    )


def _sklearn() -> list[Problema]:
    t, c, x = TEMA_SKLEARN, 3, CONTEXTO_SKLEARN
    return [
        _p("S01", 1, t, c, x, "Partición de datos",
           "Explique para qué se usa train_test_split, qué hacen los parámetros test_size, random_state y stratify, y cuándo "
           "conviene usar stratify=y en el Caso 1.",
           "train_test_split separa los datos en entrenamiento (para ajustar el modelo) y prueba (para evaluarlo con datos no "
           "vistos y estimar su desempeño real). test_size fija la proporción de prueba (p. ej. 0.2). random_state fija la "
           "semilla para que la partición sea reproducible. stratify=y conserva en ambos conjuntos la misma proporción de "
           "clases; conviene en el Caso 1 porque la clase 'acepta' es minoritaria (clases desbalanceadas) y una partición "
           "aleatoria simple podría dejar muy pocos positivos en prueba.",
           ["Explica el propósito: evaluar con datos no vistos / evitar evaluar donde se entrenó.",
            "Describe test_size y random_state (proporción y reproducibilidad).",
            "Explica qué hace stratify (mantiene la proporción de clases).",
            "Justifica su uso en el Caso 1 por el desbalance de clases."]),
        _p("S02", 2, t, c, x, "Preprocesamiento y Pipeline",
           "Describa cómo construiría con ColumnTransformer y Pipeline el preprocesamiento del Caso 2 (Metros Cuadrados, Habitaciones, "
           "Distrito). Indique qué transformador usaría para Distrito y qué ventaja tiene el Pipeline.",
           "Se define un ColumnTransformer que aplica OneHotEncoder (drop='first' en regresión lineal para evitar la trampa de "
           "las variables dummy) a 'Distrito' y deja pasar (passthrough) o escala las variables numéricas. Luego se encadena "
           "con el modelo en un Pipeline([('prep', ct), ('modelo', LinearRegression())]). Ventajas: un solo objeto que aplica "
           "el mismo preprocesamiento en fit y predict, evita fuga de datos (el preprocesamiento se aprende solo con "
           "entrenamiento, también dentro de la validación cruzada) y simplifica el despliegue.",
           ["Usa ColumnTransformer para tratar columnas por tipo (categórica vs numérica).",
            "Elige OneHotEncoder para Distrito (nominal) y menciona drop='first' o multicolinealidad.",
            "Encadena preprocesamiento y modelo en un Pipeline.",
            "Explica la ventaja: reproducibilidad / evita fuga de datos / un solo objeto para fit y predict."]),
        _p("S03", 3, t, c, x, "fit, transform y fuga de datos",
           "Diferencie fit, transform y fit_transform. ¿Por qué es un error ajustar (fit) un escalador o codificador con todos "
           "los datos antes de dividir en entrenamiento y prueba?",
           "fit aprende los parámetros a partir de los datos (media y desviación, categorías, coeficientes); transform los "
           "aplica; fit_transform hace ambos pasos sobre el mismo conjunto. Se usa fit_transform solo en entrenamiento y solo "
           "transform en prueba. Ajustar con todos los datos produce fuga de datos (data leakage): la información del conjunto "
           "de prueba influye en el preprocesamiento, y las métricas salen optimistas y no reflejan el desempeño con datos "
           "nuevos.",
           ["Define fit (aprende parámetros) y transform (los aplica).",
            "Explica fit_transform y en qué conjunto se usa cada método.",
            "Identifica el problema como fuga de datos (data leakage).",
            "Explica la consecuencia: métricas optimistas / evaluación no confiable."]),
        _p("S04", 4, t, c, x, "Validación cruzada",
           "¿Qué es la validación cruzada k-fold y qué ventaja tiene frente a una única partición entrenamiento/prueba? Indique "
           "cómo la usaría con cross_val_score en el Caso 2 y qué métrica elegiría.",
           "En k-fold los datos se dividen en k bloques; el modelo se entrena k veces, cada vez con k−1 bloques y validando en "
           "el restante, y se promedian los k resultados. Da una estimación más estable y menos dependiente de una partición "
           "afortunada o desafortunada, y aprovecha mejor datos escasos (útil con pocos departamentos). Ejemplo: "
           "cross_val_score(pipeline, X, y, cv=5, scoring='neg_mean_absolute_error'); scikit-learn maximiza el score, por eso "
           "las métricas de error se reportan con signo negativo y se multiplican por −1 para leer el MAE.",
           ["Describe correctamente k-fold (k particiones, k entrenamientos, promedio).",
            "Explica la ventaja: estimación más estable / menos dependiente de una sola partición.",
            "Muestra el uso de cross_val_score con cv y scoring apropiado para regresión.",
            "Menciona la convención de signo negativo del scoring o interpreta el promedio y la dispersión de los resultados."]),
        _p("S05", 5, t, c, x, "Métricas en sklearn.metrics",
           "Indique qué funciones de sklearn.metrics usaría para evaluar el Caso 1 (clasificación) y el Caso 2 (regresión), y qué "
           "debe pasarles como argumentos.",
           "Clasificación: confusion_matrix(y_real, y_pred), accuracy_score, precision_score, recall_score, f1_score "
           "(todas con y_real e y_pred en ese orden) y classification_report para un resumen. Regresión: "
           "mean_absolute_error(y_real, y_pred), mean_squared_error y su raíz (root_mean_squared_error en versiones "
           "recientes), r2_score, mean_absolute_percentage_error. Se evalúan siempre sobre el conjunto de prueba. El primer "
           "argumento es el valor real y el segundo la predicción.",
           ["Nombra al menos tres funciones de clasificación (confusion_matrix, precision_score, recall_score, etc.).",
            "Nombra al menos dos funciones de regresión (mean_absolute_error, r2_score, mean_squared_error...).",
            "Indica los argumentos correctos: y_real y y_pred.",
            "Señala que se calculan sobre el conjunto de prueba (datos no vistos)."]),
        _p("S06", 6, t, c, x, "Random Forest y umbral",
           "En RandomForestClassifier, ¿qué diferencia hay entre predict y predict_proba? ¿Cómo usaría predict_proba para ajustar "
           "el umbral de decisión del Caso 1 y qué hiperparámetros ajustaría ante clases desbalanceadas?",
           "predict devuelve la clase (0/1), que internamente equivale a umbral 0.5; predict_proba devuelve la probabilidad de "
           "cada clase. Con proba = modelo.predict_proba(X)[:, 1] se puede clasificar como (proba >= 0.3).astype(int) para "
           "subir el recall a costa de la precisión. Ante desbalance se puede usar class_weight='balanced' o "
           "'balanced_subsample', y ajustar n_estimators, max_depth y min_samples_leaf para controlar el sobreajuste.",
           ["Diferencia predict (clase) de predict_proba (probabilidad).",
            "Explica cómo aplicar un umbral propio sobre la columna de la clase positiva.",
            "Relaciona el cambio de umbral con el trade-off precisión-recall.",
            "Menciona hiperparámetros pertinentes (class_weight, n_estimators, max_depth, min_samples_leaf)."]),
        _p("S07", 7, t, c, x, "Regresión lineal",
           "Después de ajustar LinearRegression en el Caso 2, ¿qué contienen coef_ e intercept_ y cómo interpretaría el coeficiente de "
           "Metros Cuadrados y el de una dummy de Distrito?",
           "intercept_ es el valor esperado del precio cuando todas las variables valen 0 (término constante); coef_ es el "
           "vector de coeficientes, uno por variable de entrada, en el orden de las columnas. El coeficiente de Metros "
           "Cuadrados indica el cambio esperado del precio (miles de USD) por cada m² adicional, manteniendo las demás "
           "variables constantes. El de una dummy (p. ej. Norte) es la diferencia esperada de precio respecto de la categoría "
           "de referencia (Centro) con las demás variables iguales.",
           ["Explica qué son intercept_ y coef_ (constante y un coeficiente por variable).",
            "Interpreta el coeficiente de Metros Cuadrados con 'manteniendo constantes las demás'.",
            "Interpreta la dummy como diferencia respecto de la categoría de referencia.",
            "Usa unidades correctas (miles de USD) o indica que el orden de coef_ sigue el de las columnas."]),
        _p("S08", 8, t, c, x, "Ajuste de hiperparámetros",
           "Explique para qué sirve GridSearchCV, qué parámetros principales recibe y por qué, después de usarlo, se debe evaluar "
           "el mejor modelo en un conjunto de prueba que no participó en la búsqueda.",
           "GridSearchCV prueba todas las combinaciones de una grilla de hiperparámetros (param_grid) con validación cruzada "
           "(cv) según una métrica (scoring) y devuelve best_params_, best_score_ y best_estimator_. Recibe el estimador (o "
           "Pipeline), param_grid, cv y scoring. Como los hiperparámetros se eligen mirando el desempeño en validación, esa "
           "puntuación es optimista; un conjunto de prueba reservado da una estimación honesta del desempeño con datos "
           "nuevos y evita sobreajustar a la validación.",
           ["Explica el propósito: buscar la mejor combinación de hiperparámetros con validación cruzada.",
            "Menciona los parámetros principales: estimador, param_grid, cv, scoring.",
            "Indica los resultados útiles: best_params_ / best_estimator_ / best_score_.",
            "Justifica la evaluación final en un conjunto de prueba independiente (el score de validación es optimista)."]),
    ]


def _reportes() -> list[Problema]:
    t, c, x = TEMA_REPORTES, 4, CONTEXTO_REPORTES
    return [
        _p("R01", 1, t, c, x, "Estructura del reporte",
           "Describa la estructura que debería tener un reporte de un proyecto de ciencia de datos dirigido a la gerencia y qué "
           "iría en cada sección.",
           "Estructura típica: (1) resumen ejecutivo con el hallazgo principal y la recomendación; (2) contexto y objetivo del "
           "negocio; (3) datos y metodología resumidos (fuentes, variables, preprocesamiento, modelo); (4) resultados con "
           "métricas y gráficos clave; (5) interpretación y limitaciones; (6) conclusiones y recomendaciones con próximos "
           "pasos; (7) anexos técnicos para quien quiera el detalle.",
           ["Incluye un resumen ejecutivo al inicio con hallazgo y recomendación.",
            "Incluye contexto/objetivo y una descripción de datos y metodología.",
            "Incluye resultados (métricas, gráficos) e interpretación o limitaciones.",
            "Incluye conclusiones/recomendaciones y propone anexos técnicos para el detalle."]),
        _p("R02", 2, t, c, x, "Adaptación a la audiencia",
           "Compare cómo presentaría los resultados del Caso 1 a un comité técnico y al Gerente de Marketing. Ilustre con un "
           "ejemplo de cómo reformularía una métrica.",
           "Al comité técnico: matriz de confusión, precisión, recall, F1, umbral, validación y limitaciones del modelo, con "
           "detalle metodológico. Al gerente: lenguaje de negocio, pocas cifras, impacto en costos y decisiones y una "
           "recomendación clara. Ejemplo: en vez de 'precisión = 33 %', decir 'de cada 100 llamadas sugeridas por el modelo, "
           "33 terminan en préstamo y 67 son improductivas'.",
           ["Describe el enfoque técnico (métricas, método, limitaciones).",
            "Describe el enfoque gerencial (lenguaje de negocio, impacto, decisión).",
            "Da un ejemplo concreto de reformulación de una métrica en términos de negocio.",
            "Argumenta que el nivel de detalle depende de lo que la audiencia necesita decidir."]),
        _p("R03", 3, t, c, x, "Elección de gráficos",
           "¿Qué gráficos usaría para comunicar el desempeño del modelo del Caso 1 y del Caso 2? Justifique cada elección y mencione "
           "una mala práctica que evitaría.",
           "Caso 1: matriz de confusión como mapa de calor con conteos o porcentajes, y curva precisión-recall (o ROC) para "
           "mostrar el efecto del umbral. Caso 2: dispersión de valor real vs predicción con la recta ŷ = y, y gráfico de "
           "residuos o barras del error por departamento. Se justifica por lo que cada gráfico permite ver (tipos de error, "
           "trade-off, sesgo, casos atípicos). Malas prácticas: ejes truncados o sin unidades, 3D, colores sin significado, "
           "sobrecargar el gráfico.",
           ["Propone un gráfico adecuado para clasificación (matriz de confusión, curva PR/ROC).",
            "Propone un gráfico adecuado para regresión (real vs predicción, residuos).",
            "Justifica qué información aporta cada gráfico.",
            "Menciona una mala práctica a evitar (ejes engañosos, falta de unidades/títulos, exceso de elementos)."]),
        _p("R04", 4, t, c, x, "Comunicar métricas",
           "Explique cómo comunicaría a un público no técnico las métricas MAE y recall del Caso 1 y del Caso 2, evitando "
           "jerga. ¿Qué dos errores de comunicación evitaría?",
           "MAE: 'en promedio, nos equivocamos por X mil USD al estimar el precio', con su valor relativo al precio medio. "
           "Recall: 'de cada 100 clientes que sí aceptarían, el modelo detecta N'. Se usan unidades del negocio, "
           "comparaciones y ejemplos concretos. Errores a evitar: dar una sola métrica sin contexto (p. ej. solo exactitud con "
           "clases desbalanceadas) y presentar cifras sin decir qué decisión apoyan, o prometer certeza que el modelo no tiene.",
           ["Traduce el MAE a lenguaje de negocio con unidades.",
            "Traduce el recall a una frase del tipo 'de cada 100 ... detecta N'.",
            "Evita jerga y usa ejemplos o comparaciones con el negocio.",
            "Identifica dos errores de comunicación (métrica sin contexto, sobreprometer, no ligar a decisión)."]),
        _p("R05", 5, t, c, x, "Limitaciones y riesgos",
           "¿Qué limitaciones y riesgos incluiría en el reporte del modelo inmobiliario (Caso 2) y por qué es importante declararlas?",
           "Muestra de prueba muy pequeña (5 departamentos) que vuelve inestables MAE y R²; posible sesgo si los datos no "
           "representan todos los distritos o épocas; variables omitidas; riesgo de extrapolar fuera del rango de precios "
           "observado; errores mayores en ciertos segmentos; posible fuga de datos si hubo mala partición. Declararlas "
           "evita decisiones sobreconfiadas, protege la credibilidad del análisis y orienta mejoras (más datos, validación "
           "cruzada).",
           ["Menciona la limitación del tamaño de la muestra de prueba.",
            "Menciona al menos otra limitación (representatividad, variables omitidas, extrapolación, errores por segmento).",
            "Explica por qué declararlas importa (evitar sobreconfianza, credibilidad).",
            "Vincula las limitaciones con acciones de mejora o validación."]),
        _p("R06", 6, t, c, x, "Reproducibilidad",
           "Explique qué prácticas harían reproducible un análisis de ciencia de datos y por qué esto importa para quien lee el "
           "reporte.",
           "Fijar semillas (random_state), versionar el código (Git/GitHub), registrar versiones de librerías "
           "(requirements.txt), documentar el origen y el diccionario de datos, usar Pipelines y notebooks ordenados que se "
           "ejecuten de principio a fin, y guardar los parámetros del modelo. Importa porque otra persona (o el mismo analista "
           "meses después) debe obtener los mismos resultados y auditar cómo se llegó a ellos.",
           ["Menciona fijar semillas (random_state) y/o código ejecutable de principio a fin.",
            "Menciona control de versiones del código y/o de las librerías (requirements.txt).",
            "Menciona documentación de datos (origen, diccionario) y del proceso (Pipeline, parámetros).",
            "Explica por qué importa: verificar, auditar y repetir los resultados."]),
        _p("R07", 7, t, c, x, "Calidad de datos",
           "¿Qué aspectos de calidad de datos reportaría antes de presentar los resultados del modelo del Caso 1 y cómo los comunicaría?",
           "Valores faltantes (cantidad y tratamiento), valores atípicos o inconsistentes (p. ej. ingresos o deuda imposibles), "
           "duplicados, desbalance de clases (solo una minoría acepta), representatividad de la muestra y posibles sesgos, y "
           "las decisiones tomadas (imputar, eliminar, codificar). Se comunican en una sección breve o tabla de resumen con "
           "el impacto esperado en los resultados, dejando el detalle para un anexo.",
           ["Menciona faltantes y atípicos/inconsistencias.",
            "Menciona el desbalance de clases y/o la representatividad de la muestra.",
            "Indica que se reportan las decisiones de tratamiento tomadas (imputar, eliminar, codificar).",
            "Propone comunicarlo de forma breve (tabla/resumen) con su impacto y anexo para el detalle."]),
        _p("R08", 8, t, c, x, "Recomendaciones y siguientes pasos",
           "¿Cómo redactaría las recomendaciones de un reporte para que sean accionables y estén respaldadas por la evidencia? "
           "Dé un ejemplo para el Caso 1.",
           "Cada recomendación debe ser concreta, estar ligada a un resultado (métrica o hallazgo), indicar el beneficio o costo "
           "esperado y proponer un siguiente paso verificable, con responsable o plazo cuando sea posible. Ejemplo: 'Usar el "
           "modelo para priorizar la lista de llamadas y hacer un piloto de 4 semanas comparando umbrales 0.5 y 0.3, porque "
           "bajar el umbral aumenta el recall y se evaluará si la ganancia por préstamo compensa el costo por llamada'.",
           ["Indica que la recomendación debe ser concreta y accionable.",
            "Indica que debe apoyarse en un resultado o métrica del análisis.",
            "Incluye beneficio/costo esperado o criterio de decisión.",
            "Da un ejemplo coherente para el Caso 1 con un siguiente paso verificable (piloto, umbral, costos)."]),
    ]


def obtener_teoria(tema: str) -> list[Problema]:
    """Devuelve las preguntas teóricas del tema ('Scikit-learn' o 'Reportes de datos')."""
    return _sklearn() if tema == TEMA_SKLEARN else _reportes()
