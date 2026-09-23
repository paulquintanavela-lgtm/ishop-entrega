# Chatbot web de iShop con n8n y Chatwoot

Proyecto local y gratuito para la demostración de tesis. El cliente habla con
la IA y con un asesor humano en el mismo widget. El estado de Chatwoot decide
quién responde.

## Arquitectura

```text
Página local :8080
  → Widget Chatwoot
  → Conversación Chatwoot :3000
      estado pending → n8n AgentBot :5678 → Gemini + Qdrant → misma conversación
      estado open    → bandeja del asesor en Chatwoot → misma conversación
```

Redis y PostgreSQL de Chatwoot quedan internos en Docker. No se publican en el
Mac para no chocar con otros servicios.

No incluye WhatsApp, Shopify Admin, tracking de pedidos ni citas reales.

## Requisitos

- Docker Desktop iniciado.
- Una API key gratuita de Google Gemini:
  <https://aistudio.google.com/app/apikey>
- Un correo personal únicamente si se activa el workflow opcional de derivación.

## Archivos

- `compose.yml`: n8n, Qdrant, Ollama, Chatwoot CE, PostgreSQL y Redis.
- `workflows/01-cargar-conocimiento.json`: formulario para cargar archivos RAG.
- `workflows/02-chatbot-web.json`: chatbot web directo de n8n, como reserva.
- `workflows/03-solicitud-asesor-email.json`: formulario de correo opcional.
- `workflows/04-chatwoot-agent-bot.json`: AgentBot con RAG y handoff humano.
- `scripts/setup_chatwoot.py`: crea el inbox web y el bot después del alta inicial.
- `knowledge/`: documentos que se cargan al RAG.
- `widget/`: el sitio carga `chatbot-widget.js`. Si existe token de Chatwoot,
  usa el SDK oficial; si no, mantiene el chat de n8n.

Los tokens privados viven en `.env` y `widget/chatwoot-config.json`. No se
suben a Git.

## 1. Actualizar la base documental

Desde la raíz de la tienda:

```bash
python3 chatbot/scripts/sync_knowledge.py
```

Esto genera:

- `knowledge/catalogo-productos.md`
- `knowledge/contenido-publico-ishop.md`

## 2. Iniciar los servicios

```bash
bash chatbot/start.sh
```

Abrir:

- Chatwoot: <http://localhost:3000>
- n8n: <http://localhost:5678>
- Qdrant: <http://localhost:6333/dashboard>
- Tienda: <http://localhost:8080>

La primera vez, n8n y Chatwoot solicitarán crear un usuario propietario local.

## 3. Conectar Chatwoot con el widget

1. Entra a <http://localhost:3000> y crea la cuenta propietaria.
2. Abre **Profile Settings** y copia el Access Token.
3. Pégalo en `chatbot/.env` como `CHATWOOT_ACCESS_TOKEN=...`
4. Ejecuta:

```bash
python3 chatbot/scripts/setup_chatwoot.py
docker compose -f chatbot/compose.yml restart n8n
```

El script crea o reutiliza el inbox `iShop Web`, el AgentBot y escribe el token
público en `chatbot/widget/chatwoot-config.json`. El token administrativo no se
guarda en el repositorio.

Usa la tienda en `http://localhost:8080` para que el widget coincida con el
inbox.

## 4. Importar los workflows

Después de que n8n haya iniciado:

```bash
bash chatbot/import-workflows.sh
```

También se pueden importar manualmente desde n8n usando los JSON de
`chatbot/workflows/`.

## 5. Crear credenciales en n8n

### Google Gemini(PaLM) Api

1. En n8n, abrir **Credentials**.
2. Crear `Google Gemini(PaLM) Api`.
3. Pegar la API key de Google AI Studio.
4. Asignarla al nodo `Google Gemini` de los workflows 02 y 04.

### Ollama API

1. Crear la credencial `Ollama API`.
2. URL interna: `http://ollama:11434`
3. Asignarla a `Embeddings Ollama` en los workflows 01, 02 y 04.
4. Modelo: `nomic-embed-text:latest`.

Ollama genera los embeddings localmente, sin API key, cuota ni costo.

### QdrantApi

1. Crear la credencial `QdrantApi`.
2. En la credencial de n8n usar la URL interna: `http://qdrant:6333`
3. API key: dejar vacía. Si la interfaz obliga a escribir una, usar `local`.
4. Asignarla a los nodos Qdrant de los workflows 01, 02 y 04.

> `http://qdrant:6333` solo funciona entre los contenedores Docker. No se abre
> directamente en el navegador de macOS. Para revisar Qdrant desde el navegador
> usa <http://localhost:6333/dashboard>.

### SMTP opcional

Para Gmail se recomienda activar verificación en dos pasos y crear una
contraseña de aplicación. Asignar la credencial SMTP al workflow 03 y reemplazar
`TU_CORREO_PERSONAL` en ese workflow y en el System Message del workflow 02.

## 6. Cargar documentos a Qdrant

1. Configurar y activar `iShop 01 - Cargar conocimiento RAG`.
2. En el nodo `Dividir texto`, usar **Chunk Size 5000** y
   **Chunk Overlap 300**.
3. Abrir la **Production URL** del nodo `Cargar documento`.
4. Subir, uno por uno:
   - `catalogo-productos.md`
   - `contenido-publico-ishop.md`
   - `reglas-asistente.md`
5. No subir `preguntas-prueba.md`: se utiliza para evaluar.

La colección utilizada se llama `ishop_knowledge`.

## 7. Activar el AgentBot

1. Configurar las credenciales del workflow `iShop 04 - AgentBot Chatwoot`.
2. Guardar y publicar/activar el workflow.
3. Abrir <http://localhost:8080> y usar el botón naranja del chat.

El widget oficial de Chatwoot carga el historial en el mismo hilo. Si todavía
no existe `chatwoot-config.json`, el sitio usa el chatbot directo de n8n.

## 8. Hablar con un asesor

1. En el widget, escribe una consulta normal. La IA debe responder con RAG.
2. Escribe “quiero hablar con un asesor”. La conversación pasa de `pending` a
   `open` y la IA deja de responder.
3. Abre <http://localhost:3000>, entra a la bandeja y responde. El mensaje
   aparece en el mismo widget del cliente.
4. Para devolver la conversación a la IA, cambia el estado a **Pending**.

Palabras que activan el traspaso: persona, asesor, humano, agente, reclamo,
queja o una respuesta del modelo con `[[HANDOFF]]`.

## 9. Probar

Usar las 40 preguntas de `knowledge/preguntas-prueba.md`.

Resultado mínimo:

- 32 de 40 respuestas correctas.
- Ningún precio, promoción, pedido o garantía inventados.
- Las consultas privadas deben reconocer el límite y pasar a un asesor.

## Detener

```bash
bash chatbot/stop.sh
```

Los datos de n8n, Qdrant, Ollama, Chatwoot, PostgreSQL y Redis quedan en
volúmenes Docker.
