# Manual de usuario

> Versión resumida para la entrega. El manual completo, con el detalle de
> atención como asesor humano, preguntas frecuentes y solución de problemas,
> está en [`../MANUAL-USUARIO-ISHOP.md`](../MANUAL-USUARIO-ISHOP.md).

El proyecto tiene **dos interfaces** (justificación arquitectónica en
[`arquitectura.md`](arquitectura.md#interfaz)): el **chat del cliente**, que
es la interfaz principal y la que se usa para resolver consultas, y el
**formulario de carga de conocimiento**, una interfaz secundaria para
mantener actualizada la base del asistente. Este documento cubre ambas.

## 1. Chat del cliente (interfaz principal)

### Guía paso a paso para usar la interfaz

1. Entrar a la tienda: <https://100-52-28-14.sslip.io>.
2. Pulsar el botón de chat en la esquina inferior derecha. Se abre una
   ventana de conversación sin salir de la página ni perder el carrito. No se
   pide registro, correo ni teléfono.
3. Escribir la consulta en lenguaje natural. Ejemplos probados:
   - *"quiero ver iphone 17"* → devuelve los modelos disponibles con precio y
     enlace a la ficha.
   - *"busco una laptop para programar, tengo 2000"* → filtra por presupuesto
     y recomienda una opción concreta.
   - *"compara la opción 1 y la 2"* → compara lo que el asistente acaba de
     mostrar.
   - *"cuánto cuesta el envío a domicilio"* → responde con la política real.
4. Si la consulta lo requiere, escribir **"quiero hablar con un asesor"** (o
   *soporte*, *persona*, *humano*, *agente*, *reclamo*, *queja*) para pasar a
   atención humana sin cambiar de ventana.

### Capturas de pantalla

Las capturas y la demostración en vivo del flujo completo están en el video
pitch (enlace en el [`README`](../README.md#videos-de-la-entrega)), que
incluye grabación de pantalla de la interfaz funcionando realmente, como
exige la entrega. Este repositorio no incluye capturas estáticas adicionales
para evitar documentación desactualizada frente a un catálogo que cambia.

### Explicación de cada funcionalidad

| Funcionalidad | Qué hace |
| --- | --- |
| Búsqueda por producto o categoría | Recupera del catálogo real los productos más relevantes, con precio y enlace |
| Búsqueda con presupuesto | Filtra las opciones que entran en el monto indicado |
| Comparación | Compara exactamente los productos mostrados en el turno anterior |
| Corrección ortográfica | Reconoce errores frecuentes (`microfno` → micrófono, `relok` → reloj, `mackbook` → MacBook) |
| Reconocimiento de límites | Si no hay evidencia suficiente, lo dice explícitamente y ofrece un asesor, en vez de inventar |
| Traspaso a humano | Palabras clave de derivación abren la conversación y la asignan a un asesor, silenciando la IA hasta que la devuelva |

### Troubleshooting (problemas comunes y soluciones)

| Problema | Causa probable | Solución |
| --- | --- | --- |
| El botón de chat no aparece | Caché del navegador | Recargar la página; comprobar que la URL empiece por `https` |
| El asistente no responde | La conversación está en estado "Abierta" (ya la atiende un asesor) | Comportamiento esperado, no una falla — esperar respuesta humana |
| Nadie responde tras pedir un asesor | Ningún asesor está marcado como "Disponible" | El cliente ve el aviso correspondiente; es una condición operativa, no un error del sistema |
| El asistente da un precio distinto al de la ficha | El catálogo del asistente no se ha resincronizado tras un cambio de precios | Reportar al responsable técnico para ejecutar `sync_knowledge.py` + `index_knowledge.py` |

Troubleshooting ampliado (incluida la operación del panel de asesores) en
[`../MANUAL-USUARIO-ISHOP.md`](../MANUAL-USUARIO-ISHOP.md#preguntas-frecuentes).

### FAQ (preguntas frecuentes)

**¿El asistente puede equivocarse?**
Puede no encontrar algo, y en ese caso lo dice. No inventa productos ni
precios: solo responde con lo que está en el catálogo cargado, y siempre
enlaza la ficha del producto para confirmar.

**¿Tengo que registrarme para usar el chat?**
No. El widget no pide nombre, correo ni teléfono para conversar.

**¿Puedo pedir hablar con una persona en cualquier momento?**
Sí, en cualquier punto de la conversación, sin perder el historial.

## 2. Formulario de carga de conocimiento (interfaz secundaria)

Para un asesor o administrador que necesita que el asistente conozca una
política, instructivo o promoción nueva que no está en la tienda. Detalle
técnico del formulario en [`arquitectura.md`](arquitectura.md#interfaz).

### Guía paso a paso

1. Abrir `https://n8n.100-52-28-14.sslip.io/form/cargar-conocimiento`.
2. Escribir el **tema del documento** (obligatorio), descriptivo — por
   ejemplo "Política de reservas y apartado 2026" — para que ayude al
   asistente a encontrarlo.
3. Elegir el **archivo** (obligatorio): acepta PDF y texto (`.pdf`, `.txt`,
   `.md`).
4. Pulsar **Submit**.
5. La pantalla de cierre confirma **"Documento agregado"** con el número de
   fragmentos guardados, o **"No se pudo agregar"** si algo falló (por
   ejemplo, un PDF escaneado como imagen sin texto extraíble).

Desde ese momento el asistente ya responde con ese contenido; no hace falta
reiniciar nada.

### Explicación de la funcionalidad

| Funcionalidad | Qué hace |
| --- | --- |
| Validación de campos | Tema y archivo son obligatorios; el archivo solo acepta `.pdf, .txt, .md` |
| Extracción de texto | Rama automáticamente según el archivo sea PDF o texto plano |
| Indexación | Calcula los embeddings y los agrega a la colección vectorial sin borrar lo ya cargado |
| Confirmación clara | Mensaje de éxito o error específico, no genérico |

### Troubleshooting

| Problema | Causa probable | Solución |
| --- | --- | --- |
| "No se pudo agregar" | El PDF está escaneado como imagen (sin texto extraíble) | Usar un PDF con texto real o convertir a `.txt`/`.md` |
| El asistente no usa el documento recién subido | El clasificador de intención no asoció la pregunta al tema cargado | Reformular la pregunta citando el tema del documento, o repetir la carga con un tema más descriptivo |
| Se subió una versión con un error | Los documentos cargados no se autoeliminan al actualizar el catálogo | Pedir al responsable técnico que elimine la versión anterior (ver `MANUAL-TECNICO-ISHOP.md`) |

## Información de contacto para soporte

Para incidencias del sistema (no del catálogo), el procedimiento documentado
es reportar al equipo de desarrollo: captura del error, nombre del nodo rojo
en n8n si aplica, y el comando ejecutado — ver
[`../MANUAL-TECNICO-ISHOP.md`](../MANUAL-TECNICO-ISHOP.md#fallas-conocidas-y-cómo-diagnosticarlas).
Dentro de la tienda, la vía de contacto para un cliente real es el propio
chat, pidiendo un asesor.
