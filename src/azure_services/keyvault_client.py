from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import pandas as pd
import io
from typing import Optional

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
            return pd.read_csv(io.StringIO(csv_content))
        except Exception as e:
            print(f"Error retrieving users from Key Vault: {e}")
            return pd.DataFrame()
    
    def update_users_df(self, df: pd.DataFrame) -> bool:
        """Update users CSV in Key Vault from DataFrame"""
        try:
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
            
            self.client.set_secret(self.secret_name, csv_content)
            return True
        except Exception as e:
            print(f"Error updating users in Key Vault: {e}")
            return False
    
    def backup_users(self) -> str:
        """Create backup of current users data"""
        try:
            secret = self.client.get_secret(self.secret_name)
            backup_name = f"{self.secret_name}-backup-{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
            self.client.set_secret(backup_name, secret.value)
            return backup_name
        except Exception as e:
            print(f"Error creating backup: {e}")
            return ""