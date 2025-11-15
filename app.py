import streamlit as st
from converters.xml_parser import parse_invoice_xml
from converters.txt_generator import generate_txt
from converters.utils import extract_files_from_zip
import io

st.title("Conversor XML → TXT para Facturas Electrónicas")

uploaded_file = st.file_uploader("Sube un archivo XML o ZIP", type=["xml", "zip"])

if uploaded_file:
    st.success("Archivo cargado correctamente.")

    if st.button("Procesar archivo"):
        if uploaded_file.name.endswith(".zip"):
            xml_files = extract_files_from_zip(uploaded_file)
        else:
            xml_files = [uploaded_file]

        txt_output = io.StringIO()

        for file in xml_files:
            xml_data = file.read()
            factura = parse_invoice_xml(xml_data)
            txt_output.write(generate_txt(factura))
            txt_output.write("\n")

        st.success("Archivo procesado correctamente.")

        st.download_button(
            label="Descargar TXT",
            data=txt_output.getvalue(),
            file_name="facturas.txt",
            mime="text/plain"
        )
