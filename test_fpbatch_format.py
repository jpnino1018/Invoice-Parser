#!/usr/bin/env python3
"""
Test de validación de formato FPBATCH según especificación SIESA UNO 8.5C
Valida estructura, longitudes, tipos de datos y formato de cada campo
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple
from converters.xml_parser import parse_invoice_xml
from converters.fpbatch_generator import generate_fpbatch


class FPBATCHValidator:
    """
    Validador de formato FPBATCH según especificación técnica SIESA
    """
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
        # Especificación de campos por tipo de registro
        self.spec_01 = [
            ('NRO-REG', 1, 8, 'NUM', True),
            ('TIPO-REG', 9, 10, 'NUM', True),
            ('EMPRESA', 11, 12, 'ALFA', True),
            ('CO', 13, 15, 'ALFA', True),
            ('TIPO-DOCTO', 16, 17, 'ALFA', True),
            ('NRO-DOCTO', 18, 23, 'NUM', True),
            ('COD-TER', 24, 36, 'ALFA', True),
            ('SUC-TER', 37, 38, 'ALFA', True),
            ('FECHA-DOC', 39, 46, 'FECHA', True),
            ('PREFIJO-PROV', 47, 50, 'ALFA', False),
            ('NRO-PROV', 51, 62, 'ALFA', True),
            ('FECHA-DOC-PROV', 63, 70, 'FECHA', True),
            ('ESTADO', 71, 71, 'ALFA', True),
            ('NAT-CXP', 72, 72, 'ALFA', True),
            ('DETALLE', 73, 132, 'ALFA', False),
            ('MONEDA', 133, 134, 'ALFA', False),
            ('TASA-CONVER', 135, 146, 'MON', False),
            ('TASA-CAMBIO', 147, 158, 'MON', False),
            ('DCTO-ALT', 159, 166, 'ALFA', False),
            ('CUENTA-CXP', 167, 174, 'ALFA', False),
            ('FILLER', 175, 512, 'ALFA', False),
        ]
        
        self.spec_02 = [
            ('NRO-REG', 1, 8, 'NUM', True),
            ('TIPO-REG', 9, 10, 'NUM', True),
            ('EMPRESA', 11, 12, 'ALFA', True),
            ('CO', 13, 15, 'ALFA', True),
            ('TIPO-DOCTO', 16, 17, 'ALFA', True),
            ('NRO-DOCTO', 18, 23, 'NUM', True),
            ('DETALLE-1', 24, 83, 'ALFA', False),
            ('DETALLE-2', 84, 143, 'ALFA', False),
            ('DETALLE-3', 144, 203, 'ALFA', False),
            ('DETALLE-4', 204, 263, 'ALFA', False),
            ('DETALLE-5', 264, 323, 'ALFA', False),
            ('DETALLE-6', 324, 383, 'ALFA', False),
            ('DETALLE-7', 384, 443, 'ALFA', False),
            ('DETALLE-8', 444, 503, 'ALFA', False),
            ('FILLER', 504, 512, 'ALFA', False),
        ]
        
        self.spec_03 = [
            ('NRO-REG', 1, 8, 'NUM', True),
            ('TIPO-REG', 9, 10, 'NUM', True),
            ('EMPRESA', 11, 12, 'ALFA', True),
            ('CO', 13, 15, 'ALFA', True),
            ('TIPO-DOCTO', 16, 17, 'ALFA', True),
            ('NRO-DOCTO', 18, 23, 'NUM', True),
            ('SERVICIO', 24, 31, 'ALFA', True),
            ('CANTIDAD', 32, 44, 'CANT', True),  # 9.3 + S
            ('PRECIO-UNI', 45, 62, 'MON', False),  # 15.2 + S
            ('VALOR-BRUTO', 63, 80, 'MON', False),  # 15.2 + S
            ('TASA-DSCTO-1', 81, 85, 'TASA', False),  # 2.3
            ('TASA-DSCTO-2', 86, 90, 'TASA', False),  # 2.3
            ('COD-IMPUESTO', 91, 91, 'ALFA', False),
            ('VALOR-IVA', 92, 109, 'MON', False),  # 15.2 + S
            ('CO', 110, 112, 'ALFA', False),
            ('CCOSTO', 113, 120, 'ALFA', False),
            ('PROYECTO', 121, 130, 'ALFA', False),
            ('DETALLE', 131, 170, 'ALFA', False),
            ('TERCERO-COD', 171, 183, 'ALFA', False),
            ('TERCERO-SUC', 184, 185, 'ALFA', False),
            ('DESC-1', 186, 245, 'ALFA', False),
            ('DESC-2', 246, 305, 'ALFA', False),
            ('DESC-3', 306, 365, 'ALFA', False),
            ('DESC-4', 366, 425, 'ALFA', False),
            ('DESC-PROYEC', 426, 465, 'ALFA', False),
            ('FECINI-PROYEC', 466, 473, 'FECHA', False),
            ('FILLER', 474, 512, 'ALFA', False),
        ]
    
    def validate_line_length(self, line: str, line_num: int) -> bool:
        """Valida que la línea tenga exactamente 512 bytes"""
        if len(line) != 512:
            self.errors.append(
                f"Línea {line_num}: Longitud incorrecta. "
                f"Esperado: 512, Obtenido: {len(line)}"
            )
            return False
        return True
    
    def validate_numeric(self, value: str, field_name: str, line_num: int) -> bool:
        """Valida que el campo sea numérico (solo dígitos)"""
        if not value.strip():  # Permitir vacío en campos opcionales
            return True
        if not re.match(r'^\d+$', value.strip()):
            self.errors.append(
                f"Línea {line_num}, Campo {field_name}: "
                f"Debe ser numérico. Valor: '{value}'"
            )
            return False
        return True
    
    def validate_fecha(self, value: str, field_name: str, line_num: int) -> bool:
        """Valida formato de fecha AAAAMMDD"""
        if not value.strip():
            return True
        if not re.match(r'^\d{8}$', value):
            self.errors.append(
                f"Línea {line_num}, Campo {field_name}: "
                f"Formato incorrecto. Debe ser AAAAMMDD. Valor: '{value}'"
            )
            return False
        
        # Validar que sea una fecha válida
        year = int(value[:4])
        month = int(value[4:6])
        day = int(value[6:8])
        
        if not (1900 <= year <= 2100):
            self.warnings.append(
                f"Línea {line_num}, Campo {field_name}: "
                f"Año fuera de rango esperado: {year}"
            )
        if not (1 <= month <= 12):
            self.errors.append(
                f"Línea {line_num}, Campo {field_name}: "
                f"Mes inválido: {month}"
            )
            return False
        if not (1 <= day <= 31):
            self.errors.append(
                f"Línea {line_num}, Campo {field_name}: "
                f"Día inválido: {day}"
            )
            return False
        
        return True
    
    def validate_monetario(self, value: str, field_name: str, line_num: int) -> bool:
        """Valida formato monetario: 15.2 + S (000000000000000.00+/-)"""
        if not value.strip():
            return True
        
        # Debe terminar en + o -
        if not value.strip().endswith(('+', '-')):
            self.errors.append(
                f"Línea {line_num}, Campo {field_name}: "
                f"Debe terminar en + o -. Valor: '{value}'"
            )
            return False
        
        # Verificar que el resto sean dígitos
        num_part = value.strip()[:-1]
        if not re.match(r'^\d+$', num_part):
            self.errors.append(
                f"Línea {line_num}, Campo {field_name}: "
                f"Parte numérica debe ser solo dígitos. Valor: '{value}'"
            )
            return False
        
        return True
    
    def validate_cantidad(self, value: str, field_name: str, line_num: int) -> bool:
        """Valida formato cantidad: 9.3 + S (000000001.000+/-)"""
        if not value.strip():
            return True
        
        # Debe terminar en + o -
        if not value.strip().endswith(('+', '-')):
            self.errors.append(
                f"Línea {line_num}, Campo {field_name}: "
                f"Debe terminar en + o -. Valor: '{value}'"
            )
            return False
        
        # Verificar longitud (13 caracteres: 9 enteros + 3 decimales + signo)
        if len(value.strip()) != 13:
            self.errors.append(
                f"Línea {line_num}, Campo {field_name}: "
                f"Longitud incorrecta. Esperado: 13, Obtenido: {len(value.strip())}"
            )
            return False
        
        return True
    
    def validate_tasa(self, value: str, field_name: str, line_num: int) -> bool:
        """Valida formato tasa: 2.3 (00.000)"""
        if not value.strip():
            return True
        
        if not re.match(r'^\d{5}$', value.strip()):
            self.errors.append(
                f"Línea {line_num}, Campo {field_name}: "
                f"Formato incorrecto. Debe ser 5 dígitos. Valor: '{value}'"
            )
            return False
        
        return True
    
    def validate_field(self, line: str, spec: tuple, line_num: int) -> bool:
        """Valida un campo individual según su especificación"""
        field_name, start, end, tipo, obligatorio = spec
        value = line[start-1:end]
        
        # Si es obligatorio y está vacío
        if obligatorio and not value.strip():
            self.errors.append(
                f"Línea {line_num}, Campo {field_name}: "
                f"Campo obligatorio vacío"
            )
            return False
        
        # Validar según tipo
        if tipo == 'NUM':
            return self.validate_numeric(value, field_name, line_num)
        elif tipo == 'FECHA':
            return self.validate_fecha(value, field_name, line_num)
        elif tipo == 'MON':
            return self.validate_monetario(value, field_name, line_num)
        elif tipo == 'CANT':
            return self.validate_cantidad(value, field_name, line_num)
        elif tipo == 'TASA':
            return self.validate_tasa(value, field_name, line_num)
        elif tipo == 'ALFA':
            return True  # Alfanumérico acepta cualquier cosa
        
        return True
    
    def validate_registro_01(self, line: str, line_num: int) -> bool:
        """Valida un registro tipo 01"""
        valid = True
        
        # Validar longitud total
        if not self.validate_line_length(line, line_num):
            return False
        
        # Validar tipo de registro
        tipo_reg = line[8:10]
        if tipo_reg != '01':
            self.errors.append(
                f"Línea {line_num}: Tipo de registro incorrecto. "
                f"Esperado: '01', Obtenido: '{tipo_reg}'"
            )
            return False
        
        # Validar cada campo
        for spec in self.spec_01:
            if not self.validate_field(line, spec, line_num):
                valid = False
        
        # Validaciones adicionales específicas
        estado = line[70:71]
        if estado not in ['1', 'X', ' ']:
            self.errors.append(
                f"Línea {line_num}, Campo ESTADO: "
                f"Valor inválido. Debe ser '1' (Facturado) o 'X' (Anulado). Valor: '{estado}'"
            )
            valid = False
        
        nat_cxp = line[71:72]
        if nat_cxp not in ['C', 'D', ' ']:
            self.errors.append(
                f"Línea {line_num}, Campo NAT-CXP: "
                f"Valor inválido. Debe ser 'C' (Factura) o 'D' (Nota Crédito). Valor: '{nat_cxp}'"
            )
            valid = False
        
        return valid
    
    def validate_registro_02(self, line: str, line_num: int) -> bool:
        """Valida un registro tipo 02"""
        valid = True
        
        if not self.validate_line_length(line, line_num):
            return False
        
        tipo_reg = line[8:10]
        if tipo_reg != '02':
            self.errors.append(
                f"Línea {line_num}: Tipo de registro incorrecto. "
                f"Esperado: '02', Obtenido: '{tipo_reg}'"
            )
            return False
        
        for spec in self.spec_02:
            if not self.validate_field(line, spec, line_num):
                valid = False
        
        return valid
    
    def validate_registro_03(self, line: str, line_num: int) -> bool:
        """Valida un registro tipo 03"""
        valid = True
        
        if not self.validate_line_length(line, line_num):
            return False
        
        tipo_reg = line[8:10]
        if tipo_reg != '03':
            self.errors.append(
                f"Línea {line_num}: Tipo de registro incorrecto. "
                f"Esperado: '03', Obtenido: '{tipo_reg}'"
            )
            return False
        
        for spec in self.spec_03:
            if not self.validate_field(line, spec, line_num):
                valid = False
        
        return valid
    
    def validate_fpbatch_structure(self, lines: List[str]) -> bool:
        """
        Valida la estructura general del FPBATCH:
        - Cada factura debe tener: 1 registro 01, 1 registro 02, 1 registro 03
        - Los consecutivos deben ser secuenciales
        """
        valid = True
        current_nro_reg = None
        expected_sequence = ['01', '02', '03']
        current_seq_index = 0
        
        for i, line in enumerate(lines, 1):
            if len(line) < 10:
                continue
            
            nro_reg = line[0:8]
            tipo_reg = line[8:10]
            
            # Verificar consecutivo
            if current_nro_reg is None:
                current_nro_reg = nro_reg
            
            if nro_reg != current_nro_reg:
                # Cambió el consecutivo, debe reiniciar secuencia
                if current_seq_index != 0:
                    self.errors.append(
                        f"Línea {i}: Secuencia incompleta para consecutivo {current_nro_reg}. "
                        f"Falta registro tipo {expected_sequence[current_seq_index]}"
                    )
                    valid = False
                current_nro_reg = nro_reg
                current_seq_index = 0
            
            # Verificar secuencia de tipos
            if tipo_reg != expected_sequence[current_seq_index]:
                self.errors.append(
                    f"Línea {i}: Secuencia incorrecta. "
                    f"Esperado: {expected_sequence[current_seq_index]}, Obtenido: {tipo_reg}"
                )
                valid = False
            
            current_seq_index += 1
            if current_seq_index >= len(expected_sequence):
                current_seq_index = 0
        
        return valid
    
    def validate_fpbatch(self, content: str) -> Tuple[bool, List[str], List[str]]:
        """
        Valida un archivo FPBATCH completo
        
        Returns:
            (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        lines = content.split('\r\n')
        
        # Eliminar líneas vacías
        lines = [l for l in lines if l.strip()]
        
        if not lines:
            self.errors.append("Archivo vacío")
            return False, self.errors, self.warnings
        
        # Validar estructura general
        self.validate_fpbatch_structure(lines)
        
        # Validar cada línea según su tipo
        for i, line in enumerate(lines, 1):
            if len(line) < 10:
                self.errors.append(f"Línea {i}: Línea demasiado corta")
                continue
            
            tipo_reg = line[8:10]
            
            if tipo_reg == '01':
                self.validate_registro_01(line, i)
            elif tipo_reg == '02':
                self.validate_registro_02(line, i)
            elif tipo_reg == '03':
                self.validate_registro_03(line, i)
            else:
                self.errors.append(
                    f"Línea {i}: Tipo de registro desconocido: '{tipo_reg}'"
                )
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings


def test_fpbatch_with_examples():
    """
    Test con los archivos XML de ejemplo
    """
    print("=" * 80)
    print("TEST DE VALIDACIÓN DE FORMATO FPBATCH")
    print("=" * 80)
    
    # Rutas de ejemplo
    examples_dir = Path("examples")
    xml_files = list(examples_dir.glob("*.xml"))
    
    if not xml_files:
        print("\n⚠️  No se encontraron archivos XML en la carpeta 'examples'")
        return
    
    print(f"\n📁 Encontrados {len(xml_files)} archivos XML para probar\n")
    
    # Parsear facturas
    facturas = []
    for xml_file in xml_files:
        try:
            with open(xml_file, 'rb') as f:
                xml_data = f.read()
            factura = parse_invoice_xml(xml_data)
            facturas.append(factura)
            print(f"✅ Parseado: {xml_file.name}")
        except Exception as e:
            print(f"❌ Error parseando {xml_file.name}: {e}")
    
    if not facturas:
        print("\n❌ No se pudieron parsear facturas")
        return
    
    print(f"\n✅ Total facturas parseadas: {len(facturas)}")
    
    # Generar FPBATCH
    print("\n🔄 Generando archivo FPBATCH...")
    try:
        fpbatch_content = generate_fpbatch(facturas)
        print(f"✅ FPBATCH generado: {len(fpbatch_content)} bytes")
    except Exception as e:
        print(f"❌ Error generando FPBATCH: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Validar formato
    print("\n🔍 Validando formato FPBATCH...")
    validator = FPBATCHValidator()
    is_valid, errors, warnings = validator.validate_fpbatch(fpbatch_content)
    
    # Mostrar resultados
    print("\n" + "=" * 80)
    print("RESULTADOS DE VALIDACIÓN")
    print("=" * 80)
    
    if is_valid:
        print("\n✅ ¡FORMATO FPBATCH VÁLIDO!")
    else:
        print("\n❌ FORMATO FPBATCH INVÁLIDO")
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} Advertencias:")
        for warning in warnings[:10]:  # Mostrar primeras 10
            print(f"  • {warning}")
        if len(warnings) > 10:
            print(f"  ... y {len(warnings) - 10} advertencias más")
    
    if errors:
        print(f"\n❌ {len(errors)} Errores encontrados:")
        for error in errors[:20]:  # Mostrar primeros 20
            print(f"  • {error}")
        if len(errors) > 20:
            print(f"  ... y {len(errors) - 20} errores más")
    
    # Estadísticas
    lines = fpbatch_content.split('\r\n')
    lines = [l for l in lines if l.strip()]
    
    reg_01 = sum(1 for l in lines if len(l) >= 10 and l[8:10] == '01')
    reg_02 = sum(1 for l in lines if len(l) >= 10 and l[8:10] == '02')
    reg_03 = sum(1 for l in lines if len(l) >= 10 and l[8:10] == '03')
    
    print("\n" + "=" * 80)
    print("ESTADÍSTICAS")
    print("=" * 80)
    print(f"Total líneas: {len(lines)}")
    print(f"Registros tipo 01 (Encabezados): {reg_01}")
    print(f"Registros tipo 02 (Detalles): {reg_02}")
    print(f"Registros tipo 03 (Movimientos): {reg_03}")
    print(f"Total facturas: {reg_01}")
    
    # Guardar resultado para inspección
    output_file = Path("FPBATCH_TEST.txt")
    with open(output_file, 'w', encoding='latin-1') as f:
        f.write(fpbatch_content)
    print(f"\n💾 Archivo guardado: {output_file}")
    
    # Vista previa
    print("\n" + "=" * 80)
    print("VISTA PREVIA (primeras 5 líneas)")
    print("=" * 80)
    for i, line in enumerate(lines[:5], 1):
        print(f"Línea {i} (Tipo {line[8:10]}): {line[:80]}...")
    
    return is_valid, errors, warnings


if __name__ == "__main__":
    test_fpbatch_with_examples()