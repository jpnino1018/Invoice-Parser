
# Conversor XML → TXT (Facturas Electrónicas)

Repositorio: Invoice-Parser

Un conversor ligero que extrae datos clave de facturas electrónicas UBL/DIAN en formato XML y genera un TXT legible (ejemplo). Está pensado para procesar facturas individuales o contenedores (`AttachedDocument`) y para manejar casos donde la factura está embebida dentro de un nodo CDATA/Description.

## Estado actual
- Parser actualizado para detectar y reparsear XML embebido (CDATAs o texto que contiene `<Invoice`), y para extraer campos clave de forma más robusta frente a namespaces.
- Generador TXT simple que produce un fichero con cabeceras y una lista de items separados por `|`.
- Scripts útiles añadidos: `test_parse.py` (resumen de parseo)

## Estructura del proyecto
- `app.py` — interfaz Streamlit (UI) para subir XML/ZIP y descargar TXT.
- `requirements.txt` — dependencias mínimas (streamlit, xmltodict).
- `converters/`
  - `xml_parser.py` — lógica principal para parsear XML UBL/DIAN y normalizar a un dict simple.
  - `txt_generator.py` — genera el TXT desde el dict normalizado.
  - `utils.py` — utilidades (p. ej. extraer archivos desde ZIP).
- `examples/` — ejemplos de facturas para pruebas (incluye `AttachedDocument` con Invoice embebido).
- `test_parse.py` — script de diagnóstico para imprimir campos extraídos de los ejemplos.


## Requisitos
- Python 3.8+ (se ha probado con 3.11/3.13 en entornos locales).
- Virtualenv recomendado.

Instalar dependencias:

```powershell
# crear y activar venv (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# instalar deps
pip install -r requirements.txt
```

## Uso rápido

1) Ejecutar un test rápido para ver qué extrae el parser de los ejemplos:

```powershell
python test_parse.py
```

Salida esperada (resumen): `numero`, `uuid`, `fecha`, `total`, `currency`, `proveedor`, `cliente` y `items_count`, además de una muestra de items.


2) Ejecutar la app Streamlit para subir archivos y descargar el TXT:

```powershell
python -m streamlit run app.py
```

## Formato TXT
El generador actual produce un TXT sencillo con este esquema:

- Cabecera: FACTURA|ID|FECHA|HORA
- EMISOR|NIT|NOMBRE
- ADQUIRIENTE|NIT|NOMBRE
- TOTAL|VALOR|CURRENCY
- ITEMS: (líneas)
    - descripcion|cantidad|unidad|precio_unitario|total_linea


## Comportamiento del parser (detalles técnicos)
- Búsqueda flexible de nodos con namespaces: la función `_strip_ns` normaliza claves (quita prefijos `cbc:`/`cac:` y `{...}`) para buscar nodos por nombre independiente del namespace.
- CDATA / XML embebido: el parser revisa recursivamente el documento y, si encuentra strings que contienen `<?xml` o `<Invoice` (u otros elementos relevantes), intenta reparsarlas con `xmltodict` y reemplazar esas cadenas por el dict resultante para que la factura sea localizada y procesada.
- Extracción de texto: la función `get_text` ahora trata la lista `path` como alternativas en el mismo nivel y extrae con preferencia `#text`, luego atributos `@...`, y luego el primer valor primitivo disponible.
- Campos normalizados devueltos por `parse_invoice_xml`:
  - `numero`, `uuid`, `fecha`, `hora`
  - `proveedor`: `{name, nit}`
  - `cliente`: `{name, nit}`
  - `total`, `currency`
  - `items`: lista de `{descripcion, cantidad, unidad, precio_unitario, total_linea}`

## Limitaciones conocidas
- No hay validación XSD/DIAN: el parser no valida la factura contra los esquemas UBL o las reglas de la DIAN. Se puede añadir `lxml`/`xmlschema` para validación.
- Normalización de números: los valores numéricos se devuelven como strings tal cual aparecen en el XML. Recomendable normalizar (separadores, punto decimal) si necesitas cálculos.
- Separador TXT: no escapa `|` en descripciones; si existe la posibilidad de `|` en el texto, conviene escapar o elegir otro separador.
- Heurística de parseo embebido: la detección de XML dentro de texto es heurística (búsqueda de `<?xml` o `<Invoice`); podría falsear en textos que contengan esas cadenas por otras razones. Si quieres, podemos restringir la búsqueda a las rutas conocidas donde suele aparecer (p.ej. `cac:Attachment/cac:ExternalReference/cbc:Description`).

## Tests y CI
- Se pueden añadir tests con `pytest`. Sugerencia mínima:
  - Test 1: parseo de `examples/c1128...xml` → validar `numero`, `proveedor`, `items`.
  - Test 2: parseo de `examples/ad0900...xml` (AttachedDocument) → validar `numero`, `proveedor`, `items`.
