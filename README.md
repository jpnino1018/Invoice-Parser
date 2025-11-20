# Conversor XML → FPBATCH (SIESA UNO 8.5C)

Este proyecto automatiza la conversión de **facturas electrónicas XML (UBL 2.1 / DIAN)** al formato **FPBATCH.TXT**, requerido por el ERP **SIESA UNO 8.5C** para cargar compras de servicios.  
El sistema incluye parseo, normalización, validación y generación del archivo plano de 512 bytes por registro.

---

## 🚀 Funcionalidades principales

- Procesa **XML individuales** o **ZIP con múltiples facturas**.  
- Lee facturas estándar electrónicas colombianas (UBL 2.1).  
- Extrae automáticamente:
  - Datos del proveedor y adquiriente  
  - Totales e impuestos  
  - Identificadores (numero, CUFE, fechas)  
  - Detalles de servicios  
- Genera los 3 tipos de registros FPBATCH:
  - **01** → Encabezado  
  - **02** → Detalles adicionales  
  - **03** → Movimientos / servicios  
- Garantiza longitud exacta de **512 bytes** por registro.  
- Valida estructura, tipos de datos, fechas y padding.  
- Permite descargar el archivo FPBATCH listo para SIESA.  
- Usa parametrización desde Excel (empresa, cuentas, servicios, ciudades).

---

## 📦 Estructura general del FPBATCH generado

Cada factura produce exactamente **3 registros**:

| Tipo | Descripción | Longitud |
|------|-------------|-----------|
| 01 | Encabezado de la factura | 512 bytes |
| 02 | Detalles adicionales | 512 bytes |
| 03 | Registro del servicio o movimiento | 512 bytes |

Ejemplo de salida (`FPBATCH.txt`):  

01|...512 bytes...
02|...512 bytes...
03|...512 bytes...


---

## 🧩 Arquitectura del proyecto

- `app.py`  
  Interfaz Streamlit para cargar XML/ZIP y descargar FPBATCH.

- `converters/xml_parser.py`  
  Extrae y normaliza datos del XML UBL/DIAN.

- `converters/fpbatch_generator.py`  
  Construye el archivo FPBATCH línea por línea, aplicando padding, formatos y reglas.

- `converters/utils.py`  
  Utilidades generales (extracción ZIP, manejo de rutas, helpers).

- `parametrizacion_empresas.xlsx`  
  Parametrización completa utilizada por el generador:
  - empresas  
  - ciudades  
  - servicios  
  - cuentas  
  - configuración global  

- `test_fpbatch_format.py`  
  Script para validar automáticamente el FPBATCH generado (tamaño, estructura, secuencia 01-02-03).

- `examples/`  
  12 facturas electrónicas usadas para pruebas.

---

## 🧪 Resultados de Validación (Resumen Oficial)

El sistema fue evaluado con 12 XML reales.  
Resultado consolidado:

| Métrica | Valor |
|--------|-------|
| Facturas detectadas | **12** |
| Facturas parseadas correctamente | **12 (100%)** |
| Registros tipo 01 | 12 |
| Registros tipo 02 | 12 |
| Registros tipo 03 | 12 |
| Total registros en FPBATCH | **36** |
| Tamaño total del FPBATCH | **18,504 bytes** |
| Errores encontrados | **0** |
| Estado final | **FPBATCH 100% válido para SIESA** |


---

## 🛠 Instalación

Requerimientos:
- Python 3.8+
- Entorno virtual recomendado

Instalación:
```bash
python -m venv .venv
.\.venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

Ejecutar la aplicación Streamlit:

```bash
python -m streamlit run app.py
```

La interfaz permite:

- Subir XML sueltos o un ZIP con varios XML
- Ver cuántas facturas fueron parseadas
- Ver un preview del FPBATCH
- Descargar el archivo FPBATCH.txt final

👥 Autores

Brian Matasca
Juan Niño