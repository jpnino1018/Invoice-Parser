# Informe Final  

Conversor XML → FPBATCH para Compras de Servicios (SIESA UNO 8.5C)

---

## 1. Introducción

El ERP SIESA UNO 8.5C exige que las compras de servicios se carguen mediante un archivo plano FPBATCH.TXT, con una estructura rígida de 512 bytes por registro.  
La generación manual del archivo es compleja y genera errores frecuentes, lo que afecta directamente la contabilidad.

Este proyecto automatiza completamente la conversión de **XML → FPBATCH**.

---

## 2. Objetivo

Desarrollar una solución capaz de:

- Leer facturas electrónicas XML UBL 2.1.  
- Normalizar proveedor, cliente, ciudad, servicio e importes.  
- Generar registros FPBATCH tipo 01, 02 y 03 con padding exacto.  
- Validar el archivo final contra la especificación oficial.  
- Proveer una interfaz operativa fácil de usar.

---

## 3. Solución desarrollada

La solución implementa:

- **Parser XML** que extrae datos de la factura.  
- **Generador FPBATCH** que construye los registros byte a byte.  
- **Parametrización desde Excel** (empresas, servicios, ciudades, cuentas).  
- **Validador exhaustivo** del formato FPBATCH (512 bytes, tipos, fechas, estructura).  
- **Interfaz en Streamlit** para uso operativo (XML individual o ZIP masivo).

---

## 4. Resultados

### 4.1 Resumen general
- 12 XML procesados exitosamente.  
- 100% de facturas parseadas sin errores.  
- 36 registros FPBATCH generados (12×3).  
- Validación completa aprobada: **0 errores**.  
- Archivo FPBATCH final: totalmente compatible con SIESA UNO 8.5C.

### 4.2 Impacto
- Eliminación total del proceso manual.  
- Validación previa garantiza carga exitosa al ERP.  
- Reducción operativa significativa del tiempo: segundos en lugar de horas.  
- Escalabilidad inmediata para procesar cientos o miles de facturas.

---

## 5. Conclusión

La solución desarrollada:

- Es precisa, confiable y 100% válida frente al estándar FPBATCH.  
- Automiza un proceso crítico del área contable.  
- Está lista para adoptarse por cualquier empresa que trabaje con SIESA.  
- Permite futuras extensiones (API, multi-ítems, nuevos servicios, etc.).

En resumen, el proyecto cumple completamente los objetivos y supera las expectativas funcionales.

---

## 6. Participantes
- **Brian Matasca**  
- **Juan Niño**
