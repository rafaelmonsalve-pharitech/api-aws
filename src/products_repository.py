"""
Products Repository Module

Capa de acceso a datos para productos del sistema Seven.
Requirements: 6.1-6.23, 2.2-2.14, 3.4, 3.9, 4.5, 4.6, 4.10
"""

import pytds
from typing import Optional, Tuple, List


class ProductsRepository:
    """Repositorio de productos con queries SQL."""
    
    def __init__(self, connection: pytds.Connection, logger=None):
        """
        Inicializa el repositorio.
        
        Args:
            connection: pytds Connection activa
            logger: Optional StructuredLogger
        """
        self.connection = connection
        self.logger = logger
    
    def get_products(
        self,
        company_code: Optional[str] = None,
        status: Optional[str] = None,
        updated_since: Optional[str] = None,
        cursor: Optional[str] = None,
        page_size: int = 100
    ) -> Tuple[List[dict], bool]:
        """
        Obtiene lista de productos con filtros.
        
        Args:
            company_code: Código de empresa (EMP_CODI)
            status: Estado del producto ('ACTIVO' o 'INACTIVO')
            updated_since: Fecha SQL formato 'YYYY-MM-DD HH:MM:SS'
            cursor: Código de producto para paginación (PRO_CODI)
            page_size: Número de resultados a retornar
        
        Returns:
            Tuple (lista_productos, has_more)
        """
        from src.error_handler import DatabaseQueryError, TimeoutError
        
        # Construir query base
        query = """
            SELECT 
                p.EMP_CODI, p.PRO_CODI, p.PRO_NOMB,
                p.TIP_CODI, t.TIP_NOMB,
                p.PRO_ACTI,
                p.PRO_CO01, COALESCE(s.SIS_NOMB, '') as SIS_NOMB,
                p.PRO_CO02, COALESCE(sub.SUB_NOMB, '') as SUB_NOMB,
                p.UNI_CODI, u.UNI_NOMB,
                p.AUD_FCRE, p.AUD_UFAC
            FROM IN_PRODU p
            INNER JOIN IN_TIPRO t ON p.TIP_CODI = t.TIP_CODI
            INNER JOIN IN_UNIME u ON p.UNI_CODI = u.UNI_CODI
            LEFT JOIN IN_SISTE s ON LEFT(p.PRO_CO01, 1) = s.SIS_CODI
            LEFT JOIN IN_SUBSI sub ON p.PRO_CO02 = sub.SUB_CODI
            WHERE LEFT(p.PRO_CO01, 1) = '7'
            AND LEN(p.PRO_CO02) = 5
            AND LEN(p.PRO_CODI) >= 10
        """
        
        params = []
        
        # Filtros opcionales
        if company_code:
            query += " AND p.EMP_CODI = %s"
            params.append(company_code)
        
        if status == 'ACTIVO':
            query += " AND p.PRO_ACTI = 'A'"
        elif status == 'INACTIVO':
            query += " AND p.PRO_ACTI = 'I'"
        
        if updated_since:
            query += " AND p.AUD_UFAC >= %s"
            params.append(updated_since)
        
        if cursor:
            query += " AND p.PRO_CODI > %s"
            params.append(cursor)
        
        # Ordenamiento y límite
        query += " ORDER BY p.PRO_CODI ASC"
        
        # Pedir 1 más para detectar has_more
        limit = page_size + 1
        
        try:
            with self.connection.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Fetch resultados
                rows = cursor.fetchmany(limit)
                
                # Detectar si hay más resultados
                has_more = len(rows) > page_size
                
                # Retornar solo page_size resultados
                results = rows[:page_size]
                
                # Mapear a diccionarios
                products = [self._map_row_to_dict(row, cursor.description) for row in results]
                
                if self.logger:
                    self.logger.info(
                        f'Products query executed',
                        count=len(products),
                        has_more=has_more
                    )
                
                return (products, has_more)
                
        except pytds.Timeout:
            if self.logger:
                self.logger.error('Query timeout')
            raise TimeoutError('Tiempo de espera agotado al consultar productos')
        except pytds.DatabaseError as e:
            if self.logger:
                self.logger.error(f'Database query error: {e}')
            raise DatabaseQueryError('Error al ejecutar consulta de productos')
    
    def get_product_by_code(
        self,
        codigo: str,
        company_code: str
    ) -> Optional[dict]:
        """
        Obtiene un producto por código.
        
        Args:
            codigo: PRO_CODI del producto
            company_code: EMP_CODI de la empresa
        
        Returns:
            dict con datos del producto o None si no existe
        """
        from src.error_handler import DatabaseQueryError, TimeoutError
        
        query = """
            SELECT 
                p.EMP_CODI, p.PRO_CODI, p.PRO_NOMB,
                p.TIP_CODI, t.TIP_NOMB,
                p.PRO_ACTI,
                p.PRO_CO01, COALESCE(s.SIS_NOMB, '') as SIS_NOMB,
                p.PRO_CO02, COALESCE(sub.SUB_NOMB, '') as SUB_NOMB,
                p.UNI_CODI, u.UNI_NOMB,
                p.AUD_FCRE, p.AUD_UFAC
            FROM IN_PRODU p
            INNER JOIN IN_TIPRO t ON p.TIP_CODI = t.TIP_CODI
            INNER JOIN IN_UNIME u ON p.UNI_CODI = u.UNI_CODI
            LEFT JOIN IN_SISTE s ON LEFT(p.PRO_CO01, 1) = s.SIS_CODI
            LEFT JOIN IN_SUBSI sub ON p.PRO_CO02 = sub.SUB_CODI
            WHERE p.PRO_CODI = %s
            AND p.EMP_CODI = %s
            AND LEFT(p.PRO_CO01, 1) = '7'
            AND LEN(p.PRO_CO02) = 5
            AND LEN(p.PRO_CODI) >= 10
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (codigo, company_code))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                product = self._map_row_to_dict(row, cursor.description)
                
                if self.logger:
                    self.logger.info(f'Product found', codigo=codigo)
                
                return product
                
        except pytds.Timeout:
            if self.logger:
                self.logger.error('Query timeout')
            raise TimeoutError('Tiempo de espera agotado al consultar producto')
        except pytds.DatabaseError as e:
            if self.logger:
                self.logger.error(f'Database query error: {e}')
            raise DatabaseQueryError('Error al ejecutar consulta de producto')
    
    def _map_row_to_dict(self, row: tuple, description: list) -> dict:
        """
        Mapea tupla SQL a diccionario.
        
        Args:
            row: Tupla con valores de la fila
            description: cursor.description con nombres de columnas
        
        Returns:
            dict con columna: valor
        """
        return {
            description[i][0]: row[i]
            for i in range(len(row))
        }
