# Preparador del examen final · Introducción a Data Science

Chatbot en Streamlit para que los estudiantes practiquen el examen final y conversen con un tutor.
Evalúa con rúbrica usando Gemini y registra el uso en Supabase.

## Flujo
1. **Ingreso con código de estudiante.** Solo entran los códigos listados en el secreto `codigos`.
2. **Elección de tema** (cada tema permite *Practicar* o *Conversar con el tutor*):
   | Tema | Qué recibe el estudiante |
   |---|---|
   | 🎯 Clasificación | Elige una de las 5 dimensiones del razonamiento cuantitativo (interpretación, representación, cálculo, análisis, argumentación) y una pregunta |
   | 📈 Regresión | Ídem |
   | 🧰 Scikit-learn | Una pregunta directa de código en Python (con "Otra pregunta" para cambiar) |
   | 🗂️ Reportes de datos | Una pregunta directa de interpretación de un gráfico (barras simples y dobles, dispersión, cajas) o de comunicación de resultados |
3. **Práctica:** escribe su respuesta, recibe puntaje (0 a 2), aciertos, errores y la solución modelo.
4. **Tutor:** chat socrático con hasta 3 niveles de pista; no entrega la respuesta final.
5. **Mi progreso:** logro por tema y por dimensión.

## Archivos
| Archivo | Función |
|---|---|
| `app.py` | Interfaz Streamlit (ingreso, temas, práctica, tutor, progreso) |
| `problemas.py` | Banco de Clasificación y Regresión (30 preguntas, rúbricas, variantes con otros números) |
| `problemas_teoria.py` | Banco de Scikit-learn (11 preguntas) y Reportes de datos (16, con gráficos) |
| `tutor.py` | Gemini: evaluador con rúbrica y tutor por niveles de pista |
| `base_datos.py` | Conexión a Supabase, validación de códigos y registro de datos |
| `config.py` | Constantes y lectura de secretos |
| `supabase_esquema.sql` | Tablas `intentos`, `mensajes_tutor`, `codigos_acceso` (la app las crea sola) |
| `supabase_resumen_docente.sql` | Opcional: vistas `resumen_uso` y `resumen_por_tema` (ejecutar a mano) |
| `.streamlit/secrets.toml.example` | Plantilla de secretos (sin valores reales) |

## Qué se guarda en Supabase
**`intentos`**: una fila cada vez que el estudiante pulsa *Evaluar* (también si Gemini falla):
`id, fecha_hora_lima, codigo, id_sesion, n_registro_sesion, tema, dimension, tiempo_resp_seg, veredicto, puntaje,
long_respuesta, modelo, error_tecnico, enunciado, pedido, respuesta, clave, id_pregunta, variante`.
`enunciado` = caso y datos mostrados; `pedido` = lo que se pide; `respuesta` = lo que escribió el estudiante;
`clave` = solución modelo.

**`mensajes_tutor`**: una fila por mensaje del chat (`rol` = estudiante o tutor, `texto`, `nivel_pista`, tema, dimensión y pregunta).

## Puesta en marcha
1. Sube todos estos archivos a GitHub (sin `secrets.toml`).
2. En Streamlit Community Cloud crea la app con `app.py` como archivo principal.
3. En *Settings > Secrets* pega el contenido de `.streamlit/secrets.toml.example` con tus valores reales.
4. La primera vez, la app crea las tablas en Supabase. Con `DEBUG = "true"` verás un botón *Probar conexión*.
5. Opcional: ejecuta `supabase_resumen_docente.sql` en el SQL Editor para consultar el uso por estudiante.

## Notas
- Los números de las preguntas los calcula Python; Gemini solo compara la respuesta con la rúbrica.
- Sin contraseña: quien conozca un código puede usarlo. No publiques la lista de códigos.
- Nunca subas claves ni contraseñas al repositorio.
