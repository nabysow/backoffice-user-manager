# Backoffice User Manager

A Streamlit-based web application for managing backoffice users with Azure integration.

## Features

- **User Management**: Create, edit, view, and delete users
- **Bulk Import**: Import users from CSV files
- **Audit Logging**: Track all user management actions
- **Role-Based Access Control**: Different permission levels for different roles
- **Azure Integration**: Secure data storage in Azure Key Vault
- **Responsive UI**: Clean, modern interface built with Streamlit

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Azure subscription with Key Vault access
- Azure AD app registration (for authentication)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Backoffice
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Azure configuration
   ```

5. Configure Streamlit secrets:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # Edit secrets.toml with your Azure configuration
   ```

6. Run the application:
   ```bash
   streamlit run app.py
   ```

## Configuration

### Azure Setup

1. **Create Azure Key Vault**:
   - Create a new Key Vault in Azure
   - Configure access policies for your application
   - Create a secret to store user data (CSV format)

2. **Azure AD App Registration**:
   - Register a new application in Azure AD
   - Configure authentication settings
   - Note the Client ID and Tenant ID

3. **Managed Identity** (for production):
   - Configure managed identity for your hosting service
   - Grant Key Vault access to the managed identity

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `KEYVAULT_URL` | Azure Key Vault URL | Yes |
| `USERS_SECRET_NAME` | Name of the secret containing user data | Yes |
| `AZURE_CLIENT_ID` | Azure AD app registration client ID | Yes |
| `AZURE_TENANT_ID` | Azure AD tenant ID | Yes |
| `LOG_ANALYTICS_WORKSPACE_ID` | Log Analytics workspace ID | No |

## Usage

### User Roles

- **Super Admin**: Full access to all features
- **HR Admin**: Can create, edit, and view users; bulk import
- **Department Manager**: Can view users and edit users in their department
- **Viewer**: Can only view users

### User Management

1. Navigate to the "User Management" tab
2. Use the "View Users" subtab to see all users
3. Use the "Add User" subtab to create new users
4. Use the "Edit User" subtab to modify existing users

### Bulk Import

1. Navigate to the "Bulk Import" tab
2. Download the CSV template
3. Fill in the template with user data
4. Upload the CSV file
5. Review validation results
6. Import valid users

### Audit Logs

1. Navigate to the "Audit Logs" tab
2. View recent activity or search specific logs
3. Export logs for compliance reporting

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Structure

```
src/
├── azure_services/     # Azure integration modules
│   ├── keyvault_client.py
│   ├── auth_manager.py
│   └── audit_logger.py
├── models/            # Data models
│   └── user_model.py
├── utils/             # Utility functions
│   ├── validators.py
│   └── csv_handler.py
└── pages/             # Streamlit pages
    ├── user_management.py
    ├── bulk_import.py
    └── audit_logs.py
```

## Deployment

### Docker

Build and run with Docker:

```bash
# Build image
docker build -f deployment/Dockerfile -t backoffice-user-manager .

# Run container
docker run -p 8501:8501 \
  -e KEYVAULT_URL=your-keyvault-url \
  -e USERS_SECRET_NAME=your-secret-name \
  backoffice-user-manager
```

### Azure Container Instances

Deploy using Azure CLI:

```bash
az container create \
  --resource-group your-rg \
  --name backoffice-user-manager \
  --image your-registry/backoffice-user-manager:latest \
  --dns-name-label backoffice-user-manager \
  --ports 8501 \
  --environment-variables \
    KEYVAULT_URL=your-keyvault-url \
    USERS_SECRET_NAME=your-secret-name \
  --assign-identity \
  --location eastus
```

### CI/CD

The project includes Azure DevOps pipeline configuration:

1. Update `deployment/azure-pipelines.yml` with your settings
2. Configure service connections in Azure DevOps
3. Set up pipeline variables
4. Run the pipeline

## Security

- All secrets are stored in Azure Key Vault
- Authentication via Azure AD
- Role-based access control
- Audit logging for compliance
- Input validation and sanitization
- Container security best practices

## Troubleshooting

### Common Issues

1. **Authentication failed**: Check Azure AD configuration and credentials
2. **Key Vault access denied**: Verify access policies and managed identity
3. **CSV import errors**: Check CSV format and required columns
4. **Application not loading**: Check environment variables and dependencies

### Logs

Check application logs for detailed error information:

```bash
# View container logs
docker logs backoffice-user-manager

# View Azure Container Instance logs
az container logs --resource-group your-rg --name backoffice-user-manager
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests and ensure they pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the repository or contact the development team.