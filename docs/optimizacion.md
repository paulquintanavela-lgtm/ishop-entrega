# Optimización

> Este proyecto no entrena un modelo propio, así que no hay "hiperparámetros"
> en el sentido clásico (tasa de aprendizaje, profundidad de árbol, etc.).
> Lo equivalente en una arquitectura RAG son los **parámetros del pipeline de
> recuperación y generación**: cuántos documentos se recuperan, a partir de
> qué umbral de similitud se confía en ellos, cómo se parte el catálogo en
> documentos, y qué modelo de embeddings se usa. Este documento trata esos
> parámetros con el mismo estándar que pediría un análisis de hiperparámetros
> (Workshop S5): qué se exploró, qué se eligió y por qué, y qué quedó
> pendiente — declarado con honestidad.

## Proceso de optimización realizado

El ajuste fue **iterativo y guiado por la batería de pruebas de extremo a
extremo** (`chatbot/scripts/test_chatbot_e2e.py`, 13 casos reales), no un
barrido sistemático. Cada cambio de parámetro se validó corriendo la batería
y comparando el resultado contra la corrida anterior.

## Parámetros explorados y rangos

| Parámetro | Rango/alternativas consideradas | Valor final | Dónde |
| --- | --- | --- | --- |
| `topK` de recuperación (Qdrant) | 5, 8, 12 | **12** | workflow 04, nodo "Buscar evidencia en Qdrant" |
| Umbral de similitud para aceptar evidencia | 0.5, 0.6, 0.7 | **0.6** | nodo "Procesar evidencia RAG" |
| Unidad de indexación | chunks de tamaño fijo vs. un documento por producto | **un documento por producto** | `index_knowledge.py` |
| Modelo de embeddings | `nomic-embed-text` (local) vs. API de embeddings de pago | **`nomic-embed-text`, 768 dim., coseno** | `index_knowledge.py` |
| Lote de indexación | 8, 16, 24 documentos | **24**, con `keep_alive: -1` | `index_knowledge.py` |
| Productos mostrados por respuesta | 3, 5, todos los que calcen | **3 (top)** | nodo "Procesar evidencia RAG" |

## Resultados del análisis de sensibilidad

**No se ejecutó un análisis de sensibilidad formal** (barrer sistemáticamente
`topK` × umbral y registrar la curva de aciertos resultante), ni se generaron
*partial dependence plots* o un ranking cuantitativo de importancia de
parámetros. Esto se declara como limitación explícita, no se oculta.

Lo que sí se midió es el **efecto observado de cada cambio sobre la batería
de 13 casos e2e**, que funciona como evidencia indirecta de sensibilidad:

| Cambio | Resultado antes | Resultado después |
| --- | --- | --- |
| Corrección del nombre de la credencial de Qdrant (`qdrantUrl` en vez de `url`) | 3/13 correctas (respuestas vacías en cualquier consulta de catálogo) | **13/13 correctas** |
| Indexación con chunks de tamaño fijo (`ishop_knowledge`) → un documento por producto (`ishop_rag_v2`) | Búsquedas mezclaban fichas de productos distintos | Sin mezclas; comparaciones y recomendaciones consistentes |
| `contentType: raw` → `contentType: json` en los nodos HTTP hacia Gemini | El flujo caía en la plantilla de respaldo sin avisar (fallo silencioso por `neverError`) | Llamadas reales a Gemini, respuestas redactadas en vez de listadas |

De estos tres cambios, los dos con **mayor impacto observado** fueron la
corrección de la credencial de Qdrant (sin la cual el sistema no tenía
evidencia alguna) y el rediseño de la unidad de indexación (sin el cual la
evidencia recuperada era poco confiable aunque existiera).

## Ranking de importancia de los parámetros (cualitativo)

En ausencia de un barrido formal, el ranking siguiente se basa en el impacto
observado durante el desarrollo, de mayor a menor:

1. **Conectividad correcta a Qdrant** (prerequisito, no un hiperparámetro en
   sentido estricto, pero el de mayor impacto medido: 3/13 → 13/13).
2. **Unidad de indexación** (documento por producto vs. chunks): determina si
   la evidencia recuperada está "limpia" o mezclada.
3. **Umbral de similitud**: determina cuándo el asistente se abstiene de
   responder en vez de ofrecer evidencia débil.
4. **`topK`**: afecta cuánta evidencia llega al paso de redacción; valores
   muy bajos (5) dejaban fuera opciones relevantes en comparaciones con varias
   alternativas; 12 fue el valor con mejor cobertura sin saturar el contexto
   enviado a Gemini.
5. **Tamaño de lote de indexación**: afecta solo el tiempo de indexación, no
   la calidad de las respuestas.

## Configuración final y justificación

La configuración final (`topK=12`, umbral=0.6, un documento por producto,
embeddings `nomic-embed-text` locales, lotes de 24) es la que sostiene el
resultado reportado en
[`../RESULTADOS-Y-EVIDENCIAS.md`](../RESULTADOS-Y-EVIDENCIAS.md): **13/13**
en la batería e2e (tres ejecuciones seguidas, 39/39) y **219 documentos**
indexados sin mezclas detectadas en las pruebas.

## Comparación antes/después de la optimización

| Métrica | Baseline (primera prueba en producción) | Después de las correcciones |
| --- | --- | --- |
| Batería e2e (13 casos) | 3/13 correctas | 13/13 correctas |
| Tiempo promedio por respuesta (local) | 1.02 s (con plantilla de respaldo, sin llamadas reales a Gemini) | 2.83 s (con dos llamadas reales a Gemini por mensaje) |
| Mezcla de productos en una misma respuesta | Sí (chunks genéricos) | No observada en las pruebas (un documento por producto) |

El aumento de tiempo de respuesta (1.02 s → 2.83 s) es un **trade-off
consciente**: el sistema pasó de responder con una plantilla local fija a
redactar realmente con Gemini sobre la evidencia recuperada, lo que cuesta
más tiempo pero produce respuestas más naturales y contextuales.

## Qué queda pendiente (declarado con honestidad)

- Barrido sistemático de `topK` y umbral de similitud con la misma batería de
  preguntas, registrando la curva de aciertos.
- *Partial dependence plots* o un ranking cuantitativo (no solo cualitativo)
  de importancia de parámetros.
- Repetir la batería e2e en producción con el flujo ya corregido (la cifra de
  1.27 s vigente en producción es anterior a la corrección de las llamadas a
  Gemini).

Ver también [`../RESULTADOS-Y-EVIDENCIAS.md`](../RESULTADOS-Y-EVIDENCIAS.md)
§§5, 7 y 11 para el detalle completo y la lista de pendientes del proyecto.
