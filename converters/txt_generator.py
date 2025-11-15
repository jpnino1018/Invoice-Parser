# converters/txt_generator.py

def generate_txt(invoice: dict) -> str:
    """
    Generador TXT legible (ejemplo). Lo puedes adaptar a la estructura FPBATCH.
    """
    lines = []
    lines.append(f"FACTURA|{invoice.get('numero') or ''}|{invoice.get('fecha') or ''}|{invoice.get('hora') or ''}")
    prov = invoice.get("proveedor", {})
    cli = invoice.get("cliente", {})
    lines.append(f"EMISOR|{prov.get('nit','')}|{prov.get('name','')}")
    lines.append(f"ADQUIRIENTE|{cli.get('nit','')}|{cli.get('name','')}")
    lines.append(f"TOTAL|{invoice.get('total') or ''}|{invoice.get('currency') or ''}")
    lines.append("ITEMS:")
    for it in invoice.get("items", []):
        # ejemplo: descripcion|cantidad|unidad|precio_unitario|total_linea
        lines.append("|".join([
            it.get("descripcion",""),
            it.get("cantidad",""),
            it.get("unidad",""),
            it.get("precio_unitario",""),
            it.get("total_linea","")
        ]))
    return "\n".join(lines)
