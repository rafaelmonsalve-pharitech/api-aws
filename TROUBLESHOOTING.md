# Guía de Troubleshooting - API Seven Arkeo Fleet

Esta guía proporciona soluciones a problemas comunes que pueden ocurrir durante el desarrollo, testing y operación de la API.

## Tabla de Contenidos

1. [Errores de Deployment](#errores-de-deployment)
2. [Errores de Conexión](#errores-de-conexión)
3. [Errores de Autenticación](#errores-de-autenticación)
4. [Problemas de Performance](#problemas-de-performance)
5. [Errores de Paginación](#errores-de-paginación)
6. [Problemas de Logging](#problemas-de-logging)

---

## Errores de Deployment

### SAM Build Falla

**Síntoma**: `sam build` falla con error de dependencias

**Soluciones**:

```bash
# Limpiar caché de SAM
rm -rf .aws-sam/

# Reconstruir con contenedor Docker
sam build --use-container

# Si falla pytds, verificar que el Layer esté disponible
aws lambda get-layer-version \
  --layer-name pytds_layer \
  --version-number 1 \
  --region us-east-2
```

### SAM Deploy Falla por VPC

**Síntoma**: Error "Lambda was unable to configure your environment variables"

**Causa**: Lambda no puede acceder a Secrets Manager desde la VPC

**Soluciones**:

1. Verificar VPC Endpoint para Secrets Manager existe
2. Verificar Security Group permite tráfico HTTPS saliente
3. Verificar subnet tiene ruta a NAT Gateway o VPC Endpoint

```bash
# Verificar VPC endpoints
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=vpc-01c7cedbf7ffc4bda" \
  --region us-east-2
```

### Timeout durante Deployment

**Síntoma**: CloudFormation stack queda en `CREATE_IN_PROGRESS` por largo tiempo

**Causa**: Lambda está creando ENI (Elastic Network Interface) en VPC

**Solución**: Esperar pacientemente (puede tomar 5-10 minutos). Si excede 15 minutos:

```bash
# Cancelar el stack
aws cloudformation cancel-update-stack \
  --stack-name tv-prd-seven-arkeo-fleet \
  --region us-east-2

# Verificar estado del stack
aws cloudformation describe-stacks \
  --stack-name tv-prd-seven-arkeo-fleet \
  --region us-east-2
```

---

## Errores de Conexión

### HTTP 503 - Service Unavailable

**Síntoma**: API retorna 503 con mensaje "Servicio de base de datos no disponible temporalmente"

**Posibles Causas**:

1. **Security Group incorrecto**
   ```bash
   # Verificar reglas del Security Group
   aws ec2 describe-security-groups \
     --group-ids sg-0b5608dadf9ea4c28 \
     --region us-east-2
   
   # Debe tener regla outbound TCP 1433
   ```

2. **SQL Server no accesible**
   - Verificar que SQL Server esté ejecutándose: `10.125.18.16:1433`
   - Hacer ping desde instancia EC2 en la misma subnet
   - Verificar firewall del servidor SQL permite conexiones desde la subnet

3. **Credenciales incorrectas en Secrets Manager**
   ```bash
   # Verificar secret existe
   aws secretsmanager get-secret-value \
     --secret-id seven/db/credentials \
     --region us-east-2
   
   # Probar conexión con las credenciales
   ```

4. **Lambda no está en la subnet correcta**
   - Verificar Lambda configuration incluye `subnet-0fbaebb0a7171c1f0`

### HTTP 504 - Gateway Timeout

**Síntoma**: API retorna 504 después de ~30 segundos

**Posibles Causas**:

1. **Query SQL muy lento**
   - Verificar índices en tablas: `PRO_CODI`, `AUD_UFAC`, `EMP_CODI`
   - Ejecutar query directamente en SQL Server para medir tiempo
   - Considerar agregar índices compuestos

   ```sql
   -- Índices recomendados
   CREATE INDEX idx_produ_codi ON IN_PRODU(PRO_CODI ASC);
   CREATE INDEX idx_produ_audit ON IN_PRODU(AUD_UFAC, PRO_CODI);
   CREATE INDEX idx_produ_empresa ON IN_PRODU(EMP_CODI, PRO_CODI);
   ```

2. **Connection pool saturado**
   - Revisar CloudWatch Metric `DatabaseConnectionTime`
   - Considerar aumentar `max_pool_size` en `db_connector.py`

3. **Lambda timeout muy bajo**
   - Verificar timeout Lambda está configurado en 30 segundos
   - Considerar aumentar a 45-60 segundos si queries legítimamente lentos

### Connection Refused

**Síntoma**: Error en logs "Connection refused" o "Network unreachable"

**Solución**:

```bash
# 1. Verificar Lambda está en VPC correcta
aws lambda get-function-configuration \
  --function-name tv-prd-lambda-seven-arkeo-fleet \
  --region us-east-2 \
  --query 'VpcConfig'

# 2. Verificar ruta de tabla de enrutamiento de la subnet
aws ec2 describe-route-tables \
  --filters "Name=association.subnet-id,Values=subnet-0fbaebb0a7171c1f0" \
  --region us-east-2

# 3. Probar conectividad desde EC2 en misma subnet
# Lanzar instancia EC2 temporal en subnet-0fbaebb0a7171c1f0
# Ejecutar: telnet 10.125.18.16 1433
```

---

## Errores de Autenticación

### HTTP 401 - Unauthorized

**Síntoma**: API retorna 401 con mensaje "API Key inválida"

**Causas y Soluciones**:

1. **Header faltante o incorrecto**
   ```bash
   # Correcto
   curl -H "X-API-Key: LXH61UdMdT4w2aDWgfZj016PKKhAGsp45FMmgC12" \
     https://api.phari.tech/api/v1/seven/products
   
   # Incorrecto (sin header)
   curl https://api.phari.tech/api/v1/seven/products
   
   # Incorrecto (header mal escrito)
   curl -H "X-Api-Key: ..." # Debe ser X-API-Key (mayúsculas)
   ```

2. **API Key no está en Secrets Manager**
   ```bash
   # Verificar keys válidas
   aws secretsmanager get-secret-value \
     --secret-id seven/api/keys \
     --region us-east-2 \
     --query 'SecretString' \
     --output text | jq '.valid_keys'
   
   # Agregar nueva key
   aws secretsmanager update-secret \
     --secret-id seven/api/keys \
     --secret-string '{"valid_keys":["key1","key2","key3"]}' \
     --region us-east-2
   ```

3. **Lambda no tiene permisos para leer Secrets Manager**
   - Verificar IAM role de Lambda tiene policy `SecretsManagerReadPolicy`

### HTTP 429 - Too Many Requests

**Síntoma**: API retorna 429 con mensaje "Límite de tasa excedido"

**Causa**: Más de 1000 peticiones por minuto desde el mismo API Key

**Soluciones**:

1. **Implementar backoff exponencial en el cliente**
   ```python
   import time
   import requests
   
   def call_api_with_retry(url, headers, max_retries=3):
       for i in range(max_retries):
           response = requests.get(url, headers=headers)
           if response.status_code == 429:
               wait_time = 2 ** i  # 1, 2, 4 segundos
               time.sleep(wait_time)
               continue
           return response
       return response
   ```

2. **Distribuir carga entre múltiples API Keys**

3. **Contactar administrador para aumentar límite**

---

## Problemas de Performance

### Respuestas Lentas (>2 segundos)

**Síntoma**: `ResponseTime` metric en CloudWatch consistentemente >2000ms

**Diagnóstico**:

```bash
# Revisar métricas
aws cloudwatch get-metric-statistics \
  --namespace Seven/ArkeoFleet \
  --metric-name ResponseTime \
  --dimensions Name=Endpoint,Value=products \
  --start-time 2024-10-16T00:00:00Z \
  --end-time 2024-10-16T23:59:59Z \
  --period 300 \
  --statistics Average,Maximum \
  --region us-east-2
```

**Soluciones**:

1. **Optimizar queries SQL**
   - Agregar índices (ver sección Gateway Timeout)
   - Reducir JOINs innecesarios
   - Usar `SELECT` específico en lugar de `SELECT *`

2. **Reducir pageSize**
   - Default es 100, considerar reducir a 50
   - Cliente puede hacer múltiples peticiones paginadas

3. **Implementar caché**
   - Agregar Redis/ElastiCache para resultados frecuentes
   - Cachear por 5-10 minutos

### High Database Connection Time

**Síntoma**: `DatabaseConnectionTime` metric >5000ms

**Causa**: Connection pool lleno o latencia de red alta

**Soluciones**:

1. **Aumentar connection pool size**
   ```python
   # En db_connector.py
   self.max_pool_size = 10  # Aumentar de 5 a 10
   ```

2. **Verificar latencia de red**
   ```bash
   # Desde Lambda, agregar logging de tiempo de conexión
   # Revisar CloudWatch Logs para patterns
   ```

3. **Considerar RDS Proxy** (si SQL Server en AWS RDS en el futuro)

---

## Errores de Paginación

### Productos Duplicados al Paginar

**Síntoma**: Al usar cursor, algunos productos aparecen dos veces

**Causa**: Productos insertados/actualizados durante la paginación cambian el orden

**Soluciones**:

1. **Usar sincronización delta con snapshot**
   ```bash
   # Cliente guarda timestamp de inicio
   START_TIME="2024-10-16T10:00:00-05:00"
   
   # Primera petición
   curl "...products?updatedSince=$START_TIME&pageSize=100"
   
   # Siguientes peticiones usan mismo updatedSince
   curl "...products?updatedSince=$START_TIME&pageSize=100&cursor=..."
   ```

2. **Reducir ventana de tiempo entre peticiones**

3. **Documentar comportamiento eventual consistency**

### Cursor Inválido o Expirado

**Síntoma**: HTTP 400 con mensaje "El cursor proporcionado es inválido o ha expirado"

**Causas**:

1. **Cursor no es base64 válido**
   - Verificar que no está corrupto durante transmisión
   - No modificar el cursor manualmente

2. **Producto referenciado por cursor fue eliminado**
   - Obtener nuevo cursor desde primera página

**Solución**:

```bash
# Decodificar cursor para debugging
echo "N1NVQlNNMDAxQQ==" | base64 --decode
# Output: 7SUBSM001A

# Reiniciar paginación sin cursor
curl "...products?pageSize=100"
```

---

## Problemas de Logging

### Logs No Aparecen en CloudWatch

**Síntoma**: Después de invocar Lambda, no hay logs en CloudWatch

**Causas y Soluciones**:

1. **Lambda no tiene permisos para escribir logs**
   ```bash
   # Verificar IAM role tiene policy
   aws iam list-attached-role-policies \
     --role-name tv-prd-lambda-seven-arkeo-fleet-role \
     --region us-east-2
   
   # Debe incluir: CloudWatchLogsFullAccess o policy custom con:
   # - logs:CreateLogGroup
   # - logs:CreateLogStream
   # - logs:PutLogEvents
   ```

2. **Log Group no existe**
   ```bash
   # Crear manualmente si necesario
   aws logs create-log-group \
     --log-group-name /aws/lambda/tv-prd-lambda-seven-arkeo-fleet \
     --region us-east-2
   ```

3. **VPC no tiene endpoint para CloudWatch Logs**
   - Subnet privada necesita VPC Endpoint o NAT Gateway
   - Verificar VPC endpoint para `logs.us-east-2.amazonaws.com`

### TraceId No Aparece en Logs

**Síntoma**: Logs no incluyen campo `traceId`

**Causa**: Logger no está usando structured logging correctamente

**Solución**:

```python
# Verificar en logger.py que se incluye traceId
logger.info("Request started", extra={
    "traceId": trace_id,
    "method": method,
    "path": path
})
```

---

## Comandos Útiles de Debugging

### Ver Logs en Tiempo Real

```bash
# Tail logs de Lambda
sam logs --name tv-prd-lambda-seven-arkeo-fleet --tail --region us-east-2

# Filtrar por traceId específico
aws logs filter-log-events \
  --log-group-name /aws/lambda/tv-prd-lambda-seven-arkeo-fleet \
  --filter-pattern "550e8400-e29b-41d4-a716-446655440000" \
  --region us-east-2
```

### Invocar Lambda con Evento Custom

```bash
# Crear evento de prueba
cat > test-event.json <<EOF
{
  "httpMethod": "GET",
  "path": "/api/v1/seven/products",
  "headers": {
    "X-API-Key": "LXH61UdMdT4w2aDWgfZj016PKKhAGsp45FMmgC12"
  },
  "queryStringParameters": {
    "pageSize": "10"
  }
}
EOF

# Invocar localmente
sam local invoke SevenArkeoFleetFunction --event test-event.json

# Invocar en AWS
aws lambda invoke \
  --function-name tv-prd-lambda-seven-arkeo-fleet \
  --payload file://test-event.json \
  --region us-east-2 \
  output.json
```

### Verificar Métricas

```bash
# Listar métricas disponibles
aws cloudwatch list-metrics \
  --namespace Seven/ArkeoFleet \
  --region us-east-2

# Ver estadísticas de una métrica
aws cloudwatch get-metric-statistics \
  --namespace Seven/ArkeoFleet \
  --metric-name RequestCount \
  --start-time 2024-10-16T00:00:00Z \
  --end-time 2024-10-16T23:59:59Z \
  --period 3600 \
  --statistics Sum \
  --region us-east-2
```

---

## Contacto de Soporte

Si ninguna de estas soluciones resuelve tu problema:

- **Email**: soporte@tecnovia.com
- **Slack**: #team-arkeo-fleet
- **JIRA**: Proyecto ARKEO - Crear ticket con etiqueta `api-seven`

Al reportar un problema, incluye:
1. TraceId de la petición fallida
2. Timestamp exacto del error
3. Request completo (URL, headers, body)
4. Response recibido
5. Logs relevantes de CloudWatch
