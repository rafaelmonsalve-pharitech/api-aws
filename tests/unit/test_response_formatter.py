"""
Unit Tests for Response Formatter Module

Tests para validar:
- Mapeo completo de campos SQL a JSON (17 campos)
- Conversión de estado A/I a ACTIVO/INACTIVO
- Cálculo de trabajoRepuesto basado en PRO_CO02
- Formateo de fechas a ISO 8601 con timezone -05:00
- Estructura de respuestas exitosas
- Estructura de respuestas de error

Requirements: 6.6-6.20, 7.1-7.23
"""

import json
from datetime import datetime

import pytest

from src.response_formatter import ResponseFormatter


class TestMapProductFields:
    """Tests para mapeo de campos SQL a JSON español"""
    
    def test_map_product_fields_complete(self):
        """
        Test: Todos los 17 campos requeridos deben estar presentes
        Validates: Requirements 7.3-7.17
        """
        row = {
            "EMP_CODI": "001",
            "PRO_CODI": "7SUBSM001A",
            "PRO_NOMB": "Producto de prueba",
            "TIP_CODI": "TIP001",
            "TIP_NOMB": "Tipo de producto",
            "PRO_ACTI": "A",
            "PRO_CO01": "7ABC",
            "SIS_NOMB": "ARKEO FLEET",
            "PRO_CO02": "SUBSM",
            "SUB_NOMB": "Subsistema Mantenimiento",
            "UNI_CODI": "UND",
            "UNI_NOMB": "Unidad",
            "AUD_FCRE": datetime(2024, 1, 15, 10, 30, 0),
            "AUD_UFAC": datetime(2024, 1, 20, 15, 45, 0)
        }
        
        result = ResponseFormatter.map_product_fields(row)
        
        # Verificar que están todos los 17 campos esperados
        expected_fields = {
            "codigoEmpresa", "codigoProducto", "nombreProducto",
            "codigoTipo", "nombreTipo", "estado",
            "codigoSistema", "nombreSistema",
            "codigoSubsistema", "nombreSubsistema",
            "codigoUnidad", "nombreUnidad",
            "trabajoRepuesto",
            "fechaCreacion", "fechaActualizacion"
        }
        
        assert set(result.keys()) == expected_fields
        assert len(result) == 15  # 15 campos únicos (17 contando fechas como 2)
    
    def test_map_product_fields_values_correct(self):
        """
        Test: Los valores se mapean correctamente de SQL a JSON
        Validates: Requirements 6.6-6.20
        """
        row = {
            "EMP_CODI": "001",
            "PRO_CODI": "7SUBSM001A",
            "PRO_NOMB": "Producto de prueba",
            "TIP_CODI": "TIP001",
            "TIP_NOMB": "Tipo de producto",
            "PRO_ACTI": "A",
            "PRO_CO01": "7ABC",
            "SIS_NOMB": "ARKEO FLEET",
            "PRO_CO02": "SUBSM",
            "SUB_NOMB": "Subsistema Mantenimiento",
            "UNI_CODI": "UND",
            "UNI_NOMB": "Unidad",
            "AUD_FCRE": datetime(2024, 1, 15, 10, 30, 0),
            "AUD_UFAC": datetime(2024, 1, 20, 15, 45, 0)
        }
        
        result = ResponseFormatter.map_product_fields(row)
        
        assert result["codigoEmpresa"] == "001"
        assert result["codigoProducto"] == "7SUBSM001A"
        assert result["nombreProducto"] == "Producto de prueba"
        assert result["codigoTipo"] == "TIP001"
        assert result["nombreTipo"] == "Tipo de producto"
        assert result["codigoSistema"] == "7"  # Primer carácter de PRO_CO01
        assert result["nombreSistema"] == "ARKEO FLEET"
        assert result["codigoSubsistema"] == "SUBSM"
        assert result["nombreSubsistema"] == "Subsistema Mantenimiento"
        assert result["codigoUnidad"] == "UND"
        assert result["nombreUnidad"] == "Unidad"
    
    def test_map_estado_activo(self):
        """
        Test: PRO_ACTI='A' debe convertirse a estado='ACTIVO'
        Validates: Requirements 6.11, 7.8
        """
        row = {
            "PRO_ACTI": "A",
            "PRO_CO01": "7",
            "PRO_CO02": "SUBSA",
            "EMP_CODI": "001",
            "PRO_CODI": "7SUBSA001",
            "PRO_NOMB": "Test",
            "TIP_CODI": "T1",
            "TIP_NOMB": "Tipo",
            "SIS_NOMB": "Sistema",
            "SUB_NOMB": "Subsistema",
            "UNI_CODI": "U1",
            "UNI_NOMB": "Unidad",
            "AUD_FCRE": datetime(2024, 1, 1, 0, 0, 0),
            "AUD_UFAC": datetime(2024, 1, 1, 0, 0, 0)
        }
        
        result = ResponseFormatter.map_product_fields(row)
        
        assert result["estado"] == "ACTIVO"
    
    def test_map_estado_inactivo(self):
        """
        Test: PRO_ACTI='I' debe convertirse a estado='INACTIVO'
        Validates: Requirements 6.11, 7.8
        """
        row = {
            "PRO_ACTI": "I",
            "PRO_CO01": "7",
            "PRO_CO02": "SUBSA",
            "EMP_CODI": "001",
            "PRO_CODI": "7SUBSA001",
            "PRO_NOMB": "Test",
            "TIP_CODI": "T1",
            "TIP_NOMB": "Tipo",
            "SIS_NOMB": "Sistema",
            "SUB_NOMB": "Subsistema",
            "UNI_CODI": "U1",
            "UNI_NOMB": "Unidad",
            "AUD_FCRE": datetime(2024, 1, 1, 0, 0, 0),
            "AUD_UFAC": datetime(2024, 1, 1, 0, 0, 0)
        }
        
        result = ResponseFormatter.map_product_fields(row)
        
        assert result["estado"] == "INACTIVO"
    
    def test_map_codigo_sistema_extracts_first_char(self):
        """
        Test: codigoSistema debe ser el primer carácter de PRO_CO01
        Validates: Requirements 6.12, 7.9
        """
        row = {
            "PRO_CO01": "7ABCDEF",  # Código largo
            "PRO_ACTI": "A",
            "PRO_CO02": "SUBSA",
            "EMP_CODI": "001",
            "PRO_CODI": "7SUBSA001",
            "PRO_NOMB": "Test",
            "TIP_CODI": "T1",
            "TIP_NOMB": "Tipo",
            "SIS_NOMB": "Sistema",
            "SUB_NOMB": "Subsistema",
            "UNI_CODI": "U1",
            "UNI_NOMB": "Unidad",
            "AUD_FCRE": datetime(2024, 1, 1, 0, 0, 0),
            "AUD_UFAC": datetime(2024, 1, 1, 0, 0, 0)
        }
        
        result = ResponseFormatter.map_product_fields(row)
        
        assert result["codigoSistema"] == "7"
        assert len(result["codigoSistema"]) == 1


