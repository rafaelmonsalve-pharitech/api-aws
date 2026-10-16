"""
Pagination Engine Module

Motor de paginación cursor-based para API Seven Arkeo Fleet.
Requirements: 2.7, 2.8, 2.10, 2.11, 2.13, 2.15, 8.4, 8.5, 8.6
"""

import base64
from typing import Optional


class InvalidCursorError(Exception):
    """Excepción para cursores inválidos o expirados."""
    pass


class PaginationEngine:
    """Motor de paginación cursor-based."""
    
    MAX_PAGE_SIZE = 500
    DEFAULT_PAGE_SIZE = 100
    
    @staticmethod
    def encode_cursor(value: str) -> str:
        """
        Codifica valor en base64 URL-safe.
        
        Args:
            value: String a codificar (típicamente PRO_CODI)
        
        Returns:
            String base64 URL-safe
        
        Example:
            >>> PaginationEngine.encode_cursor("7SUBSM001A")
            'N1NVQlNNMDAxQQ=='
        """
        encoded = base64.urlsafe_b64encode(value.encode('utf-8'))
        return encoded.decode('utf-8')
    
    @staticmethod
    def decode_cursor(cursor: str) -> str:
        """
        Decodifica cursor base64.
        
        Args:
            cursor: Cursor base64 a decodificar
        
        Returns:
            String decodificado
        
        Raises:
            InvalidCursorError: Si cursor es inválido o no es base64
        
        Example:
            >>> PaginationEngine.decode_cursor('N1NVQlNNMDAxQQ==')
            '7SUBSM001A'
        """
        try:
            decoded = base64.urlsafe_b64decode(cursor.encode('utf-8'))
            return decoded.decode('utf-8')
        except Exception as e:
            raise InvalidCursorError('El cursor proporcionado es inválido o ha expirado')
    
    @staticmethod
    def validate_page_size(page_size: any) -> int:
        """
        Valida y retorna pageSize como entero.
        
        Args:
            page_size: Valor a validar (puede ser str, int, etc.)
        
        Returns:
            int validado entre 1 y MAX_PAGE_SIZE (500)
        
        Raises:
            ValidationError: Si no es numérico o está fuera de rango
        
        Example:
            >>> PaginationEngine.validate_page_size(100)
            100
            >>> PaginationEngine.validate_page_size("50")
            50
            >>> PaginationEngine.validate_page_size(1000)  # Raises ValidationError
        """
        from src.error_handler import ValidationError
        
        # Intentar convertir a int
        try:
            size = int(page_size)
        except (ValueError, TypeError):
            raise ValidationError('El parámetro pageSize debe ser un número entero')
        
        # Validar rango
        if size < 1 or size > PaginationEngine.MAX_PAGE_SIZE:
            raise ValidationError(
                f'El parámetro pageSize debe estar entre 1 y {PaginationEngine.MAX_PAGE_SIZE}'
            )
        
        return size
    
    @staticmethod
    def build_pagination_object(
        products: list,
        requested_page_size: int,
        has_more: bool
    ) -> dict:
        """
        Construye objeto de paginación estándar.
        
        Args:
            products: Lista de productos retornados (ya mapeados a JSON)
            requested_page_size: Tamaño de página solicitado
            has_more: True si hay más resultados disponibles
        
        Returns:
            dict con estructura:
            {
                "totalPagina": int,           # Número de registros en esta página
                "siguienteCursor": str|None,  # Cursor base64 o None
                "tieneMasPaginas": bool       # True si hay más páginas
            }
        
        Example:
            >>> products = [{"codigoProducto": "7SUBSM001A"}, {"codigoProducto": "7SUBSM002B"}]
            >>> PaginationEngine.build_pagination_object(products, 100, True)
            {
                "totalPagina": 2,
                "siguienteCursor": "N1NVQlNNMDAyQg==",
                "tieneMasPaginas": True
            }
        """
        total_pagina = len(products)
        siguiente_cursor = None
        
        # Si hay más resultados y la página tiene productos
        if has_more and total_pagina > 0:
            # Obtener el codigoProducto del último producto
            last_product = products[-1]
            codigo_producto = last_product.get('codigoProducto')
            
            if codigo_producto:
                siguiente_cursor = PaginationEngine.encode_cursor(codigo_producto)
        
        return {
            'totalPagina': total_pagina,
            'siguienteCursor': siguiente_cursor,
            'tieneMasPaginas': has_more
        }
