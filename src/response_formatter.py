"""
Response Formatter Module

Este módulo proporciona la clase ResponseFormatter con métodos estáticos para:
- Formatear respuestas exitosas con estructura estándar JSON en español
- Formatear respuestas de error con estructura estándar
- Mapear campos SQL a nombres JSON en español
- Calcular campos derivados (trabajoRepuesto)
- Formatear fechas a ISO 8601 con timezone

Requirements: 7.1, 7.2, 7.3-7.17, 7.18, 7.19, 7.20, 7.21, 7.22, 7.23, 6.6-6.20
"""

import json
from datetime import datetime
from typing import Any


class ResponseFormatter:
    """
    Formateador de respuestas HTTP para la API Seven Arkeo Fleet.
    
    Responsabilidades:
    - Serializar respuestas exitosas con estructura estándar
    - Formatear respuestas de error con estructura estándar
    - Mapear campos SQL a nombres JSON en español
    - Formatear fechas SQL a ISO 8601 con timezone
    - Calcular campo booleano trabajoRepuesto
    - Generar headers HTTP apropiados
    """
    
    @staticmethod
    def format_success_response(
        products: list[dict],
        pagination: dict,
        trace_id: str
    ) -> dict:
        """
        Formatea una respuesta exitosa con estructura estándar.
        
        Args:
            products: Lista de diccionarios con datos de productos
            pagination: Diccionario con información de paginación
                {
                    "totalPagina": int,
                    "siguienteCursor": str | None,
                    "tieneMasPaginas": bool
                }
            trace_id: UUID de correlación para la petición
        
        Returns:
            dict con estructura:
            {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json; charset=utf-8"},
                "body": json_string con {
                    "datos": [...],
                    "paginacion": {...},
                    "traceId": "..."
                }
            }
        
        Validates: Requirements 7.1, 7.2, 7.18, 7.20
        """
        response_body = {
            "datos": products,
            "paginacion": pagination,
            "traceId": trace_id
        }
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json; charset=utf-8"
            },
            "body": json.dumps(response_body, ensure_ascii=False)
        }
    
    @staticmethod
    def format_error_response(
        status_code: int,
        error_code: str,
        message: str,
        trace_id: str
    ) -> dict:
        """
        Formatea una respuesta de error con estructura estándar.
        
        Args:
            status_code: Código HTTP de estado (400, 401, 404, etc.)
            error_code: Código del error (puede ser el status_code como string)
            message: Mensaje descriptivo en español
            trace_id: UUID de correlación para la petición
        
        Returns:
            dict con estructura:
            {
                "statusCode": status_code,
                "headers": {"Content-Type": "application/json; charset=utf-8"},
                "body": json_string con {
                    "error": error_code,
                    "mensaje": message,
                    "traceId": trace_id
                }
            }
        
        Validates: Requirements 7.21, 7.22
        """
        error_body = {
            "error": error_code,
            "mensaje": message,
            "traceId": trace_id
        }
        
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json; charset=utf-8"
            },
            "body": json.dumps(error_body, ensure_ascii=False)
        }
    
    @staticmethod
    def map_product_fields(row: dict) -> dict:
        """
        Mapea campos SQL a nombres JSON en español con transformaciones necesarias.
        
        Args:
            row: Diccionario con campos SQL de la base de datos:
                {
                    "EMP_CODI": str,
                    "PRO_CODI": str,
                    "PRO_NOMB": str,
                    "TIP_CODI": str,
                    "TIP_NOMB": str,
                    "PRO_ACTI": str ('A' o 'I'),
                    "PRO_CO01": str,
                    "SIS_NOMB": str,
                    "PRO_CO02": str (5 caracteres),
                    "SUB_NOMB": str,
                    "UNI_CODI": str,
                    "UNI_NOMB": str,
                    "AUD_FCRE": datetime,
                    "AUD_UFAC": datetime
                }
        
        Returns:
            dict con campos JSON en español:
            {
                "codigoEmpresa": str,
                "codigoProducto": str,
                "nombreProducto": str,
                "codigoTipo": str,
                "nombreTipo": str,
                "estado": str ('ACTIVO' o 'INACTIVO'),
                "codigoSistema": str (primer carácter),
                "nombreSistema": str,
                "codigoSubsistema": str,
                "nombreSubsistema": str,
                "codigoUnidad": str,
                "nombreUnidad": str,
                "trabajoRepuesto": bool,
                "fechaCreacion": str (ISO 8601),
                "fechaActualizacion": str (ISO 8601)
            }
        
        Validates: Requirements 6.6-6.20, 7.3-7.17, 7.18, 7.19
        """
        # Extraer primer carácter de PRO_CO01 para codigoSistema
        codigo_sistema = row["PRO_CO01"][0] if row.get("PRO_CO01") else ""
        
        # Convertir PRO_ACTI ('A'/'I') a estado ('ACTIVO'/'INACTIVO')
        estado_map = {
            "A": "ACTIVO",
            "I": "INACTIVO"
        }
        estado = estado_map.get(row.get("PRO_ACTI", ""), "INACTIVO")
        
        # Calcular trabajoRepuesto evaluando si PRO_CO02 contiene 'M'
        trabajo_repuesto = ResponseFormatter.calculate_trabajo_repuesto(
            row.get("PRO_CO02", "")
        )
        
        # Formatear fechas a ISO 8601 con timezone -05:00
        fecha_creacion = ResponseFormatter.format_datetime(row.get("AUD_FCRE"))
        fecha_actualizacion = ResponseFormatter.format_datetime(row.get("AUD_UFAC"))
        
        return {
            "codigoEmpresa": row.get("EMP_CODI", ""),
            "codigoProducto": row.get("PRO_CODI", ""),
            "nombreProducto": row.get("PRO_NOMB", ""),
            "codigoTipo": row.get("TIP_CODI", ""),
            "nombreTipo": row.get("TIP_NOMB", ""),
            "estado": estado,
            "codigoSistema": codigo_sistema,
            "nombreSistema": row.get("SIS_NOMB", ""),
            "codigoSubsistema": row.get("PRO_CO02", ""),
            "nombreSubsistema": row.get("SUB_NOMB", ""),
            "codigoUnidad": row.get("UNI_CODI", ""),
            "nombreUnidad": row.get("UNI_NOMB", ""),
            "trabajoRepuesto": trabajo_repuesto,
            "fechaCreacion": fecha_creacion,
            "fechaActualizacion": fecha_actualizacion
        }
    
    @staticmethod
    def calculate_trabajo_repuesto(codigo_subsistema: str) -> bool:
        """
        Calcula si un producto es trabajo o repuesto basado en el código de subsistema.
        
        Lógica: Retorna True si PRO_CO02 contiene la letra 'M' (mayúscula o minúscula).
        
        Args:
            codigo_subsistema: Código de subsistema (PRO_CO02, 5 caracteres)
        
        Returns:
            bool: True si contiene 'M', False en caso contrario
        
        Examples:
            "SUBSM" -> True (contiene M)
            "SUBSA" -> False (no contiene M)
            "subsm" -> True (m minúscula también cuenta)
            "MAINT" -> True (M al inicio)
            ""      -> False (string vacío)
        
        Validates: Requirements 6.18, 7.17
        """
        if not codigo_subsistema:
            return False
        
        return "M" in codigo_subsistema.upper()
    
    @staticmethod
    def format_datetime(dt: Any) -> str:
        """
        Convierte un datetime a formato ISO 8601 con timezone -05:00 (Colombia).
        
        Args:
            dt: datetime object o None
        
        Returns:
            str: Fecha en formato "YYYY-MM-DDTHH:MM:SS-05:00"
            Si dt es None, retorna string vacío
        
        Examples:
            datetime(2024, 1, 15, 10, 30, 0) -> "2024-01-15T10:30:00-05:00"
            datetime(2024, 12, 31, 23, 59, 59) -> "2024-12-31T23:59:59-05:00"
            None -> ""
        
        Validates: Requirements 6.19, 6.20, 7.13, 7.14, 7.19
        """
        if dt is None:
            return ""
        
        if not isinstance(dt, datetime):
            return ""
        
        # Formatear fecha en ISO 8601 base sin timezone
        formatted = dt.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Agregar timezone -05:00 (Colombia)
        return f"{formatted}-05:00"
