# iShop — Asistente virtual con RAG para la atención de clientes

Proyecto integrador: un asistente conversacional con IA generativa y RAG
(generación aumentada por recuperación) que responde consultas de productos,
precios publicados, envíos, garantías y posventa de una tienda como
[iShop Ecuador](https://ec.tiendasishop.com/), usando **solo información
verificable del catálogo real**, y que deriva a un asesor humano cuando la
consulta lo requiere.

El sistema está desplegado y funcionando en un servidor público con HTTPS.
La profesora puede probarlo directamente en la sección
[Prototipo en línea](#prototipo-en-línea).

## Integrantes y reparto de preguntas del video

| Orden | Integrante | Preguntas del video de respuestas |
| --- | --- | --- |
| 1.º | **Cristian Paúl Quintana Velásquez** | Impares: 1, 3, 5, 7 y 9 |
| 2.º | **Luis Sebastián Arias Loaiza** | Pares: 2, 4, 6, 8 y 10 |

> Según la rúbrica, el integrante que aparece primero en este README responde
> las preguntas impares y el segundo las pares.

## Videos de la entrega

| Entrega | Duración máxima | Enlace |
| --- | --- | --- |
| Video 1 — Presentación del proyecto (pitch con demostración) | 5 minutos | _Pendiente: insertar enlace de YouTube (no listado) o Google Drive_ |
| Video 2 — Respuestas a las 10 preguntas | 2 minutos por pregunta | _Pendiente: insertar enlace de YouTube (no listado) o Google Drive_ |

## Prototipo en línea

| Qué es | Dirección |
| --- | --- |
| Tienda con el asistente (interfaz real del proyecto) | <https://100-52-28-14.sslip.io> |
| Panel de asesores humanos (Chatwoot) | <https://chat.100-52-28-14.sslip.io> |
| Editor de automatizaciones (n8n) | <https://n8n.100-52-28-14.sslip.io> |

En la tienda, el botón de chat abre el asistente. Se puede preguntar por
productos, presupuestos, envíos o garantía; escribir «quiero hablar con un
asesor» demuestra el traspaso a una persona.

## El problema y el usuario

- **Problema:** un cliente de la tienda en línea que tiene una duda sobre un
  producto, una política o el posventa debe navegar por varias páginas o
  cambiar de canal para conseguir respuesta, con demoras y riesgo de compra
  perdida.
- **Usuarios principales:** clientes actuales y potenciales de la tienda.
  **Beneficiarios secundarios:** los asesores, que quedan libres para los
  casos complejos.
- **Qué haría hoy sin el sistema:** buscar la información por su cuenta entre
  las páginas del sitio, revisar preguntas frecuentes o contactar a un asesor
  por otro canal.

La propuesta no reemplaza al personal: resuelve lo frecuente con información
autorizada y **deriva a una persona** lo delicado, lo no documentado o lo que
requiere una decisión comercial.

## Cómo funciona

```
Cliente escribe en el widget de la tienda
  → Chatwoot recibe el mensaje (estado "pendiente")
  → n8n (workflow 04, 22 nodos) coordina la respuesta:
        1. Gemini interpreta la intención, categoría y presupuesto
        2. Ollama convierte la consulta en un vector (embeddings locales)
        3. Qdrant busca los documentos más parecidos en ishop_rag_v2
        4. n8n ordena, filtra por presupuesto y arma la evidencia
        5. Gemini redacta usando ÚNICAMENTE esa evidencia
  → La respuesta llega al mismo chat del cliente
```

- **RAG:** el modelo de lenguaje nunca decide qué productos existen ni qué
  precios tienen; solo redacta sobre los fragmentos recuperados del catálogo.
  Si no hay evidencia suficiente, el asistente lo dice y ofrece un asesor
  en lugar de improvisar.
- **Base de conocimiento:** 219 documentos (uno por producto o tema
  informativo), generados desde la copia local de la tienda con
  `sync_knowledge.py` e indexados en Qdrant con `index_knowledge.py`
  (embeddings `nomic-embed-text` de 768 dimensiones, generados localmente
  con Ollama).
- **Traspaso a humano:** escribir «asesor», «soporte», «persona», «humano»,
  «agente», «reclamo» o «queja» abre la conversación, la asigna a un asesor
  y silencia a la IA hasta que el asesor la devuelva.
- **Resiliencia:** si Gemini se queda sin cuota, una interpretación de
  respaldo recorre el mismo camino (Ollama + Qdrant) y entrega una respuesta
  verificada, aunque menos conversacional.

## Estructura del repositorio

```
ishop/
├── index.html, products/, collections/, pages/, search/, css/, js/
│                                     tienda estática (copia local de iShop)
├── server.py, localize.py            servidor local y clonado de páginas
├── chatbot/
│   ├── compose.yml                   servicios Docker (desarrollo)
│   ├── compose.prod.yml, Caddyfile   capa de producción (HTTPS)
│   ├── workflows/*.json              lógica del asistente (n8n)
│   ├── knowledge/*.md                fuente del conocimiento RAG
│   ├── widget/                       integración del chat en la tienda
│   ├── scripts/*.py                  sync, indexación, setup y pruebas
│   └── deploy/                       scripts y guía de despliegue
├── GUIA-PAUL-ISHOP.md                cómo levantar el ambiente local
├── GUIA-NUBE-ISHOP.md                cómo se publicó en la nube
├── MANUAL-TECNICO-ISHOP.md           arquitectura y funcionamiento interno
├── MANUAL-USUARIO-ISHOP.md           uso del asistente y del panel
└── RESULTADOS-Y-EVIDENCIAS.md        pruebas, métricas y evidencias
```

## Cómo ejecutar el proyecto

Requisitos: Docker Desktop, Python 3 y una API key gratuita de
[Google Gemini](https://aistudio.google.com/app/apikey).

```bash
# 1. Levantar los servicios (n8n, Chatwoot, Qdrant, Ollama, PostgreSQL, Redis)
bash chatbot/start.sh

# 2. Configurar Chatwoot (inbox + AgentBot + widget), tras crear la cuenta
#    propietaria en http://localhost:3000 y poner su token en chatbot/.env
python3 chatbot/scripts/setup_chatwoot.py
bash chatbot/import-workflows.sh

# 3. Generar e indexar la base de conocimiento
python3 chatbot/scripts/sync_knowledge.py
python3 chatbot/scripts/index_knowledge.py

# 4. Servir la tienda y abrir http://localhost:8080
python3 -m http.server 8080        # o: python3 server.py (clona páginas faltantes)
```

La guía paso a paso completa (incluida la configuración inicial de Chatwoot y
las credenciales de n8n) está en
[`GUIA-PAUL-ISHOP.md`](GUIA-PAUL-ISHOP.md). Para publicarlo en un servidor
público con HTTPS, ver [`GUIA-NUBE-ISHOP.md`](GUIA-NUBE-ISHOP.md) y
[`chatbot/deploy/README.md`](chatbot/deploy/README.md).

## Documentación

| Documento | Contenido |
| --- | --- |
| [`MANUAL-TECNICO-ISHOP.md`](MANUAL-TECNICO-ISHOP.md) | Arquitectura, pipeline RAG, scripts, fallas conocidas |
| [`MANUAL-USUARIO-ISHOP.md`](MANUAL-USUARIO-ISHOP.md) | Cómo usa el cliente el chat y cómo atiende el asesor |
| [`GUIA-PAUL-ISHOP.md`](GUIA-PAUL-ISHOP.md) | Instalación y operación del ambiente local |
| [`GUIA-NUBE-ISHOP.md`](GUIA-NUBE-ISHOP.md) | Publicación en la nube, costos y operación diaria |
| [`RESULTADOS-Y-EVIDENCIAS.md`](RESULTADOS-Y-EVIDENCIAS.md) | Pruebas, métricas, baseline, errores y limitaciones |
| [`chatbot/README.md`](chatbot/README.md) | Detalle del componente chatbot |

## Pruebas y resultados

- **Batería automática de extremo a extremo**
  (`chatbot/scripts/test_chatbot_e2e.py`): 13 casos reales contra la API de
  Chatwoot (búsquedas, presupuesto, comparación, errores ortográficos,
  políticas, control de alucinaciones y traspaso a humano).
  **Resultado: 13/13 correctas, 1,02 s de promedio** (local) y
  **13/13, 1,27 s** en el servidor de producción.
- **Batería manual de 40 preguntas** (`chatbot/knowledge/preguntas-prueba.md`)
  con meta mínima de 32/40: registradas **39/39 aciertos en tres ejecuciones
  completas** del protocolo.
- El detalle completo (métricas, evolución desde el baseline, errores
  encontrados y qué quedó pendiente) está en
  [`RESULTADOS-Y-EVIDENCIAS.md`](RESULTADOS-Y-EVIDENCIAS.md).

## Decisiones técnicas principales

| Decisión | Alternativas descartadas | Por qué |
| --- | --- | --- |
| RAG con fuentes propias | LLM sin RAG (inventa precios); FAQ estática (rígida) | Respuestas en lenguaje natural **verificables** contra el catálogo |
| Un producto = un documento vectorial | Chunks de tamaño fijo | Evita mezclar una MacBook con cables o adaptadores en la misma respuesta |
| Embeddings locales (Ollama) | API de embeddings de pago | Sin costo recurrente ni fuga de datos del catálogo |
| Gemini solo para interpretar y redactar | Modelo local para todo | Un servidor pequeño no sostiene un LLM de redacción; Gemini nunca decide qué productos existen |
| n8n como orquestador | Código a medida | La lógica es un diagrama auditable, modificable sin recompilar |
| Chatwoot para el chat y la bandeja | Widget propio | Traspaso IA ↔ humano probado, en el mismo hilo de conversación |

## Seguridad y privacidad

- **Qué sale del servidor:** únicamente el texto del mensaje del cliente y los
  fragmentos recuperados del catálogo viajan a Gemini para interpretar y
  redactar. El chat no pide ni almacena nombres, teléfonos, direcciones ni
  datos de tarjetas.
- **Secretos fuera de Git:** `chatbot/.env` y los tokens viven en
  `.gitignore`; nunca se subieron al repositorio.
- **Producción:** HTTPS con certificados de Let's Encrypt renovados solos;
  solo los puertos 22/80/443 abiertos; Qdrant, Ollama, PostgreSQL y Redis
  solo escuchan en `127.0.0.1`; Caddy devuelve 404 ante rutas sensibles
  (verificado: `https://100-52-28-14.sslip.io/chatbot/.env`); registro
  público de Chatwoot desactivado.
- **Control de alucinaciones:** si la evidencia recuperada no supera el
  umbral, el asistente reconoce el límite y ofrece un asesor. Los casos
  37–40 de la batería de pruebas existen precisamente para detectar
  invenciones.

## Limitaciones reconocidas

- Es una demostración académica: no consulta inventario en tiempo real ni se
  conecta al sistema de pedidos.
- No incluye WhatsApp ni seguimiento de envíos.
- La tienda es una copia estática; las páginas nunca visitadas en local no
  existen en el servidor.
- Servidor de gama básica (CPU por ráfagas): las reindexaciones completas van
  lentas; se resolvió calculando embeddings fuera del servidor por túnel SSH.
- La cuota gratuita de Gemini es limitada; sin ella el sistema responde con
  el modo de respaldo, más seco pero verificado.
- Pendiente: comparación cuantitativa entre alternativas con el mismo set de
  preguntas y análisis formal de sensibilidad de parámetros (ver
  [`RESULTADOS-Y-EVIDENCIAS.md`](RESULTADOS-Y-EVIDENCIAS.md)).

---

Proyecto académico desarrollado para la asignatura de Proyecto Integrador.
Tienda de referencia: [iShop Ecuador](https://ec.tiendasishop.com/).
