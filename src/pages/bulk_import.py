import streamlit as st
import pandas as pd
from datetime import datetime
from src.azure_services.keyvault_client import KeyVaultUserManager
from src.azure_services.auth_manager import check_permission
from src.azure_services.audit_logger import AuditLogger
from src.models.user_model import BackofficeUser, get_permissions_for_role
from src.utils.validators import validate_user_data
from src.utils.csv_handler import CSVHandler

def render():
    st.title("📂 Bulk Import Users")
    
    # Check permissions
    if not check_permission("bulk_import"):
        st.error("You don't have permission to bulk import users")
        return
    
    # Initialize services
    try:
        kv_manager = KeyVaultUserManager(
            vault_url=st.secrets["azure"]["keyvault_url"],
            secret_name=st.secrets["azure"]["users_secret_name"]
        )
        audit_logger = AuditLogger()
    except Exception as e:
        st.error(f"Error initializing services: {e}")
        return
    
    # Tabs for different import options
    tab1, tab2, tab3 = st.tabs(["Upload CSV", "Download Template", "Import History"])
    
    with tab1:
        render_csv_upload(kv_manager, audit_logger)
    
    with tab2:
        render_template_download()
    
    with tab3:
        render_import_history(audit_logger)

def render_csv_upload(kv_manager: KeyVaultUserManager, audit_logger: AuditLogger):
    """Handle CSV file upload and processing"""
    st.subheader("Upload CSV File")
    
    st.info("Upload a CSV file containing user data. The file must include all required columns.")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="Upload a CSV file with user data"
    )
    
    if uploaded_file is not None:
        try:
            # Read the uploaded file
            csv_content = uploaded_file.read().decode('utf-8')
            
            # Validate CSV format
            is_valid, errors = CSVHandler.validate_csv_format(csv_content)
            
            if not is_valid:
                st.error("CSV validation failed:")
                for error in errors:
                    st.error(f"• {error}")
                return
            
            # Parse CSV
            df = pd.read_csv(uploaded_file)
            st.success("CSV file uploaded and validated successfully!")
            
            # Display preview
            st.subheader("Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            if len(df) > 10:
                st.info(f"Showing first 10 rows of {len(df)} total rows")
            
            # Validation summary
            st.subheader("Validation Summary")
            
            # Get existing users for validation
            existing_users_df = kv_manager.get_users_df()
            existing_usernames = existing_users_df['username'].tolist() if not existing_users_df.empty else []
            existing_emails = existing_users_df['email'].tolist() if not existing_users_df.empty else []
            
            validation_results = []
            valid_users = []
            
            for index, row in df.iterrows():
                user_data = {
                    'username': row['username'],
                    'email': row['email'],
                    'full_name': row['full_name'],
                    'role': row['role'],
                    'department': row['department']
                }
                
                is_valid, errors = validate_user_data(user_data, existing_usernames)
                
                # Check for duplicate emails
                if row['email'] in existing_emails:
                    errors.append(f"Email already exists: {row['email']}")
                    is_valid = False
                
                validation_results.append({
                    'row': index + 1,
                    'username': row['username'],
                    'email': row['email'],
                    'valid': is_valid,
                    'errors': errors
                })
                
                if is_valid:
                    valid_users.append(user_data)
                    existing_usernames.append(row['username'])
                    existing_emails.append(row['email'])
            
            # Display validation results
            valid_count = sum(1 for r in validation_results if r['valid'])
            invalid_count = len(validation_results) - valid_count
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", len(validation_results))
            with col2:
                st.metric("Valid Users", valid_count)
            with col3:
                st.metric("Invalid Users", invalid_count)
            
            # Show errors if any
            if invalid_count > 0:
                st.subheader("Validation Errors")
                
                error_df = pd.DataFrame([
                    {
                        'Row': r['row'],
                        'Username': r['username'],
                        'Email': r['email'],
                        'Errors': '; '.join(r['errors'])
                    }
                    for r in validation_results if not r['valid']
                ])
                
                st.dataframe(error_df, use_container_width=True)
            
            # Import options
            st.subheader("Import Options")
            
            col1, col2 = st.columns(2)
            with col1:
                import_mode = st.radio(
                    "Import Mode",
                    ["Import valid users only", "Fix errors first"],
                    help="Choose whether to import only valid users or fix all errors first"
                )
            
            with col2:
                create_backup = st.checkbox(
                    "Create backup before import",
                    value=True,
                    help="Create a backup of existing users before importing"
                )
            
            # Import button
            if st.button("Import Users", type="primary", disabled=valid_count == 0):
                if import_mode == "Fix errors first" and invalid_count > 0:
                    st.error("Please fix all validation errors before importing")
                else:
                    import_users(kv_manager, audit_logger, valid_users, create_backup)
        
        except Exception as e:
            st.error(f"Error processing CSV file: {str(e)}")

def render_template_download():
    """Provide CSV template for download"""
    st.subheader("Download CSV Template")
    
    st.info("Download a sample CSV template to ensure your file has the correct format.")
    
    # Generate sample CSV
    sample_csv = CSVHandler.get_sample_csv()
    
    # Display sample data
    st.subheader("Template Preview")
    sample_df = pd.read_csv(pd.io.common.StringIO(sample_csv))
    st.dataframe(sample_df, use_container_width=True)
    
    # Download button
    st.download_button(
        label="Download Template",
        data=sample_csv,
        file_name="user_template.csv",
        mime="text/csv"
    )
    
    # Column descriptions
    st.subheader("Column Descriptions")
    
    column_descriptions = {
        "username": "Unique username (3+ characters, letters, numbers, dots, hyphens, underscores)",
        "email": "Valid email address",
        "full_name": "Full name (2+ characters)",
        "role": "User role (Super Admin, HR Admin, Department Manager, Viewer)",
        "department": "Department name",
        "is_active": "Account status (True/False)",
        "created_date": "Account creation date (ISO format)",
        "last_modified": "Last modification date (ISO format)",
        "permissions": "Comma-separated list of permissions"
    }
    
    for column, description in column_descriptions.items():
        st.write(f"**{column}**: {description}")

def render_import_history(audit_logger: AuditLogger):
    """Display import history"""
    st.subheader("Import History")
    
    # Get audit logs for bulk import actions
    try:
        logs_df = audit_logger.get_audit_logs(
            start_date=datetime.now().replace(day=1),
            end_date=datetime.now()
        )
        
        # Filter for bulk import actions
        import_logs = logs_df[logs_df['action'] == 'bulk_import'] if not logs_df.empty else pd.DataFrame()
        
        if import_logs.empty:
            st.info("No bulk import history found")
        else:
            st.dataframe(import_logs, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error retrieving import history: {str(e)}")

def import_users(kv_manager: KeyVaultUserManager, audit_logger: AuditLogger, 
                valid_users: list, create_backup: bool):
    """Import validated users to Key Vault"""
    try:
        # Create backup if requested
        if create_backup:
            backup_name = kv_manager.backup_users()
            if backup_name:
                st.success(f"Backup created: {backup_name}")
            else:
                st.error("Failed to create backup")
                return
        
        # Get existing users
        existing_users_df = kv_manager.get_users_df()
        existing_users = CSVHandler.csv_to_users(existing_users_df.to_csv(index=False)) if not existing_users_df.empty else []
        
        # Create new user objects
        new_users = []
        for user_data in valid_users:
            new_user = BackofficeUser(
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data['full_name'],
                role=user_data['role'],
                department=user_data['department'],
                is_active=True,
                created_date=datetime.now(),
                last_modified=datetime.now(),
                permissions=get_permissions_for_role(user_data['role'])
            )
            new_users.append(new_user)
        
        # Combine existing and new users
        all_users = existing_users + new_users
        
        # Update Key Vault
        new_df = pd.DataFrame([user.to_dict() for user in all_users])
        
        if kv_manager.update_users_df(new_df):
            st.success(f"Successfully imported {len(new_users)} users!")
            
            # Log the bulk import action
            audit_logger.log_user_action(
                user_id=st.session_state.get('username', 'unknown'),
                action="bulk_import",
                details={
                    "users_imported": len(new_users),
                    "backup_created": create_backup,
                    "usernames": [user.username for user in new_users]
                }
            )
            
            st.balloons()
            st.rerun()
        else:
            st.error("Failed to import users to Key Vault")
    
    except Exception as e:
        st.error(f"Error importing users: {str(e)}")