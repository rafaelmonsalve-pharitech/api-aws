# Guía de Deployment - API Seven Arkeo Fleet

Esta guía detalla el proceso completo de deployment de la API desde el desarrollo local hasta producción.

## Tabla de Contenidos

1. [Pre-requisitos](#pre-requisitos)
2. [Preparación del Entorno](#preparación-del-entorno)
3. [Build y Validación](#build-y-validación)
4. [Deployment a Staging](#deployment-a-staging)
5. [Testing en Staging](#testing-en-staging)
6. [Deployment a Producción](#deployment-a-producción)
7. [Rollback](#rollback)
8. [Post-Deployment](#post-deployment)

---

## Pre-requisitos

### Credenciales AWS

Asegúrate de tener configuradas las credenciales AWS con los permisos necesarios:

```bash
# Verificar credenciales configuradas
aws sts get-caller-identity

# Salida esperada:
# {
#     "UserId": "AIDAI...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/tu-usuario"
# }
```

### Permisos Requeridos

Tu usuario/rol AWS debe tener:
- `CloudFormationFullAccess` (crear/actualizar stacks)
- `IAMFullAccess` (crear roles y policies)
- `LambdaFullAccess` (crear/actualizar funciones)
- `APIGatewayAdministrator` (crear API Gateway)
- `SecretsManagerReadWrite` (leer credenciales)
- `CloudWatchLogsFullAccess` (crear log groups)
- `EC2FullAccess` (VPC operations)
- `S3FullAccess` (SAM artifacts)

### Herramientas Instaladas

```bash
# Python 3.11
python --version
# Python 3.11.x

# AWS CLI
aws --version
# aws-cli/2.x.x

# SAM CLI
sam --version
# SAM CLI, version 1.100.0

# Git
git --version
# git version 2.x.x
```

---

## Preparación del Entorno

### 1. Clonar y Configurar

```bash
# Clonar repositorio
git clone <repository-url>
cd tv-prd-api-seven-arkeo-fleet

# Crear rama de trabajo
git checkout -b feature/initial-deployment
```

### 2. Instalar Dependencias Locales

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Ejecutar Tests Localmente

```bash
# Unit tests
pytest tests/unit/ -v --cov=src

# Verificar cobertura >80%
# Si falla, corregir antes de continuar
```

---

## Build y Validación

### 1. Build SAM

```bash
# Build con contenedor Docker (recomendado)
sam build --use-container

# O sin contenedor (más rápido, pero menos reproducible)
sam build
```

**Salida esperada**:
```
Build Succeeded

Built Artifacts  : .aws-sam/build
Built Template   : .aws-sam/build/template.yaml
```

### 2. Validar Template

```bash
# Validar sintaxis CloudFormation
sam validate

# Salida esperada:
# /path/to/template.yaml is a valid SAM Template
```

### 3. Testing Local con SAM

```bash
# Iniciar API local
sam local start-api

# En otra terminal, probar endpoint
curl -H "X-API-Key: test-key" http://127.0.0.1:3000/api/v1/seven/products

# Detener con Ctrl+C
```

### 4. Invocar Lambda Localmente

```bash
# Con evento de prueba
sam local invoke SevenArkeoFleetFunction \
  --event events/list_products.json

# Verificar respuesta exitosa
```

---

## Deployment a Staging

### 1. Configurar SAM Config

Crear archivo `samconfig.toml`:

```toml
version = 0.1

[default]
[default.global.parameters]
stack_name = "tv-stg-seven-arkeo-fleet"

[default.build.parameters]
cached = true
parallel = true

[default.deploy.parameters]
capabilities = "CAPABILITY_IAM"
confirm_changeset = true
resolve_s3 = true
region = "us-east-2"
parameter_overrides = "Environment=staging"
tags = "Proyecto=SevenArkeoFleet Ambiente=staging Responsable=DevOps"

[production]
[production.deploy.parameters]
stack_name = "tv-prd-seven-arkeo-fleet"
parameter_overrides = "Environment=production"
tags = "Proyecto=SevenArkeoFleet Ambiente=production Responsable=DevOps"
```

### 2. Deploy a Staging

```bash
# Primera vez (guided)
sam deploy --config-env default --guided

# Responder prompts:
# Stack Name: tv-stg-seven-arkeo-fleet
# AWS Region: us-east-2
# Confirm changes before deploy: Y
# Allow SAM CLI IAM role creation: Y
# Save arguments to config: Y

# Deployments posteriores
sam deploy --config-env default
```

### 3. Monitorear Deployment

```bash
# Ver eventos de CloudFormation en tiempo real
aws cloudformation describe-stack-events \
  --stack-name tv-stg-seven-arkeo-fleet \
  --region us-east-2 \
  --max-items 10

# Esperar a que stack llegue a CREATE_COMPLETE o UPDATE_COMPLETE
```

### 4. Obtener Outputs

```bash
# Ver outputs del stack
aws cloudformation describe-stacks \
  --stack-name tv-stg-seven-arkeo-fleet \
  --region us-east-2 \
  --query 'Stacks[0].Outputs'

# Guardar API URL
export API_URL=$(aws cloudformation describe-stacks \
  --stack-name tv-stg-seven-arkeo-fleet \
  --region us-east-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

echo "API URL: $API_URL"
```

---

## Testing en Staging

### 1. Smoke Tests Manuales

```bash
# Test 1: Health check (si existe)
curl -H "X-API-Key: LXH61UdMdT4w2aDWgfZj016PKKhAGsp45FMmgC12" \
  $API_URL/health

# Test 2: Listado de productos
curl -H "X-API-Key: LXH61UdMdT4w2aDWgfZj016PKKhAGsp45FMmgC12" \
  "$API_URL/products?pageSize=10" | jq

# Test 3: Autenticación fallida
curl -v $API_URL/products
# Debe retornar 401

# Test 4: Detalle de producto
curl -H "X-API-Key: LXH61UdMdT4w2aDWgfZj016PKKhAGsp45FMmgC12" \
  "$API_URL/products/7SUBSM001A?companyCode=001" | jq
```

### 2. Postman Collection

```bash
# Importar colección en Postman
# Archivo: postman/seven-arkeo-api.postman_collection.json

# Configurar environment con:
# - baseUrl: <API_URL>
# - apiKey: LXH61UdMdT4w2aDWgfZj016PKKhAGsp45FMmgC12
# - companyCode: 001

# Ejecutar todos los tests
# Verificar que todos pasan (verde)
```

### 3. Verificar Logs

```bash
# Tail logs en tiempo real
sam logs --name tv-stg-lambda-seven-arkeo-fleet --tail --region us-east-2

# Buscar errores
aws logs filter-log-events \
  --log-group-name /aws/lambda/tv-stg-lambda-seven-arkeo-fleet \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '10 minutes ago' +%s)000 \
  --region us-east-2

# No debe haber errores críticos
```

### 4. Verificar Métricas

```bash
# Ver métricas en CloudWatch Console
# O via CLI:
aws cloudwatch get-metric-statistics \
  --namespace Seven/ArkeoFleet \
  --metric-name ErrorCount \
  --dimensions Name=Endpoint,Value=products \
  --start-time $(date -u -d '1 hour ago' --iso-8601=seconds) \
  --end-time $(date -u --iso-8601=seconds) \
  --period 300 \
  --statistics Sum \
  --region us-east-2

# ErrorCount debe ser 0 o muy bajo
```

---

## Deployment a Producción

### 1. Pre-Deployment Checklist

- [ ] Todos los tests de staging pasaron
- [ ] Logs de staging sin errores críticos
- [ ] Métricas de staging normales
- [ ] Code review aprobado
- [ ] Documentación actualizada
- [ ] Secrets de producción configurados en Secrets Manager
- [ ] Notificación al equipo de deployment

### 2. Configurar Secrets de Producción

```bash
# Verificar que existen los secrets de producción
aws secretsmanager describe-secret \
  --secret-id seven/db/credentials \
  --region us-east-2

aws secretsmanager describe-secret \
  --secret-id seven/api/keys \
  --region us-east-2

# Si no existen, crearlos:
aws secretsmanager create-secret \
  --name seven/db/credentials \
  --description "SQL Server credentials for Seven ERP" \
  --secret-string '{"username":"<user>","password":"<pass>"}' \
  --region us-east-2

aws secretsmanager create-secret \
  --name seven/api/keys \
  --description "Valid API Keys for Seven Arkeo Fleet API" \
  --secret-string '{"valid_keys":["LXH61UdMdT4w2aDWgfZj016PKKhAGsp45FMmgC12"]}' \
  --region us-east-2
```

### 3. Build Final

```bash
# Asegurarse de tener última versión
git pull origin main

# Build limpio
rm -rf .aws-sam/
sam build --use-container
sam validate
```

### 4. Deploy con Changeset

```bash
# Crear changeset sin ejecutar
sam deploy --config-env production --no-execute-changeset

# Revisar changeset en CloudFormation Console
# O via CLI:
aws cloudformation describe-change-set \
  --stack-name tv-prd-seven-arkeo-fleet \
  --change-set-name <change-set-id> \
  --region us-east-2

# Si todo OK, ejecutar changeset
sam deploy --config-env production
```

### 5. Monitorear Deployment

```bash
# Ver progreso en tiempo real
watch -n 5 'aws cloudformation describe-stacks \
  --stack-name tv-prd-seven-arkeo-fleet \
  --region us-east-2 \
  --query "Stacks[0].StackStatus"'

# Esperar a UPDATE_COMPLETE (puede tomar 10-15 minutos)
```

---

## Rollback

Si algo sale mal en producción:

### Rollback Automático (si falla deployment)

CloudFormation automáticamente hará rollback si el deployment falla.

### Rollback Manual

```bash
# Opción 1: Rollback de CloudFormation
aws cloudformation cancel-update-stack \
  --stack-name tv-prd-seven-arkeo-fleet \
  --region us-east-2

# Opción 2: Volver a versión anterior
# Checkout del commit anterior
git log --oneline
git checkout <commit-hash-anterior>

# Re-deploy
sam build --use-container
sam deploy --config-env production

# Opción 3: Delete y recreate (última opción)
# PELIGRO: Perderá recursos existentes
sam delete --stack-name tv-prd-seven-arkeo-fleet --region us-east-2
# Luego redeploy desde versión estable
```

---

## Post-Deployment

### 1. Smoke Tests en Producción

```bash
# Obtener URL de producción
export PROD_API_URL=$(aws cloudformation describe-stacks \
  --stack-name tv-prd-seven-arkeo-fleet \
  --region us-east-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

# Test básico
curl -H "X-API-Key: LXH61UdMdT4w2aDWgfZj016PKKhAGsp45FMmgC12" \
  "$PROD_API_URL/products?pageSize=5" | jq

# Verificar respuesta exitosa con estructura correcta
```

### 2. Configurar Alertas

```bash
# Verificar que alarmas están configuradas
aws cloudwatch describe-alarms \
  --alarm-name-prefix "SevenArkeoFleet" \
  --region us-east-2

# Suscribirse a notificaciones SNS
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-2:xxxx:tv-prd-alerts-seven-arkeo-fleet \
  --protocol email \
  --notification-endpoint tu-email@tecnovia.com \
  --region us-east-2

# Confirmar subscription en el email recibido
```

### 3. Actualizar Documentación

```bash
# Actualizar README.md con URL de producción
# Actualizar CHANGELOG.md con nueva versión
# Commit y push

git add README.md CHANGELOG.md
git commit -m "docs: update production URLs after deployment"
git push origin main
```

### 4. Notificar al Equipo

Enviar mensaje en Slack #team-arkeo-fleet:

```
🚀 Deployment a Producción Completado

✅ API Seven Arkeo Fleet v1.0.0
📍 URL: https://api.phari.tech/api/v1/seven
📊 Dashboard: <link-to-cloudwatch-dashboard>
📖 Docs: https://api.phari.tech/docs

Smoke tests: Pasados ✓
Logs: Sin errores ✓
Métricas: Normales ✓
```

### 5. Monitoreo Inicial (primeras 24h)

```bash
# Revisar logs cada hora durante primeras 4 horas
sam logs --name tv-prd-lambda-seven-arkeo-fleet --tail --region us-east-2

# Revisar métricas en Dashboard
# Abrir: <dashboard-url>

# Verificar no hay alarmas disparadas
aws cloudwatch describe-alarms \
  --state-value ALARM \
  --region us-east-2
```

---

## Checklist de Deployment

### Pre-Deployment
- [ ] Tests unitarios pasando (100%)
- [ ] Tests de integración pasando
- [ ] Code review aprobado
- [ ] Documentación actualizada
- [ ] Secrets configurados correctamente
- [ ] VPC/Subnets/Security Groups verificados

### Durante Deployment
- [ ] Build exitoso
- [ ] Template validado
- [ ] Changeset revisado
- [ ] Deployment sin errores
- [ ] Stack en estado COMPLETE

### Post-Deployment
- [ ] Smoke tests pasando
- [ ] Logs sin errores
- [ ] Métricas normales
- [ ] Alarmas configuradas
- [ ] Equipo notificado
- [ ] Documentación actualizada
- [ ] Tag de versión creado en Git

---

## Troubleshooting de Deployment

Ver [TROUBLESHOOTING.md](TROUBLESHOOTING.md) para problemas comunes durante deployment.

## Contacto

Para soporte durante deployment:
- **DevOps On-Call**: #devops-oncall (Slack)
- **Email**: devops@tecnovia.com
- **PagerDuty**: Escalate critical deployment issues
