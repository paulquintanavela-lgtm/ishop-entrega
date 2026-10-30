# Pruebas del proyecto

> Este repositorio no tiene pruebas unitarias clásicas (`test_data_processing.py`,
> `test_model.py`) porque no hay un pipeline de datos ni un modelo entrenado
> con funciones Python aisladas que probar: la lógica del asistente vive en
> un **workflow de n8n** (no-code) que coordina Chatwoot, Qdrant, Ollama y
> Gemini. Por eso la estrategia de pruebas elegida es **end-to-end (e2e)**:
> se prueba el sistema completo, tal como lo usa un cliente real, contra la
> API real de Chatwoot.

## Dónde está la prueba

El script vive en
[`../chatbot/scripts/test_chatbot_e2e.py`](../chatbot/scripts/test_chatbot_e2e.py)
(no en esta carpeta) porque depende de las variables de entorno y la
configuración de `chatbot/.env`. Esta carpeta documenta cómo ejecutarlo y qué
cubre, para que quede visible como la "suite de pruebas" del proyecto.

## Qué cubre (13 casos)

| # | Entrada | Qué verifica |
| --- | --- | --- |
| 1 | `hola` | Saludo rápido, sin gastar llamadas al modelo |
| 2 | `busco una laptop para programar, tengo 2000` | Recomienda MacBook Air; **no** debe aparecer "adaptador" ni "multipuerto" (evita mezclar accesorios) |
| 3 | `compara la opcion 1 y la 2` | Usa exactamente las opciones mostradas antes; no debe aparecer "thule" (producto no relacionado) |
| 4 | `ahora quiero un microfno` | Corrige el error ortográfico, reconoce que no hay micrófonos en catálogo; **no** debe devolver "soundlink micro" (caso prohibido explícito) |
| 5 | `mejor un relok` | Corrige a "Apple Watch" |
| 6 | `cuanto cuesta el envio a domicilio` | Responde con la política real de envío ($6) |
| 7 | `que tarjetas aceptan para pagar` | Responde con los medios de pago reales |
| 8 | `cuanto dura la garantia` | Responde "1 año" |
| 9 | `tienen servicio tecnico autorizado` | Responde sobre el servicio técnico autorizado |
| 10 | `quiero ver iphone 17` | Devuelve los modelos de iPhone 17 disponibles |
| 11 | `quiero audifonos para el gimnasio` | Devuelve opciones de audífonos (JBL, etc.) |
| 12 | `busco una mochila para mi macbook` | Devuelve mochilas compatibles |
| 13 | `quiero hablar con un asesor humano` | Verifica el traspaso a humano: la conversación queda asignada y la respuesta reconoce al "asesor" |

Cada caso define fragmentos que **deben** aparecer (`expected_any`) y, en
varios casos, fragmentos **prohibidos** (`forbidden`) que detectarían una
mezcla de productos o una alucinación — ver el código fuente para el detalle
exacto de cada aserción.

## Cómo ejecutar las pruebas

Requiere el ambiente completo levantado (ver
[`../GUIA-AMBIENTE-LOCAL-ISHOP.md`](../GUIA-AMBIENTE-LOCAL-ISHOP.md)):

```bash
bash chatbot/start.sh                       # si no está levantado
python3 chatbot/scripts/test_chatbot_e2e.py
```

El script crea una conversación real llamada `Prueba automática RAG` en
Chatwoot, envía los 13 mensajes en orden, espera la respuesta del asistente
(timeout de 45 s por mensaje) y al final imprime:

```text
Resultado: 13/13 correctas
Tiempo promedio: 2.83s
```

Resultados históricos registrados (local y producción) en
[`../RESULTADOS-Y-EVIDENCIAS.md`](../RESULTADOS-Y-EVIDENCIAS.md) §4.

## Cobertura adicional: batería manual de 40 preguntas

[`../chatbot/knowledge/preguntas-prueba.md`](../chatbot/knowledge/preguntas-prueba.md)
define 40 preguntas en cinco grupos (productos, compras/envíos,
garantía/posventa, corporativo/derivación y **control de alucinaciones**),
con una meta mínima de 32/40. Es una prueba manual (se ejecuta conversando
con el widget) porque incluye casos de juicio subjetivo (naturalidad de la
respuesta) que la prueba automática no evalúa. Resultado registrado: **39/39
correctas** en tres ejecuciones completas del protocolo.

## Por qué no hay pruebas unitarias de los scripts de utilidad

`sync_knowledge.py` e `index_knowledge.py` no tienen pruebas unitarias
propias porque son scripts de E/S (leen la tienda local, escriben en Qdrant)
sin lógica de negocio aislable en funciones puras relevantes de probar por
separado. Su corrección se verifica **indirectamente**: si la indexación
falla o genera documentos mal formados, la prueba e2e lo detecta porque el
asistente deja de encontrar evidencia o empieza a mezclar productos (ver los
fragmentos prohibidos de los casos 2-4 en la tabla de arriba).
