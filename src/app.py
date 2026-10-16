"""
Lambda Handler Principal - API Seven Arkeo Fleet

Handler principal que orquesta autenticación, routing, consultas y respuestas.
Requirements: 2.1-2.12, 3.1-3.10, 4.1-4.12, 8.1-8.17, 12.1-12.18
"""

import json
import uuid
import boto3
from typing import Optional

# Importar módulos locales
from src.logger import StructuredLogger
from src.metrics import MetricsEmitter
from src.error_handler import ErrorHandler, ValidationError, NotFoundError
from src.auth import AuthValidator
from src.pagination import PaginationEngine, InvalidCursorError
from src.delta_sync import DeltaSync, InvalidDateFormatError, FutureDateError
from src.response_formatter import ResponseFormatter
from src.db_connector import SQLServerConnector
from src.products_repository import ProductsRepository


def lambda_handler(event: dict, context):
    """
    Punto de entrada Lambda para API Seven Arkeo Fleet.
    
    Args:
        event: API Gateway Proxy event
        context: Lambda context
    
    Returns:
        dict con statusCode, headers, body
    """
    # Generar traceId único
    trace_id = str(uuid.uuid4())
    
    # Inicializar logger
    logger = StructuredLogger(trace_id)
    logger.info('Lambda invocation started', method=event.get('httpMethod'), path=event.get('path'))
    
    # Inicializar clientes AWS
    secrets_client = boto3.client('secretsmanager')
    cloudwatch_client = boto3.client('cloudwatch')
    
    # Inicializar componentes
    metrics = MetricsEmitter(cloudwatch_client)
    db_connector = None
    
    try:
        # Extraer información del evento
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        headers = event.get('headers', {})
        query_params = event.get('queryStringParameters') or {}
        path_params = event.get('pathParameters') or {}
        source_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
        
        # Registrar inicio
        start_time = context.get_remaining_time_in_millis() if hasattr(context, 'get_remaining_time_in_millis') else 30000
        
        # Autenticación
        api_key = headers.get('X-API-Key') or headers.get('x-api-key')
        auth_validator = AuthValidator(secrets_client, logger)
        auth_result = auth_validator.validate_api_key(api_key, source_ip, trace_id)
        
        if not auth_result.is_valid:
            metrics.record_error('authentication', str(auth_result.status_code))
            metrics.flush()
            return ResponseFormatter.format_error_response(
                auth_result.status_code,
                str(auth_result.status_code),
                auth_result.error_message,
                trace_id
            )
        
        # Routing por endpoint
        if path == '/api/v1/seven/products' and http_method == 'GET':
            endpoint_name = 'products'
            response = handle_list_products(query_params, trace_id, logger, metrics, secrets_client)
        
        elif path.startswith('/api/v1/seven/products/') and path.endswith('/changes') and http_method == 'GET':
            endpoint_name = 'products-changes'
            response = handle_product_changes(query_params, trace_id, logger, metrics, secrets_client)
        
        elif path.startswith('/api/v1/seven/products/') and http_method == 'GET':
            endpoint_name = 'products-detail'
            codigo = path_params.get('codigo')
            response = handle_product_detail(codigo, query_params, trace_id, logger, metrics, secrets_client)
        
        elif path == '/api/v1/seven/openapi.json' and http_method == 'GET':
            endpoint_name = 'openapi'
            response = handle_openapi_spec(trace_id)
        
        else:
            metrics.record_error('unknown', '404')
            metrics.flush()
            return ResponseFormatter.format_error_response(404, '404', 'Endpoint no encontrado', trace_id)
        
        # Registrar métricas de éxito
        metrics.record_request(endpoint_name)
        
        # Calcular tiempo de respuesta
        if hasattr(context, 'get_remaining_time_in_millis'):
            elapsed = start_time - context.get_remaining_time_in_millis()
            metrics.record_response_time(endpoint_name, elapsed)
        
        metrics.flush()
        
        logger.info('Request completed successfully', status_code=response.get('statusCode'))
        return response
        
    except Exception as e:
        logger.error(f'Unhandled exception: {str(e)}')
        metrics.record_error('internal', '500')
        metrics.flush()
        return ErrorHandler.handle_exception(e, trace_id)


