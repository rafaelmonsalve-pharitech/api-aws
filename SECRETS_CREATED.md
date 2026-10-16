# Secrets Manager - API Seven Arkeo Fleet

## Estado: ✓ CREADOS

Los siguientes secrets fueron creados exitosamente en AWS Secrets Manager (us-east-2):

### 1. Credenciales Base de Datos
- **Nombre**: 	v-prd-seven-db-credentials
- **ARN**: rn:aws:secretsmanager:us-east-2:481133585213:secret:tv-prd-seven-db-credentials-dzKiGZ
- **Descripción**: Credenciales SQL Server para API Seven Arkeo Fleet
- **Contenido**:
  - username: talend
  - password: Tx#n7hbu
  - host: 10.125.18.16
  - port: 1433
  - database: seven_db

### 2. API Keys
- **Nombre**: 	v-prd-seven-api-keys
- **ARN**: rn:aws:secretsmanager:us-east-2:481133585213:secret:tv-prd-seven-api-keys-tZfqAQ
- **Descripción**: API Keys validas para Seven Arkeo Fleet
- **Contenido**:
  - valid_keys: ["sk_prod_seven_arkeo_2024"]

## Fecha de Creación
16 de octubre de 2026, 15:12 (UTC-5)

## Verificar Secrets
```powershell
aws secretsmanager list-secrets --region us-east-2 --query "SecretList[?contains(Name, 'seven')]"
```

## Acceder a Secrets en Lambda
Los secrets están configurados en el SAM template y serán accesibles automáticamente:
- DB_SECRET_ARN: !Ref DbCredentialsSecret
- API_KEYS_SECRET_ARN: !Ref ApiKeysSecret

## Consola AWS
https://us-east-2.console.aws.amazon.com/secretsmanager/listsecrets?region=us-east-2
