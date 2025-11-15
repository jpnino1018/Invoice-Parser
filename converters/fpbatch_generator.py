# converters/fpbatch_generator.py
"""
Generador de archivos FPBATCH para SIESA UNO 8.5C
TODO parametrizado desde Excel (sin valores quemados)
"""

import re
import unicodedata
from pathlib import Path
from typing import List, Tuple
import pandas as pd


class FPBATCHGenerator:
    
    def __init__(self, excel_path: str = None):
        if excel_path is None:
            excel_path = Path(__file__).parent.parent / "parametrizacion_empresas.xlsx"
        
        self.empresas = None
        self.ciudades = None
        self.servicios = None
        self.cuentas = None
        self.config = None
        
        self._load_excel(excel_path)
        
        # Índice por NIT
        self.empresas_by_nit = {}
        if self.empresas is not None:
            for _, row in self.empresas.iterrows():
                nit = str(row.get('NIT', '')).strip()
                if nit:
                    self.empresas_by_nit[nit] = row
        
        # Config general
        self.cfg = {}
        if self.config is not None:
            for _, row in self.config.iterrows():
                param = str(row.get('PARAMETRO', '')).strip()
                valor = str(row.get('VALOR', '')).strip()
                if param:
                    self.cfg[param] = valor
        
        self.TIPO_DOCTO = self.cfg.get('TIPO_DOCUMENTO', 'PA')
        self.NATURALEZA = self.cfg.get('NAT_CXP', 'C')
        self.COD_SERVICIO_DEFAULT = self.cfg.get('CODIGO_SERVICIO_DEFAULT', '001')
    
    def _load_excel(self, excel_path: str):
        try:
            xls = pd.ExcelFile(excel_path)
            if 'empresas' in xls.sheet_names:
                self.empresas = pd.read_excel(xls, 'empresas')
            if 'ciudades' in xls.sheet_names:
                self.ciudades = pd.read_excel(xls, 'ciudades')
            if 'servicios' in xls.sheet_names:
                self.servicios = pd.read_excel(xls, 'servicios')
            if 'cuentas' in xls.sheet_names:
                self.cuentas = pd.read_excel(xls, 'cuentas')
            if 'config' in xls.sheet_names:
                self.config = pd.read_excel(xls, 'config')
            print(f"✅ Parametrizaciones cargadas: {excel_path}")
        except:
            self._load_defaults()
    
    def _load_defaults(self):
        self.empresas = pd.DataFrame({'NIT': ['805007280'], 'RAZON_SOCIAL_REGEX': ['aladdin.*casino'], 'SIGLA_EMPRESA': ['AH']})
        self.ciudades = pd.DataFrame({'SIGLA_EMPRESA': ['AH'], 'CIUDAD_NORMALIZADA': ['CALI'], 'CENTRO_OPERACION': ['001']})
        self.servicios = pd.DataFrame({'REGEX': [r'\b(arriendo|canon)\b'], 'CODIGO_SERVICIO': ['001'], 'DESCRIPCION': ['ARRENDAMIENTOS']})
        self.cuentas = pd.DataFrame({'SIGLA_EMPRESA': ['AH'], 'CUENTA_CXP': ['00000000']})
        self.config = pd.DataFrame({'PARAMETRO': ['TIPO_DOCUMENTO', 'NAT_CXP', 'CODIGO_SERVICIO_DEFAULT'], 'VALOR': ['PA', 'C', '001']})
    
    def fmt(self, value, length: int, tipo: str) -> str:
        s = str(value or '')
        if tipo == 'NUM':
            s = s.zfill(length)
        elif tipo == 'ALFA':
            s = s.ljust(length, ' ')
        elif tipo == 'MON':
            num = float(value) if value else 0.0
            sign = '-' if num < 0 else '+'
            parts = f"{abs(num):.2f}".split('.')
            s = parts[0].zfill(length - 3) + parts[1].ljust(2, '0') + sign
        return s[:length]
    
    def yyyymmdd(self, fecha: str) -> str:
        if not fecha:
            return '0' * 8
        return fecha.replace('-', '').zfill(8)[:8]
    
    def fmt_q(self, value) -> str:
        num = float(value) if value else 0.0
        sign = '-' if num < 0 else '+'
        parts = f"{abs(num):.3f}".split('.')
        return parts[0].zfill(9) + parts[1].ljust(3, '0') + sign
    
    def fmt_m(self, value) -> str:
        num = float(value) if value else 0.0
        sign = '-' if num < 0 else '+'
        parts = f"{abs(num):.2f}".split('.')
        return parts[0].zfill(15) + parts[1].ljust(2, '0') + sign
    
    def fmt_tasa(self, value) -> str:
        try:
            num = float(value or 0.0)
        except:
            num = 0.0

        sign = '+' if num >= 0 else '-'
        total = abs(num)

        enteros = int(total)
        decimales = int(round((total - enteros) * 100))

        # Ajuste por redondeo
        if decimales >= 100:
            enteros += 1
            decimales = 0

        # 9 enteros + 2 decimales + 1 signo = 12
        return f"{enteros:09d}{decimales:02d}{sign}"

    def normalize(self, s: str) -> str:
        if not s:
            return ''
        s = unicodedata.normalize('NFD', str(s))
        s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
        return s.strip().lower()
    
    def digits(self, s: str) -> str:
        return re.sub(r'\D+', '', str(s or ''))
    
    def normalize_city(self, city_raw: str) -> str:
        if not city_raw:
            return ''
        c = unicodedata.normalize('NFD', str(city_raw))
        c = ''.join(ch for ch in c if unicodedata.category(ch) != 'Mn')
        c = re.sub(r'\s+', ' ', c)
        c = re.sub(r'[–—]', '-', c)
        c = re.sub(r'\s*-\s*', '-', c)
        return c.strip().upper()
    
    def detect_empresa(self, nit_receptor: str, razon_social_receptor: str) -> str:
        nit_clean = self.digits(nit_receptor)
        if nit_clean in self.empresas_by_nit:
            return str(self.empresas_by_nit[nit_clean].get('SIGLA_EMPRESA', 'XX'))
        
        if self.empresas is not None:
            for _, row in self.empresas.iterrows():
                regex = str(row.get('RAZON_SOCIAL_REGEX', ''))
                sigla = str(row.get('SIGLA_EMPRESA', ''))
                if regex and sigla:
                    try:
                        if re.search(regex, razon_social_receptor or '', re.IGNORECASE):
                            return sigla
                    except:
                        pass
        
        stop_words = {'&', 'S.A.S.', 'SAS', 'LTDA', 'S.', 'A.', 'Ltda', 'Ltda.', 'Y'}
        palabras = re.sub(r'[.,]', '', razon_social_receptor or '').split()
        palabras = [p for p in palabras if p and p.upper() not in stop_words]
        inicial1 = palabras[0][0] if len(palabras) > 0 else 'X'
        inicial2 = palabras[1][0] if len(palabras) > 1 else 'X'
        return (inicial1 + inicial2).upper()
    
    def detect_co(self, sigla_empresa: str, ciudad: str) -> str:
        if not sigla_empresa or not ciudad or self.ciudades is None:
            return '001'
        for _, row in self.ciudades.iterrows():
            if (str(row.get('SIGLA_EMPRESA', '')).strip() == sigla_empresa and
                str(row.get('CIUDAD_NORMALIZADA', '')).strip().upper() == ciudad):
                return str(row.get('CENTRO_OPERACION', '001'))
        return '001'
    
    def detect_service(self, descripcion: str) -> Tuple[str, str]:
        if self.servicios is None:
            return (self.COD_SERVICIO_DEFAULT, 'NO CLASIFICADO')
        desc_norm = self.normalize(descripcion)
        for _, row in self.servicios.iterrows():
            regex = str(row.get('REGEX', ''))
            codigo = str(row.get('CODIGO_SERVICIO', ''))
            concepto = str(row.get('DESCRIPCION', ''))
            if regex and codigo:
                try:
                    if re.search(regex, desc_norm, re.IGNORECASE):
                        return (codigo, concepto)
                except:
                    pass
        return (self.COD_SERVICIO_DEFAULT, 'NO CLASIFICADO')
    
    def get_cuenta_cxp(self, sigla_empresa: str) -> str:
        if self.cuentas is None:
            return '00000000'
        for _, row in self.cuentas.iterrows():
            if str(row.get('SIGLA_EMPRESA', '')).strip() == sigla_empresa:
                return str(row.get('CUENTA_CXP', '00000000'))
        return '00000000'
    
    
    
    def build_reg_01(self, factura: dict, nro_reg: str) -> str:
        empresa = self.detect_empresa(factura.get('proveedor', {}).get('nit', ''), factura.get('cliente', {}).get('name', ''))
        ciudad = self.normalize_city(factura.get('ciudad', ''))
        co = self.detect_co(empresa, ciudad)
        cuenta_cxp = self.get_cuenta_cxp(empresa)
        
        numero_factura = factura.get('numero', '')
        prefijo_prov = re.sub(r'[0-9]', '', numero_factura)[:4].ljust(4, ' ')
        nro_prov = re.sub(r'[A-Za-z]', '', numero_factura).ljust(12, ' ')
        nro_docto_num = self.digits(numero_factura)[-6:].zfill(6)
        
        nit_emisor = factura.get('proveedor', {}).get('nit', '')
        fecha_doc = self.yyyymmdd(factura.get('fecha', ''))
        items = factura.get('items', [])
        detalle = items[0].get('descripcion', '') if items else ''
        
        rec = nro_reg
        rec += self.fmt('01', 2, 'NUM')
        rec += self.fmt(empresa, 2, 'ALFA')
        rec += self.fmt(co, 3, 'ALFA')
        rec += self.fmt(self.TIPO_DOCTO, 2, 'ALFA')
        rec += self.fmt(nro_docto_num, 6, 'NUM')
        rec += self.fmt(nit_emisor, 13, 'ALFA')
        rec += self.fmt('00', 2, 'ALFA')
        rec += fecha_doc
        rec += prefijo_prov
        rec += nro_prov
        rec += fecha_doc
        rec += self.fmt('1', 1, 'ALFA')
        rec += self.fmt(self.NATURALEZA, 1, 'ALFA')
        rec += self.fmt(detalle, 60, 'ALFA')
        rec += self.fmt('', 2, 'ALFA')
        tasa_conver = float(factura.get('tasa_conver', 1))
        tasa_cambio = float(factura.get('tasa_cambio', 1))
        rec += self.fmt_tasa(tasa_conver)
        rec += self.fmt_tasa(tasa_cambio)
        rec += self.fmt('', 8, 'ALFA')
        rec += self.fmt(cuenta_cxp, 8, 'ALFA')
        rec += ' ' * 338
        return rec[:512].ljust(512, ' ')
    
    def build_reg_02(self, factura: dict, nro_reg: str) -> str:
        empresa = self.detect_empresa(factura.get('proveedor', {}).get('nit', ''), factura.get('cliente', {}).get('name', ''))
        ciudad = self.normalize_city(factura.get('ciudad', ''))
        co = self.detect_co(empresa, ciudad)
        numero_factura = factura.get('numero', '')
        nro_docto_num = self.digits(numero_factura)[-6:].zfill(6)
        
        rec = nro_reg
        rec += self.fmt('02', 2, 'NUM')
        rec += self.fmt(empresa, 2, 'ALFA')
        rec += self.fmt(co, 3, 'ALFA')
        rec += self.fmt(self.TIPO_DOCTO, 2, 'ALFA')
        rec += self.fmt(nro_docto_num, 6, 'NUM')
        for i in range(8):
            rec += ' ' * 60
        rec += ' ' * 9
        return rec[:512].ljust(512, ' ')
    
    def build_reg_03(self, factura: dict, nro_reg: str) -> str:
        empresa = self.detect_empresa(factura.get('proveedor', {}).get('nit', ''), factura.get('cliente', {}).get('name', ''))
        ciudad = self.normalize_city(factura.get('ciudad', ''))
        co = self.detect_co(empresa, ciudad)
        numero_factura = factura.get('numero', '')
        nro_docto_num = self.digits(numero_factura)[-6:].zfill(6)
        
        items = factura.get('items', [])
        descripcion_servicio = items[0].get('descripcion', '') if items else ''
        servicio_code, _ = self.detect_service(descripcion_servicio)
        
        total = float(factura.get('total', 0) or 0)
        iva = float(factura.get('iva', 0) or 0)
        valor_sin_iva = total - iva
        
        nit_emisor = factura.get('proveedor', {}).get('nit', '')
        
        rec = nro_reg
        rec += self.fmt('03', 2, 'NUM')
        rec += self.fmt(empresa, 2, 'ALFA')
        rec += self.fmt(co, 3, 'ALFA')
        rec += self.fmt(self.TIPO_DOCTO, 2, 'ALFA')
        rec += self.fmt(nro_docto_num, 6, 'NUM')
        rec += self.fmt(servicio_code, 8, 'ALFA')
        rec += self.fmt_q(1)
        rec += self.fmt_m(valor_sin_iva)
        rec += self.fmt_m(valor_sin_iva)
        rec += '00000'
        rec += '00000'
        rec += ' '
        rec += self.fmt_m(iva)
        rec += self.fmt(co, 3, 'ALFA')
        rec += '1001    '
        rec += '0000000000'
        rec += ' ' * 40
        rec += self.fmt(nit_emisor, 13, 'ALFA')
        rec += self.fmt('00', 2, 'ALFA')
        rec += ' ' * 60
        rec += ' ' * 60
        rec += ' ' * 60
        rec += ' ' * 60
        rec += ' ' * 40
        rec += ' ' * 8
        rec += ' ' * 39
        return rec[:512].ljust(512, ' ')
    
    def generate_fpbatch(self, facturas: List[dict]) -> str:
        lines = []
        for i, factura in enumerate(facturas, start=1):
            nro_reg = str(i).zfill(8)
            lines.append(self.build_reg_01(factura, nro_reg))
            lines.append(self.build_reg_02(factura, nro_reg))
            lines.append(self.build_reg_03(factura, nro_reg))
        return '\r\n'.join(lines) + '\r\n'


def generate_fpbatch(facturas: List[dict], excel_path: str = None) -> str:
    generator = FPBATCHGenerator(excel_path)
    return generator.generate_fpbatch(facturas)