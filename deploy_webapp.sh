#!/bin/bash

# Deploy to Azure App Service
# This script deploys the Backoffice User Manager to Azure App Service

set -e  # Exit on error

echo "🚀 Deploying to Azure App Service"
echo "================================="

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "❌ .env file not found. Please run ./setup_production.sh first."
    exit 1
fi

# Configuration
RESOURCE_GROUP=${RESOURCE_GROUP:-rg-backoffice-prod}
APP_SERVICE_PLAN=${APP_SERVICE_PLAN:-asp-backoffice-prod}
WEB_APP_NAME=${WEB_APP_NAME:-webapp-backoffice-$(date +%s | tail -c 6)}
IMAGE_NAME=${IMAGE_NAME:-backoffice-user-manager}

echo "📋 Deployment Configuration:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   App Service Plan: $APP_SERVICE_PLAN"
echo "   Web App Name: $WEB_APP_NAME"
echo "   Image: $IMAGE_NAME"
echo ""

# Build Docker image
echo "🐳 Building Docker image..."
docker build -f deployment/Dockerfile -t $IMAGE_NAME .

echo "✅ Docker image built successfully"

# Create App Service Plan
echo "📦 Creating App Service Plan..."
az appservice plan create \
  --resource-group $RESOURCE_GROUP \
  --name $APP_SERVICE_PLAN \
  --sku B2 \
  --is-linux \
  --output table

# Create Web App
echo "🌐 Creating Web App..."
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $WEB_APP_NAME \
  --deployment-container-image-name $IMAGE_NAME \
  --output table

# Configure managed identity
echo "🆔 Configuring managed identity..."
az webapp identity assign \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --output table

# Get managed identity principal ID
WEBAPP_PRINCIPAL_ID=$(az webapp identity show \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --query "principalId" \
  --output tsv)

# Grant Key Vault access to web app identity
echo "🔑 Granting Key Vault access..."
KEY_VAULT_NAME=$(echo $KEYVAULT_URL | sed 's/https:\/\///' | sed 's/\.vault\.azure\.net\///')

az keyvault set-policy \
  --name $KEY_VAULT_NAME \
  --object-id $WEBAPP_PRINCIPAL_ID \
  --secret-permissions get list \
  --output table

# Configure app settings
echo "⚙️ Configuring application settings..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings \
    KEYVAULT_URL="$KEYVAULT_URL" \
    USERS_SECRET_NAME="$USERS_SECRET_NAME" \
    AZURE_CLIENT_ID="$AZURE_CLIENT_ID" \
    AZURE_TENANT_ID="$AZURE_TENANT_ID" \
    LOG_ANALYTICS_WORKSPACE_ID="$LOG_ANALYTICS_WORKSPACE_ID" \
    ENVIRONMENT="production" \
    WEBSITES_PORT=8501 \
  --output table

# Enable HTTPS only
echo "🔒 Enabling HTTPS only..."
az webapp update \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --https-only true \
  --output table

# Configure container settings
echo "🐳 Configuring container settings..."
az webapp config container set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --docker-custom-image-name $IMAGE_NAME \
  --output table

# Get the app URL
APP_URL="https://${WEB_APP_NAME}.azurewebsites.net"

echo ""
echo "🎉 Deployment completed successfully!"
echo "====================================="
echo ""
echo "🌐 Application URL: $APP_URL"
echo "📊 App Service Status:"

az webapp show \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --query "{Name:name,State:state,Location:location,SKU:appServicePlanId}" \
  --output table

echo ""
echo "📝 Next Steps:"
echo "   1. Wait 5-10 minutes for the application to start"
echo "   2. Access the application at: $APP_URL"
echo "   3. Login with any credentials (will connect to Azure)"
echo "   4. Configure custom domain (optional)"
echo "   5. Set up monitoring and alerts"
echo ""
echo "🔧 Management Commands:"
echo "   View logs: az webapp log tail --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME"
echo "   Restart: az webapp restart --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME"
echo "   Scale: az appservice plan update --resource-group $RESOURCE_GROUP --name $APP_SERVICE_PLAN --sku P1V2"
echo ""
echo "🔗 Useful Links:"
echo "   App Service: https://portal.azure.com/#resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$WEB_APP_NAME"
echo "   Key Vault: https://portal.azure.com/#resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KEY_VAULT_NAME"