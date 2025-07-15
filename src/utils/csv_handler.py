import pandas as pd
import io
from typing import List, Dict, Any, Tuple
from src.models.user_model import BackofficeUser

class CSVHandler:
    @staticmethod
    def users_to_csv(users: List[BackofficeUser]) -> str:
        """Convert list of BackofficeUser objects to CSV string matching exact Azure format"""
        if not users:
            # Return header only if no users
            return "UserName;Email;Password;IsConfirmed;Roles;\n"
        
        # Build CSV manually to ensure exact format with trailing semicolons
        lines = ["UserName;Email;Password;IsConfirmed;Roles;"]
        
        for user in users:
            row_data = user.to_csv_row()
            line = f"{row_data['UserName']};{row_data['Email']};{row_data['Password']};{row_data['IsConfirmed']};{row_data['Roles']};"
            lines.append(line)
        
        return "\n".join(lines) + "\n"
    
    @staticmethod
    def csv_to_users(csv_content: str) -> List[BackofficeUser]:
        """Convert CSV string to list of BackofficeUser objects preserving exact structure"""
        if not csv_content.strip():
            return []
        
        try:
            df = pd.read_csv(io.StringIO(csv_content), sep=';')
            users = []
            
            for _, row in df.iterrows():
                user_data = row.to_dict()
                # Keep exact CSV column names and structure
                user = BackofficeUser.from_dict(user_data)
                users.append(user)
            
            return users
        except Exception as e:
            print(f"Error parsing CSV: {e}")
            return []
    
    @staticmethod
    def validate_csv_format(csv_content: str) -> Tuple[bool, List[str]]:
        """Validate CSV format matches exact structure for Azure service integration"""
        expected_columns = ['UserName', 'Email', 'Password', 'IsConfirmed', 'Roles']
        required_columns = ['UserName', 'Email', 'IsConfirmed']
        
        try:
            df = pd.read_csv(io.StringIO(csv_content), sep=';')
            errors = []
            
            # Check columns (handle trailing semicolon creating empty column)
            actual_columns = [col for col in df.columns if col.strip() and not col.startswith('Unnamed')]
            if actual_columns != expected_columns:
                errors.append(f"Column structure must exactly match: {';'.join(expected_columns)};")
            
            # Check for required columns
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                errors.append(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Check for empty DataFrame
            if df.empty:
                errors.append("CSV file is empty")
            
            # Check for duplicate usernames
            if 'UserName' in df.columns:
                duplicate_usernames = df[df.duplicated(subset=['UserName'], keep=False)]['UserName'].tolist()
                if duplicate_usernames:
                    errors.append(f"Duplicate usernames found: {', '.join(duplicate_usernames)}")
            
            # Check for duplicate emails
            if 'Email' in df.columns:
                duplicate_emails = df[df.duplicated(subset=['Email'], keep=False)]['Email'].tolist()
                if duplicate_emails:
                    errors.append(f"Duplicate emails found: {', '.join(duplicate_emails)}")
            
            # Validate email format
            if 'Email' in df.columns:
                import re
                email_pattern = r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$'
                invalid_emails = []
                for email in df['Email'].dropna():
                    if str(email).strip() and not re.match(email_pattern, str(email)):
                        invalid_emails.append(str(email))
                if invalid_emails:
                    errors.append(f"Invalid email formats: {', '.join(invalid_emails)}")
            
            # Validate IsConfirmed values
            if 'IsConfirmed' in df.columns:
                invalid_confirmed = []
                for confirmed in df['IsConfirmed'].dropna():
                    if str(confirmed).lower() not in ['true', 'false']:
                        invalid_confirmed.append(str(confirmed))
                if invalid_confirmed:
                    errors.append(f"Invalid IsConfirmed values (must be true/false): {', '.join(invalid_confirmed)}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Error parsing CSV: {str(e)}"]
    
    @staticmethod
    def get_sample_csv() -> str:
        """Generate sample CSV matching exact format for Azure service integration"""
        # Use exact format from the provided pattern with trailing semicolons
        return "UserName;Email;Password;IsConfirmed;Roles;\njohn.doe;john.doe@company.com;;true;HR Admin;\njane.smith;jane.smith@company.com;;true;Department Manager;\nbob.wilson;bob.wilson@company.com;;false;;\n"