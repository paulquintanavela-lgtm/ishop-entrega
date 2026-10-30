# Planificación del proyecto

> Este documento resume la planificación de **iShop — Asistente virtual con
> RAG**. El detalle técnico está en
> [`../MANUAL-TECNICO-ISHOP.md`](../MANUAL-TECNICO-ISHOP.md) y
> [`../GUIA-NUBE-ISHOP.md`](../GUIA-NUBE-ISHOP.md); los resultados medidos, en
> [`../RESULTADOS-Y-EVIDENCIAS.md`](../RESULTADOS-Y-EVIDENCIAS.md).

## Definición del problema y objetivos

**Problema:** un cliente de una tienda en línea (iShop Ecuador) que tiene una
duda sobre un producto, una política de envíos/garantía o el posventa debe
navegar por varias páginas o cambiar de canal para conseguir respuesta, con
demoras y riesgo de perder la compra.

**Objetivo general:** construir un asistente conversacional que resuelva esas
consultas usando **solo información verificable del catálogo real** (sin
inventar precios ni promociones) y que derive a un asesor humano cuando la
consulta lo requiera.

**Objetivos específicos:**
- Indexar el catálogo público de la tienda en una base vectorial para
  responder por significado, no por coincidencia exacta de palabras.
- Evitar que el modelo de lenguaje invente información: toda respuesta debe
  anclarse en evidencia recuperada del catálogo (RAG).
- Permitir el traspaso de la conversación a una persona sin que el cliente
  cambie de canal ni repita lo ya dicho.
- Desplegar el sistema en un servidor público con HTTPS, accesible para
  cualquier persona.

## Justificación de la relevancia

Una tienda con catálogo amplio (212 productos en este caso) genera preguntas
repetitivas sobre disponibilidad, precio, comparación de modelos y políticas.
Resolverlas automáticamente, sin perder la posibilidad de escalar a un humano,
reduce la carga del equipo de atención y el tiempo de respuesta al cliente.

## Alcance

**Qué incluye:**
- Asistente de chat embebido en la tienda, con RAG sobre el catálogo público y
  las políticas públicas (envíos, garantía, pagos).
- Traspaso de la conversación a un asesor humano dentro del mismo hilo de
  chat (Chatwoot).
- Carga de documentos adicionales al conocimiento del asistente vía un
  formulario web, sin acceso al servidor.
- Despliegue en producción con HTTPS, dominio, certificados automáticos y
  puertos internos cerrados al exterior.
- Batería de pruebas automáticas de extremo a extremo y una batería manual de
  40 preguntas, incluidos casos de control de alucinaciones.

**Qué NO incluye:**
- Inventario en tiempo real ni conexión al sistema real de pedidos de iShop
  (es una demostración académica sobre una copia estática del catálogo).
- Canales adicionales como WhatsApp o seguimiento de envíos.
- Procesamiento de pagos o datos de tarjetas.
- Un modelo de machine learning entrenado desde cero: el sistema usa un LLM de
  terceros (Google Gemini) para interpretar y redactar, y un modelo de
  embeddings local (Ollama) para la búsqueda semántica — ver justificación en
  [`arquitectura.md`](arquitectura.md).

## Cronograma de desarrollo (planificado vs. real)

| Etapa | Planificado | Real |
| --- | --- | --- |
| Clonado y preparación de la tienda estática (`localize.py`, `server.py`) | Primera semana | Cumplido |
| Diseño de la base de conocimiento y la indexación vectorial | Segunda semana | Cumplido, con rediseño posterior (ver abajo) |
| Primer flujo n8n + Chatwoot funcionando en local | Tercera semana | Cumplido, con una falla inicial del 3/13 en pruebas (credencial de Qdrant mal nombrada) resuelta en la misma semana |
| Rediseño de la indexación: de chunks genéricos (`ishop_knowledge`) a un documento por producto (`ishop_rag_v2`) | No planificado inicialmente | Se agregó al detectar que las búsquedas mezclaban productos distintos |
| Despliegue en la nube (AWS Lightsail, Caddy, HTTPS) | Cuarta semana | Cumplido |
| Batería de pruebas e2e y batería manual de 40 preguntas | Última semana | Cumplido: 13/13 (e2e) y 39/39 en tres corridas |
| Análisis de sensibilidad formal de parámetros (topK, umbral) | Planificado | **No se ejecutó** — queda declarado como pendiente |
| Documentación final y videos | Última semana | En curso, entrega 30 de octubre de 2026 |

## Recursos necesarios

- **Datos:** catálogo público de iShop Ecuador (`products.json` de la tienda),
  descargado y versionado localmente (`chatbot/knowledge/`).
- **Hardware:** laptop de desarrollo + servidor en la nube (AWS Lightsail,
  4 GB RAM, 2 núcleos compartidos, 80 GB disco).
- **Software:** Docker, Python 3, n8n, Chatwoot, Qdrant, Ollama, Caddy — todo
  software libre, sin costo de licencia.
- **Servicio externo de pago/cuota:** API de Google Gemini (cuota gratuita
  usada durante el desarrollo y las pruebas).
- **Costo de operación real:** ~24 USD/mes en Lightsail (ver
  [`../GUIA-NUBE-ISHOP.md`](../GUIA-NUBE-ISHOP.md) §8), cubiertos con créditos
  gratuitos de AWS durante el proyecto.

## Riesgos identificados y mitigación

| Riesgo | Mitigación aplicada |
| --- | --- |
| El modelo de lenguaje inventa precios o productos | RAG: el modelo solo redacta sobre evidencia recuperada de Qdrant; si no hay evidencia suficiente, el asistente lo reconoce y ofrece un asesor |
| Búsquedas que mezclan productos distintos (p. ej. una laptop con un cable) | Rediseño de la indexación a "un producto = un documento" con metadatos estructurados y filtro por categoría |
| Agotamiento de la cuota gratuita de Gemini | Modo de respaldo: interpretación heurística local + Qdrant, que mantiene respuestas verificadas aunque menos conversacionales |
| Servidor de gama básica con CPU por ráfagas (reindexación lenta) | Cálculo de embeddings en una computadora personal y escritura remota a Qdrant por túnel SSH |
| Exposición de credenciales o servicios internos | `.env` fuera de Git, servicios internos solo en `127.0.0.1`, Caddy bloquea rutas sensibles (verificado con `/chatbot/.env` → 404) |
| Cuentas de Chatwoot creadas por error (pantalla de configuración inicial) | Documentado en los manuales: agregar asesores desde Settings → Agents, nunca desde el registro público |
| No alcanzar el criterio mínimo de 32/40 en la batería de preguntas | Mitigado: resultado real 39/39 en tres ejecuciones; ver `RESULTADOS-Y-EVIDENCIAS.md` |
