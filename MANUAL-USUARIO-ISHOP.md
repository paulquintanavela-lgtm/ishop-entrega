---
title: "Manual de usuario de iShop"
subtitle: "Cómo usar el asistente virtual y cómo atender desde el panel de asesores"
author: "Proyecto de tesis iShop"
date: "22 de octubre de 2026"
lang: es
toc: true
---

# Para quién es este manual

Este manual explica **cómo se usa el sistema**, no cómo se construyó. No hace
falta saber programar ni entrar al servidor en ningún momento.

Hay dos tipos de usuario y cada uno tiene su parte:

| Usuario | Dónde trabaja | Qué encontrará aquí |
|---|---|---|
| Cliente | Chat de la tienda | Cómo preguntar y qué puede esperar |
| Asesor | Panel de Chatwoot | Cómo atender, responder y cerrar conversaciones |

Para entender qué tecnologías se usaron está la *Guía de la publicación en la
nube*; para el detalle interno, el *Manual técnico*.

# Direcciones

| Para qué | Dirección |
|---|---|
| Tienda con el chat | `https://100-52-28-14.sslip.io` |
| Panel de asesores | `https://chat.100-52-28-14.sslip.io` |
| Automatizaciones | `https://n8n.100-52-28-14.sslip.io` |

Las tres funcionan desde cualquier computadora o teléfono con Internet. No hace
falta instalar nada.

# Parte 1: el cliente en la tienda

## Abrir el chat

En cualquier página de la tienda aparece un botón de chat en la esquina inferior
derecha. Al pulsarlo se abre una ventana de conversación sin salir de la página
ni perder el carrito.

No se pide registro, correo ni teléfono para conversar.

## Qué se le puede preguntar

El asistente responde **solo con información real del catálogo de iShop**. Estos
son casos verificados, con la respuesta que realmente devuelve:

**Buscar un producto por lo que necesita**

> *quiero ver iphone 17*
>
> Devuelve el iPhone 17 Pro desde $1629, el iPhone 17 desde $1259 y el iPhone 17
> Pro Max desde $1789, cada uno con su enlace a la ficha.

**Buscar por uso, sin saber el nombre del producto**

> *quiero audífonos para el gimnasio*
>
> Devuelve los JBL Endurance Run 3 desde $49 y los Bose QuietComfort desde $559,
> entre otros.

**Buscar con presupuesto**

> *busco una laptop para programar, tengo 2000*
>
> Filtra el catálogo por ese precio y propone las opciones que entran.

**Comparar dos opciones que acaba de ver**

> *compara la opción 1 y la 2*
>
> El asistente recuerda lo que acaba de mostrar y responde sobre esos productos.

**Preguntar por envíos, garantía o pagos**

> *cuánto cuesta el envío a domicilio*
>
> Responde con la política real: envío gratis en compras superiores a $100 y
> envío a todo el país por $6.

> *cuánto dura la garantía*
>
> Responde que la garantía oficial es de 1 año, excepto en liquidación.

## Qué pasa si escribe con errores

El asistente corrige los errores de escritura más frecuentes. Estos tres casos
están probados y funcionan:

| Lo que escribe el cliente | Lo que entiende el asistente |
|---|---|
| *mejor un relok* | Reloj Apple Watch |
| *ahora quiero un microfno* | Micrófono |
| *un mackbook* | MacBook |

## Qué pasa si pregunta algo que no está en el catálogo

El asistente **no inventa**. Cuando no encuentra la información, lo dice y
ofrece una salida:

> *que tarjetas aceptan para pagar*
>
> "No encontré 'que tarjetas aceptan para pagar' como producto en el catálogo
> actual de iShop. Puedes reformular la búsqueda o escribir 'quiero un asesor'."

Esto es intencional. Es preferible que el asistente reconozca un límite a que
responda con un precio o una condición inventada.

## Pedir hablar con una persona

En cualquier momento el cliente puede escribir **"quiero hablar con un asesor"**.
También funcionan las palabras *soporte*, *persona*, *humano*, *agente*,
*reclamo* y *queja*.

El asistente responde que lo conecta, deja de intervenir y la conversación pasa
a la bandeja del asesor. **El cliente no cambia de ventana ni vuelve a empezar**:
sigue en el mismo chat y ahí mismo le responde una persona.

# Parte 2: el asesor en el panel

## Entrar

1. Abrir `https://chat.100-52-28-14.sslip.io`.
2. Escribir el correo y la contraseña.
3. Pulsar **Iniciar sesión**.

Una advertencia importante: **si aparece una pantalla de configuración inicial
pidiendo datos de la empresa, no hay que completarla**. Esa pantalla crea una
cuenta nueva y vacía, sin conversaciones. Si ocurre, cerrar sesión y volver a
entrar con el usuario correcto.

## Marcarse disponible

Al entrar, pulsar la foto de perfil abajo a la izquierda y cambiar el estado a
**Disponible**.

Esto importa por dos razones: el asesor empieza a recibir conversaciones, y el
widget de la tienda deja de mostrar el aviso "Estamos ausentes" a los clientes.

