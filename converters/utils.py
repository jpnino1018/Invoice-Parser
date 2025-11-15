import zipfile
import io

def extract_files_from_zip(zip_file):
    z = zipfile.ZipFile(zip_file)
    xml_files = []
    for name in z.namelist():
        if name.endswith(".xml"):
            xml_files.append(io.BytesIO(z.read(name)))
    return xml_files
