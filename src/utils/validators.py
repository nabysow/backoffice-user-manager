import re
from typing import List, Tuple

def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format"""
    if not email:
        return False, "Email is required"
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    return True, ""

def validate_username(username: str, existing_users: List[str]) -> Tuple[bool, str]:
    """Validate username uniqueness and format"""
    if not username:
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        return False, "Username can only contain letters, numbers, dots, hyphens, and underscores"
    
    if username in existing_users:
        return False, "Username already exists"
    
    return True, ""

def validate_full_name(full_name: str) -> Tuple[bool, str]:
    """Validate full name"""
    if not full_name:
        return False, "Full name is required"
    
    if len(full_name) < 2:
        return False, "Full name must be at least 2 characters long"
    
    return True, ""

def validate_role(role: str, available_roles: List[str]) -> Tuple[bool, str]:
    """Validate role selection"""
    if not role:
        return False, "Role is required"
    
    if role not in available_roles:
        return False, f"Role must be one of: {', '.join(available_roles)}"
    
    return True, ""

def validate_department(department: str) -> Tuple[bool, str]:
    """Validate department"""
    if not department:
        return False, "Department is required"
    
    return True, ""

def validate_user_data(user_data: dict, existing_users: List[str] = None) -> Tuple[bool, List[str]]:
    """Comprehensive user data validation"""
    errors = []
    
    # Validate email
    is_valid, error = validate_email(user_data.get('email', ''))
    if not is_valid:
        errors.append(f"Email: {error}")
    
    # Validate username
    is_valid, error = validate_username(
        user_data.get('username', ''), 
        existing_users or []
    )
    if not is_valid:
        errors.append(f"Username: {error}")
    
    # Validate full name
    is_valid, error = validate_full_name(user_data.get('full_name', ''))
    if not is_valid:
        errors.append(f"Full name: {error}")
    
    # Validate role
    available_roles = ["Super Admin", "HR Admin", "Department Manager", "Viewer"]
    is_valid, error = validate_role(user_data.get('role', ''), available_roles)
    if not is_valid:
        errors.append(f"Role: {error}")
    
    # Validate department
    is_valid, error = validate_department(user_data.get('department', ''))
    if not is_valid:
        errors.append(f"Department: {error}")
    
    return len(errors) == 0, errors