class TestCalculateTrabajoRepuesto:
    """Tests para cálculo del campo trabajoRepuesto"""
    
    def test_calculate_trabajo_repuesto_true_uppercase(self):
        """
        Test: 'SUBSM' (contiene M mayúscula) debe retornar True
        Validates: Requirements 6.18, 7.17
        """
        result = ResponseFormatter.calculate_trabajo_repuesto("SUBSM")
        
        assert result is True
    
    def test_calculate_trabajo_repuesto_false(self):
        """
        Test: 'SUBSA' (no contiene M) debe retornar False
        Validates: Requirements 6.18, 7.17
        """
        result = ResponseFormatter.calculate_trabajo_repuesto("SUBSA")
        
        assert result is False
    
    def test_calculate_trabajo_repuesto_lowercase(self):
        """
        Test: 'subsm' (m minúscula) debe retornar True (case insensitive)
        Validates: Requirements 6.18, 7.17
        """
        result = ResponseFormatter.calculate_trabajo_repuesto("subsm")
        
        assert result is True
    
    def test_calculate_trabajo_repuesto_mixed_case(self):
        """
        Test: 'SuBsM' (caso mixto con M) debe retornar True
        """
        result = ResponseFormatter.calculate_trabajo_repuesto("SuBsM")
        
        assert result is True
    
    def test_calculate_trabajo_repuesto_m_at_start(self):
        """
        Test: 'MAINT' (M al inicio) debe retornar True
        """
        result = ResponseFormatter.calculate_trabajo_repuesto("MAINT")
        
        assert result is True
    
    def test_calculate_trabajo_repuesto_m_at_end(self):
        """
        Test: 'STRTM' (M al final) debe retornar True
        """
        result = ResponseFormatter.calculate_trabajo_repuesto("STRTM")
        
        assert result is True
    
    def test_calculate_trabajo_repuesto_empty_string(self):
        """
        Test: String vacío debe retornar False
        """
        result = ResponseFormatter.calculate_trabajo_repuesto("")
        
        assert result is False
    
    def test_calculate_trabajo_repuesto_no_m(self):
        """
        Test: Códigos sin M deben retornar False
        """
        test_cases = ["ABCDE", "SUBSA", "NOREP", "12345"]
        
        for codigo in test_cases:
            result = ResponseFormatter.calculate_trabajo_repuesto(codigo)
            assert result is False, f"Expected False for '{codigo}'"


