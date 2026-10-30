# Consideraciones éticas

> Documento crítico según la rúbrica del proyecto. Cubre sesgos, equidad,
> privacidad, transparencia, impacto social, responsabilidad, uso dual y
> limitaciones, específicamente para un asistente de atención al cliente con
> RAG sobre un catálogo real.

## 1. Análisis de sesgos

**¿El dataset tiene sesgos demográficos, culturales o de otro tipo?**
El catálogo no contiene datos de personas (no hay nombres, edades, género ni
ubicación de clientes), así que no hay sesgo demográfico en los datos de
entrada. El sesgo relevante aquí es de **dominio y de volumen**:

- **Sesgo de dominio:** el catálogo cubre únicamente productos Apple y
  accesorios de una tienda en Ecuador. Fuera de ese ámbito (otra marca, otro
  país, otro tipo de producto), el asistente debe reconocer el límite en
  lugar de responder como si lo supiera.
- **Sesgo de volumen:** 116 de 212 productos (55%) son Apple o la marca propia
  NCO, y los accesorios superan ampliamente a los equipos (ver
  `analisis_datos.md`). Una búsqueda genérica sin filtrar por categoría tiende
  a devolver accesorios simplemente porque son mayoría.

**¿Cómo podrían afectar estos sesgos las respuestas?** Sin mitigación, una
pregunta como "quiero una laptop" podría mezclarse con resultados de
accesorios, o una consulta fuera de catálogo podría recibir una respuesta
genérica en vez de un "no lo tenemos".

**¿Qué grupos podrían ser perjudicados?** Clientes que buscan marcas o
categorías poco representadas en el catálogo (por ejemplo, accesorios de
marcas con 1-2 productos) podrían recibir menos variedad de opciones que
quienes buscan Apple o NCO.

## 2. Equidad y fairness

**¿El modelo trata a todos los grupos de forma equitativa?** No hay grupos de
*usuarios* protegidos en juego (el sistema no perfila personas), por lo que no
aplican métricas de fairness en el sentido de clasificación entre grupos
demográficos. La equidad relevante aquí es **entre categorías de producto**:
que la recomendación no favorezca sistemáticamente una marca por estar
sobrerrepresentada en el catálogo.

**Estrategia implementada para mitigar esa inequidad:** filtro por categoría
**antes** de medir similitud vectorial (ver `arquitectura.md`), de modo que
una búsqueda de "reloj" no devuelva un MacBook ni una pregunta sobre una marca
minoritaria se diluya entre los resultados de las marcas mayoritarias.

**Métricas de fairness evaluadas:** no se calcularon métricas formales de
fairness (no aplican directamente a este caso de uso); la mitigación se validó
cualitativamente con los casos de la batería de pruebas que piden productos de
categorías específicas.

## 3. Privacidad

**¿Se utilizan datos personales o sensibles?** El widget de chat **no pide**
nombre, teléfono, dirección ni datos de pago. Solo se envía a Gemini el texto
del mensaje del cliente y los fragmentos de catálogo recuperados — nunca datos
de identificación.

**¿Cómo se protege la privacidad de los usuarios?**
- Los secretos (`GEMINI_API_KEY`, tokens de Chatwoot) viven en `chatbot/.env`,
  fuera de control de versiones.
- Los servicios internos (Qdrant, Ollama, PostgreSQL, Redis) solo escuchan en
  `127.0.0.1`: no son alcanzables desde internet.
- Caddy devuelve 404 ante rutas sensibles del repositorio (verificado contra
  `/chatbot/.env` en producción).
- El registro público de cuentas en Chatwoot está desactivado.

**Cumplimiento con regulaciones (GDPR, CCPA, etc.):** no se hizo un análisis
formal de cumplimiento normativo porque el sistema no recolecta datos
personales identificables; si en producción real se activara una base de
contactos (nombre, correo) dentro de Chatwoot, ese flujo quedaría fuera del
diseño actual y necesitaría una política de privacidad y retención propia —
señalado aquí como trabajo futuro, no como algo ya resuelto.

## 4. Transparencia y explicabilidad

**¿El modelo es interpretable?** No en el sentido de un modelo estadístico con
coeficientes o importancia de variables (no aplica SHAP/LIME porque no hay un
clasificador entrenado). Lo que sí es trazable y auditable es **el camino que
sigue cada respuesta**: qué documentos recuperó Qdrant, con qué puntaje, y qué
evidencia se le pasó a Gemini — visible en los registros de ejecución de n8n
para cada conversación.

