# Subir iShop a la nube con los créditos gratis de AWS

Guía completa para pasar el proyecto de Docker local a un servidor público con
HTTPS. El mismo `compose.yml` de local se reutiliza; solo se suma el archivo
`compose.prod.yml` y el proxy Caddy.

## Qué vas a tener al final

| Dirección | Servicio |
| --- | --- |
| `https://TU-DOMINIO` | La tienda iShop con el widget del chatbot |
| `https://chat.TU-DOMINIO` | Panel de Chatwoot para atender como asesor |
| `https://n8n.TU-DOMINIO` | Editor de n8n con los workflows |

Qdrant, Ollama, PostgreSQL y Redis quedan cerrados: solo responden dentro del
servidor, nunca desde internet.

## Cuánto cuesta

| Concepto | Costo |
| --- | --- |
| Créditos AWS para cuenta nueva | US$100 al registrarte + hasta US$100 extra |
| Servidor Lightsail 4 GB RAM / 2 vCPU / 80 GB | US$24 al mes, descontados de los créditos |
| Dominio DuckDNS | US$0 |
| Certificado HTTPS (Let's Encrypt) | US$0 |
| Google Gemini (cuota gratuita) | US$0 |

Con los US$200 completos cubres los 6 meses que dura el plan gratuito, que es
el máximo que AWS permite. El plan Free no cobra a la tarjeta: cuando se
acaban los créditos o se cumplen los 6 meses, AWS cierra la cuenta sola.

> Lightsail cobra el plan aunque la instancia esté apagada. Si vas a dejar de
> usarla un tiempo, toma un snapshot y elimina la instancia; el snapshot cuesta
> centavos y después recreas la instancia desde ahí.

## Paso 1. Crear la cuenta de AWS

1. Entra a <https://aws.amazon.com/free/> y elige **Create a free account**.
2. Selecciona el plan **Free** (no el Paid). Pide tarjeta solo para verificar
   identidad; no se cobra mientras estés en el plan Free.
3. Ya dentro de la consola, busca el widget **Explore AWS** en la página de
   inicio y completa las actividades (lanzar una instancia EC2, probar Bedrock,
   crear un presupuesto). Cada una suma créditos hasta llegar a los US$200.
4. Revisa el saldo en **Billing and Cost Management → Credits**.

## Paso 2. Crear el servidor

1. Abre <https://lightsail.aws.amazon.com/> → **Create instance**.
2. Región: la más cercana a Ecuador (por ejemplo `us-east-1`, Virginia).
3. Plataforma **Linux/Unix** → blueprint **OS Only → Ubuntu 24.04 LTS**.
4. Plan: **4 GB RAM, 2 vCPU, 80 GB SSD** (US$24/mes). Con menos RAM, Chatwoot
   y Ollama no entran juntos.
5. Nombre: `ishop-tesis`. Crea la instancia.
6. En la pestaña **Networking** de la instancia:
   - **Attach static IP** y anota la IP.
   - En el firewall deja abiertos solo **22 (SSH)**, **80 (HTTP)** y
     **443 (HTTPS)**.
7. Conéctate con el botón **Connect using SSH** del navegador, o desde tu Mac
   con la llave descargada:

   ```bash
   ssh -i ~/Downloads/LightsailDefaultKey.pem ubuntu@LA-IP-ESTATICA
   ```

## Paso 3. Registrar el dominio gratis

1. Entra a <https://www.duckdns.org/> e inicia sesión con Google o GitHub.
2. Crea un subdominio, por ejemplo `ishop-pierre`.
3. En el campo **current ip** escribe la IP estática de Lightsail y pulsa
   **update ip**.
4. Tu dominio base queda como `ishop-pierre.duckdns.org`. Los subdominios
   `chat.` y `n8n.` funcionan automáticamente, no hay que registrarlos.
5. Comprueba desde tu Mac que ya resuelve:

   ```bash
   ping -c 1 ishop-pierre.duckdns.org
   ping -c 1 chat.ishop-pierre.duckdns.org
   ```

   Si todavía responde otra IP, espera unos minutos: Caddy no puede emitir el
   certificado hasta que el DNS apunte bien.

## Paso 4. Copiar el proyecto al servidor

El repositorio es privado, así que la forma más simple es copiarlo desde el Mac
con `rsync`. Desde **tu Mac**, no desde el servidor:

```bash
rsync -avz --delete \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '.DS_Store' \
  --exclude 'chatbot/.env' \
  --exclude 'chatbot/.env.bak' \
  --exclude 'chatbot/.chatwoot-prepared' \
  --exclude 'chatbot/widget/chatwoot-config.json' \
  -e "ssh -i ~/Downloads/LightsailDefaultKey.pem" \
  ~/Documents/ishop/ ubuntu@LA-IP-ESTATICA:~/ishop/
```

Las exclusiones importan: el `.env` y los tokens de tu Mac no sirven en el
servidor, y `.chatwoot-prepared` haría que el arranque se saltara la creación
de la base de datos.

Son unos 100 MB, así que tarda un par de minutos. Para actualizar el servidor
más adelante, repite el mismo comando.

> Si prefieres `git clone`, primero haz público el repositorio o crea un deploy
> key en GitHub. En ese caso recuerda que `.chatwoot-prepared` y los `.env` ya
> están en `.gitignore`, así que no se copian.

## Paso 5. Preparar el servidor

Dentro del servidor, por SSH:

```bash
cd ~/ishop
bash chatbot/deploy/setup-server.sh
```

El script instala Docker con el plugin Compose, crea 2 GB de swap e instala
`git` y `python3`. Al terminar, **cierra la sesión SSH y vuelve a entrar** para
poder usar `docker` sin `sudo`.

## Paso 6. Configurar el entorno de producción

```bash
cd ~/ishop
bash chatbot/deploy/configure.sh ishop-pierre.duckdns.org tu-correo@ejemplo.com
```

Esto escribe `chatbot/.env` con los dominios, las URLs públicas y contraseñas
nuevas generadas al azar. Falta una sola cosa, la API key gratuita de Gemini de
<https://aistudio.google.com/app/apikey>:

```bash
nano chatbot/.env   # completa GEMINI_API_KEY=...
```

El archivo incluye `COMPOSE_FILE=compose.yml:compose.prod.yml`, así que
cualquier `docker compose` que ejecutes dentro de `chatbot/` ya usa la
configuración de producción.

## Paso 7. Levantar el stack

```bash
cd ~/ishop
bash chatbot/deploy/start-prod.sh
```

La primera vez tarda entre 10 y 15 minutos: descarga las imágenes, prepara la
base de Chatwoot y baja el modelo de embeddings `nomic-embed-text`. Si algo
falla, mira los registros:

```bash
cd chatbot
docker compose ps
docker compose logs -f caddy      # certificados HTTPS
docker compose logs -f chatwoot
```

Abre `https://TU-DOMINIO` en el navegador. La tienda debe cargar con candado de
seguridad.

## Paso 8. Conectar Chatwoot con el widget

1. Entra a `https://chat.TU-DOMINIO` y crea la cuenta propietaria.
2. **Profile Settings → Access Token**: copia el token.
3. Pégalo en `chatbot/.env` como `CHATWOOT_ACCESS_TOKEN=...`
4. Ejecuta:

   ```bash
   cd ~/ishop
   python3 chatbot/scripts/setup_chatwoot.py
   cd chatbot && docker compose up -d n8n && cd ..
   ```

   Se usa `up -d` y no `restart` porque n8n tiene que volver a leer el `.env`
   para recibir `CHATWOOT_BOT_TOKEN`.

El script crea el inbox `iShop Web` y el AgentBot, y genera
`chatbot/widget/chatwoot-config.json` apuntando a `https://chat.TU-DOMINIO`.
El widget de la tienda lo lee solo, sin tocar código.

## Paso 9. Workflows y credenciales de n8n

1. Entra a `https://n8n.TU-DOMINIO` y crea el usuario propietario.
2. Importa los workflows:

   ```bash
   bash chatbot/import-workflows.sh
   ```

3. En n8n crea las credenciales como en local (las URLs internas no cambian
   porque los contenedores siguen hablando entre ellos):
   - `Ollama API`: `http://ollama:11434`
   - `QdrantApi`: `http://qdrant:6333`, API key vacía o `local`
   - `Google Gemini(PaLM) Api`: tu API key
4. Activa el workflow `iShop 04 - AgentBot Chatwoot`.

## Paso 10. Cargar el índice RAG

`start-prod.sh` ya lo crea si no existe. Para reconstruirlo después de
actualizar el catálogo:

```bash
cd ~/ishop
python3 chatbot/scripts/sync_knowledge.py
python3 chatbot/scripts/index_knowledge.py
```

## Paso 11. Cerrar el registro público de Chatwoot

Con el propietario ya creado, evita que cualquiera abra una cuenta en tu panel:

```bash
nano chatbot/.env            # ENABLE_ACCOUNT_SIGNUP=false
cd chatbot && docker compose up -d chatwoot chatwoot-sidekiq
```

## Paso 12. Verificar

```bash
cd ~/ishop
python3 chatbot/scripts/test_chatbot_e2e.py
```

Y a mano, desde el navegador:

1. `https://TU-DOMINIO` carga con HTTPS y aparece el botón naranja del chat.
2. Pregunta algo del catálogo: la IA responde con precios reales.
3. Escribe "quiero hablar con un asesor": la conversación pasa a la bandeja de
   `https://chat.TU-DOMINIO` y la IA deja de responder.
4. Responde desde Chatwoot y comprueba que el mensaje llega al widget.
5. Confirma que `https://TU-DOMINIO/chatbot/.env` devuelve 404.

## Operación diaria

```bash
cd ~/ishop/chatbot
docker compose ps                  # estado
docker compose logs -f n8n         # registros
docker compose up -d n8n           # aplicar cambios del .env en un servicio
docker compose down                # apagar todo (los datos quedan)
bash deploy/start-prod.sh          # volver a encender
free -h                            # memoria y swap
```

Respaldo de los datos de Chatwoot antes de que expire la cuenta:

```bash
cd ~/ishop/chatbot
docker compose exec -T chatwoot-postgres \
  pg_dump -U postgres chatwoot_production > ~/chatwoot-backup.sql
```

## Cuando se acaben los créditos

El plan Free termina a los 6 meses. Para seguir con el proyecto, el mismo
`compose.yml` y `compose.prod.yml` funcionan sin cambios en cualquier VPS con
Docker (Hetzner CPX21, 4 GB, ~US$8 al mes). Solo hay que repetir los pasos 4 a
9 en el servidor nuevo y actualizar la IP en DuckDNS.

## Diferencia con el entorno local

El servidor no clona páginas nuevas de la tienda original: `server.py` solo
existe en local. En la nube, Caddy sirve las páginas ya descargadas, así que
cualquier URL que nunca se haya visitado en local dará 404. Si falta alguna,
ábrela primero en `http://localhost:8080`, confirma que se creó la carpeta y
vuelve a copiar el proyecto con el `rsync` del paso 4.
