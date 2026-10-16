#!/usr/bin/env pwsh
# Script de Deployment para API Seven Arkeo Fleet
# Empresa: TecnoVia (tv)
# Proyecto: api-seven-arkeo-fleet

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  DEPLOYMENT: API Seven Arkeo Fleet" -ForegroundColor Cyan
Write-Host "  Empresa: TecnoVia (tv-prd)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Cambiar al directorio del proyecto
cd "C:\Users\rafael.monsalve\Documents\aws\api-aws"

Write-Host "`n[1/6] Verificando prerequisitos..." -ForegroundColor Yellow

# Verificar AWS CLI
if (!(Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: AWS CLI no esta instalado" -ForegroundColor Red
    exit 1
}

# Verificar SAM CLI
if (!(Get-Command sam -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: SAM CLI no esta instalado" -ForegroundColor Red
    exit 1
}

Write-Host "✓ AWS CLI instalado" -ForegroundColor Green
Write-Host "✓ SAM CLI instalado" -ForegroundColor Green

Write-Host "`n[2/6] Validando template SAM..." -ForegroundColor Yellow
sam validate --template infrastructure/template.yaml --region us-east-2

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Template SAM invalido" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Template valido" -ForegroundColor Green

Write-Host "`n[3/6] Building aplicacion..." -ForegroundColor Yellow
sam build --template infrastructure/template.yaml

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build fallo" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Build exitoso" -ForegroundColor Green

Write-Host "`n[4/6] Verificando Secrets Manager..." -ForegroundColor Yellow
Write-Host "Verificando secret: seven/db/credentials..."
aws secretsmanager describe-secret --secret-id seven/db/credentials --region us-east-2 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Secret seven/db/credentials no existe" -ForegroundColor Yellow
    Write-Host "Debes crearlo con:" -ForegroundColor Yellow
    Write-Host 'aws secretsmanager create-secret --name seven/db/credentials --secret-string ''{"username":"USER","password":"PASS"}'' --region us-east-2' -ForegroundColor White
    $continue = Read-Host "Continuar de todas formas? (y/n)"
    if ($continue -ne 'y') { exit 1 }
}

Write-Host "Verificando secret: seven/api/keys..."
aws secretsmanager describe-secret --secret-id seven/api/keys --region us-east-2 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Secret seven/api/keys no existe" -ForegroundColor Yellow
    Write-Host "Debes crearlo con:" -ForegroundColor Yellow
    Write-Host 'aws secretsmanager create-secret --name seven/api/keys --secret-string ''{"valid_keys":["KEY_AQUI"]}'' --region us-east-2' -ForegroundColor White
    $continue = Read-Host "Continuar de todas formas? (y/n)"
    if ($continue -ne 'y') { exit 1 }
}

Write-Host "`n[5/6] Deploy a AWS..." -ForegroundColor Yellow
Write-Host "Stack: tv-stg-seven-arkeo-fleet (Staging)" -ForegroundColor Cyan

$deploy = Read-Host "Desplegar a STAGING? (y/n)"
if ($deploy -eq 'y') {
    sam deploy `
        --stack-name tv-stg-seven-arkeo-fleet `
        --region us-east-2 `
        --capabilities CAPABILITY_IAM `
        --resolve-s3 `
        --parameter-overrides Environment=staging `
        --no-confirm-changeset
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Deploy exitoso" -ForegroundColor Green
        
        Write-Host "`n[6/6] Obteniendo URL del API..." -ForegroundColor Yellow
        $apiUrl = aws cloudformation describe-stacks `
            --stack-name tv-stg-seven-arkeo-fleet `
            --region us-east-2 `
            --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' `
            --output text
        
        Write-Host "`n================================================" -ForegroundColor Green
        Write-Host "  DEPLOYMENT COMPLETADO" -ForegroundColor Green
        Write-Host "================================================" -ForegroundColor Green
        Write-Host "API URL: $apiUrl" -ForegroundColor Cyan
        Write-Host "`nPrueba el API con:" -ForegroundColor Yellow
        Write-Host "curl -H 'X-API-Key: TU_API_KEY' $apiUrl/api/v1/seven/openapi.json" -ForegroundColor White
    } else {
        Write-Host "ERROR: Deploy fallo" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Deploy cancelado por el usuario" -ForegroundColor Yellow
}
