#!/bin/bash

# Production Environment Setup Script
# This script helps set up Azure resources for the Backoffice User Manager

set -e  # Exit on error

echo "🏭 Backoffice User Manager - Production Setup"
echo "=============================================="

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install it first."
    echo "   Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if user is logged in to Azure
if ! az account show &> /dev/null; then
    echo "🔐 Please log in to Azure CLI first:"
    az login
fi

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query "id" --output tsv)
TENANT_ID=$(az account show --query "tenantId" --output tsv)

echo "📋 Current Azure Subscription: $SUBSCRIPTION_ID"
echo "🏢 Tenant ID: $TENANT_ID"

# Get configuration from user
read -p "🌍 Enter Azure region (default: eastus): " LOCATION
LOCATION=${LOCATION:-eastus}

read -p "📦 Enter resource group name (default: rg-backoffice-prod): " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-rg-backoffice-prod}

read -p "🔑 Enter Key Vault name prefix (default: kv-backoffice): " KV_PREFIX
KV_PREFIX=${KV_PREFIX:-kv-backoffice}

# Generate unique suffix
UNIQUE_SUFFIX=$(date +%s | tail -c 6)
KEY_VAULT_NAME="${KV_PREFIX}-${UNIQUE_SUFFIX}"

echo ""
echo "🚀 Creating Azure resources..."
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Location: $LOCATION"
echo "   Key Vault: $KEY_VAULT_NAME"
echo ""

# Create resource group
echo "📦 Creating resource group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --output table

# Create Key Vault
echo "🔑 Creating Key Vault..."
az keyvault create \
  --resource-group $RESOURCE_GROUP \
  --name $KEY_VAULT_NAME \
  --location $LOCATION \
  --enable-rbac-authorization false \
  --enable-soft-delete true \
  --enable-purge-protection true \
  --output table

# Get Key Vault URL
KEYVAULT_URL=$(az keyvault show \
  --name $KEY_VAULT_NAME \
  --query "properties.vaultUri" \
  --output tsv)

echo "✅ Key Vault created: $KEYVAULT_URL"

# Create Azure AD App Registration
echo "🔐 Creating Azure AD App Registration..."
APP_NAME="Backoffice User Manager - $UNIQUE_SUFFIX"

# Create the app registration
APP_ID=$(az ad app create \
  --display-name "$APP_NAME" \
  --query "appId" \
  --output tsv)

echo "✅ App Registration created: $APP_ID"

# Create Log Analytics Workspace
echo "📊 Creating Log Analytics Workspace..."
WORKSPACE_NAME="la-backoffice-${UNIQUE_SUFFIX}"

az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $WORKSPACE_NAME \
  --location $LOCATION \
  --output table

WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $WORKSPACE_NAME \
  --query "customerId" \
  --output tsv)

echo "✅ Log Analytics Workspace created: $WORKSPACE_ID"

# Initialize user data in Key Vault
echo "👥 Creating initial user data in Key Vault..."

# Create initial CSV with admin user
INITIAL_CSV="username,email,full_name,role,department,is_active,created_date,last_modified,permissions
admin,admin@yourcompany.com,Admin User,Super Admin,IT,True,$(date -u +%Y-%m-%dT%H:%M:%S),$(date -u +%Y-%m-%dT%H:%M:%S),\"create_user,edit_user,delete_user,view_users,bulk_import,view_audit_logs,manage_roles\""

az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "backoffice-users-csv" \
  --value "$INITIAL_CSV" \
  --output table

echo "✅ Initial user data created in Key Vault"

# Create .env file
echo "📝 Creating .env file..."
cat > .env << EOF
# Azure Key Vault
KEYVAULT_URL=$KEYVAULT_URL
USERS_SECRET_NAME=backoffice-users-csv

# Azure AD
AZURE_CLIENT_ID=$APP_ID
AZURE_TENANT_ID=$TENANT_ID

# Azure Log Analytics
LOG_ANALYTICS_WORKSPACE_ID=$WORKSPACE_ID

# Production settings
ENVIRONMENT=production
DEBUG=false
EOF

echo "✅ .env file created"

# Update Streamlit secrets
echo "🔧 Updating Streamlit secrets..."
mkdir -p .streamlit

cat > .streamlit/secrets.toml << EOF
[azure]
keyvault_url = "$KEYVAULT_URL"
users_secret_name = "backoffice-users-csv"
tenant_id = "$TENANT_ID"
client_id = "$APP_ID"
log_analytics_workspace_id = "$WORKSPACE_ID"

[app]
admin_users = ["admin@yourcompany.com", "hr@yourcompany.com"]
default_role = "Viewer"
session_timeout = 3600

[production]
debug_mode = false
sample_data = false
EOF

echo "✅ Streamlit secrets updated"

# Create managed identity for deployment
echo "🆔 Creating managed identity..."
IDENTITY_NAME="id-backoffice-${UNIQUE_SUFFIX}"

az identity create \
  --resource-group $RESOURCE_GROUP \
  --name $IDENTITY_NAME \
  --output table

PRINCIPAL_ID=$(az identity show \
  --resource-group $RESOURCE_GROUP \
  --name $IDENTITY_NAME \
  --query "principalId" \
  --output tsv)

IDENTITY_ID=$(az identity show \
  --resource-group $RESOURCE_GROUP \
  --name $IDENTITY_NAME \
  --query "id" \
  --output tsv)

# Grant Key Vault access to managed identity
echo "🔑 Granting Key Vault access to managed identity..."
az keyvault set-policy \
  --name $KEY_VAULT_NAME \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get set list delete backup restore \
  --output table

echo "✅ Managed identity configured"

# Output summary
echo ""
echo "🎉 Production environment setup complete!"
echo "========================================"
echo ""
echo "📋 Resource Summary:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Key Vault: $KEY_VAULT_NAME"
echo "   Key Vault URL: $KEYVAULT_URL"
echo "   App Registration ID: $APP_ID"
echo "   Tenant ID: $TENANT_ID"
echo "   Log Analytics Workspace: $WORKSPACE_NAME"
echo "   Managed Identity: $IDENTITY_NAME"
echo ""
echo "📝 Configuration Files Created:"
echo "   ✅ .env"
echo "   ✅ .streamlit/secrets.toml"
echo ""
echo "🚀 Next Steps:"
echo "   1. Test the application locally:"
echo "      streamlit run app.py"
echo ""
echo "   2. Deploy to Azure Container Instances:"
echo "      ./deploy_aci.sh"
echo ""
echo "   3. Or deploy to Azure App Service:"
echo "      ./deploy_webapp.sh"
echo ""
echo "   4. Configure custom domain and SSL (optional)"
echo "   5. Set up monitoring and alerts"
echo ""
echo "🔒 Security Notes:"
echo "   - The .env and secrets.toml files contain sensitive information"
echo "   - These files are already in .gitignore"
echo "   - Use Azure Key Vault references in production"
echo "   - Regularly rotate secrets and review access"
echo ""
echo "📚 For detailed deployment instructions, see:"
echo "   PRODUCTION_SETUP.md"