# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2024-10-16

### Añadido

#### Infraestructura
- Configuración AWS SAM con Lambda Python 3.11
- API Gateway REST con 4 endpoints principales
- Integración VPC privada (vpc-01c7cedbf7ffc4bda)
- Lambda Layer para pytds driver
- CloudWatch Logs, Metrics y Alarms
- X-Ray tracing activo
- Secrets Manager para credenciales

#### Endpoints
- `GET /api/v1/seven/products` - Listado paginado de productos
- `GET /api/v1/seven/products/{codigo}` - Detalle de producto específico
- `GET /api/v1/seven/products/changes` - Sincronización delta incremental
- `GET /api/v1/seven/openapi.json` - Especificación OpenAPI 3.0.3

#### Características
- Autenticación via API Key (header X-API-Key)
- Paginación cursor-based con límite configurable (1-500)
- Filtrado por empresa, estado (ACTIVO/INACTIVO)
- Sincronización incremental con parámetro `updatedSince` (ISO 8601)
- Respuestas JSON en español con estructura estándar
- Rate limiting: 1000 peticiones/minuto por API Key
- Manejo de errores completo con mensajes descriptivos
- Logging estructurado con traceId UUID
- Métricas custom en CloudWatch

#### Documentación
- Documentación OpenAPI 3.0.3 completa
- Colección Postman con 8 tests de validación
- README.md con instrucciones de setup y deployment
- Ejemplos de uso con curl

#### Testing
- Configuración pytest con cobertura de código
- Unit tests para módulos de utilidades
- Integration tests para endpoints
- Eventos de prueba para SAM local

### Seguridad
- Credenciales almacenadas en AWS Secrets Manager
- Validación de entrada para prevenir SQL injection
- Sanitización de mensajes de error
- Comunicación VPC privada con SQL Server
- Security Group configurado para puerto 1433 únicamente

### Performance
- Connection pooling para SQL Server (máximo 5 conexiones)
- Timeout de conexión: 10 segundos
- Timeout de query: 30 segundos
- Timeout Lambda: 30 segundos
- Memory: 512 MB

### Nomenclatura Corporativa
- Empresa: `tv` (TecnoVía)
- Ambiente: `prd` (Producción)
- Patrón: `tv-prd-{tipo}-seven-arkeo-fleet`

---

## [Unreleased]

### Planeado
- Caché distribuida con Redis/ElastiCache
- Webhooks para notificaciones de cambios
- Soporte para múltiples formatos (CSV, XML)
- Dashboard personalizado en QuickSight