class TestFormatDatetime:
    """Tests para formateo de fechas a ISO 8601 con timezone"""
    
    def test_format_datetime_with_timezone(self):
        """
        Test: datetime debe formatearse a ISO 8601 con timezone -05:00
        Validates: Requirements 6.19, 6.20, 7.13, 7.14, 7.19
        """
        dt = datetime(2024, 1, 15, 10, 30, 0)
        
        result = ResponseFormatter.format_datetime(dt)
        
        assert result == "2024-01-15T10:30:00-05:00"
    
    def test_format_datetime_midnight(self):
        """
        Test: Medianoche debe formatearse correctamente
        """
        dt = datetime(2024, 1, 1, 0, 0, 0)
        
        result = ResponseFormatter.format_datetime(dt)
        
        assert result == "2024-01-01T00:00:00-05:00"
    
    def test_format_datetime_last_second_of_day(self):
        """
        Test: Último segundo del día debe formatearse correctamente
        """
        dt = datetime(2024, 12, 31, 23, 59, 59)
        
        result = ResponseFormatter.format_datetime(dt)
        
        assert result == "2024-12-31T23:59:59-05:00"
    
    def test_format_datetime_none(self):
        """
        Test: None debe retornar string vacío
        """
        result = ResponseFormatter.format_datetime(None)
        
        assert result == ""
    
    def test_format_datetime_non_datetime_object(self):
        """
        Test: Objeto que no es datetime debe retornar string vacío
        """
        result = ResponseFormatter.format_datetime("not a datetime")
        
        assert result == ""


