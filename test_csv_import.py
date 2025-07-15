#!/usr/bin/env python3
"""
Test script for CSV import functionality with new semicolon-delimited format
"""

from src.utils.csv_handler import CSVHandler

# Test CSV content matching the new pattern
test_csv = """UserName;Email;Password;IsConfirmed;Roles;
jg.anders;JanGerrit.Anders@uba.de;;true;;
ma.dahham;MohammadAmin.Dahham@uba.de;;true;TeamDaten;
juliane.haufe;Juliane.Haufe@uba.de;;true;;
jana.rehmann;Jana.Rehmann@uba.de;;true;;
juliane.rode;Juliane.Rode@uba.de;;true;TeamFinanzen;"""

def test_csv_validation():
    """Test CSV validation with new format"""
    print("Testing CSV validation...")
    is_valid, errors = CSVHandler.validate_csv_format(test_csv)
    print(f"Valid: {is_valid}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("No validation errors found")
    print()

def test_csv_parsing():
    """Test CSV parsing with new format"""
    print("Testing CSV parsing...")
    users = CSVHandler.csv_to_users(test_csv)
    print(f"Parsed {len(users)} users:")
    for user in users:
        print(f"  - {user.username} ({user.email}) - Role: {user.role} - Active: {user.is_active}")
    print()

def test_sample_csv():
    """Test sample CSV generation"""
    print("Testing sample CSV generation...")
    sample = CSVHandler.get_sample_csv()
    print("Sample CSV:")
    print(sample)

if __name__ == "__main__":
    test_csv_validation()
    test_csv_parsing()
    test_sample_csv()