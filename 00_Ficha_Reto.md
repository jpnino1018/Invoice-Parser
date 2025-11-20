# Nombre del reto
Conversor automático de facturas XML a archivo FPBATCH para SIESA UNO 8.5C

# Empresa aliada
Cualquier empresa que necesite transformar facturas electrónicas XML para cargarlas al sistema contable SIESA UNO 8.5C.

# Descripción del problema / necesidad de negocio
Las empresas deben cargar compras de servicios al ERP SIESA mediante un archivo plano rígido llamado **FPBATCH.TXT**, cuyo formato es complejo (512 bytes por registro, 3 tipos de registros por factura, padding, reglas de negocio estrictas).  
Actualmente este proceso suele hacerse manualmente o con macros poco confiables, generando errores que impiden la carga al ERP, retrasan la contabilidad y aumentan costos operativos.

El reto consiste en construir un sistema confiable que:
- Lea facturas XML (UBL 2.1).
- Extraiga y normalice la información relevante.
- Genere automáticamente un FPBATCH completamente válido.
- Permita validar antes de cargar a SIESA.

# Oportunidad de IA generativa
El problema principal es determinista y altamente estructurado, por lo cual **no requiere IA generativa para resolver la conversión XML→FPBATCH**.  
Sin embargo, la IA generativa se puede utilizar como apoyo para:
- Generar casos de prueba y validadores.
- Depurar patrones y expresiones regulares.
- Documentar variaciones de estructuras XML.

La oportunidad de IA existe más como **asistencia complementaria**, no como núcleo del algoritmo.

# Datos disponibles (tipo, volumen, acceso)
- Archivos XML de facturas electrónicas (formato UBL 2.1).
- Volumen inicial: 12 facturas de prueba.
- Acceso: provistos localmente por la empresa o cargados vía aplicación.

# Entregable esperado
- Prototipo funcional que:
  - Convierte XML individuales o ZIP en un archivo FPBATCH válido.
  - Permite descargar el resultado.
  - Incluye un validador automático del formato FPBATCH.
  - Incluye parametrización por archivo Excel.

# Nivel de madurez esperado (TRL)
**TRL 6 – Prototipo probado en entorno relevante.**  
El sistema funciona, genera FPBATCH válidos y está listo para integración con operaciones reales.

# Métricas de impacto
- **Tasa de éxito de validación FPBATCH:** 100% en pruebas.
- **Reducción de tiempo operativo:** de horas manuales → segundos automáticos.
- **Eliminación de errores humanos:** validación estricta 512 bytes/registro.
- **Escalabilidad:** procesamiento masivo vía ZIP.

# Responsables (empresa, docente, equipo de estudiantes)
- **Empresa:** entidad usuaria que desee cargar facturas en SIESA.
- **Equipo de estudiantes:** Brian Matasca, Juan Niño.
