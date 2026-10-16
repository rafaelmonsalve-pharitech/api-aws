"""
Error Handler Module

Manejo centralizado de errores y excepciones.
Requirements: 8.1-8.16
"""

import json
import re
from typing import Optional


# Excepciones custom
class ValidationError(Exception):
    pass

class AuthenticationError(Exception):
    pass

class RateLimitError(Exception):
    pass

class NotFoundError(Exception):
    pass

class DatabaseConnectionError(Exception):
    pass

class DatabaseQueryError(Exception):
    pass

class TimeoutError(Exception):
    pass


class ErrorHandler:
    """Manejador centralizado de errores."""
    
    ERROR_MESSAGES = {
        'MISSING_API_KEY': 'Autenticación requerida. Proporcione el header X-API-Key',
        'INVALID_API_KEY': 'API Key inválida',
        'MISSING_PARAMETER': 'Parámetro obligatorio no proporcionado',
        'INVALID_DATE_FORMAT': 'Formato de fecha inválido. Use ISO 8601: YYYY-MM-DDTHH:MM:SS-05:00',
        'INVALID_PAGE_SIZE': 'El parámetro pageSize debe estar entre 1 y 500',
        'INVALID_CURSOR': 'El cursor proporcionado es inválido o ha expirado',
        'PRODUCT_NOT_FOUND': 'Producto no encontrado',
        'DATABASE_UNAVAILABLE': 'Servicio de base de datos no disponible temporalmente',
        'INTERNAL_ERROR': 'Error interno del servidor',
        'GATEWAY_TIMEOUT': 'Tiempo de espera agotado procesando la solicitud',
        'RATE_LIMIT_EXCEEDED': 'Límite de tasa excedido. Intente nuevamente en 60 segundos'
    }
    
    @staticmethod
    def handle_exception(exc: Exception, trace_id: str) -> dict:
        """
        Maneja excepción y retorna respuesta HTTP.
        
        Args:
            exc: Excepción capturada
            trace_id: UUID de correlación
        
        Returns:
            dict con statusCode, headers, body
        """
        # Mapeo de excepciones a HTTP status codes
        exception_map = {
            ValidationError: (400, '400', ErrorHandler.ERROR_MESSAGES['MISSING_PARAMETER']),
            AuthenticationError: (401, '401', ErrorHandler.ERROR_MESSAGES['INVALID_API_KEY']),
            RateLimitError: (429, '429', ErrorHandler.ERROR_MESSAGES['RATE_LIMIT_EXCEEDED']),
            NotFoundError: (404, '404', ErrorHandler.ERROR_MESSAGES['PRODUCT_NOT_FOUND']),
            DatabaseConnectionError: (503, '503', ErrorHandler.ERROR_MESSAGES['DATABASE_UNAVAILABLE']),
            DatabaseQueryError: (500, '500', ErrorHandler.ERROR_MESSAGES['INTERNAL_ERROR']),
            TimeoutError: (504, '504', ErrorHandler.ERROR_MESSAGES['GATEWAY_TIMEOUT'])
        }
        
        exc_type = type(exc)
        status_code, error_code, default_message = exception_map.get(
            exc_type, (500, '500', ErrorHandler.ERROR_MESSAGES['INTERNAL_ERROR'])
        )
        
        # Usar mensaje de excepción si existe, sino usar default
        message = str(exc) if str(exc) else default_message
        message = ErrorHandler.sanitize_error_message(message)
        
        return {
            'statusCode': status_code,
            'headers': {'Content-Type': 'application/json; charset=utf-8'},
            'body': json.dumps({
                'error': error_code,
                'mensaje': message,
                'traceId': trace_id
            }, ensure_ascii=False)
        }
    
    @staticmethod
    def sanitize_error_message(message: str) -> str:
        """
        Sanitiza mensaje de error removiendo información sensible.
        
        Args:
            message: Mensaje original
        
        Returns:
            Mensaje sanitizado
        """
        # Remover rutas de archivos
        message = re.sub(r'[A-Za-z]:\\[^\s]+', '[PATH]', message)
        message = re.sub(r'/[\w/]+\.py', '[FILE]', message)
        
        # Remover nombres de tablas SQL
        message = re.sub(r'\b[A-Z_]{2,}\.[A-Z_]{2,}\b', '[TABLE]', message)
        
        # Remover IPs internas
        message = re.sub(r'\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', message)
        message = re.sub(r'\b192\.168\.\d{1,3}\.\d{1,3}\b', '[IP]', message)
        
        # Remover credenciales
        message = re.sub(r'password[=:]\s*\S+', 'password=[REDACTED]', message, flags=re.IGNORECASE)
        message = re.sub(r'user[=:]\s*\S+', 'user=[REDACTED]', message, flags=re.IGNORECASE)
        
        return message
