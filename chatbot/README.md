# Chatbot web de iShop con n8n

Proyecto local y gratuito para la demostración de tesis. Toda la infraestructura
del chatbot vive en esta carpeta. La tienda solo carga el archivo
`/chatbot/widget/chatbot-widget.js`.

## Arquitectura

```text
Página local :8080
  → Chat Trigger de n8n :5678
  → AI Agent + Gemini
  → Ollama local para embeddings :11434
  → Qdrant local :6333
  → respuesta en el widget
```

No incluye WhatsApp, Shopify Admin, tracking de pedidos ni citas reales.

## Requisitos

- Docker Desktop iniciado.
- Una API key gratuita de Google Gemini:
  <https://aistudio.google.com/app/apikey>
- Un correo personal únicamente si se activa el workflow opcional de derivación.

## Archivos

- `compose.yml`: n8n Community + Qdrant + Ollama.
- `workflows/01-cargar-conocimiento.json`: formulario para cargar archivos RAG.
- `workflows/02-chatbot-web.json`: chatbot web con Gemini y Qdrant.
- `workflows/03-solicitud-asesor-email.json`: formulario de correo opcional.
- `knowledge/`: documentos que se cargan al RAG.
- `scripts/sync_knowledge.py`: actualiza catálogo y contenido público.
- `widget/`: integración visual cargada por `index.html`.

## 1. Actualizar la base documental

Desde la raíz de la tienda:

```bash
python3 chatbot/scripts/sync_knowledge.py
```

Esto genera:

- `knowledge/catalogo-productos.md`
- `knowledge/contenido-publico-ishop.md`

## 2. Iniciar n8n y Qdrant

```bash
bash chatbot/start.sh
```

Abrir:

- n8n: <http://localhost:5678>
- Qdrant: <http://localhost:6333/dashboard>
- Tienda: <http://localhost:8080>

La primera vez, n8n solicitará crear un usuario propietario local.

## 3. Importar los workflows

Después de que n8n haya iniciado:

```bash
bash chatbot/import-workflows.sh
```

También se pueden importar manualmente desde n8n usando los tres JSON de
`chatbot/workflows/`.

## 4. Crear credenciales en n8n

### Google Gemini(PaLM) Api

1. En n8n, abrir **Credentials**.
2. Crear `Google Gemini(PaLM) Api`.
3. Pegar la API key de Google AI Studio.
4. Asignarla únicamente al nodo `Google Gemini` del workflow 02.

### Ollama API

1. Crear la credencial `Ollama API`.
2. URL interna: `http://ollama:11434`
3. Asignarla a `Embeddings Ollama` en los workflows 01 y 02.
4. Modelo: `nomic-embed-text:latest`.

Ollama genera los embeddings localmente, sin API key, cuota ni costo.

### QdrantApi

1. Crear la credencial `QdrantApi`.
2. En la credencial de n8n usar la URL interna: `http://qdrant:6333`
3. API key: dejar vacía. Si la interfaz obliga a escribir una, usar `local`.
4. Asignarla a los nodos Qdrant de los workflows 01 y 02.

> `http://qdrant:6333` solo funciona entre los contenedores Docker. No se abre
> directamente en el navegador de macOS. Para revisar Qdrant desde el navegador
> usa <http://localhost:6333/dashboard>.

### SMTP opcional

Para Gmail se recomienda activar verificación en dos pasos y crear una
contraseña de aplicación. Asignar la credencial SMTP al workflow 03 y reemplazar
`TU_CORREO_PERSONAL` en ese workflow y en el System Message del workflow 02.

## 5. Cargar documentos a Qdrant

1. Configurar y activar `iShop 01 - Cargar conocimiento RAG`.
2. En el nodo `Dividir texto`, usar **Chunk Size 5000** y
   **Chunk Overlap 300**.
3. Abrir la **Production URL** del nodo `Cargar documento`.
4. Subir, uno por uno:
   - `catalogo-productos.md`
   - `contenido-publico-ishop.md`
   - `reglas-asistente.md`
5. No subir `preguntas-prueba.md`: se utiliza para evaluar.

La colección utilizada por ambos workflows se llama `ishop_knowledge`.

## 6. Activar el chatbot

1. Configurar las credenciales del workflow `iShop 02 - Chatbot web con RAG`.
2. Sustituir `TU_CORREO_PERSONAL` en el System Message.
3. En `Cuando llega un mensaje`, activar **Make Chat Publicly Available** y
   seleccionar **Embedded Chat**.
4. En ese mismo nodo, configurar **Load Previous Session → From Memory**.
5. Conectar `Memoria simple` tanto a `Asistente iShop` como a
   `Cuando llega un mensaje`.
6. Guardar y publicar/activar el workflow.
7. Abrir <http://localhost:8080> y usar el botón del chat.

El widget ya apunta al webhook:

```text
http://localhost:5678/webhook/7b30dce3-a9c0-4e49-b25c-3d2f6a71c980/chat
```

## 7. Probar

Usar las 40 preguntas de `knowledge/preguntas-prueba.md`.

Resultado mínimo:

- 32 de 40 respuestas correctas.
- Ningún precio, promoción, pedido o garantía inventados.
- Las consultas privadas deben reconocer el límite y derivar.

## Detener

```bash
bash chatbot/stop.sh
```

Los datos de n8n, Qdrant y Ollama quedan guardados en volúmenes Docker.
