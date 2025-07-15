# Production Environment Setup Guide

## 🏭 Production Deployment

This guide walks you through deploying the Backoffice User Manager in a production environment with full Azure integration.

## Prerequisites

- Azure subscription with appropriate permissions
- Azure CLI installed and configured
- Docker (for containerized deployment)
- Domain name (optional, for custom URLs)

## Step 1: Azure Resources Setup

### 1.1 Create Resource Group

```bash
# Create a resource group
az group create \
  --name rg-backoffice-prod \
  --location eastus
```

### 1.2 Create Azure Key Vault

```bash
# Create Key Vault
az keyvault create \
  --resource-group rg-backoffice-prod \
  --name kv-backoffice-prod-[random] \
  --location eastus \
  --enable-rbac-authorization true

# Get Key Vault URL (save this)
az keyvault show \
  --name kv-backoffice-prod-[random] \
  --query "properties.vaultUri" \
  --output tsv
```

### 1.3 Create Azure AD App Registration

```bash
# Create app registration
az ad app create \
  --display-name "Backoffice User Manager" \
  --web-redirect-uris "https://your-domain.com/auth/callback"

# Get Application (client) ID
az ad app list \
  --display-name "Backoffice User Manager" \
  --query "[0].appId" \
  --output tsv

# Get Tenant ID
az account show --query "tenantId" --output tsv
```

### 1.4 Create Log Analytics Workspace (Optional)

```bash
# Create Log Analytics workspace for audit logging
az monitor log-analytics workspace create \
  --resource-group rg-backoffice-prod \
  --workspace-name la-backoffice-prod \
  --location eastus
```

## Step 2: Environment Configuration

### 2.1 Configure .env File

Create a `.env` file with your Azure configuration:

```bash
# Azure Key Vault
KEYVAULT_URL=https://kv-backoffice-prod-[random].vault.azure.net/
USERS_SECRET_NAME=backoffice-users-csv

# Azure AD
AZURE_CLIENT_ID=your-app-registration-id
AZURE_TENANT_ID=your-tenant-id

# Optional: Azure Log Analytics
LOG_ANALYTICS_WORKSPACE_ID=your-workspace-id

# Application Insights (Optional)
APPLICATIONINSIGHTS_CONNECTION_STRING=your-connection-string

# Production settings
ENVIRONMENT=production
DEBUG=false
```

### 2.2 Configure Streamlit Secrets

Update `.streamlit/secrets.toml`:

```toml
[azure]
keyvault_url = "https://kv-backoffice-prod-[random].vault.azure.net/"
users_secret_name = "backoffice-users-csv"
tenant_id = "your-tenant-id"
client_id = "your-app-registration-id"
log_analytics_workspace_id = "your-workspace-id"

[app]
admin_users = ["admin@yourcompany.com", "hr@yourcompany.com"]
default_role = "Viewer"
session_timeout = 3600

[production]
debug_mode = false
sample_data = false
```

## Step 3: Initialize User Data

### 3.1 Create Initial Users Secret in Key Vault

```bash
# Create initial CSV structure in Key Vault
az keyvault secret set \
  --vault-name kv-backoffice-prod-[random] \
  --name backoffice-users-csv \
  --value "username,email,full_name,role,department,is_active,created_date,last_modified,permissions
admin,admin@yourcompany.com,Admin User,Super Admin,IT,True,$(date -u +%Y-%m-%dT%H:%M:%S),$(date -u +%Y-%m-%dT%H:%M:%S),create_user,edit_user,delete_user,view_users,bulk_import,view_audit_logs,manage_roles"
```

## Step 4: Deployment Options

### Option A: Azure Container Instances (Recommended for small-medium scale)

#### 4.1 Build and Push Docker Image

```bash
# Build Docker image
docker build -f deployment/Dockerfile -t backoffice-user-manager .

# Tag for Azure Container Registry
docker tag backoffice-user-manager your-registry.azurecr.io/backoffice-user-manager:latest

# Push to registry
docker push your-registry.azurecr.io/backoffice-user-manager:latest
```

#### 4.2 Deploy to Azure Container Instances

```bash
# Create managed identity
az identity create \
  --resource-group rg-backoffice-prod \
  --name id-backoffice-prod

# Get identity details
IDENTITY_ID=$(az identity show \
  --resource-group rg-backoffice-prod \
  --name id-backoffice-prod \
  --query "id" --output tsv)

PRINCIPAL_ID=$(az identity show \
  --resource-group rg-backoffice-prod \
  --name id-backoffice-prod \
  --query "principalId" --output tsv)

# Grant Key Vault access to managed identity
az keyvault set-policy \
  --name kv-backoffice-prod-[random] \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get set list

# Deploy container instance
az container create \
  --resource-group rg-backoffice-prod \
  --name aci-backoffice-prod \
  --image your-registry.azurecr.io/backoffice-user-manager:latest \
  --assign-identity $IDENTITY_ID \
  --dns-name-label backoffice-user-manager \
  --ports 8501 \
  --environment-variables \
    KEYVAULT_URL=https://kv-backoffice-prod-[random].vault.azure.net/ \
    USERS_SECRET_NAME=backoffice-users-csv \
    AZURE_CLIENT_ID=your-app-registration-id \
    AZURE_TENANT_ID=your-tenant-id \
  --cpu 2 \
  --memory 4 \
  --restart-policy Always
```

### Option B: Azure App Service (Recommended for high availability)

#### 4.1 Create App Service Plan

```bash
# Create App Service Plan
az appservice plan create \
  --resource-group rg-backoffice-prod \
  --name asp-backoffice-prod \
  --sku B2 \
  --is-linux
```

