"""
Authentication Validator Module

Validación de API Keys y rate limiting.
Requirements: 1.1, 1.2, 1.3, 1.4, 1.6, 1.7, 1.8, 12.7
"""

import json
import time
from typing import NamedTuple, Optional
from collections import defaultdict


class ValidationResult(NamedTuple):
    """Resultado de validación de API Key."""
    is_valid: bool
    error_message: Optional[str]
    status_code: int


class AuthValidator:
    """Validador de autenticación mediante API Key."""
    
    RATE_LIMIT_PER_MINUTE = 1000
    RATE_LIMIT_WINDOW = 60  # segundos
    
    def __init__(self, secrets_client, logger=None):
        """
        Inicializa el validador.
        
        Args:
            secrets_client: boto3 Secrets Manager client
            logger: Optional StructuredLogger para logging
        """
        self.secrets_client = secrets_client
        self.logger = logger
        self._valid_keys_cache = None
        self._cache_time = 0
        self._cache_ttl = 300  # 5 minutos
        
        # Rate limiting en memoria: {api_key: [timestamp1, timestamp2, ...]}
        self._rate_limits = defaultdict(list)
    
    def validate_api_key(
        self,
        api_key: Optional[str],
        source_ip: str,
        trace_id: str
    ) -> ValidationResult:
        """
        Valida API Key.
        
        Args:
            api_key: API Key del header X-API-Key
            source_ip: IP origen de la petición
            trace_id: UUID de correlación
        
        Returns:
            ValidationResult con is_valid, error_message, status_code
        """
        # Validar presencia
        if not api_key:
            if self.logger:
                self.logger.warn(
                    'API Key missing',
                    source_ip=source_ip,
                    trace_id=trace_id
                )
            return ValidationResult(
                is_valid=False,
                error_message='Autenticación requerida. Proporcione el header X-API-Key',
                status_code=401
            )
        
        # Validar formato (43 caracteres alfanuméricos)
        if len(api_key) != 43 or not api_key.isalnum():
            if self.logger:
                self.logger.warn(
                    'API Key invalid format',
                    source_ip=source_ip,
                    api_key_prefix=api_key[:8],
                    trace_id=trace_id
                )
            return ValidationResult(
                is_valid=False,
                error_message='API Key inválida',
                status_code=401
            )
        
        # Validar contra lista autorizada
        valid_keys = self._fetch_valid_keys()
        if api_key not in valid_keys:
            if self.logger:
                self.logger.warn(
                    'API Key not authorized',
                    source_ip=source_ip,
                    api_key_prefix=api_key[:8],
                    trace_id=trace_id
                )
            return ValidationResult(
                is_valid=False,
                error_message='API Key inválida',
                status_code=401
            )
        
        # Validar rate limit
        if not self._check_rate_limit(api_key):
            if self.logger:
                self.logger.warn(
                    'Rate limit exceeded',
                    source_ip=source_ip,
                    api_key_prefix=api_key[:8],
                    trace_id=trace_id
                )
            return ValidationResult(
                is_valid=False,
                error_message='Límite de tasa excedido. Intente nuevamente en 60 segundos',
                status_code=429
            )
        
        # Éxito
        return ValidationResult(
            is_valid=True,
            error_message=None,
            status_code=200
        )
    
    def _fetch_valid_keys(self) -> list:
        """
        Obtiene lista de API Keys válidas de Secrets Manager.
        
        Returns:
            Lista de API Keys válidas
        """
        # Usar caché si es válido
        current_time = time.time()
        if (self._valid_keys_cache is not None and 
            (current_time - self._cache_time) < self._cache_ttl):
            return self._valid_keys_cache
        
        try:
            response = self.secrets_client.get_secret_value(
                SecretId='seven/api/keys'
            )
            secret_data = json.loads(response['SecretString'])
            valid_keys = secret_data.get('valid_keys', [])
            
            # Actualizar caché
            self._valid_keys_cache = valid_keys
            self._cache_time = current_time
            
            return valid_keys
            
        except Exception as e:
            if self.logger:
                self.logger.error(f'Error fetching API keys from Secrets Manager: {e}')
            # Retornar caché antiguo si existe, sino lista vacía
            return self._valid_keys_cache if self._valid_keys_cache else []
    
    def _check_rate_limit(self, api_key: str) -> bool:
        """
        Verifica rate limit para API Key.
        
        Args:
            api_key: API Key a verificar
        
        Returns:
            True si está dentro del límite, False si excedido
        """
        current_time = time.time()
        
        # Obtener timestamps de peticiones del último minuto
        timestamps = self._rate_limits[api_key]
        
        # Filtrar solo los del último minuto
        cutoff_time = current_time - self.RATE_LIMIT_WINDOW
        timestamps[:] = [ts for ts in timestamps if ts > cutoff_time]
        
        # Verificar si excede límite
        if len(timestamps) >= self.RATE_LIMIT_PER_MINUTE:
            return False
        
        # Agregar timestamp actual
        timestamps.append(current_time)
        
        return True
