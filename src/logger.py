"""
Structured Logger Module

Logging estructurado JSON para CloudWatch Logs.
Requirements: 12.1, 12.17, 8.11, 8.12
"""

import json
from datetime import datetime
from typing import Any


class StructuredLogger:
    """Logger que emite logs estructurados en formato JSON."""
    
    SENSITIVE_FIELDS = {
        'X-API-Key', 'x-api-key', 'password', 'api_key', 
        'secret', 'token', 'authorization', 'Authorization'
    }
    
    def __init__(self, trace_id: str):
        """
        Inicializa el logger con un trace ID.
        
        Args:
            trace_id: UUID de correlación para la petición
        """
        self.trace_id = trace_id
    
    def info(self, message: str, **metadata):
        """Log nivel INFO"""
        self._log('INFO', message, metadata)
    
    def warn(self, message: str, **metadata):
        """Log nivel WARN"""
        self._log('WARN', message, metadata)
    
    def error(self, message: str, **metadata):
        """Log nivel ERROR"""
        self._log('ERROR', message, metadata)
    
    def debug(self, message: str, **metadata):
        """Log nivel DEBUG"""
        self._log('DEBUG', message, metadata)
    
    def _log(self, level: str, message: str, metadata: dict):
        """
        Genera y emite log estructurado.
        
        Args:
            level: Nivel de log (INFO, WARN, ERROR, DEBUG)
            message: Mensaje del log
            metadata: Metadata adicional
        """
        sanitized_metadata = self.sanitize(metadata)
        log_entry = self._format_log(level, message, sanitized_metadata)
        print(log_entry)
    
    def _format_log(self, level: str, message: str, metadata: dict) -> str:
        """
        Formatea log como JSON estructurado.
        
        Args:
            level: Nivel de log
            message: Mensaje
            metadata: Metadata sanitizada
        
        Returns:
            String JSON con campos: timestamp, level, traceId, message, metadata
        """
        log_obj = {
            'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'level': level,
            'traceId': self.trace_id,
            'message': message,
            'metadata': metadata
        }
        return json.dumps(log_obj, ensure_ascii=False)
    
    def sanitize(self, data: Any) -> Any:
        """
        Remueve campos sensibles de metadata.
        
        Args:
            data: Dict, list u otro tipo de dato
        
        Returns:
            Data sanitizada sin campos sensibles
        """
        if isinstance(data, dict):
            return {
                k: '***REDACTED***' if k in self.SENSITIVE_FIELDS else self.sanitize(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self.sanitize(item) for item in data]
        else:
            return data
