import pytest
from datetime import datetime
from src.models.user_model import BackofficeUser, get_permissions_for_role
from src.utils.validators import validate_email, validate_username, validate_user_data
from src.utils.csv_handler import CSVHandler

class TestBackofficeUser:
    
    def test_user_creation(self):
        """Test user model creation and validation"""
        user = BackofficeUser(
            username="test_user",
            email="test@example.com",
            full_name="Test User",
            role="HR Admin",
            department="Human Resources",
            is_active=True,
            created_date=datetime.now(),
            last_modified=datetime.now(),
            permissions=["create_user", "edit_user", "view_users"]
        )
        
        assert user.username == "test_user"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == "HR Admin"
        assert user.department == "Human Resources"
        assert user.is_active is True
        assert isinstance(user.created_date, datetime)
        assert isinstance(user.last_modified, datetime)
        assert user.permissions == ["create_user", "edit_user", "view_users"]
    
    def test_user_to_dict(self):
        """Test user serialization to dictionary"""
        created_date = datetime(2023, 1, 1, 12, 0, 0)
        modified_date = datetime(2023, 1, 2, 12, 0, 0)
        
        user = BackofficeUser(
            username="test_user",
            email="test@example.com",
            full_name="Test User",
            role="HR Admin",
            department="Human Resources",
            is_active=True,
            created_date=created_date,
            last_modified=modified_date,
            permissions=["create_user", "edit_user"]
        )
        
        user_dict = user.to_dict()
        
        assert user_dict['username'] == "test_user"
        assert user_dict['email'] == "test@example.com"
        assert user_dict['created_date'] == "2023-01-01T12:00:00"
        assert user_dict['last_modified'] == "2023-01-02T12:00:00"
        assert user_dict['permissions'] == "create_user,edit_user"
    
    def test_user_from_dict(self):
        """Test user deserialization from dictionary"""
        user_dict = {
            'username': "test_user",
            'email': "test@example.com",
            'full_name': "Test User",
            'role': "HR Admin",
            'department': "Human Resources",
            'is_active': True,
            'created_date': "2023-01-01T12:00:00",
            'last_modified': "2023-01-02T12:00:00",
            'permissions': "create_user,edit_user"
        }
        
        user = BackofficeUser.from_dict(user_dict)
        
        assert user.username == "test_user"
        assert user.email == "test@example.com"
        assert user.created_date == datetime(2023, 1, 1, 12, 0, 0)
        assert user.last_modified == datetime(2023, 1, 2, 12, 0, 0)
        assert user.permissions == ["create_user", "edit_user"]
    
    def test_user_update_permissions(self):
        """Test updating user permissions"""
        user = BackofficeUser(
            username="test_user",
            email="test@example.com",
            full_name="Test User",
            role="HR Admin",
            department="Human Resources",
            is_active=True,
            created_date=datetime.now(),
            last_modified=datetime.now(),
            permissions=["view_users"]
        )
        
        original_modified = user.last_modified
        new_permissions = ["create_user", "edit_user", "view_users"]
        
        user.update_permissions(new_permissions)
        
        assert user.permissions == new_permissions
        assert user.last_modified > original_modified
    
    def test_user_activate_deactivate(self):
        """Test user activation and deactivation"""
        user = BackofficeUser(
            username="test_user",
            email="test@example.com",
            full_name="Test User",
            role="HR Admin",
            department="Human Resources",
            is_active=False,
            created_date=datetime.now(),
            last_modified=datetime.now(),
            permissions=["view_users"]
        )
        
        # Test activation
        user.activate()
        assert user.is_active is True
        
        # Test deactivation
        user.deactivate()
        assert user.is_active is False
    
    def test_get_permissions_for_role(self):
        """Test role-based permissions"""
        super_admin_permissions = get_permissions_for_role("Super Admin")
        assert "create_user" in super_admin_permissions
        assert "delete_user" in super_admin_permissions
        assert "manage_roles" in super_admin_permissions
        
        viewer_permissions = get_permissions_for_role("Viewer")
        assert viewer_permissions == ["view_users"]
        
        unknown_role_permissions = get_permissions_for_role("Unknown Role")
        assert unknown_role_permissions == []