**¿Los usuarios entienden cómo funciona?** El cliente ve una conversación
normal de chat; no se le explica el mecanismo interno (RAG, embeddings), lo
cual es consistente con otros asistentes comerciales. Lo que sí es visible
para el usuario es el límite del sistema: cuando no encuentra evidencia, lo
dice explícitamente ("No encontré X como producto en el catálogo actual de
iShop") en vez de simular certeza.

**Técnicas de explicabilidad implementadas:** ninguna técnica tipo SHAP/LIME
(no aplican a este pipeline); la forma de explicabilidad elegida es
**arquitectónica**: separar recuperación de generación para que cada
respuesta pueda verificarse contra la ficha real del producto (el asistente
siempre enlaza la URL del producto).

## 5. Impacto social

**¿Qué impacto positivo puede tener el proyecto?** Reduce el tiempo de espera
de clientes con preguntas frecuentes, libera a los asesores humanos para
casos complejos, y mantiene la atención disponible fuera de horario de
oficina.

**¿Qué impactos negativos podrían surgir?**
- Si el sistema fallara y empezara a inventar (alucinar) información de
  precios o garantías, podría inducir a una compra basada en datos falsos —
  por eso existen los casos 37-40 de la batería de pruebas, diseñados
  específicamente para detectar ese fallo.
- Dependencia de un servicio externo (Gemini): si no está disponible, la
  calidad conversacional baja (modo de respaldo más seco), aunque el sistema
  sigue siendo veraz.

**¿Quiénes se benefician? ¿Quiénes podrían ser perjudicados?** Se benefician
los clientes (respuesta más rápida) y el equipo de atención (menos carga
repetitiva). Podrían verse perjudicados clientes que confíen ciegamente en
una respuesta sin verificarla en la ficha del producto, o que esperen que el
asistente resuelva casos que están fuera de su alcance (reembolsos,
disputas) sin pedir explícitamente un asesor.

## 6. Responsabilidad

**¿Quién es responsable si el modelo falla?** El equipo de desarrollo del
proyecto es responsable de la configuración del pipeline (umbral de
evidencia, filtros, reglas de derivación) y de documentar sus límites. El
asistente **no toma decisiones comerciales** (reembolsos, garantías,
confirmaciones de pedido): esas siempre se derivan a un asesor humano, que es
quien tiene la autoridad y la responsabilidad final sobre esos casos.

**¿Qué mecanismos de accountability existen?** Los registros de ejecución de
n8n permiten reconstruir, para cualquier conversación, qué evidencia se
recuperó y qué se le pidió a Gemini que redactara — es la base para auditar
una respuesta incorrecta después de ocurrida.

**Plan de monitoreo y actualización del modelo:** el catálogo se actualiza
manualmente ejecutando `sync_knowledge.py` + `index_knowledge.py` cuando
cambian precios o productos (no hay actualización automática/continua); la
batería de pruebas e2e se usa como chequeo de regresión antes de dar por
buena una actualización del flujo o del catálogo.

## 7. Uso dual y mal uso

**¿Podría el modelo usarse con fines maliciosos?** El sistema está acotado a
responder sobre el catálogo de una tienda específica; no genera contenido
libre ni ejecuta acciones fuera de ese dominio (no hace pagos, no accede a
datos de terceros). El riesgo de uso dual es bajo por el propio diseño RAG
(redacta solo sobre evidencia acotada), pero no es cero: alguien podría
intentar manipular el prompt para que el asistente afirme algo fuera de su
evidencia (*prompt injection*).

**¿Qué salvaguardas se han implementado?** La instrucción al modelo de
redactar **únicamente** con la evidencia recuperada, el umbral de similitud
que obliga a reconocer un límite, y la derivación a humano ante palabras
clave de riesgo (reclamo, queja, garantía) actúan como barreras, aunque no se
hizo una prueba formal de *red-teaming* contra *prompt injection* — declarado
como pendiente.

**Limitaciones de uso claramente documentadas:** ver sección 8 y
[`../README.md`](../README.md#limitaciones-reconocidas).

## 8. Limitaciones reconocidas

**¿En qué casos NO debe usarse el asistente?**
- Reembolsos excepcionales, rechazo de garantías, confirmación de
  transacciones o cualquier decisión comercial — el propio asistente deriva
  estos casos a un asesor humano.
- Consultas de inventario en tiempo real o estado de un pedido real: el
  sistema trabaja sobre una copia estática del catálogo, no sobre el sistema
  real de inventario/pedidos de iShop.

**¿Qué advertencias deben darse a los usuarios?** Los precios y la
disponibilidad mostrados corresponden al momento de la última sincronización
del catálogo, no a disponibilidad en tiempo real; el asistente lo indica y
siempre enlaza la ficha del producto para confirmar.

**Casos límite donde el modelo no es confiable:**
- Preguntas ambiguas sin presupuesto ni categoría clara (el sistema pide una
  aclaración, no adivina).
- Preguntas engañosas que piden inventar algo (p. ej. "asegúrame que mi
  reparación será gratuita"): deben reconocer el límite, y están cubiertas
  explícitamente en la batería de pruebas (casos 37-40).
- Fuera del dominio del catálogo (otra tienda, otro país, otro tipo de
  producto no vendido): el asistente debe decir que no lo tiene, no ofrecer
  algo parecido como si lo fuera.

Para el detalle de control de alucinaciones y los casos de prueba específicos
diseñados para esto, ver
[`../RESULTADOS-Y-EVIDENCIAS.md`](../RESULTADOS-Y-EVIDENCIAS.md) §§8 y 9.
