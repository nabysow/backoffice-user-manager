#!/usr/bin/env python3
"""
Test Azure integration with exact CSV format
"""

from src.utils.csv_handler import CSVHandler
from src.models.user_model import BackofficeUser

def test_azure_csv_format():
    """Test the exact Azure CSV format integration"""
    print("=== Azure CSV Format Integration Test ===")
    
    # Create sample users using exact CSV structure
    users = [
        BackofficeUser(
            UserName="test.user1",
            Email="test.user1@company.com", 
            Password="",
            IsConfirmed=True,
            Roles="HR Admin"
        ),
        BackofficeUser(
            UserName="test.user2",
            Email="test.user2@company.com",
            Password="",
            IsConfirmed=False,
            Roles=""
        )
    ]
    
    # Test CSV generation
    print("1. Testing CSV generation...")
    csv_output = CSVHandler.users_to_csv(users)
    print("Generated CSV:")
    print(csv_output)
    
    # Test CSV parsing back
    print("2. Testing CSV parsing...")
    parsed_users = CSVHandler.csv_to_users(csv_output)
    print(f"Parsed {len(parsed_users)} users:")
    for user in parsed_users:
        print(f"  - {user.UserName} | {user.Email} | IsConfirmed: {user.IsConfirmed} | Roles: '{user.Roles}'")
    
    # Test backward compatibility properties
    print("\\n3. Testing backward compatibility...")
    for user in parsed_users:
        print(f"  - username: {user.username} | email: {user.email} | is_active: {user.is_active} | role: '{user.role}'")
    
    # Validate format
    print("\\n4. Validating Azure service format...")
    is_valid, errors = CSVHandler.validate_csv_format(csv_output)
    print(f"Valid: {is_valid}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Ready for Azure .NET container app!")

def test_sample_download():
    """Test sample CSV download"""
    print("\\n=== Sample CSV Test ===")
    sample = CSVHandler.get_sample_csv()
    print("Sample CSV for users:")
    print(sample)
    
    # Validate sample
    is_valid, errors = CSVHandler.validate_csv_format(sample)
    print(f"Sample valid: {is_valid}")
    if errors:
        for error in errors:
            print(f"  - {error}")

if __name__ == "__main__":
    test_azure_csv_format()
    test_sample_download()