# iShop — Asistente virtual con RAG para la atención de clientes

Proyecto integrador: un asistente conversacional con IA generativa y RAG
(generación aumentada por recuperación) que responde consultas de productos,
precios publicados, envíos, garantías y posventa de una tienda como
[iShop Ecuador](https://ec.tiendasishop.com/), usando **solo información
verificable del catálogo real**, y que deriva a un asesor humano cuando la
consulta lo requiere.

El sistema está desplegado y funcionando en un servidor público con HTTPS.
Se puede probar directamente en la sección
[Prototipo en línea](#prototipo-en-línea).

## Integrantes y reparto de preguntas del video

| Orden | Integrante | Preguntas del video de respuestas |
| --- | --- | --- |
| 1.º | **Cristian Paúl Quintana Velásquez** | Impares: 1, 3, 5, 7 y 9 |
| 2.º | **Luis Sebastián Arias Loaiza** | Pares: 2, 4, 6, 8 y 10 |

## Videos de la entrega

| Entrega | Duración máxima | Enlace |
| --- | --- | --- |
| Video 1 — Presentación del proyecto (pitch con demostración) | 5 minutos | <https://drive.google.com/file/d/13m8T07LmotDpD1bGad4QrXiTn1qHYiKv/view> |
| Video 2 — Respuestas a las 10 preguntas (intercaladas entre los dos integrantes) | 2 minutos por pregunta | <https://drive.google.com/file/d/1YVGQWalicO9Deuld0mXAn657M8PcDgA6/view> |

## Prototipo en línea

| Qué es | Dirección |
| --- | --- |
| Tienda con el asistente (interfaz real del proyecto) | <https://100-52-28-14.sslip.io> |
| Panel de asesores humanos (Chatwoot) | <https://chat.100-52-28-14.sslip.io> |
| Editor de automatizaciones (n8n) | <https://n8n.100-52-28-14.sslip.io> |

En la tienda, el botón de chat abre el asistente. Se puede preguntar por
productos, presupuestos, envíos o garantía; escribir «quiero hablar con un
asesor» demuestra el traspaso a una persona.

## Interfaz de usuario

Este proyecto no usa un framework de demo tipo Streamlit/Gradio/Flask: la
interfaz es un **widget de chat** embebido en la tienda, más un **formulario
de carga** para mantener la base de conocimiento. Son dos interfaces con
roles distintos, no una sola:

### 1. Chat del cliente (interfaz principal)

Es la que resuelve el problema del proyecto y la que se muestra en el video
pitch. Vive en <https://100-52-28-14.sslip.io> y se construye sobre el widget
de Chatwoot, integrado y configurado para este proyecto
(`chatbot/widget/`, `chatbot/scripts/setup_chatwoot.py`,
`chatbot/scripts/install_widget.py`), no escrito desde cero.

- **Input:** texto libre, sin registro. El usuario pregunta como lo haría por
  WhatsApp.
- **Procesamiento:** indicador de "escribiendo" mientras el asistente
  interpreta la consulta, busca evidencia en el catálogo y redacta la
  respuesta (ver [`docs/arquitectura.md`](docs/arquitectura.md)).
- **Output:** respuesta en lenguaje natural con el producto, precio y enlace
  a la ficha; si no hay evidencia suficiente, lo dice explícitamente en vez
  de inventar.
- **Manejo de errores:** ante una consulta fuera de catálogo o ambigua, el
  asistente reconoce el límite y ofrece reformular o pedir un asesor — ver
  casos de prueba en [`tests/README.md`](tests/README.md).
- **Qué le falta frente al "Streamlit típico":** no muestra un nivel de
  confianza/probabilidad, ni tiene una sección "Acerca de" con métricas del
  sistema dentro de la propia interfaz (esas métricas están documentadas en
  [`RESULTADOS-Y-EVIDENCIAS.md`](RESULTADOS-Y-EVIDENCIAS.md), fuera de la UI),
  ni un botón "probar con ejemplo" — la guía de prueba manual con preguntas
  sugeridas cumple ese rol desde fuera de la interfaz
  (`chatbot/knowledge/preguntas-prueba.md`).

### 2. Formulario de carga de conocimiento (interfaz secundaria/administrativa)

Disponible en `https://n8n.100-52-28-14.sslip.io/form/cargar-conocimiento`
(workflow `01-cargar-conocimiento.json`). No prueba el modelo — lo alimenta.
Se incluye aquí porque, de las dos interfaces, es la que más literalmente
cumple los "requisitos mínimos de la interfaz" de la rúbrica del curso:

- **Input con validación:** campo "Tema del documento" (obligatorio) y campo
  "Archivo" (obligatorio, restringido a `.pdf, .txt, .md`).
- **Procesamiento:** extrae el texto del PDF o del archivo de texto y lo
  indexa en la base de conocimiento vectorial.
- **Output:** pantalla de cierre con mensaje dinámico de éxito o error
  ("Documento agregado" / "No se pudo agregar"), no un mensaje genérico.
- **Uso:** pensado para que un asesor agregue una política o instructivo
  nuevo sin tocar el servidor — ver
  [`MANUAL-USUARIO-ISHOP.md`](MANUAL-USUARIO-ISHOP.md#agregar-documentos-al-conocimiento-del-asistente).

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

## Arquitectura

El sistema vive en un único servidor y se apoya en un solo servicio externo.
Cada pieza tiene una responsabilidad clara:

![Diagrama de arquitectura de iShop: el cliente llega por HTTPS a Caddy, que reparte el tráfico entre la tienda estática, Chatwoot y n8n dentro de un único servidor; n8n coordina Ollama y Qdrant en ese servidor y llama a Google Gemini como único servicio externo; un asesor humano atiende desde Chatwoot.](docs/img/arquitectura.svg)

<sub>Fuente editable en [`docs/img/arquitectura.mmd`](docs/img/arquitectura.mmd)
(sintaxis [Mermaid](https://mermaid.js.org/)); se regenera con
`npx @mermaid-js/mermaid-cli -i docs/img/arquitectura.mmd -o docs/img/arquitectura.svg -b white`.</sub>

- **Caddy** es la única puerta pública: recibe el tráfico HTTPS y lo reparte
  por dominio hacia la tienda, Chatwoot o n8n.
- **Chatwoot** es el chat que ve el cliente y la bandeja donde un asesor
  humano puede tomar la conversación.
- **n8n** contiene toda la lógica del asistente: en cada mensaje coordina a
  Gemini, Ollama y Qdrant.
- **Qdrant** guarda el catálogo convertido en vectores; **Ollama** genera
  esos vectores localmente, sin costo ni fuga de datos.
- **Google Gemini** es el único servicio fuera del servidor: interpreta la
  intención y redacta la respuesta, pero nunca decide qué productos existen
  ni qué precios tienen — eso lo entrega Qdrant.

El detalle de los ocho contenedores Docker y la topología de red está en
[`MANUAL-TECNICO-ISHOP.md`](MANUAL-TECNICO-ISHOP.md).

## Cómo funciona

Así recorre un mensaje las piezas anteriores, de principio a fin:

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
├── GUIA-AMBIENTE-LOCAL-ISHOP.md                cómo levantar el ambiente local
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
[`GUIA-AMBIENTE-LOCAL-ISHOP.md`](GUIA-AMBIENTE-LOCAL-ISHOP.md). Para publicarlo en un servidor
público con HTTPS, ver [`GUIA-NUBE-ISHOP.md`](GUIA-NUBE-ISHOP.md) y
[`chatbot/deploy/README.md`](chatbot/deploy/README.md).

## Documentación

| Documento | Contenido |
| --- | --- |
| [`MANUAL-TECNICO-ISHOP.md`](MANUAL-TECNICO-ISHOP.md) | Arquitectura, pipeline RAG, scripts, fallas conocidas |
| [`MANUAL-USUARIO-ISHOP.md`](MANUAL-USUARIO-ISHOP.md) | Cómo usa el cliente el chat y cómo atiende el asesor |
| [`GUIA-AMBIENTE-LOCAL-ISHOP.md`](GUIA-AMBIENTE-LOCAL-ISHOP.md) | Instalación y operación del ambiente local |
| [`GUIA-NUBE-ISHOP.md`](GUIA-NUBE-ISHOP.md) | Publicación en la nube, costos y operación diaria |
| [`RESULTADOS-Y-EVIDENCIAS.md`](RESULTADOS-Y-EVIDENCIAS.md) | Pruebas, métricas, baseline, errores y limitaciones |
| [`chatbot/README.md`](chatbot/README.md) | Detalle del componente chatbot |
| [`docs/planificacion.md`](docs/planificacion.md) | Problema, objetivos, alcance, cronograma, recursos y riesgos |
| [`docs/analisis_datos.md`](docs/analisis_datos.md) | Descripción del catálogo, estadísticas descriptivas y decisiones de preprocesamiento |
| [`docs/arquitectura.md`](docs/arquitectura.md) | Tipo de "modelo" (RAG), componentes, diagrama de flujo, interfaz y tecnologías |
| [`docs/optimizacion.md`](docs/optimizacion.md) | Parámetros del pipeline (equivalente a hiperparámetros), antes/después |
| [`docs/consideraciones_eticas.md`](docs/consideraciones_eticas.md) | Sesgos, privacidad, transparencia, impacto social y limitaciones |
| [`docs/manual_usuario.md`](docs/manual_usuario.md) | Guía rápida de uso de las dos interfaces (chat y carga de conocimiento) |
| [`tests/README.md`](tests/README.md) | Qué cubre la batería de pruebas y cómo ejecutarla |

## Pruebas y resultados

- **Batería automática de extremo a extremo**
  (`chatbot/scripts/test_chatbot_e2e.py`): 13 casos reales contra la API de
  Chatwoot (búsquedas, presupuesto, comparación, errores ortográficos,
  políticas, control de alucinaciones y traspaso a humano).
  **Resultado: 13/13 correctas, 2,83 s de promedio** (local, tras la
  corrección de las llamadas a Gemini) y **13/13 correctas** en el servidor
  de producción (medición de 1,27 s anterior a esa corrección; pendiente de
  repetir).
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

## Licencia

El código original del proyecto (`chatbot/`, `server.py`, `localize.py` y la
documentación) se publica bajo licencia [MIT](LICENSE).

**Alcance:** esta licencia cubre el código y la documentación escritos por el
equipo. La copia estática de la tienda (`products/`, `collections/`, `pages/`,
`css/`, `js/`, imágenes) es un clon local de
[iShop Ecuador](https://ec.tiendasishop.com/) con fines **exclusivamente
académicos y de demostración**; no es contenido original del equipo y no está
cubierto por la licencia MIT. Los nombres de marca, productos e imágenes que
aparecen en esa copia pertenecen a sus respectivos dueños (iShop, Apple y
otras marcas representadas).

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