## La pantalla principal

El menú de la izquierda tiene estas secciones:

| Sección | Para qué sirve |
|---|---|
| Mi bandeja de entrada | Lo asignado a usted |
| Conversaciones | Todas las conversaciones de la tienda |
| Contactos | Las personas que han escrito |
| Informes | Estadísticas de atención |
| Ajustes | Configuración y gestión de asesores |

Dentro de **Conversaciones** hay tres pestañas:

- **Mías**: las asignadas a usted. Es su lista de trabajo.
- **Sin asignar**: llegaron pero nadie las tomó.
- **Todos**: todo lo que existe, para supervisar.

## Entender los estados

El estado indica quién está a cargo de la conversación:

| Estado | Significado | Qué hacer |
|---|---|---|
| Pendiente | El asistente virtual está respondiendo | Nada, salvo supervisar |
| Abierta | El cliente pidió una persona | Responder |
| Resuelta | La consulta terminó | Nada |

Esta es la regla que hay que recordar: **Pendiente significa que la máquina
atiende; Abierta significa que le toca a usted**.

## Atender una conversación

Cuando un cliente pide un asesor, el sistema hace tres cosas solo: cambia la
conversación a **Abierta**, se la asigna al asesor configurado y deja una **nota
interna** avisando del traspaso. Desde ese momento el asistente virtual deja de
responder para no pisar a la persona.

Para atender:

1. Abrir la conversación desde la lista.
2. Leer el historial. Todo lo que el cliente habló con el asistente está ahí
   arriba, no hay que pedirle que repita.
3. Escribir en la pestaña **Responder** y pulsar **Enviar**.

El cliente lo ve al instante en el mismo chat de la tienda.

## Notas internas

Junto a **Responder** está la pestaña **Nota privada**. Lo que se escribe ahí
**no lo ve el cliente**: sirve para dejar contexto a otro asesor, por ejemplo
"cliente pregunta por disponibilidad en Guayaquil, confirmar con bodega".

Las notas se distinguen por su fondo de color diferente.

## Devolver la conversación al asistente

Si la duda que requería una persona ya se resolvió y el cliente sigue
preguntando cosas del catálogo, se cambia el estado a **Pendiente** y el
asistente virtual retoma la atención.

## Cerrar una conversación

Cuando la atención termina, pulsar **Resolver** arriba a la derecha. La
conversación sale de la lista activa pero no se borra: queda en el historial del
contacto y se puede reabrir.

## Cambiar la contraseña

Pulsar la foto de perfil, entrar a **Perfil** y cambiar la contraseña desde ahí.
Conviene hacerlo la primera vez que se entra.

## Agregar otro asesor

Desde **Ajustes → Agentes → Agregar agente**. Llega una invitación al correo de
la persona.

Nunca hay que pedirle que se registre por su cuenta desde la página de inicio:
eso crea una cuenta separada y vacía, que es el error más frecuente al empezar.

# Preguntas frecuentes

**El botón del chat no aparece en la tienda.**
Recargar la página con la ventana cerrada y vuelta a abrir. Si sigue sin
aparecer, comprobar que la dirección empiece por `https`.

**El asistente no responde.**
Revisar en el panel si la conversación está en **Abierta**: si lo está, el
asistente cedió el turno a una persona y espera respuesta humana. Es el
comportamiento correcto, no una falla.

**El cliente dice que nadie le responde.**
Comprobar que haya un asesor marcado como **Disponible**. Si todos están
ausentes, el cliente ve el aviso correspondiente y nadie recibe la conversación.

**Entro al panel y no veo ninguna conversación.**
Lo más probable es estar en una cuenta equivocada, creada sin querer desde la
pantalla de configuración inicial. Cerrar sesión y entrar con el usuario que fue
invitado desde **Ajustes → Agentes**.

**El asistente da un precio distinto al de la página del producto.**
El catálogo del asistente se actualiza cuando se reconstruye la base de
conocimiento. Si la tienda cambió precios recientemente, hay que pedir esa
actualización al responsable técnico; el procedimiento está en el manual
técnico.

**¿El asistente puede equivocarse?**
Puede no encontrar algo, y en ese caso lo dice. Lo que no hace es inventar
productos ni precios: solo responde con lo que está en el catálogo cargado. Por
eso la respuesta siempre incluye el enlace a la ficha, para confirmar precio y
disponibilidad.

# Buenas prácticas de atención

- Revisar la pestaña **Sin asignar** al empezar el turno: ahí quedan las
  conversaciones que nadie tomó.
- Leer el historial antes de responder. El cliente ya explicó lo que busca y
  repetir preguntas da mala impresión.
- Usar notas privadas en lugar de mensajes al cliente para coordinar
  internamente.
- Resolver las conversaciones terminadas. Una lista llena de conversaciones
  abiertas impide distinguir lo que de verdad está pendiente.
- Marcarse como **Ausente** al terminar el turno, para que las conversaciones no
  queden asignadas a alguien que no está.
