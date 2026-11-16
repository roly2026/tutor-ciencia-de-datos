# Preparador del examen final · Introducción a Data Science

Chatbot de práctica para **clasificación** y **regresión**, evaluado en las 5 dimensiones del
razonamiento cuantitativo (interpretación, representación, cálculo, análisis, argumentación).

| Archivo | Rol |
|---|---|
| `app.py` | Interfaz Streamlit: ingreso, práctica con rúbrica, tutor socrático, progreso |
| `problemas.py` | Banco de 30 preguntas (15 por tema), rúbricas, soluciones y generador de variantes |
| `tutor.py` | Gemini: evaluador (JSON con rúbrica) y tutor por niveles de pista |
| `base_datos.py` | Supabase: intentos (17 columnas), mensajes del tutor y validación opcional de códigos |
| `config.py` | Constantes y lectura de secretos |
| `supabase_schema.sql` | Tablas `intentos`, `mensajes`, `codigos_habilitados`, RLS y vista `resumen_docente` |

## Puesta en marcha
1. En Supabase > SQL Editor, ejecuta `supabase_schema.sql`.
2. Copia `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml` y completa las claves (no se sube a GitHub).
3. Local: `pip install -r requirements.txt` y `streamlit run app.py`.
4. Despliegue: sube el repo a GitHub, crea la app en Streamlit Community Cloud (archivo principal `app.py`)
   y pega las mismas claves en *Settings > Secrets*.

## Decisiones de diseño
- **Los números los calcula Python, no la IA.** `problemas.py` genera los datos y las respuestas de referencia; Gemini solo
  compara la respuesta del estudiante con la rúbrica.
- **Variantes:** "Examen modelo" usa los datos exactos del docx; "Variante nueva" cambia los números (semilla aleatoria).
- **Tutor:** 3 niveles de pista (pregunta guía → fórmula general → ejemplo análogo) y nunca entrega la respuesta final.
- **Datos para el docente:** consulta la vista `resumen_docente` o las tablas `intentos` y `mensajes`.

## Banco de preguntas
- 15 preguntas por tema (3 por dimensión): las 5 del examen modelo (P1-P10, marcadas con ★) y 10 de práctica (P11-P30).
- Todas usan el mismo caso y la misma matriz o tabla del examen modelo; las de costos (P17) agregan un costo por llamada de S/ 8 y una ganancia de S/ 150 por préstamo, escritos en el enunciado.
- Cada pregunta tiene una rúbrica de 4 criterios de 0.5 puntos (total 2.0). Se validó que las referencias no tengan marcadores sin reemplazar y que P17 sea coherente en 300 variantes.

## Ingreso y registro de datos
- El estudiante ingresa **solo con su código** (4 a 20 caracteres alfanuméricos, `-` o `_`; se guarda en mayúsculas).
- Cada ingreso crea un `id_sesion`; `n_registro_sesion` cuenta los intentos dentro de la sesión.
- Cada clic en *Evaluar* guarda una fila en `intentos`, también cuando falla Gemini (`veredicto = 'Error técnico'`, `error_tecnico` con el mensaje).
- `fecha_hora_lima` la asigna la base de datos en zona `America/Lima`.
- Para restringir el acceso, carga los códigos del curso en la tabla `codigos_habilitados`. Si está vacía, entra cualquier código.

## Límites conocidos
- Sin contraseña: quien conozca un código puede usarlo. `codigos_habilitados` reduce el riesgo, pero no lo elimina.
- Verifica el nombre vigente del modelo Gemini (`GEMINI_MODEL` en secretos; por defecto `gemini-2.5-flash`).