#### 4.2 Create Web App

```bash
# Create web app
az webapp create \
  --resource-group rg-backoffice-prod \
  --plan asp-backoffice-prod \
  --name webapp-backoffice-prod-[random] \
  --deployment-container-image-name your-registry.azurecr.io/backoffice-user-manager:latest

# Configure managed identity
az webapp identity assign \
  --resource-group rg-backoffice-prod \
  --name webapp-backoffice-prod-[random]

# Configure app settings
az webapp config appsettings set \
  --resource-group rg-backoffice-prod \
  --name webapp-backoffice-prod-[random] \
  --settings \
    KEYVAULT_URL=https://kv-backoffice-prod-[random].vault.azure.net/ \
    USERS_SECRET_NAME=backoffice-users-csv \
    AZURE_CLIENT_ID=your-app-registration-id \
    AZURE_TENANT_ID=your-tenant-id \
    WEBSITES_PORT=8501
```

### Option C: Azure Kubernetes Service (Enterprise scale)

```bash
# Create AKS cluster
az aks create \
  --resource-group rg-backoffice-prod \
  --name aks-backoffice-prod \
  --node-count 2 \
  --enable-managed-identity \
  --generate-ssh-keys

# Deploy using provided Kubernetes manifests
kubectl apply -f deployment/k8s/
```

## Step 5: Security Configuration

### 5.1 Configure HTTPS and SSL

```bash
# For App Service - enable HTTPS only
az webapp update \
  --resource-group rg-backoffice-prod \
  --name webapp-backoffice-prod-[random] \
  --https-only true

# Configure custom domain (optional)
az webapp config hostname add \
  --resource-group rg-backoffice-prod \
  --webapp-name webapp-backoffice-prod-[random] \
  --hostname your-domain.com
```

### 5.2 Configure Network Security

```bash
# Create network security group
az network nsg create \
  --resource-group rg-backoffice-prod \
  --name nsg-backoffice-prod

# Allow HTTPS traffic only
az network nsg rule create \
  --resource-group rg-backoffice-prod \
  --nsg-name nsg-backoffice-prod \
  --name AllowHTTPS \
  --protocol Tcp \
  --priority 100 \
  --destination-port-range 443 \
  --access Allow
```

## Step 6: Monitoring and Logging

### 6.1 Configure Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --resource-group rg-backoffice-prod \
  --app ai-backoffice-prod \
  --location eastus \
  --kind web

# Get connection string
az monitor app-insights component show \
  --resource-group rg-backoffice-prod \
  --app ai-backoffice-prod \
  --query "connectionString" --output tsv
```

### 6.2 Configure Log Analytics

```bash
# Create diagnostic settings for Key Vault
az monitor diagnostic-settings create \
  --resource $(az keyvault show --name kv-backoffice-prod-[random] --query "id" --output tsv) \
  --name keyvault-diagnostics \
  --workspace $(az monitor log-analytics workspace show --resource-group rg-backoffice-prod --workspace-name la-backoffice-prod --query "id" --output tsv) \
  --logs '[{"category":"AuditEvent","enabled":true}]'
```

## Step 7: Backup and Disaster Recovery

### 7.1 Configure Key Vault Backup

```bash
# Enable soft delete and purge protection
az keyvault update \
  --name kv-backoffice-prod-[random] \
  --enable-soft-delete true \
  --enable-purge-protection true
```

### 7.2 Configure Automated Backups

Create an Azure Function or Logic App to:
- Daily backup of Key Vault secrets
- Export user data to blob storage
- Monitor application health

## Step 8: CI/CD Pipeline

### 8.1 Azure DevOps Pipeline

Use the provided `deployment/azure-pipelines.yml` and update:

```yaml
variables:
  containerRegistry: 'your-registry.azurecr.io'
  resourceGroupName: 'rg-backoffice-prod'
  webAppName: 'webapp-backoffice-prod-[random]'
```

### 8.2 GitHub Actions (Alternative)

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Login to Azure
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Build and deploy
      run: |
        docker build -f deployment/Dockerfile -t backoffice-user-manager .
        # Add deployment commands
```

## Step 9: Testing Production Deployment

### 9.1 Health Checks

```bash
# Test application health
curl https://your-domain.com/_stcore/health

# Test Key Vault connectivity
az keyvault secret show \
  --vault-name kv-backoffice-prod-[random] \
  --name backoffice-users-csv
```

### 9.2 Load Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Basic load test
ab -n 100 -c 10 https://your-domain.com/
```

## Step 10: Maintenance and Updates

### 10.1 Regular Maintenance Tasks

- Monitor Key Vault usage and costs
- Review audit logs monthly
- Update dependencies quarterly
- Backup user data weekly
- Test disaster recovery procedures

### 10.2 Scaling Considerations

- Monitor CPU and memory usage
- Scale App Service plan as needed
- Consider Azure Front Door for global distribution
- Implement Redis cache for session management

## Security Best Practices

1. **Never store secrets in code**
2. **Use managed identities** instead of service principals
3. **Enable audit logging** for all components
4. **Regularly rotate** application secrets
5. **Implement** network security groups
6. **Use HTTPS only** for all communications
7. **Regularly review** access permissions
8. **Monitor** for suspicious activities

## Cost Optimization

- Use Azure Cost Management for monitoring
- Implement auto-scaling policies
- Use Azure Reserved Instances for predictable workloads
- Regularly review and optimize resource usage

## Support and Troubleshooting

- Monitor Application Insights for errors
- Set up alerts for critical issues
- Review Key Vault access logs
- Monitor application performance metrics