class TestFormatSuccessResponse:
    """Tests para formateo de respuestas exitosas"""
    
    def test_format_success_response_structure(self):
        """
        Test: Respuesta exitosa debe contener statusCode, headers y body
        Validates: Requirements 7.1, 7.2, 7.18, 7.20
        """
        products = [{"codigoProducto": "7SUBSM001A"}]
        pagination = {
            "totalPagina": 1,
            "siguienteCursor": None,
            "tieneMasPaginas": False
        }
        trace_id = "550e8400-e29b-41d4-a716-446655440000"
        
        result = ResponseFormatter.format_success_response(products, pagination, trace_id)
        
        assert "statusCode" in result
        assert "headers" in result
        assert "body" in result
        assert result["statusCode"] == 200
        assert result["headers"]["Content-Type"] == "application/json; charset=utf-8"
    
    def test_format_success_response_body_structure(self):
        """
        Test: Body debe contener datos, paginacion y traceId
        Validates: Requirements 7.1, 7.2
        """
        products = [{"codigoProducto": "7SUBSM001A"}]
        pagination = {
            "totalPagina": 1,
            "siguienteCursor": None,
            "tieneMasPaginas": False
        }
        trace_id = "550e8400-e29b-41d4-a716-446655440000"
        
        result = ResponseFormatter.format_success_response(products, pagination, trace_id)
        body = json.loads(result["body"])
        
        assert "datos" in body
        assert "paginacion" in body
        assert "traceId" in body
        assert body["datos"] == products
        assert body["paginacion"] == pagination
        assert body["traceId"] == trace_id
    
    def test_format_success_response_empty_products(self):
        """
        Test: Array vacío de productos debe ser válido
        Validates: Requirements 7.23
        """
        products = []
        pagination = {
            "totalPagina": 0,
            "siguienteCursor": None,
            "tieneMasPaginas": False
        }
        trace_id = "550e8400-e29b-41d4-a716-446655440000"
        
        result = ResponseFormatter.format_success_response(products, pagination, trace_id)
        body = json.loads(result["body"])
        
        assert body["datos"] == []
        assert body["paginacion"]["totalPagina"] == 0
    
    def test_format_success_response_multiple_products(self):
        """
        Test: Múltiples productos deben incluirse correctamente
        """
        products = [
            {"codigoProducto": "7SUBSM001A"},
            {"codigoProducto": "7SUBSM002B"},
            {"codigoProducto": "7SUBSM003C"}
        ]
        pagination = {
            "totalPagina": 3,
            "siguienteCursor": "N1NVQlNNMDAzQw==",
            "tieneMasPaginas": True
        }
        trace_id = "550e8400-e29b-41d4-a716-446655440000"
        
        result = ResponseFormatter.format_success_response(products, pagination, trace_id)
        body = json.loads(result["body"])
        
        assert len(body["datos"]) == 3
        assert body["paginacion"]["tieneMasPaginas"] is True


class TestFormatErrorResponse:
    """Tests para formateo de respuestas de error"""
    
    def test_format_error_response_structure(self):
        """
        Test: Respuesta de error debe contener error, mensaje y traceId
        Validates: Requirements 7.21, 7.22
        """
        status_code = 400
        error_code = "400"
        message = "Parámetro obligatorio 'companyCode' no proporcionado"
        trace_id = "550e8400-e29b-41d4-a716-446655440000"
        
        result = ResponseFormatter.format_error_response(
            status_code, error_code, message, trace_id
        )
        
        assert result["statusCode"] == 400
        assert result["headers"]["Content-Type"] == "application/json; charset=utf-8"
        
        body = json.loads(result["body"])
        assert "error" in body
        assert "mensaje" in body
        assert "traceId" in body
        assert body["error"] == error_code
        assert body["mensaje"] == message
        assert body["traceId"] == trace_id
    
    def test_format_error_response_401(self):
        """
        Test: Error 401 de autenticación
        """
        result = ResponseFormatter.format_error_response(
            401, "401", "API Key inválida", "test-trace-id"
        )
        
        assert result["statusCode"] == 401
        body = json.loads(result["body"])
        assert body["error"] == "401"
        assert "inválida" in body["mensaje"]
    
    def test_format_error_response_404(self):
        """
        Test: Error 404 producto no encontrado
        """
        result = ResponseFormatter.format_error_response(
            404, "404", "Producto no encontrado", "test-trace-id"
        )
        
        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert body["error"] == "404"
        assert "no encontrado" in body["mensaje"]
    
    def test_format_error_response_500(self):
        """
        Test: Error 500 interno del servidor
        """
        result = ResponseFormatter.format_error_response(
            500, "500", "Error interno del servidor", "test-trace-id"
        )
        
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert body["error"] == "500"
        assert "interno" in body["mensaje"]
    
    def test_format_error_response_special_characters(self):
        """
        Test: Mensajes con caracteres especiales deben codificarse correctamente
        """
        message = "El parámetro 'pageSize' debe estar entre 1 y 500"
        result = ResponseFormatter.format_error_response(
            400, "400", message, "test-trace-id"
        )
        
        body = json.loads(result["body"])
        assert body["mensaje"] == message
        assert "pageSize" in body["mensaje"]
