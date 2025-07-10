import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from src.azure_services.keyvault_client import KeyVaultUserManager

class TestKeyVaultUserManager:
    
    @patch('src.azure_services.keyvault_client.SecretClient')
    @patch('src.azure_services.keyvault_client.DefaultAzureCredential')
    def test_init(self, mock_credential, mock_secret_client):
        """Test KeyVaultUserManager initialization"""
        vault_url = "https://test-vault.vault.azure.net/"
        secret_name = "test-secret"
        
        manager = KeyVaultUserManager(vault_url, secret_name)
        
        assert manager.secret_name == secret_name
        mock_credential.assert_called_once()
        mock_secret_client.assert_called_once()
    
    @patch('src.azure_services.keyvault_client.SecretClient')
    @patch('src.azure_services.keyvault_client.DefaultAzureCredential')
    def test_get_users_df_success(self, mock_credential, mock_secret_client):
        """Test successful retrieval of users DataFrame"""
        # Mock secret client
        mock_client = Mock()
        mock_secret_client.return_value = mock_client
        
        # Mock secret response
        mock_secret = Mock()
        mock_secret.value = "username,email,full_name,role,department,is_active,created_date,last_modified,permissions\ntest_user,test@example.com,Test User,Viewer,IT,True,2023-01-01T00:00:00,2023-01-01T00:00:00,view_users"
        mock_client.get_secret.return_value = mock_secret
        
        # Test
        manager = KeyVaultUserManager("https://test-vault.vault.azure.net/", "test-secret")
        result_df = manager.get_users_df()
        
        # Assertions
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 1
        assert result_df.iloc[0]['username'] == 'test_user'
        assert result_df.iloc[0]['email'] == 'test@example.com'
        mock_client.get_secret.assert_called_once_with("test-secret")
    
    @patch('src.azure_services.keyvault_client.SecretClient')
    @patch('src.azure_services.keyvault_client.DefaultAzureCredential')
    def test_get_users_df_error(self, mock_credential, mock_secret_client):
        """Test error handling in get_users_df"""
        # Mock secret client to raise exception
        mock_client = Mock()
        mock_secret_client.return_value = mock_client
        mock_client.get_secret.side_effect = Exception("Key Vault error")
        
        # Test
        manager = KeyVaultUserManager("https://test-vault.vault.azure.net/", "test-secret")
        result_df = manager.get_users_df()
        
        # Assertions
        assert isinstance(result_df, pd.DataFrame)
        assert result_df.empty
    
    @patch('src.azure_services.keyvault_client.SecretClient')
    @patch('src.azure_services.keyvault_client.DefaultAzureCredential')
    def test_update_users_df_success(self, mock_credential, mock_secret_client):
        """Test successful update of users DataFrame"""
        # Mock secret client
        mock_client = Mock()
        mock_secret_client.return_value = mock_client
        
        # Test data
        test_data = {
            'username': ['test_user'],
            'email': ['test@example.com'],
            'full_name': ['Test User'],
            'role': ['Viewer'],
            'department': ['IT'],
            'is_active': [True],
            'created_date': ['2023-01-01T00:00:00'],
            'last_modified': ['2023-01-01T00:00:00'],
            'permissions': ['view_users']
        }
        test_df = pd.DataFrame(test_data)
        
        # Test
        manager = KeyVaultUserManager("https://test-vault.vault.azure.net/", "test-secret")
        result = manager.update_users_df(test_df)
        
        # Assertions
        assert result is True
        mock_client.set_secret.assert_called_once()
        call_args = mock_client.set_secret.call_args
        assert call_args[0][0] == "test-secret"  # secret name
        assert "test_user" in call_args[0][1]  # CSV content
    
    @patch('src.azure_services.keyvault_client.SecretClient')
    @patch('src.azure_services.keyvault_client.DefaultAzureCredential')
    def test_update_users_df_error(self, mock_credential, mock_secret_client):
        """Test error handling in update_users_df"""
        # Mock secret client to raise exception
        mock_client = Mock()
        mock_secret_client.return_value = mock_client
        mock_client.set_secret.side_effect = Exception("Key Vault error")
        
        # Test data
        test_df = pd.DataFrame({'username': ['test_user']})
        
        # Test
        manager = KeyVaultUserManager("https://test-vault.vault.azure.net/", "test-secret")
        result = manager.update_users_df(test_df)
        
        # Assertions
        assert result is False
    
    @patch('src.azure_services.keyvault_client.SecretClient')
    @patch('src.azure_services.keyvault_client.DefaultAzureCredential')
    @patch('src.azure_services.keyvault_client.pd.Timestamp')
    def test_backup_users_success(self, mock_timestamp, mock_credential, mock_secret_client):
        """Test successful backup creation"""
        # Mock secret client
        mock_client = Mock()
        mock_secret_client.return_value = mock_client
        
        # Mock timestamp
        mock_timestamp.now.return_value.strftime.return_value = "20230101_120000"
        
        # Mock secret response
        mock_secret = Mock()
        mock_secret.value = "test,csv,data"
        mock_client.get_secret.return_value = mock_secret
        
        # Test
        manager = KeyVaultUserManager("https://test-vault.vault.azure.net/", "test-secret")
        backup_name = manager.backup_users()
        
        # Assertions
        expected_backup_name = "test-secret-backup-20230101_120000"
        assert backup_name == expected_backup_name
        mock_client.get_secret.assert_called_once_with("test-secret")
        mock_client.set_secret.assert_called_with(expected_backup_name, "test,csv,data")
    
    @patch('src.azure_services.keyvault_client.SecretClient')
    @patch('src.azure_services.keyvault_client.DefaultAzureCredential')
    def test_backup_users_error(self, mock_credential, mock_secret_client):
        """Test error handling in backup_users"""
        # Mock secret client to raise exception
        mock_client = Mock()
        mock_secret_client.return_value = mock_client
        mock_client.get_secret.side_effect = Exception("Key Vault error")
        
        # Test
        manager = KeyVaultUserManager("https://test-vault.vault.azure.net/", "test-secret")
        backup_name = manager.backup_users()
        
        # Assertions
        assert backup_name == ""