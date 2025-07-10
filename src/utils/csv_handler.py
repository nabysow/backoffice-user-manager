import pandas as pd
import io
from typing import List, Dict, Any, Tuple
from src.models.user_model import BackofficeUser

class CSVHandler:
    @staticmethod
    def users_to_csv(users: List[BackofficeUser]) -> str:
        """Convert list of BackofficeUser objects to CSV string"""
        if not users:
            return ""
        
        user_dicts = [user.to_dict() for user in users]
        df = pd.DataFrame(user_dicts)
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue()
    
    @staticmethod
    def csv_to_users(csv_content: str) -> List[BackofficeUser]:
        """Convert CSV string to list of BackofficeUser objects"""
        if not csv_content.strip():
            return []
        
        try:
            df = pd.read_csv(io.StringIO(csv_content))
            users = []
            
            for _, row in df.iterrows():
                user_data = row.to_dict()
                user = BackofficeUser.from_dict(user_data)
                users.append(user)
            
            return users
        except Exception as e:
            print(f"Error parsing CSV: {e}")
            return []
    
    @staticmethod
    def validate_csv_format(csv_content: str) -> Tuple[bool, List[str]]:
        """Validate CSV format and required columns"""
        required_columns = [
            'username', 'email', 'full_name', 'role', 'department',
            'is_active', 'created_date', 'last_modified', 'permissions'
        ]
        
        try:
            df = pd.read_csv(io.StringIO(csv_content))
            errors = []
            
            # Check for required columns
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                errors.append(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Check for empty DataFrame
            if df.empty:
                errors.append("CSV file is empty")
            
            # Check for duplicate usernames
            duplicate_usernames = df[df.duplicated(subset=['username'], keep=False)]['username'].tolist()
            if duplicate_usernames:
                errors.append(f"Duplicate usernames found: {', '.join(duplicate_usernames)}")
            
            # Check for duplicate emails
            duplicate_emails = df[df.duplicated(subset=['email'], keep=False)]['email'].tolist()
            if duplicate_emails:
                errors.append(f"Duplicate emails found: {', '.join(duplicate_emails)}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Error parsing CSV: {str(e)}"]
    
    @staticmethod
    def get_sample_csv() -> str:
        """Generate sample CSV for download/reference"""
        from datetime import datetime
        
        sample_data = [
            {
                'username': 'john.doe',
                'email': 'john.doe@company.com',
                'full_name': 'John Doe',
                'role': 'HR Admin',
                'department': 'Human Resources',
                'is_active': True,
                'created_date': datetime.now().isoformat(),
                'last_modified': datetime.now().isoformat(),
                'permissions': 'create_user,edit_user,view_users,bulk_import'
            },
            {
                'username': 'jane.smith',
                'email': 'jane.smith@company.com',
                'full_name': 'Jane Smith',
                'role': 'Department Manager',
                'department': 'Engineering',
                'is_active': True,
                'created_date': datetime.now().isoformat(),
                'last_modified': datetime.now().isoformat(),
                'permissions': 'view_users,edit_user_department'
            }
        ]
        
        df = pd.DataFrame(sample_data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue()