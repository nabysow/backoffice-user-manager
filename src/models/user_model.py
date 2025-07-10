from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import datetime

@dataclass
class BackofficeUser:
    username: str
    email: str
    full_name: str
    role: str
    department: str
    is_active: bool
    created_date: datetime
    last_modified: datetime
    permissions: List[str]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for CSV serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        data['created_date'] = self.created_date.isoformat()
        data['last_modified'] = self.last_modified.isoformat()
        # Convert permissions list to comma-separated string
        data['permissions'] = ','.join(self.permissions)
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BackofficeUser':
        """Create from dictionary (CSV deserialization)"""
        # Convert ISO format strings to datetime objects
        data['created_date'] = datetime.fromisoformat(data['created_date'])
        data['last_modified'] = datetime.fromisoformat(data['last_modified'])
        # Convert comma-separated string to permissions list
        data['permissions'] = data['permissions'].split(',') if data['permissions'] else []
        return cls(**data)
    
    def update_permissions(self, new_permissions: List[str]):
        """Update user permissions"""
        self.permissions = new_permissions
        self.last_modified = datetime.now()
    
    def activate(self):
        """Activate user account"""
        self.is_active = True
        self.last_modified = datetime.now()
    
    def deactivate(self):
        """Deactivate user account"""
        self.is_active = False
        self.last_modified = datetime.now()

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