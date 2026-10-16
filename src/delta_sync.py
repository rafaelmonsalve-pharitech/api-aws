"""
Delta Sync Module

Módulo de sincronización incremental basada en fechas.
Requirements: 4.2, 4.4, 4.11, 8.2
"""

from datetime import datetime
from dateutil import parser
from dateutil.tz import UTC


class InvalidDateFormatError(Exception):
    """Excepción para formato de fecha inválido."""
    pass


class FutureDateError(Exception):
    """Excepción para fechas futuras."""
    pass


class DeltaSync:
    """Clase con métodos estáticos para sincronización delta."""
    
    @staticmethod
    def parse_updated_since(updated_since_str: str) -> datetime:
        """
        Parsea fecha ISO 8601 con timezone y retorna datetime UTC.
        
        Args:
            updated_since_str: String ISO 8601 con timezone
                              Ejemplo: "2024-01-15T10:30:00-05:00"
        
        Returns:
            datetime en UTC
        
        Raises:
            InvalidDateFormatError: Si formato es inválido
        
        Example:
            >>> DeltaSync.parse_updated_since("2024-01-15T10:30:00-05:00")
            datetime(2024, 1, 15, 15, 30, 0, tzinfo=UTC)
        """
        try:
            # Parsear con python-dateutil (soporta ISO 8601 completo)
            dt = parser.isoparse(updated_since_str)
            
            # Verificar que tenga timezone
            if dt.tzinfo is None:
                raise InvalidDateFormatError(
                    'Formato de fecha inválido. Use ISO 8601 con timezone: YYYY-MM-DDTHH:MM:SS-05:00'
                )
            
            # Convertir a UTC
            dt_utc = dt.astimezone(UTC)
            
            return dt_utc
            
        except (ValueError, TypeError) as e:
            raise InvalidDateFormatError(
                'Formato de fecha inválido. Use ISO 8601: YYYY-MM-DDTHH:MM:SS-05:00'
            )
    
    @staticmethod
    def validate_not_future(dt: datetime) -> None:
        """
        Valida que datetime no sea futuro.
        
        Args:
            dt: datetime a validar
        
        Raises:
            FutureDateError: Si fecha es futura
        
        Example:
            >>> DeltaSync.validate_not_future(datetime(2024, 1, 1))  # OK si es pasado
            >>> DeltaSync.validate_not_future(datetime(2099, 12, 31))  # Raises FutureDateError
        """
        now = datetime.now(UTC)
        
        # Asegurar que dt tiene timezone para comparación justa
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
        
        if dt > now:
            raise FutureDateError('La fecha no puede ser futura')
    
    @staticmethod
    def to_sql_datetime(dt: datetime) -> str:
        """
        Convierte datetime a formato SQL Server DATETIME.
        
        Args:
            dt: datetime object
        
        Returns:
            String en formato 'YYYY-MM-DD HH:MM:SS'
        
        Example:
            >>> dt = datetime(2024, 1, 15, 10, 30, 0)
            >>> DeltaSync.to_sql_datetime(dt)
            '2024-01-15 10:30:00'
        """
        return dt.strftime('%Y-%m-%d %H:%M:%S')
