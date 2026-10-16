# API Seven Arkeo Fleet

API REST serverless para integración entre ERP Seven y ARKEO Fleet, desplegada en AWS Lambda con Python 3.11.

## Descripción

La API proporciona endpoints para consulta de productos del sistema Seven con capacidades de:
- Autenticación mediante API Key
- Paginación cursor-based eficiente
- Filtrado por empresa, estado y fecha de actualización
- Sincronización incremental mediante patrón delta
- Respuestas JSON en español con estructura estándar

## Arquitectura

- **Runtime**: Python 3.11
- **Compute**: AWS Lambda (serverless)
- **API Gateway**: REST API Regional
- **Database**: SQL Server Seven (on-premise) - 10.125.18.16:1433
- **VPC**: vpc-01c7cedbf7ffc4bda (conectividad privada)
- **Seguridad**: AWS Secrets Manager para credenciales
- **Observabilidad**: CloudWatch Logs, Metrics, Alarms & X-Ray Tracing

## Nomenclatura de Recursos

Todos los recursos AWS siguen el patrón corporativo: `tv-prd-{tipo}-seven-arkeo-fleet`

- **Empresa**: tv (TecnoVía)
- **Ambiente**: prd (Producción)
- **Lambda Function**: `tv-prd-lambda-seven-arkeo-fleet`
- **API Gateway**: `tv-prd-api-seven-arkeo-fleet`
- **Secrets**: `seven/db/credentials`, `seven/api/keys`

## Requisitos Previos

### Herramientas Locales

- **Python**: 3.11 o superior
- **AWS CLI**: Configurado con credenciales apropiadas
- **SAM CLI**: 1.100.0 o superior
- **Git**: Para control de versiones

### Permisos AWS

- Acceso a Secrets Manager para obtener credenciales
- Permisos de lectura en VPC (vpc-01c7cedbf7ffc4bda)
- Acceso al Lambda Layer pytds (arn:aws:lambda:us-east-2:481133585213:layer:pytds_layer:1)

### Conectividad

- Acceso a la VPC privada para comunicación con SQL Server Seven
- Security Group sg-0b5608dadf9ea4c28 configurado para tráfico saliente puerto 1433

## Setup Local

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd tv-prd-api-seven-arkeo-fleet
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
# Dependencias de producción
pip install -r requirements.txt

# Dependencias de desarrollo (testing)
pip install -r requirements-dev.txt
```

### 4. Configurar Variables de Entorno (Opcional para testing local)

Crear archivo `.env` (no commitearlo):

```env
ENVIRONMENT=local
REGION=us-east-2
DB_HOST=10.125.18.16
DB_PORT=1433
DB_NAME=seven_db
DB_SECRET_NAME=seven/db/credentials
API_KEY_SECRET_NAME=seven/api/keys
```

## Testing Local

### Ejecutar Unit Tests

```bash
# Ejecutar todos los tests unitarios
pytest tests/unit/ -v

# Con reporte de cobertura
pytest tests/unit/ -v --cov=src --cov-report=html

# Ver reporte HTML de cobertura
# Abrir htmlcov/index.html en el navegador
```

### Ejecutar Integration Tests

```bash
pytest tests/integration/ -v
```

### Invocar Lambda Localmente con SAM

```bash
# Construir la función Lambda
sam build

# Invocar con evento de prueba
sam local invoke SevenArkeoFleetFunction --event events/list_products.json

# Iniciar API local para pruebas
sam local start-api
# La API estará disponible en http://127.0.0.1:3000
```

## Deployment

### Build

Construir la aplicación SAM:

```bash
sam build --use-container
```

### Validar Template

```bash
sam validate
```

### Deploy a Staging

```bash
sam deploy --config-env staging --guided
```

### Deploy a Producción

```bash
# Revisar cambios primero
sam deploy --config-env production --no-execute-changeset

# Confirmar y desplegar
sam deploy --config-env production
```

## Endpoints

### Base URL Producción
```
https://api.phari.tech/api/v1/seven
```

### 1. Listado de Productos

```http
GET /products
```

**Query Parameters:**
- `companyCode` (string, opcional): Código de empresa
- `status` (string, opcional): Estado del producto (ACTIVO/INACTIVO)
- `pageSize` (integer, opcional): Registros por página (1-500, default: 100)
- `cursor` (string, opcional): Cursor base64 para paginación
- `updatedSince` (string, opcional): Fecha ISO 8601 para filtrado incremental

**Headers:**
- `X-API-Key` (requerido): API Key de autenticación

**Ejemplo:**
```bash
curl -H "X-API-Key: LXH61UdMdT4w2aDWgfZj016PKKhAGsp45FMmgC12" \
  "https://api.phari.tech/api/v1/seven/products?companyCode=001&pageSize=50"
```

### 2. Detalle de Producto

```http
GET /products/{codigo}
```

**Path Parameters:**
- `codigo` (string, requerido): Código del producto

**Query Parameters:**
- `companyCode` (string, requerido): Código de empresa

**Headers:**
- `X-API-Key` (requerido): API Key de autenticación

**Ejemplo:**
```bash
curl -H "X-API-Key: LXH61UdMdT4w2aDWgfZj016PKKhAGsp45FMmgC12" \
  "https://api.phari.tech/api/v1/seven/products/7SUBSM001A?companyCode=001"
