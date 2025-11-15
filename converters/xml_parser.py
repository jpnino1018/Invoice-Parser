# converters/xml_parser.py
import logging
import xmltodict
from collections import defaultdict

logger = logging.getLogger(__name__)

def _strip_ns(key: str) -> str:
    """Remueve prefijos de namespace y nombres entre llaves."""
    if key is None:
        return ""
    # quitar {urn:...}Invoice -> Invoice
    if "}" in key:
        return key.split("}")[-1]
    # quitar prefijos fe:Invoice -> Invoice
    if ":" in key:
        return key.split(":")[-1]
    return key

def _find_key(obj, candidates):
    """Busca en dict obj una key que al quitar namespace coincida con alguna candidate (case-insensitive)."""
    if not isinstance(obj, dict):
        return None
    lower_cands = {c.lower(): c for c in candidates}
    for k in obj.keys():
        kk = _strip_ns(k).lower()
        if kk in lower_cands:
            return obj[k]
    return None

def _ensure_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def parse_invoice_xml(raw_xml: bytes | str) -> dict:
    """
    Parse a UBL/DIAN invoice XML into a normalized python dict.
    Returns keys: numero, fecha, proveedor (name, nit), cliente (name, nit), total, currency, items (list)
    Each item: descripcion, cantidad, unidad, precio_unitario, total_linea
    """
    # primero parsear el XML principal
    doc = xmltodict.parse(raw_xml, force_list=None)

    # Algunos archivos (AttachedDocument) contienen el XML de la factura dentro de un
    # nodo CDATA/text (por ejemplo en cac:Attachment/cbc:Description). xmltodict deja
    # ese contenido como una string; buscamos strings que contengan XML (<?xml o <Invoice)
    # y las parseamos para que queden como dicts y puedan ser encontradas por la búsqueda.
    def _parse_possible_xml_string(s):
        if not isinstance(s, str):
            return s
        # heurística sencilla: si contiene una declaración XML o una etiqueta Invoice
        if ('<?xml' in s) or ('<Invoice' in s) or ('<AttachedDocument' in s) or ('<ApplicationResponse' in s):
            try:
                parsed = xmltodict.parse(s, force_list=None)
                logger.debug("Parsed embedded XML string into dict")
                return parsed
            except Exception:
                # no pudo parsear: dejar string y seguir
                logger.debug("Found embedded XML-like string but failed to parse it; leaving as text")
                return s
        return s

    def _walk_and_parse_embedded(obj):
        # recorre dicts/ listas y parsea strings que contienen XML
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                if isinstance(v, str):
                    newv = _parse_possible_xml_string(v)
                    obj[k] = newv
                else:
                    _walk_and_parse_embedded(v)
        elif isinstance(obj, list):
            for i, item in enumerate(list(obj)):
                if isinstance(item, str):
                    newv = _parse_possible_xml_string(item)
                    obj[i] = newv
                else:
                    _walk_and_parse_embedded(item)

    _walk_and_parse_embedded(doc)

    # buscar nodo invoice en cualquier nivel (Invoice o AttachedDocument->Description->Invoice)
    invoice = None
    # primer nivel (root)
    for k, v in doc.items():
        if _strip_ns(k).lower().endswith("invoice"):
            invoice = v
            break

    # si el root es AttachedDocument que contiene el Invoice en CDATA (caso que viste antes)
    if invoice is None:
        # buscar recursivamente por 'Invoice' clave
        def recursive_search(obj):
            if isinstance(obj, dict):
                for kk, vv in obj.items():
                    if _strip_ns(kk).lower().endswith("invoice"):
                        return vv
                    res = recursive_search(vv)
                    if res is not None:
                        return res
            elif isinstance(obj, list):
                for item in obj:
                    res = recursive_search(item)
                    if res is not None:
                        return res
            return None
        invoice = recursive_search(doc)

    if invoice is None:
        raise ValueError("No se encontró la etiqueta Invoice en el XML.")

    # helper to get nested safely (variantes con cbc/@ y con texto interno '#text')
    def get_text(node, path):
        # path: list of candidate keys for the same level (may be namespace prefixed)
        # Returns a primitive value when possible, or a dict if no primitive found.
        def _extract_value(cur):
            if isinstance(cur, dict):
                if "#text" in cur:
                    return cur.get("#text")
                # prefer attribute values like @currencyID
                for k in cur.keys():
                    if k.startswith("@"):
                        return cur.get(k)
                # prefer first primitive child
                for k, v in cur.items():
                    if isinstance(v, (str, int, float)):
                        return v
                return cur
            return cur

        if node is None:
            return None
        if not isinstance(path, (list, tuple)):
            path = [path]

        if not isinstance(node, dict):
            return _extract_value(node)

        # try each candidate at this same level and return the first match
        for p in path:
            # direct key match
            if isinstance(node, dict) and p in node:
                return _extract_value(node[p])
            # match by stripped name
            for k in node.keys():
                if _strip_ns(k).lower() == p.lower():
                    return _extract_value(node[k])

        return None

    # Numero y UUID
    numero = get_text(invoice, ["ID"]) or get_text(invoice, ["cbc:ID"]) or invoice.get("ID", None)
    uuid = get_text(invoice, ["UUID"]) or None

    # Fecha/hora
    issue_date = get_text(invoice, ["IssueDate"]) or get_text(invoice, ["cbc:IssueDate"])
    issue_time = get_text(invoice, ["IssueTime"]) or None

    # Supplier (AccountingSupplierParty)
    supplier_block = _find_key(invoice, ["AccountingSupplierParty", "SupplierParty", "AccountingSupplier"])
    supplier_name = None
    supplier_nit = None
    if supplier_block is not None:
        # navegar a Party -> PartyName/PartyTaxScheme
        party = _find_key(supplier_block, ["Party", "cac:Party", "AccountingSupplierParty"])
        if party is None:
            party = supplier_block
        # name
        supplier_name = get_text(party, ["PartyName", "cbc:PartyName", "cac:PartyName", "Party"])
        if isinstance(supplier_name, dict):
            supplier_name = get_text(supplier_name, ["Name"])
        # NIT en PartyTaxScheme -> CompanyID
        pts = _find_key(party, ["PartyTaxScheme", "cac:PartyTaxScheme"])
        if pts:
            supplier_nit = get_text(pts, ["CompanyID", "cbc:CompanyID", "CompanyID"])

    # Customer (AccountingCustomerParty)
    customer_block = _find_key(invoice, ["AccountingCustomerParty", "CustomerParty", "AccountingCustomer"])
    customer_name = None
    customer_nit = None
    if customer_block is not None:
        party = _find_key(customer_block, ["Party", "cac:Party"])
        if party is None:
            party = customer_block
        customer_name = get_text(party, ["PartyName", "cbc:PartyName"])
        if isinstance(customer_name, dict):
            customer_name = get_text(customer_name, ["Name"])
        pts = _find_key(party, ["PartyTaxScheme", "cac:PartyTaxScheme"])
        if pts:
            customer_nit = get_text(pts, ["CompanyID", "cbc:CompanyID", "CompanyID"])

    # Totales
    legal_total = _find_key(invoice, ["LegalMonetaryTotal", "cac:LegalMonetaryTotal"])
    payable = None
    currency = None
    if legal_total:
        # buscar PayableAmount
        if isinstance(legal_total, dict):
            for k,v in legal_total.items():
                if _strip_ns(k).lower() == "payableamount":
                    if isinstance(v, dict):
                        payable = v.get("#text") or next(iter(v.values()), None)
                        currency = v.get("@currencyID") or None
                    else:
                        payable = v
                    break

    # Items - InvoiceLine
    invoice_lines = _find_key(invoice, ["InvoiceLine", "cac:InvoiceLine", "cac:InvoiceLine"])
    invoice_lines = _ensure_list(invoice_lines)
    parsed_items = []
    for li in invoice_lines:
        descripcion = get_text(li, ["Item", "cbc:Item", "cac:Item"])
        if isinstance(descripcion, dict):
            descripcion = get_text(descripcion, ["Description", "cbc:Description"]) or descripcion.get("Description")
        cantidad = get_text(li, ["InvoicedQuantity", "cbc:InvoicedQuantity"])
        unidad = None
        if isinstance(cantidad, dict):
            unidad = cantidad.get("@unitCode") or cantidad.get("unitCode")
            cantidad = cantidad.get("#text") or next(iter(cantidad.values()), None)
        precio = get_text(li, ["Price", "cbc:Price", "cac:Price"])
        precio_val = None
        if isinstance(precio, dict):
            # PriceAmount
            for k,v in precio.items():
                if _strip_ns(k).lower().endswith("priceamount"):
                    precio_val = v.get("#text") if isinstance(v, dict) else v
                    break
        # Line total
        line_total = get_text(li, ["LineExtensionAmount", "cbc:LineExtensionAmount"])
        parsed_items.append({
            "descripcion": (descripcion or "").strip(),
            "cantidad": (cantidad or "").strip() if cantidad else "",
            "unidad": unidad or "",
            "precio_unitario": (precio_val or "").strip() if precio_val else "",
            "total_linea": (line_total or "").strip() if line_total else ""
        })

    return {
        "numero": str(numero) if numero else None,
        "uuid": str(uuid) if uuid else None,
        "fecha": issue_date,
        "hora": issue_time,
        "proveedor": {"name": (supplier_name or "").strip(), "nit": (supplier_nit or "").strip()},
        "cliente": {"name": (customer_name or "").strip(), "nit": (customer_nit or "").strip()},
        "total": (payable or "").strip() if payable else None,
        "currency": (currency or "").strip() if currency else None,
        "items": parsed_items
    }
