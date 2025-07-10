#!/bin/bash

# Deploy to Azure Container Instances
# This script deploys the Backoffice User Manager to Azure Container Instances

set -e  # Exit on error

echo "🚀 Deploying to Azure Container Instances"
echo "========================================="

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "❌ .env file not found. Please run ./setup_production.sh first."
    exit 1
fi

# Configuration
RESOURCE_GROUP=${RESOURCE_GROUP:-rg-backoffice-prod}
CONTAINER_NAME=${CONTAINER_NAME:-aci-backoffice-prod}
IMAGE_NAME=${IMAGE_NAME:-backoffice-user-manager}
DNS_LABEL=${DNS_LABEL:-backoffice-user-manager-$(date +%s | tail -c 6)}

echo "📋 Deployment Configuration:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Container Name: $CONTAINER_NAME"
echo "   DNS Label: $DNS_LABEL"
echo "   Image: $IMAGE_NAME"
echo ""

# Build Docker image
echo "🐳 Building Docker image..."
docker build -f deployment/Dockerfile -t $IMAGE_NAME .

echo "✅ Docker image built successfully"

# Get managed identity details
echo "🆔 Getting managed identity details..."
IDENTITY_NAME=$(az identity list --resource-group $RESOURCE_GROUP --query "[0].name" --output tsv)

if [ -z "$IDENTITY_NAME" ]; then
    echo "❌ No managed identity found. Please run ./setup_production.sh first."
    exit 1
fi

IDENTITY_ID=$(az identity show \
  --resource-group $RESOURCE_GROUP \
  --name $IDENTITY_NAME \
  --query "id" \
  --output tsv)

echo "✅ Using managed identity: $IDENTITY_NAME"

# Deploy to Azure Container Instances
echo "☁️ Deploying to Azure Container Instances..."

az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image $IMAGE_NAME \
  --assign-identity $IDENTITY_ID \
  --dns-name-label $DNS_LABEL \
  --ports 8501 \
  --environment-variables \
    KEYVAULT_URL="$KEYVAULT_URL" \
    USERS_SECRET_NAME="$USERS_SECRET_NAME" \
    AZURE_CLIENT_ID="$AZURE_CLIENT_ID" \
    AZURE_TENANT_ID="$AZURE_TENANT_ID" \
    LOG_ANALYTICS_WORKSPACE_ID="$LOG_ANALYTICS_WORKSPACE_ID" \
    ENVIRONMENT="production" \
  --cpu 2 \
  --memory 4 \
  --restart-policy Always \
  --output table

# Get the FQDN
FQDN=$(az container show \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --query "ipAddress.fqdn" \
  --output tsv)

echo ""
echo "🎉 Deployment completed successfully!"
echo "====================================="
echo ""
echo "🌐 Application URL: http://$FQDN:8501"
echo "📊 Container Status:"

az container show \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --query "{Name:name,State:containers[0].instanceView.currentState.state,CPU:containers[0].resourceRequirements.requests.cpu,Memory:containers[0].resourceRequirements.requests.memoryInGB}" \
  --output table

echo ""
echo "📝 Next Steps:"
echo "   1. Wait 2-3 minutes for the application to start"
echo "   2. Access the application at: http://$FQDN:8501"
echo "   3. Login with any credentials (will connect to Azure)"
echo "   4. Configure SSL/TLS for production use"
echo "   5. Set up monitoring and alerts"
echo ""
echo "🔧 Management Commands:"
echo "   View logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
echo "   Restart: az container restart --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
echo "   Delete: az container delete --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"