```

### 3. Cambios Delta

```http
GET /products/changes
```

**Query Parameters:**
- `updatedSince` (string, requerido): Fecha ISO 8601 (ej: 2024-01-15T10:30:00-05:00)
- `companyCode` (string, opcional): Código de empresa
- `status` (string, opcional): Estado del producto (ACTIVO/INACTIVO)
- `pageSize` (integer, opcional): Registros por página (1-500, default: 100)
- `cursor` (string, opcional): Cursor base64 para paginación

**Headers:**
- `X-API-Key` (requerido): API Key de autenticación

**Ejemplo:**
```bash
curl -H "X-API-Key: LXH61UdMdT4w2aDWgfZj016PKKhAGsp45FMmgC12" \
  "https://api.phari.tech/api/v1/seven/products/changes?updatedSince=2024-01-15T10:30:00-05:00"
```

### 4. Documentación OpenAPI

```http
GET /openapi.json
```

Retorna la especificación OpenAPI 3.0.3 completa de la API.

## Estructura de Respuesta

### Respuesta Exitosa

```json
{
  "datos": [
    {
      "codigoEmpresa": "001",
      "codigoProducto": "7SUBSM001A",
      "nombreProducto": "Producto de ejemplo",
      "codigoTipo": "TIP001",
      "nombreTipo": "Tipo de producto",
      "estado": "ACTIVO",
      "codigoSistema": "7",
      "nombreSistema": "ARKEO FLEET",
      "codigoSubsistema": "SUBSM",
      "nombreSubsistema": "Subsistema Mantenimiento",
      "codigoUnidad": "UND",
      "nombreUnidad": "Unidad",
      "trabajoRepuesto": true,
      "fechaCreacion": "2024-01-15T10:30:00-05:00",
      "fechaActualizacion": "2024-01-20T15:45:00-05:00"
    }
  ],
  "paginacion": {
    "totalPagina": 100,
    "siguienteCursor": "N1NVQlNNMDAxQQ==",
    "tieneMasPaginas": true
  },
  "traceId": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Respuesta de Error

```json
{
  "error": "400",
  "mensaje": "Parámetro obligatorio 'companyCode' no proporcionado",
  "traceId": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Códigos HTTP

- **200 OK**: Petición exitosa
- **400 Bad Request**: Parámetros inválidos o faltantes
- **401 Unauthorized**: API Key inválida o ausente
- **404 Not Found**: Producto no encontrado
- **429 Too Many Requests**: Rate limit excedido (>1000 req/min)
- **500 Internal Server Error**: Error interno del servidor
- **503 Service Unavailable**: Base de datos no disponible
- **504 Gateway Timeout**: Timeout de conexión o query

## Documentación

- **OpenAPI Spec**: `/api/v1/seven/openapi.json`
- **Swagger UI**: Disponible en bucket S3 de documentación
- **Postman Collection**: `postman/seven-arkeo-api.postman_collection.json`

## Monitoreo

### CloudWatch Logs

- Lambda Logs: `/aws/lambda/tv-prd-lambda-seven-arkeo-fleet`
- API Gateway Logs: `/aws/apigateway/tv-prd-api-seven-arkeo-fleet`

### CloudWatch Metrics (Namespace: Seven/ArkeoFleet)

- `RequestCount`: Número de peticiones por endpoint
- `ErrorCount`: Número de errores por tipo
- `ResponseTime`: Tiempo de respuesta en ms
- `DatabaseConnectionTime`: Tiempo de conexión a DB en ms

### CloudWatch Alarms

- `SevenArkeoFleet-HighErrorRate`: Alerta cuando error rate > 5% en 5 minutos
- `SevenArkeoFleet-HighLatency`: Alerta cuando response time > 5000ms
- `SevenArkeoFleet-SlowDatabase`: Alerta cuando DB connection time > 10000ms

### Dashboard

CloudWatch Dashboard `Seven-Arkeo-Fleet-Monitoring` con widgets para todas las métricas clave.

## Troubleshooting

### Lambda Timeout (504)

**Síntoma**: Respuestas HTTP 504 Gateway Timeout

**Posibles Causas**:
- Query SQL muy lento (falta índice en PRO_CODI, AUD_UFAC)
- Pagesize muy grande (>500)
- Connection pooling saturado

**Soluciones**:
1. Verificar índices SQL: `CREATE INDEX idx_produ_codi ON IN_PRODU(PRO_CODI ASC)`
2. Reducir pageSize en la petición
3. Revisar CloudWatch Metric `DatabaseConnectionTime`

### Connection Refused (503)

**Síntoma**: Respuestas HTTP 503 Service Unavailable

**Posibles Causas**:
- Security Group no permite tráfico saliente puerto 1433
- VPC config incorrecta
- SQL Server no accesible desde la subnet

**Soluciones**:
1. Verificar Security Group sg-0b5608dadf9ea4c28 tiene regla outbound TCP 1433
2. Verificar Lambda está en subnet correcta (subnet-0fbaebb0a7171c1f0)
3. Hacer ping al servidor SQL desde otra instancia EC2 en la misma subnet

### Rate Limit Exceeded (429)

**Síntoma**: Respuestas HTTP 429 Too Many Requests

**Causa**: Más de 1000 peticiones por minuto desde el mismo API Key

**Solución**:
1. Implementar backoff exponencial en el cliente
2. Distribuir carga entre múltiples API Keys si es posible
3. Contactar al administrador para aumentar el límite

### Paginación Inconsistente

**Síntoma**: Productos duplicados o faltantes al paginar

**Causa**: Cambios en la base de datos durante la paginación

**Solución**:
- Usar parámetro `updatedSince` para obtener snapshot consistente
- Implementar ventana de tiempo fija en el cliente

## Soporte

Para reportar issues o solicitar soporte:
- **Email**: soporte@tecnovia.com
- **Slack**: #team-arkeo-fleet
- **JIRA**: Proyecto ARKEO

## Licencia

Propiedad de TecnoVía - Uso interno únicamente

---

**Versión**: 1.0.0  
**Última actualización**: Octubre 2024  
**Responsable**: Equipo DevOps TecnoVía
