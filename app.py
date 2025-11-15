import streamlit as st
from converters.xml_parser import parse_invoice_xml
from converters.fpbatch_generator import generate_fpbatch
from converters.utils import extract_files_from_zip
from pathlib import Path

st.title("Conversor XML → FPBATCH para Facturas Electrónicas")

st.markdown("""
**Sistema de conversión de facturas electrónicas XML a formato FPBATCH (SIESA UNO 8.5C)**

El formato FPBATCH genera:
- **Registro 01**: Encabezado de factura
- **Registro 02**: Detalles adicionales
- **Registro 03**: Movimientos/servicios
""")

# Ubicación del Excel de parametrización
excel_path = Path(__file__).parent / "parametrizacion_empresas.xlsx"
excel_exists = excel_path.exists()

if excel_exists:
    st.info(f"✅ Parametrizaciones cargadas desde: {excel_path.name}")
else:
    st.warning("⚠️ No se encontró parametrizacion_empresas.xlsx. Usando valores por defecto.")

uploaded_file = st.file_uploader("Sube un archivo XML o ZIP", type=["xml", "zip"])

if uploaded_file:
    st.success("Archivo cargado correctamente.")

    if st.button("Procesar archivo", type="primary"):
        with st.spinner("Procesando facturas..."):
            # Extraer archivos XML
            if uploaded_file.name.endswith(".zip"):
                xml_files = extract_files_from_zip(uploaded_file)
                st.info(f"📦 {len(xml_files)} archivos XML encontrados en el ZIP")
            else:
                xml_files = [uploaded_file]
            
            # Parsear todas las facturas
            facturas_parseadas = []
            errores = []
            
            for idx, file in enumerate(xml_files, 1):
                try:
                    xml_data = file.read()
                    factura = parse_invoice_xml(xml_data)
                    facturas_parseadas.append(factura)
                except Exception as e:
                    filename = getattr(file, 'name', f'archivo_{idx}')
                    errores.append(f"❌ Error en {filename}: {str(e)}")
            
            # Mostrar resultados del parseo
            if facturas_parseadas:
                st.success(f"✅ {len(facturas_parseadas)} facturas procesadas correctamente")
            
            if errores:
                st.error("❌ Errores encontrados:")
                for error in errores:
                    st.write(error)
            
            # Generar FPBATCH si hay facturas válidas
            if facturas_parseadas:
                try:
                    # Generar el contenido FPBATCH
                    fpbatch_content = generate_fpbatch(
                        facturas_parseadas,
                        str(excel_path) if excel_exists else None
                    )
                    
                    st.success("✅ Archivo FPBATCH generado correctamente")
                    
                    # Mostrar preview
                    with st.expander("🔍 Vista previa del archivo FPBATCH"):
                        preview_lines = fpbatch_content.split('\r\n')[:10]
                        st.code('\n'.join(preview_lines), language='text')
                        if len(preview_lines) < fpbatch_content.count('\r\n'):
                            st.write(f"... (+{fpbatch_content.count(chr(10)) - 10} líneas más)")
                    
                    # Estadísticas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Facturas", len(facturas_parseadas))
                    with col2:
                        st.metric("Registros", len(facturas_parseadas) * 3)
                    with col3:
                        st.metric("Tamaño", f"{len(fpbatch_content):,} bytes")
                    
                    # Botón de descarga
                    st.download_button(
                        label="📥 Descargar FPBATCH.txt",
                        data=fpbatch_content.encode('latin-1'),
                        file_name="FPBATCH.txt",
                        mime="text/plain",
                        type="primary"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Error al generar FPBATCH: {str(e)}")
                    import traceback
                    with st.expander("Ver detalles del error"):
                        st.code(traceback.format_exc())

# Sidebar con información
with st.sidebar:
    st.header("ℹ️ Información")
    st.markdown("""
    ### Formato FPBATCH
    
    **Estructura por factura:**
    - 1 registro tipo 01 (encabezado)
    - 1 registro tipo 02 (detalles)
    - 1 registro tipo 03 (servicios)
    
    **Cada registro:** 512 bytes
    
    ### 📄 Parametrización desde Excel
    
    El sistema lee TODO desde:
    `parametrizacion_empresas.xlsx`
    
    **5 hojas requeridas:**
    - empresas
    - ciudades
    - servicios
    - cuentas
    - config
    """)