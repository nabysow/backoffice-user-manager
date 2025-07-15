#!/usr/bin/env python3
"""
Test script to verify exact CSV structure matches the Azure service pattern
"""

from src.utils.csv_handler import CSVHandler
from src.models.user_model import BackofficeUser

# Exact CSV from your pattern
original_csv = """UserName;Email;Password;IsConfirmed;Roles;
jg.anders;JanGerrit.Anders@uba.de;;true;;
ma.dahham;MohammadAmin.Dahham@uba.de;;true;TeamDaten;
juliane.haufe;Juliane.Haufe@uba.de;;true;;
jana.rehmann;Jana.Rehmann@uba.de;;true;;
juliane.rode;Juliane.Rode@uba.de;;true;TeamFinanzen;"""

def test_exact_structure():
    """Test that we can parse and regenerate the exact same CSV structure"""
    print("=== Testing Exact CSV Structure ===")
    print("Original CSV:")
    print(original_csv)
    print()
    
    # Parse users
    users = CSVHandler.csv_to_users(original_csv)
    print(f"Parsed {len(users)} users:")
    for user in users:
        print(f"  - {user.UserName} | {user.Email} | '{user.Password}' | {user.IsConfirmed} | '{user.Roles}'")
    print()
    
    # Convert back to CSV
    regenerated_csv = CSVHandler.users_to_csv(users)
    print("Regenerated CSV:")
    print(regenerated_csv)
    print()
    
    # Check if they match (ignoring whitespace differences)
    original_lines = [line.strip() for line in original_csv.strip().split('\n')]
    regenerated_lines = [line.strip() for line in regenerated_csv.strip().split('\n')]
    
    print("=== Structure Validation ===")
    if original_lines == regenerated_lines:
        print("✅ CSV structure matches exactly!")
    else:
        print("❌ CSV structure differs:")
        for i, (orig, regen) in enumerate(zip(original_lines, regenerated_lines)):
            if orig != regen:
                print(f"  Line {i+1}:")
                print(f"    Original:    {orig}")
                print(f"    Regenerated: {regen}")

def test_azure_compatibility():
    """Test Azure service compatibility"""
    print("\n=== Azure Service Compatibility Test ===")
    
    # Validate CSV format
    is_valid, errors = CSVHandler.validate_csv_format(original_csv)
    print(f"Valid for Azure service: {is_valid}")
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ No validation errors - ready for Azure service!")
    
    # Test sample CSV
    sample = CSVHandler.get_sample_csv()
    print("\nSample CSV for Azure service:")
    print(sample)

if __name__ == "__main__":
    test_exact_structure()
    test_azure_compatibility()