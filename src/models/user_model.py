from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import datetime

@dataclass
class BackofficeUser:
    UserName: str
    Email: str
    Password: str
    IsConfirmed: bool
    Roles: str
    
    # Internal fields for app functionality (not in CSV)
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    permissions: Optional[List[str]] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for CSV serialization - only CSV columns"""
        return {
            'UserName': self.UserName,
            'Email': self.Email, 
            'Password': self.Password,
            'IsConfirmed': self.IsConfirmed,
            'Roles': self.Roles
        }
    
    def to_csv_row(self) -> dict:
        """Convert to CSV row format exactly matching the pattern"""
        return {
            'UserName': self.UserName,
            'Email': self.Email,
            'Password': self.Password,
            'IsConfirmed': 'true' if self.IsConfirmed else 'false',  # Keep lowercase
            'Roles': self.Roles
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BackofficeUser':
        """Create from dictionary (CSV deserialization)"""
        import pandas as pd
        
        # Handle NaN and empty values exactly as in original CSV
        password = data.get('Password', '')
        if pd.isna(password):
            password = ''
            
        roles = data.get('Roles', '')
        if pd.isna(roles):
            roles = ''
        
        csv_data = {
            'UserName': data.get('UserName', ''),
            'Email': data.get('Email', ''),
            'Password': password,
            'IsConfirmed': str(data.get('IsConfirmed', 'true')).lower() == 'true',
            'Roles': roles
        }
        
        # Set internal fields
        csv_data['created_date'] = datetime.now()
        csv_data['last_modified'] = datetime.now() 
        csv_data['permissions'] = get_permissions_for_role(csv_data['Roles']) if csv_data['Roles'] else []
        
        return cls(**csv_data)
    
    def update_permissions(self, new_permissions: List[str]):
        """Update user permissions"""
        if self.permissions is not None:
            self.permissions = new_permissions
        if self.last_modified is not None:
            self.last_modified = datetime.now()
    
    def activate(self):
        """Activate user account"""
        self.IsConfirmed = True
        if self.last_modified is not None:
            self.last_modified = datetime.now()
    
    def deactivate(self):
        """Deactivate user account"""
        self.IsConfirmed = False
        if self.last_modified is not None:
            self.last_modified = datetime.now()
    
    @property
    def username(self) -> str:
        """Alias for UserName for backward compatibility"""
        return self.UserName
    
    @property
    def email(self) -> str:
        """Alias for Email for backward compatibility"""
        return self.Email
    
    @property
    def is_active(self) -> bool:
        """Alias for IsConfirmed for backward compatibility"""
        return self.IsConfirmed
    
    @property
    def role(self) -> str:
        """Alias for Roles for backward compatibility"""
        return self.Roles

# Role-based permissions mapping
ROLE_PERMISSIONS = {
    "Super Admin": [
        "create_user", "edit_user", "delete_user", "view_users",
        "bulk_import", "view_audit_logs", "manage_roles"
    ],
    "HR Admin": [
        "create_user", "edit_user", "view_users", "bulk_import"
    ],
    "Department Manager": [
        "view_users", "edit_user_department"
    ],
    "Viewer": [
        "view_users"
    ]
}

def get_permissions_for_role(role: str) -> List[str]:
    """Get permissions for a specific role"""
    return ROLE_PERMISSIONS.get(role, [])