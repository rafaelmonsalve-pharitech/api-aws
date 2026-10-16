"""
SQL Server Connector Module

Conector a SQL Server usando pytds con connection pooling.
Requirements: 5.1-5.15
"""

import json
import pytds
from typing import Optional


class SQLServerConnector:
    """Conector a SQL Server con connection pooling."""
    
    def __init__(self, secrets_client, logger=None):
        """
        Inicializa el conector.
        
        Args:
            secrets_client: boto3 Secrets Manager client
            logger: Optional StructuredLogger
        """
        self.secrets_client = secrets_client
        self.logger = logger
        self.pool = []
        self.max_pool_size = 5
        self._credentials = None
    
    def _get_credentials(self) -> dict:
        """Obtiene credenciales de Secrets Manager."""
        if self._credentials:
            return self._credentials
        
        try:
            response = self.secrets_client.get_secret_value(
                SecretId='seven/db/credentials'
            )
            self._credentials = json.loads(response['SecretString'])
            return self._credentials
        except Exception as e:
            if self.logger:
                self.logger.error(f'Error fetching DB credentials: {e}')
            from src.error_handler import DatabaseConnectionError
            raise DatabaseConnectionError('No se pudieron obtener las credenciales de la base de datos')
    
    def _create_connection(self) -> pytds.Connection:
        """
        Crea nueva conexión a SQL Server.
        
        Returns:
            pytds.Connection
        
        Raises:
            DatabaseConnectionError: Si falla la conexión
        """
        from src.error_handler import DatabaseConnectionError
        
        creds = self._get_credentials()
        
        try:
            conn = pytds.connect(
                server='10.125.18.16',
                port=1433,
                database='seven_db',
                user=creds['username'],
                password=creds['password'],
                timeout=10,
                query_timeout=30,
                tds_version=pytds.TDS74,
                appname='ArkeoFleetAPI',
                autocommit=True
            )
            
            if self.logger:
                self.logger.info('Database connection established')
            
            return conn
            
        except pytds.OperationalError as e:
            if self.logger:
                self.logger.error(f'Database connection failed: {e}')
            raise DatabaseConnectionError('Servicio de base de datos no disponible temporalmente')
        except pytds.DatabaseError as e:
            if self.logger:
                self.logger.error(f'Database authentication failed: {e}')
            raise DatabaseConnectionError('Error de autenticación con la base de datos')
        except Exception as e:
            if self.logger:
                self.logger.error(f'Unexpected database error: {e}')
            raise DatabaseConnectionError('Error al conectar con la base de datos')
    
    def get_connection(self) -> pytds.Connection:
        """
        Obtiene conexión del pool o crea nueva.
        
        Returns:
            pytds.Connection
        """
        # Intentar reusar conexión del pool
        while self.pool:
            conn = self.pool.pop()
            try:
                # Verificar que la conexión esté viva
                with conn.cursor() as cursor:
                    cursor.execute('SELECT 1')
                return conn
            except Exception:
                # Conexión muerta, continuar al siguiente
                try:
                    conn.close()
                except Exception:
                    pass
        
        # Crear nueva conexión
        return self._create_connection()
    
    def release_connection(self, conn: pytds.Connection):
        """
        Devuelve conexión al pool.
        
        Args:
            conn: Conexión a devolver
        """
        if len(self.pool) < self.max_pool_size:
            self.pool.append(conn)
        else:
            try:
                conn.close()
            except Exception:
                pass
    
    def close_all(self):
        """Cierra todas las conexiones del pool."""
        while self.pool:
            conn = self.pool.pop()
            try:
                conn.close()
            except Exception:
                pass
        
        if self.logger:
            self.logger.info('All database connections closed')
