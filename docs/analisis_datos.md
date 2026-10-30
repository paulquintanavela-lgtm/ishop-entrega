# Análisis de datos

> El "dataset" de este proyecto no es una tabla estadística sino un
> **catálogo de comercio electrónico** convertido en documentos para
> búsqueda semántica (RAG). Este documento describe esos datos con el mismo
> rigor que pediría un EDA clásico, adaptado a lo que realmente hay: texto
> estructurado, no variables numéricas para modelar.

## Descripción detallada del dataset

**Fuente:** catálogo público de [iShop Ecuador](https://ec.tiendasishop.com/),
obtenido vía `products.json` de la tienda y sincronizado con
`chatbot/scripts/sync_knowledge.py`. Las políticas públicas (envíos, garantía,
pagos, devoluciones) se extraen de las páginas públicas de la misma tienda.

**Licencia y uso:** es información pública del sitio, usada **solo con fines
académicos y de demostración** (ver [`../LICENSE`](../LICENSE) y la sección
"Licencia" del [`README`](../README.md) para el alcance exacto). No es un
dataset de terceros con licencia abierta explícita, por lo que no se
redistribuye fuera de este proyecto académico.

**Composición, verificada con `chatbot/scripts/index_knowledge.py` sobre
`chatbot/knowledge/catalogo-productos.md`:**

- **212 productos** (`catalogo-productos.md`), cada uno como un bloque con:
  título, URL, tipo, marca, etiquetas, descripción larga y variantes con
  precio.
- **7 documentos informativos** (`contenido-publico-ishop.md`): envíos,
  garantía, pagos, devoluciones y otras políticas.
- **Total indexado en Qdrant (`ishop_rag_v2`): 219 documentos**, uno por
  producto o tema informativo.

## Estadísticas descriptivas

Calculadas directamente sobre `chatbot/knowledge/catalogo-productos.md`
(212 productos, 212 con precio publicado, 0 sin precio):

| Marca | Nº de productos |
| --- | --- |
| Apple | 66 |
| NCO (marca propia) | 50 |
| Belkin | 20 |
| Zagg | 14 |
| Bose | 10 |
| JBL | 7 |
| Satechi | 7 |
| Catalyst | 7 |
| ItSkins | 7 |
| Thule | 6 |
| Marshall | 5 |
| Speck | 3 |
| Beats | 3 |
| Microsoft | 2 |
| Mophie | 2 |
| Targus, Decoded, Gear4 | 1 cada uno |

**Precio mínimo por producto (212 valores):**

| Estadístico | Valor |
| --- | --- |
| Mínimo | $9.00 |
| Máximo | $4,349.00 |
| Mediana | $59.00 |
| Media | $273.91 |

La mediana muy por debajo de la media confirma lo que se observa en la tabla
de marcas: el catálogo está dominado en volumen por **accesorios económicos**
(fundas, cables, correas — en su mayoría Apple y NCO), mientras que los
equipos (iPhone, Mac, iPad) son pocos en número pero concentran los precios
más altos.

## Identificación de patrones, correlaciones y outliers

- **Patrón dominante:** el catálogo es de **accesorios, no de equipos**. Los
  accesorios (fundas, cables, correas, cargadores) superan ampliamente en
  cantidad a laptops, tablets y teléfonos.
- **Outliers de precio:** equipos como MacBook Pro o iPhone Pro Max (hasta
  $4,349) conviven con accesorios de $9–20. Un filtrado por categoría es
  obligatorio antes de comparar o recomendar por precio; de lo contrario, una
  búsqueda genérica por presupuesto mezclaría un cable con una laptop.
- **Concentración por marca:** Apple y la marca propia NCO suman el 55% de
  los productos (116 de 212), lo que sesga las búsquedas genéricas hacia esas
  dos marcas si no se filtra por lo que el cliente pidió explícitamente.

## Decisiones de preprocesamiento justificadas

**Decisión principal: un producto = un documento completo**, en vez de
trocear el catálogo en fragmentos (*chunks*) de tamaño fijo, que es la
práctica más común en sistemas RAG genéricos.

- **Por qué no chunks de tamaño fijo:** con chunks genéricos, la primera
  versión de la indexación (`ishop_knowledge`) devolvía fragmentos que
  mezclaban la mitad de la ficha de una MacBook con texto de un cable o
  adaptador parecido, porque el corte de texto no respeta los límites de un
  producto.
- **Con un documento por producto:** cada punto en Qdrant conserva campos
  estructurados completos (`doc_kind, category, title, url, product_type,
  brand, tags, min_price, variants, description, content`), lo que permite
  **filtrar por categoría antes de medir similitud** — así "quiero un reloj"
  nunca devuelve un MacBook por parecido de redacción.
- **Embeddings:** `nomic-embed-text` (768 dimensiones), generado localmente
  con Ollama, sin costo recurrente ni envío del catálogo a un tercero.
- **Lotes de indexación de 24 documentos** con `keep_alive: -1`, para que
  Ollama no descargue el modelo de memoria entre lotes (evita el cuello de
  botella que alargaba la indexación en el servidor).

## Manejo de datos faltantes o desbalanceados

- **Datos faltantes:** no se detectaron productos sin precio (212/212 con al
  menos una variante con precio). Los campos opcionales (etiquetas) suelen
  venir vacíos ("Sin etiquetas"); el sistema no depende de ellos para
  recuperar evidencia.
- **Desbalance de categorías:** confirmado arriba (accesorios >> equipos). Se
  mitiga en el flujo de n8n con un **filtro por categoría previo a la
  búsqueda vectorial** (ver `arquitectura.md`), de modo que una pregunta sobre
  "laptop" no devuelva fundas solo porque son mayoría en el catálogo.
- **Actualidad de los datos:** es una copia estática tomada en el momento de
  la sincronización, no un feed en vivo — limitación declarada también en
  [`../README.md`](../README.md) y en `RESULTADOS-Y-EVIDENCIAS.md`.
