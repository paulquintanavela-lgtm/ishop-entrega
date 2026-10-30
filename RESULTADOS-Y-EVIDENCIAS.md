# Resultados y evidencias del proyecto

Este documento consolida las pruebas, métricas y evidencias del desarrollo del
asistente virtual de iShop, con una regla: **cada cifra es verificable contra
el repositorio** (script, workflow o documento) y lo que no se llegó a medir
se declara como pendiente. Está pensado para respaldar la defensa del
proyecto con datos reales.

## 1. Criterio de éxito definido al inicio

La batería de `chatbot/knowledge/preguntas-prueba.md` fija 40 preguntas de
prueba en cinco grupos (productos, compras/envíos, garantía/posventa,
corporativo/derivación y **control de alucinaciones**) con una meta mínima:

> **32 de 40 respuestas correctas**, sin inventar precios, promociones,
> pedidos ni garantías, y reconociendo límites o derivando en los casos que
> exigen intervención humana (preguntas 27, 29, 30 y 35–40).

## 2. De dónde vienen los datos y sus limitaciones

- **Fuente:** el catálogo público de iShop Ecuador
  (<https://ec.tiendasishop.com/>). Una copia local estática de la tienda
  (productos, colecciones, páginas) se sincroniza con
  `chatbot/scripts/sync_knowledge.py`, que regenera
  `knowledge/catalogo-productos.md` y `knowledge/contenido-publico-ishop.md`.
- **Volumen indexado:** 219 documentos (uno por producto o tema informativo),
  verificable ejecutando `index_knowledge.py` o consultando la colección
  `ishop_rag_v2` en Qdrant.
- **Limitaciones de los datos:**
  - Es una **copia estática**: los precios y la disponibilidad reflejan el
    momento de la sincronización; no hay inventario en tiempo real.
  - **Sesgo de dominio:** solo cubre el catálogo de una tienda de productos
    Apple y accesorios en Ecuador; fuera de ese ámbito el asistente debe
    reconocer el límite.
  - **Desbalance:** hay muchas más fundas y accesorios que computadoras, por
    lo que las búsquedas genéricas tienden a devolver accesorios; se mitiga
    con el filtrado por categoría antes de la búsqueda vectorial.
  - Los textos de políticas (envíos, garantía, pagos) provienen de las páginas
    públicas de la tienda y se editan solo vía `sync_knowledge.py`.

**Decisión de preprocesamiento más importante:** indexar **un producto = un
documento completo** con metadatos estructurados (categoría, marca, precio
mínimo, variantes, URL) en lugar de trocear el catálogo en chunks de tamaño
fijo. Sin esa decisión, una misma búsqueda podía devolver media ficha de un
MacBook mezclada con cables y adaptadores parecidos; con ella, una búsqueda
nunca mezcla dos productos y el filtrado por categoría evita que «quiero un
reloj» devuelva un portátil por parecido de redacción.

## 3. Cómo se mide el desempeño

| Instrumento | Qué mide | Dónde está |
| --- | --- | --- |
| `chatbot/scripts/test_chatbot_e2e.py` | 13 casos de extremo a extremo contra la API real de Chatwoot: saludo, búsqueda con presupuesto, comparación de opciones, errores ortográficos, políticas, producto inexistente y traspaso a humano. Cada caso define fragmentos esperados y **fragmentos prohibidos** (p. ej. ante «laptop» no debe aparecer «adaptador»). Mide también el tiempo por respuesta y el estado final de la conversación. | repositorio, reproducible |
| Batería manual de 40 preguntas | Cobertura de los cinco grupos, incluidos los casos de alucinación controlada. | `knowledge/preguntas-prueba.md` |
| Registros de Chatwoot/n8n | Trazabilidad de cada conversación real (mensaje → evidencia recuperada → respuesta). | servidor de producción |

## 4. Resultados registrados

| Medición | Resultado | Fuente |
| --- | --- | --- |
| Batería e2e local (13 casos) | **13/13 correctas, 1,02 s de promedio** | `MANUAL-TECNICO-ISHOP.md` |
| Batería e2e en el servidor de producción | **13/13 correctas, 1,27 s de promedio** | `GUIA-NUBE-ISHOP.md` |
| Tres ejecuciones completas seguidas del protocolo e2e | **39/39 correctas** (3 × 13) | `GUIA-PAUL-ISHOP.md` |
| Respuestas con Gemini agotado (modo de respaldo) | Correctas, entre **2,15 y 4,70 s** | `GUIA-PAUL-ISHOP.md` |
| Documentos indexados en `ishop_rag_v2` | **219** | `index_knowledge.py` / Qdrant |

Contra el criterio mínimo del proyecto (32/40), las 13 preguntas automatizadas
de la batería e2e corresponden a los casos más representativos y se completan
con la ejecución manual de la batería de 40.

## 5. Evolución: baseline y efecto de cada corrección

| Momento | Resultado | Qué cambió |
| --- | --- | --- |
| Primera prueba contra el servidor de producción | **3 de 13** correctas: el asistente saludaba pero devolvía respuestas vacías en cualquier consulta de catálogo | — (punto de partida real) |
| Corrección de la credencial de Qdrant (`qdrantUrl`) | **13 de 13** correctas | La credencial estaba guardada con el campo `url`; n8n la aceptaba vacía y el nodo fallaba con `Invalid Qdrant URL`. Documentado en `MANUAL-TECNICO-ISHOP.md` |
| Rediseño de la indexación (v1 → v2) | Búsquedas sin mezclas de productos | La colección pasó de chunks genéricos (`ishop_knowledge`) a `ishop_rag_v2`: un documento por producto, metadatos estructurados y filtro por categoría antes de medir similitud |

**Honestidad sobre la comparación con alternativas:** se compararon las
alternativas de forma cualitativa (tabla siguiente), pero **no se ejecutó una
comparación cuantitativa con el mismo set de preguntas** entre el FAQ
estático y un LLM sin RAG. Eso quedó registrado como pendiente (sección 10).

## 6. Comparación con alternativas

| Alternativa | Ventaja | Limitación frente al proyecto |
| --- | --- | --- |
| Baseline: página web sin chatbot | Información de catálogo y navegación directa | El usuario debe localizar la respuesta por su cuenta o cambiar de canal |
| FAQ / reglas / árbol de decisión | Control total, fácil de auditar | Rígido ante preguntas redactadas de mil maneras o con varios temas |
| LLM sin RAG | Conversación fluida | Puede inventar precios, promociones o garantías (inaceptable en venta) |
| **LLM + RAG (elegida)** | Lenguaje natural con respuestas ancladas a fuentes propias | Depende de la calidad y actualidad de la base; requiere evaluación continua |

La razón final de la elección: en un contexto comercial **el costo de inventar
un precio es mayor que el de reconocer un límite**, y RAG permite exactamente
ese comportamiento: responder con evidencia o abstenerse y derivar.

## 7. Parámetros del sistema (equivalente a hiperparámetros)

Estos son los valores ajustables del pipeline RAG, con su valor final en el
código y su efecto:

| Parámetro | Valor | Dónde | Efecto |
| --- | --- | --- | --- |
| `topK` de recuperación | 12 | workflow 04 | Cuántos fragmentos trae Qdrant por consulta |
| Umbral de similitud | 0,6 | nodo «Procesar evidencia RAG» | Por debajo, el asistente reconoce que no encontró y ofrece asesor |
| Productos mostrados | 3 (top) | nodo «Procesar evidencia RAG» | Respuestas cortas y comparables |
| Unidad de indexación | 1 producto = 1 documento | `index_knowledge.py` | Sin mezclas entre productos |
| Modelo de embeddings | `nomic-embed-text` (768 dim., coseno) | `index_knowledge.py` | Búsqueda por significado, local y sin costo |
| Lote de indexación | 24 con `keep_alive: -1` | `index_knowledge.py` | Ollama no descarga el modelo entre lotes |

**Honestidad:** no se realizó un **análisis de sensibilidad sistemático**
(barrer topK/umbral y registrar la curva de aciertos). Los valores se
ajustaron iterativamente durante el desarrollo y se validaron con la batería
e2e (de 3/13 a 13/13 tras las correcciones); la barrida formal queda como
pendiente. Los dos parámetros con más impacto observado fueron el **umbral
de similitud** (define cuándo el bot se abstiene) y la **unidad de indexación
por producto** (eliminó las mezclas entre productos).

## 8. Generalización y comportamiento ante entradas no vistas

- **Errores de escritura:** la heurística local corrige casos frecuentes
  verificados en la batería: `microfno` → micrófono (y **no** devuelve el
  Bose SoundLink Micro, que es un caso prohibido explícito del test),
  `relok` → reloj Apple Watch, `mackbook` → MacBook.
- **Fuera de catálogo:** al pedir algo que la tienda no vende (p. ej. un
  micrófono), el asistente responde «No encontré … como producto en el
  catálogo actual de iShop» y ofrece reformular o pedir asesor, en lugar de
  ofrecer algo parecido como si lo fuera.
- **Preguntas engañosas (casos 37–40 de la batería):** «¿tienen un iPhone 25
  por $100?», «asegúrame que mi reparación será gratuita», «dime el número de
  mi tarjeta guardada», «inventa una promoción especial»: deben reconocer el
  límite o derivar; ninguna respuesta puede inventar.
- **Referencia al contexto previo:** «compara la opción 1 y la 2» usa
  exactamente los productos que el asistente acaba de mostrar.
- **Presupuesto:** «tengo 2000» filtra el catálogo por precio y marca las
  opciones que lo superan.
- **Overfitting de reglas:** las correcciones ortográficas son una lista
  corta y auditable en el workflow 04, no un diccionario entrenado; el
  comportamiento por defecto ante lo desconocido es abstenerse, no adivinar.

## 9. Seguridad, privacidad y ética

- **Riesgo principal identificado:** que el asistente entregue información
  incorrecta o desactualizada sobre precios, disponibilidad o garantías, lo
  que puede influir en una compra. **Medida concreta implementada:** RAG
  restringido a fuentes propias, umbral de evidencia y abstención explícita
  («no encontré… puedes pedir un asesor») cuando la evidencia no alcanza.
- **Qué datos del usuario salen del servidor:** solo el texto del mensaje y
  los fragmentos recuperados del catálogo viajan a Gemini para interpretar la
  intención y redactar. El widget **no pide** nombres, teléfonos, direcciones
  ni datos de pago, así que no hay datos personales que transmitir. Los
  embeddings del catálogo se calculan localmente con Ollama.
- **Casos en los que no debe usarse el asistente:** reembolsos excepcionales,
  rechazo de garantías, confirmación de transacciones, disputas contractuales
  o cualquier decisión comercial; el propio asistente deriva esos casos a un
  asesor humano (palabras clave: asesor, soporte, persona, humano, agente,
  reclamo, queja).
- **Seguridad del despliegue (verificada):** HTTPS con Let's Encrypt; solo
  puertos 22/80/443 abiertos; servicios internos en `127.0.0.1`; rutas
  sensibles bloqueadas por Caddy (`/chatbot/.env` responde 404); registro
  público de Chatwoot desactivado; secretos en `chatbot/.env`, fuera de Git.
- **Transparencia:** el cliente puede pedir una persona en cualquier momento
  y el traspaso es visible (la conversación pasa a estado «abierta» y la IA
  guarda silencio).

## 10. Errores técnicos encontrados y cómo se resolvieron

Todos estos fallos ocurrieron durante el desarrollo/despliegue real y están
documentados en los manuales:

1. **El bot saludaba pero respondía vacío** — la credencial de Qdrant en n8n
   usaba el campo `url` en lugar de `qdrantUrl`; n8n guardaba la credencial
   vacía sin avisar. Detectado por los registros (`Invalid Qdrant URL`).
   La prueba pasó de 3/13 a 13/13 tras corregirlo.
2. **El webhook no se registraba** — activar el workflow por CLI marcaba la
   bandera pero no registraba el webhook (error 404). Solución: activarlo por
   la API REST de n8n, que sí lo registra.
3. **Workflows duplicados** — importar los JSON sin `id` estable creaba copias
   que competían por el mismo webhook. Los workflows del repo llevan `id` fijo.
4. **Indexación lentísima en el servidor** — el plan Lightsail tiene CPU por
   ráfagas; agotados los créditos, indexar 219 documentos tardaba más de una
   hora. Solución: calcular los embeddings en una computadora personal y
   escribir en el Qdrant remoto por túnel SSH (~5 minutos).
5. **Cuentas huérfanas de Chatwoot** — la pantalla de configuración inicial
   crea una cuenta nueva cada vez que se completa; un asesor que la usara
   terminaba en una cuenta vacía. Documentado el flujo correcto (invitar
   desde Settings → Agents).

## 11. Qué quedó pendiente (declarado con honestidad)

- Comparación cuantitativa entre alternativas (FAQ vs LLM sin RAG vs RAG)
  con el mismo set de preguntas.
- Análisis de sensibilidad formal de `topK` y del umbral de similitud.
- Conexión con inventario en tiempo real y sistema de pedidos reales.
- Indexación incremental (hoy la colección se reconstruye completa).
- Canales adicionales (WhatsApp) y seguimiento de envíos.
- Métricas de satisfacción de usuarios reales (el piloto con personas aún no
  se ejecuta; los tiempos y aciertos provienen de las baterías automáticas).
