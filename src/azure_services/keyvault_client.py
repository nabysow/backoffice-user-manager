from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import pandas as pd
import io
from typing import Optional, List
from src.utils.csv_handler import CSVHandler
from src.models.user_model import BackofficeUser

class KeyVaultUserManager:
    def __init__(self, vault_url: str, secret_name: str):
        self.credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=vault_url, credential=self.credential)
        self.secret_name = secret_name
    
    def get_users_df(self) -> pd.DataFrame:
        """Retrieve users CSV from Key Vault and return as DataFrame"""
        try:
            secret = self.client.get_secret(self.secret_name)
            csv_content = secret.value
            # Use semicolon delimiter for exact Azure format
            return pd.read_csv(io.StringIO(csv_content), sep=';')
        except Exception as e:
            print(f"Error retrieving users from Key Vault: {e}")
            return pd.DataFrame()
    
    def get_users(self) -> List[BackofficeUser]:
        """Retrieve users from Key Vault in exact Azure CSV format"""
        try:
            secret = self.client.get_secret(self.secret_name)
            csv_content = secret.value
            return CSVHandler.csv_to_users(csv_content)
        except Exception as e:
            print(f"Error retrieving users from Key Vault: {e}")
            return []
    
    def update_users_df(self, df: pd.DataFrame) -> bool:
        """Update users CSV in Key Vault from DataFrame with exact Azure format"""
        try:
            csv_buffer = io.StringIO()
            # Use semicolon delimiter for exact Azure format
            df.to_csv(csv_buffer, index=False, sep=';')
            csv_content = csv_buffer.getvalue()
            
            self.client.set_secret(self.secret_name, csv_content)
            return True
        except Exception as e:
            print(f"Error updating users in Key Vault: {e}")
            return False
    
    def update_users(self, users: List[BackofficeUser]) -> bool:
        """Update users in Key Vault with exact Azure CSV format"""
        try:
            csv_content = CSVHandler.users_to_csv(users)
            self.client.set_secret(self.secret_name, csv_content)
            return True
        except Exception as e:
            print(f"Error updating users in Key Vault: {e}")
            return False
    
    def backup_users(self) -> str:
        """Create backup of current users data in exact Azure format"""
        try:
            secret = self.client.get_secret(self.secret_name)
            backup_name = f"{self.secret_name}-backup-{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
            self.client.set_secret(backup_name, secret.value)
            return backup_name
        except Exception as e:
            print(f"Error creating backup: {e}")
            return ""
    
    def validate_stored_format(self) -> bool:
        """Validate that stored CSV matches exact Azure service format"""
        try:
            secret = self.client.get_secret(self.secret_name)
            csv_content = secret.value
            is_valid, errors = CSVHandler.validate_csv_format(csv_content)
            if not is_valid:
                print(f"Stored CSV format validation errors: {errors}")
            return is_valid
        except Exception as e:
            print(f"Error validating stored format: {e}")
            return False