def handle_list_products(query_params: dict, trace_id: str, logger, metrics, secrets_client) -> dict:
    """
    Maneja GET /api/v1/seven/products
    
    Args:
        query_params: Query string parameters
        trace_id: UUID de correlación
        logger: StructuredLogger
        metrics: MetricsEmitter
        secrets_client: boto3 Secrets Manager client
    
    Returns:
        dict con respuesta HTTP
    """
    # Extraer y validar parámetros
    company_code = query_params.get('companyCode')
    status = query_params.get('status')
    updated_since_str = query_params.get('updatedSince')
    page_size_str = query_params.get('pageSize', str(PaginationEngine.DEFAULT_PAGE_SIZE))
    cursor_encoded = query_params.get('cursor')
    
    # Validar status si existe
    if status and status not in ['ACTIVO', 'INACTIVO']:
        raise ValidationError("Valor de 'status' inválido. Valores permitidos: ACTIVO, INACTIVO")
    
    # Validar y parsear page_size
    page_size = PaginationEngine.validate_page_size(page_size_str)
    
    # Decodificar cursor si existe
    cursor = None
    if cursor_encoded:
        try:
            cursor = PaginationEngine.decode_cursor(cursor_encoded)
        except InvalidCursorError:
            raise ValidationError('El cursor proporcionado es inválido o ha expirado')
    
    # Parsear updated_since si existe
    updated_since_sql = None
    if updated_since_str:
        dt = DeltaSync.parse_updated_since(updated_since_str)
        DeltaSync.validate_not_future(dt)
        updated_since_sql = DeltaSync.to_sql_datetime(dt)
    
    # Conectar a base de datos
    db_connector = SQLServerConnector(secrets_client, logger)
    conn = db_connector.get_connection()
    
    try:
        # Consultar productos
        repo = ProductsRepository(conn, logger)
        products_raw, has_more = repo.get_products(
            company_code=company_code,
            status=status,
            updated_since=updated_since_sql,
            cursor=cursor,
            page_size=page_size
        )
        
        # Mapear a formato JSON español
        products = [ResponseFormatter.map_product_fields(row) for row in products_raw]
        
        # Construir objeto paginación
        pagination = PaginationEngine.build_pagination_object(products, page_size, has_more)
        
        # Formatear respuesta
        return ResponseFormatter.format_success_response(products, pagination, trace_id)
        
    finally:
        db_connector.release_connection(conn)
        db_connector.close_all()


def handle_product_detail(codigo: Optional[str], query_params: dict, trace_id: str, logger, metrics, secrets_client) -> dict:
    """
    Maneja GET /api/v1/seven/products/{codigo}
    """
    # Validar parámetros
    if not codigo:
        raise ValidationError("Parámetro obligatorio 'codigo' no proporcionado")
    
    company_code = query_params.get('companyCode')
    if not company_code:
        raise ValidationError("Parámetro obligatorio 'companyCode' no proporcionado")
    
    # Validar formato de código (solo alfanuméricos y guiones)
    if not all(c.isalnum() or c == '-' for c in codigo):
        raise ValidationError("El parámetro 'codigo' contiene caracteres inválidos")
    
    # Conectar a base de datos
    db_connector = SQLServerConnector(secrets_client, logger)
    conn = db_connector.get_connection()
    
    try:
        # Consultar producto
        repo = ProductsRepository(conn, logger)
        product_raw = repo.get_product_by_code(codigo, company_code)
        
        if not product_raw:
            raise NotFoundError('Producto no encontrado')
        
        # Mapear a formato JSON español
        product = ResponseFormatter.map_product_fields(product_raw)
        
        # Paginación para un solo producto
        pagination = {
            'totalPagina': 1,
            'siguienteCursor': None,
            'tieneMasPaginas': False
        }
        
        # Formatear respuesta
        return ResponseFormatter.format_success_response([product], pagination, trace_id)
        
    finally:
        db_connector.release_connection(conn)
        db_connector.close_all()

