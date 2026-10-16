#!/usr/bin/env pwsh
# Script para crear Secrets Manager en AWS
# Proyecto: API Seven Arkeo Fleet

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  CREACION DE SECRETS MANAGER AWS" -ForegroundColor Cyan
Write-Host "  Proyecto: API Seven Arkeo Fleet" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Verificar AWS CLI
if (!(Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: AWS CLI no instalado" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Secret 1: Credenciales Base de Datos ===" -ForegroundColor Yellow
Write-Host "Secret Name: seven/db/credentials"
Write-Host "Contenido: Usuario talend, DB seven_db en 10.125.18.16:1433"

$secretDB = '{"username":"talend","password":"Tx#n7hbu","host":"10.125.18.16","port":1433,"database":"seven_db"}'

aws secretsmanager create-secret `
    --name seven/db/credentials `
    --description "Credenciales SQL Server Seven para API Arkeo Fleet" `
    --secret-string "$secretDB" `
    --region us-east-2

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Secret seven/db/credentials creado" -ForegroundColor Green
} elseif ($LASTEXITCODE -eq 254) {
    Write-Host "⚠ Secret ya existe, actualizando..." -ForegroundColor Yellow
    aws secretsmanager update-secret `
        --secret-id seven/db/credentials `
        --secret-string "$secretDB" `
        --region us-east-2
    Write-Host "✓ Secret actualizado" -ForegroundColor Green
} else {
    Write-Host "❌ Error creando secret" -ForegroundColor Red
}

Write-Host "`n=== Secret 2: API Keys ===" -ForegroundColor Yellow
Write-Host "Secret Name: seven/api/keys"
Write-Host "Contenido: Lista de API Keys validas"

$secretKeys = '{"valid_keys":["LXH61UdMdT4w2aDWgfZj016PKKhAGsp45FMmgC12"]}'

aws secretsmanager create-secret `
    --name seven/api/keys `
    --description "API Keys autorizadas para Seven Arkeo Fleet API" `
    --secret-string "$secretKeys" `
    --region us-east-2

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Secret seven/api/keys creado" -ForegroundColor Green
} elseif ($LASTEXITCODE -eq 254) {
    Write-Host "⚠ Secret ya existe, actualizando..." -ForegroundColor Yellow
    aws secretsmanager update-secret `
        --secret-id seven/api/keys `
        --secret-string "$secretKeys" `
        --region us-east-2
    Write-Host "✓ Secret actualizado" -ForegroundColor Green
} else {
    Write-Host "❌ Error creando secret" -ForegroundColor Red
}

Write-Host "`n=== Verificacion ===" -ForegroundColor Yellow
Write-Host "Listando secrets creados..."

aws secretsmanager list-secrets `
    --region us-east-2 `
    --query "SecretList[?contains(Name, 'seven')].[Name, Description]" `
    --output table

Write-Host "`n================================================" -ForegroundColor Green
Write-Host "  SECRETS CREADOS EXITOSAMENTE" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "`nPuedes verificar en AWS Console:"
Write-Host "https://us-east-2.console.aws.amazon.com/secretsmanager/listsecrets?region=us-east-2"
