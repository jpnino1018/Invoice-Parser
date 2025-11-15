from converters.xml_parser import parse_invoice_xml
import json

paths = [
    r"examples\ad0900923112000250000067396.xml",
    r"examples\c1128a739aae8f596302961627a3aa0a995fba6a92d971318d3054ed6c2d8f64be1562622f2a9fe403062c1cbca76137.xml"
]

for p in paths:
    print('\n---', p)
    with open(p, 'rb') as f:
        data = f.read()
    try:
        inv = parse_invoice_xml(data)
        summary = {
            'numero': inv.get('numero'),
            'uuid': inv.get('uuid'),
            'fecha': inv.get('fecha'),
            'total': inv.get('total'),
            'currency': inv.get('currency'),
            'items_count': len(inv.get('items', [])),
            'proveedor': inv.get('proveedor'),
            'cliente': inv.get('cliente')
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print('\nSample items (first 2):')
        for it in inv.get('items', [])[:2]:
            print(json.dumps(it, ensure_ascii=False))
    except Exception as e:
        print('ERROR:', e)