def handle_product_changes(query_params: dict, trace_id: str, logger, metrics, secrets_client) -> dict:
    """
    Maneja GET /api/v1/seven/products/changes
    
    Args:
        query_params: Query string parameters
        trace_id: UUID de correlación
        logger: StructuredLogger
        metrics: MetricsEmitter
        secrets_client: boto3 Secrets Manager client
    
    Returns:
        dict con respuesta HTTP
    """
    # Extraer parámetros
    updated_since_str = query_params.get('updatedSince')
    company_code = query_params.get('companyCode')
    status = query_params.get('status')
    page_size_str = query_params.get('pageSize', str(PaginationEngine.DEFAULT_PAGE_SIZE))
    cursor_encoded = query_params.get('cursor')
    
    # Validar parámetro obligatorio updatedSince
    if not updated_since_str:
        raise ValidationError("Parámetro obligatorio 'updatedSince' no proporcionado")
    
    # Parsear y validar fecha
    try:
        dt = DeltaSync.parse_updated_since(updated_since_str)
        DeltaSync.validate_not_future(dt)
        updated_since_sql = DeltaSync.to_sql_datetime(dt)
    except InvalidDateFormatError as e:
        raise ValidationError(str(e))
    except FutureDateError as e:
        raise ValidationError(str(e))
    
    # Validar status si existe
    if status and status not in ['ACTIVO', 'INACTIVO']:
        raise ValidationError("Valor de 'status' inválido. Valores permitidos: ACTIVO, INACTIVO")
    
    # Validar page_size
    page_size = PaginationEngine.validate_page_size(page_size_str)
    
    # Decodificar cursor si existe
    cursor = None
    if cursor_encoded:
        try:
            cursor = PaginationEngine.decode_cursor(cursor_encoded)
        except InvalidCursorError:
            raise ValidationError('El cursor proporcionado es inválido o ha expirado')
    
    # Conectar a base de datos
    db_connector = SQLServerConnector(secrets_client, logger)
    conn = db_connector.get_connection()
    
    try:
        # Consultar productos con filtro de fecha
        repo = ProductsRepository(conn, logger)
        products_raw, has_more = repo.get_products(
            company_code=company_code,
            status=status,
            updated_since=updated_since_sql,
            cursor=cursor,
            page_size=page_size
        )
        
        # Mapear a formato JSON español
        products = [ResponseFormatter.map_product_fields(row) for row in products_raw]
        
        # Construir objeto paginación
        pagination = PaginationEngine.build_pagination_object(products, page_size, has_more)
        
        # Formatear respuesta
        return ResponseFormatter.format_success_response(products, pagination, trace_id)
        
    finally:
        db_connector.release_connection(conn)
        db_connector.close_all()


def handle_openapi_spec(trace_id: str) -> dict:
    """
    Maneja GET /api/v1/seven/openapi.json
    
    Retorna especificación OpenAPI 3.0.3 de la API.
    
    Args:
        trace_id: UUID de correlación
    
    Returns:
        dict con respuesta HTTP
    """
    # Especificación OpenAPI básica
    openapi_spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "API Seven Arkeo Fleet",
            "version": "1.0.0",
            "description": "API REST serverless para integración entre ERP Seven y ARKEO Fleet"
        },
        "servers": [
            {
                "url": "https://api.phari.tech/api/v1/seven",
                "description": "Servidor de producción"
            }
        ],
        "paths": {
            "/products": {
                "get": {
                    "summary": "Listado paginado de productos",
                    "parameters": [
                        {
                            "name": "companyCode",
                            "in": "query",
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "status",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["ACTIVO", "INACTIVO"]}
                        },
                        {
                            "name": "pageSize",
                            "in": "query",
                            "schema": {"type": "integer", "minimum": 1, "maximum": 500, "default": 100}
                        },
                        {
                            "name": "cursor",
                            "in": "query",
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Listado exitoso"},
                        "400": {"description": "Parámetros inválidos"},
                        "401": {"description": "No autorizado"}
                    }
                }
            },
            "/products/{codigo}": {
                "get": {
                    "summary": "Detalle de producto",
                    "parameters": [
                        {
                            "name": "codigo",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "companyCode",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Producto encontrado"},
                        "404": {"description": "Producto no encontrado"}
                    }
                }
            },
            "/products/changes": {
                "get": {
                    "summary": "Sincronización delta de productos",
                    "parameters": [
                        {
                            "name": "updatedSince",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "date-time"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Cambios obtenidos exitosamente"}
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                }
            }
        },
        "security": [
            {"ApiKeyAuth": []}
        ]
    }
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json; charset=utf-8'
        },
        'body': json.dumps(openapi_spec, ensure_ascii=False)
    }