class TestValidators:
    
    def test_validate_email(self):
        """Test email validation logic"""
        # Valid emails
        valid, error = validate_email("test@example.com")
        assert valid is True
        assert error == ""
        
        valid, error = validate_email("user.name+tag@example.co.uk")
        assert valid is True
        assert error == ""
        
        # Invalid emails
        valid, error = validate_email("")
        assert valid is False
        assert "required" in error
        
        valid, error = validate_email("invalid-email")
        assert valid is False
        assert "Invalid email format" in error
        
        valid, error = validate_email("@example.com")
        assert valid is False
        assert "Invalid email format" in error
    
    def test_validate_username(self):
        """Test username validation logic"""
        existing_users = ["existing_user", "another_user"]
        
        # Valid usernames
        valid, error = validate_username("new_user", existing_users)
        assert valid is True
        assert error == ""
        
        valid, error = validate_username("user123", existing_users)
        assert valid is True
        assert error == ""
        
        # Invalid usernames
        valid, error = validate_username("", existing_users)
        assert valid is False
        assert "required" in error
        
        valid, error = validate_username("ab", existing_users)
        assert valid is False
        assert "3 characters" in error
        
        valid, error = validate_username("user@invalid", existing_users)
        assert valid is False
        assert "can only contain" in error
        
        valid, error = validate_username("existing_user", existing_users)
        assert valid is False
        assert "already exists" in error
    
    def test_validate_user_data(self):
        """Test comprehensive user data validation"""
        existing_users = ["existing_user"]
        
        # Valid user data
        valid_data = {
            'username': 'new_user',
            'email': 'new@example.com',
            'full_name': 'New User',
            'role': 'HR Admin',
            'department': 'Human Resources'
        }
        
        is_valid, errors = validate_user_data(valid_data, existing_users)
        assert is_valid is True
        assert len(errors) == 0
        
        # Invalid user data
        invalid_data = {
            'username': 'existing_user',  # Already exists
            'email': 'invalid-email',      # Invalid format
            'full_name': '',               # Empty
            'role': 'Invalid Role',        # Invalid role
            'department': ''               # Empty
        }
        
        is_valid, errors = validate_user_data(invalid_data, existing_users)
        assert is_valid is False
        assert len(errors) > 0
        assert any("already exists" in error for error in errors)
        assert any("Invalid email format" in error for error in errors)

class TestCSVHandler:
    
    def test_users_to_csv(self):
        """Test converting users to CSV"""
        users = [
            BackofficeUser(
                username="user1",
                email="user1@example.com",
                full_name="User One",
                role="HR Admin",
                department="HR",
                is_active=True,
                created_date=datetime(2023, 1, 1),
                last_modified=datetime(2023, 1, 1),
                permissions=["create_user", "view_users"]
            ),
            BackofficeUser(
                username="user2",
                email="user2@example.com",
                full_name="User Two",
                role="Viewer",
                department="IT",
                is_active=False,
                created_date=datetime(2023, 1, 2),
                last_modified=datetime(2023, 1, 2),
                permissions=["view_users"]
            )
        ]
        
        csv_content = CSVHandler.users_to_csv(users)
        
        assert "user1" in csv_content
        assert "user2" in csv_content
        assert "user1@example.com" in csv_content
        assert "HR Admin" in csv_content
        assert "create_user,view_users" in csv_content
    
    def test_csv_to_users(self):
        """Test converting CSV to users"""
        csv_content = """username,email,full_name,role,department,is_active,created_date,last_modified,permissions
user1,user1@example.com,User One,HR Admin,HR,True,2023-01-01T00:00:00,2023-01-01T00:00:00,create_user,view_users
user2,user2@example.com,User Two,Viewer,IT,False,2023-01-02T00:00:00,2023-01-02T00:00:00,view_users"""
        
        users = CSVHandler.csv_to_users(csv_content)
        
        assert len(users) == 2
        assert users[0].username == "user1"
        assert users[0].email == "user1@example.com"
        assert users[0].role == "HR Admin"
        assert users[0].is_active is True
        assert users[1].username == "user2"
        assert users[1].is_active is False
    
    def test_validate_csv_format(self):
        """Test CSV format validation"""
        # Valid CSV
        valid_csv = """username,email,full_name,role,department,is_active,created_date,last_modified,permissions
user1,user1@example.com,User One,HR Admin,HR,True,2023-01-01T00:00:00,2023-01-01T00:00:00,create_user"""
        
        is_valid, errors = CSVHandler.validate_csv_format(valid_csv)
        assert is_valid is True
        assert len(errors) == 0
        
        # Missing columns
        invalid_csv = """username,email
user1,user1@example.com"""
        
        is_valid, errors = CSVHandler.validate_csv_format(invalid_csv)
        assert is_valid is False
        assert len(errors) > 0
        assert any("Missing required columns" in error for error in errors)
        
        # Empty CSV
        empty_csv = ""
        
        is_valid, errors = CSVHandler.validate_csv_format(empty_csv)
        assert is_valid is False
        assert any("empty" in error for error in errors)
    
    def test_get_sample_csv(self):
        """Test sample CSV generation"""
        sample_csv = CSVHandler.get_sample_csv()
        
        assert "username" in sample_csv
        assert "email" in sample_csv
        assert "john.doe" in sample_csv
        assert "jane.smith" in sample_csv
        assert "HR Admin" in sample_csv
        assert "Department Manager" in sample_csv