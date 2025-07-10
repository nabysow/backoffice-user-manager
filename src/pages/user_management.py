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
    st.title("👥 User Management")
    
    # Check permissions
    if not check_permission("view_users"):
        st.error("You don't have permission to view this page")
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
    
    # Tabs for different operations
    tab1, tab2, tab3 = st.tabs(["View Users", "Add User", "Edit User"])
    
    with tab1:
        render_users_table(kv_manager, audit_logger)
    
    with tab2:
        if check_permission("create_user"):
            render_add_user_form(kv_manager, audit_logger)
        else:
            st.error("You don't have permission to create users")
    
    with tab3:
        if check_permission("edit_user"):
            render_edit_user_form(kv_manager, audit_logger)
        else:
            st.error("You don't have permission to edit users")

def render_users_table(kv_manager: KeyVaultUserManager, audit_logger: AuditLogger):
    """Display users in a table with search and filter options"""
    st.subheader("Current Users")
    
    # Get users data
    users_df = kv_manager.get_users_df()
    
    if users_df.empty:
        st.info("No users found. Add some users to get started.")
        return
    
    # Search and filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("Search by name or email", "")
    with col2:
        role_filter = st.selectbox("Filter by role", ["All"] + list(users_df['role'].unique()))
    with col3:
        status_filter = st.selectbox("Filter by status", ["All", "Active", "Inactive"])
    
    # Apply filters
    filtered_df = users_df.copy()
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['full_name'].str.contains(search_term, case=False, na=False) |
            filtered_df['email'].str.contains(search_term, case=False, na=False)
        ]
    
    if role_filter != "All":
        filtered_df = filtered_df[filtered_df['role'] == role_filter]
    
    if status_filter != "All":
        status_bool = status_filter == "Active"
        filtered_df = filtered_df[filtered_df['is_active'] == status_bool]
    
    # Display table
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Action buttons
    if check_permission("delete_user"):
        st.subheader("User Actions")
        selected_user = st.selectbox(
            "Select user for actions",
            options=filtered_df['username'].tolist(),
            index=None,
            placeholder="Choose a user..."
        )
        
        if selected_user:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Deactivate User", type="secondary"):
                    deactivate_user(kv_manager, audit_logger, selected_user)
            with col2:
                if st.button("Delete User", type="primary"):
                    delete_user(kv_manager, audit_logger, selected_user)

def render_add_user_form(kv_manager: KeyVaultUserManager, audit_logger: AuditLogger):
    """Form for adding new users"""
    st.subheader("Add New User")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username*")
            email = st.text_input("Email*")
            full_name = st.text_input("Full Name*")
        
        with col2:
            role = st.selectbox("Role*", ["Super Admin", "HR Admin", "Department Manager", "Viewer"])
            department = st.text_input("Department*")
            is_active = st.checkbox("Active", value=True)
        
        submitted = st.form_submit_button("Add User")
        
        if submitted:
            # Validate input
            user_data = {
                'username': username,
                'email': email,
                'full_name': full_name,
                'role': role,
                'department': department
            }
            
            # Get existing users for validation
            existing_users_df = kv_manager.get_users_df()
            existing_usernames = existing_users_df['username'].tolist() if not existing_users_df.empty else []
            
            is_valid, errors = validate_user_data(user_data, existing_usernames)
            
            if not is_valid:
                for error in errors:
                    st.error(error)
            else:
                # Create new user
                new_user = BackofficeUser(
                    username=username,
                    email=email,
                    full_name=full_name,
                    role=role,
                    department=department,
                    is_active=is_active,
                    created_date=datetime.now(),
                    last_modified=datetime.now(),
                    permissions=get_permissions_for_role(role)
                )
                
                # Add to existing users
                existing_users = CSVHandler.csv_to_users(existing_users_df.to_csv(index=False)) if not existing_users_df.empty else []
                existing_users.append(new_user)
                
                # Update Key Vault
                new_df = pd.DataFrame([user.to_dict() for user in existing_users])
                if kv_manager.update_users_df(new_df):
                    st.success(f"User {username} added successfully!")
                    audit_logger.log_user_action(
                        user_id=st.session_state.get('username', 'unknown'),
                        action="create_user",
                        target_user=username,
                        details={"role": role, "department": department}
                    )
                    st.rerun()
                else:
                    st.error("Failed to add user to Key Vault")

def render_edit_user_form(kv_manager: KeyVaultUserManager, audit_logger: AuditLogger):
    """Form for editing existing users"""
    st.subheader("Edit User")
    
    # Get users for selection
    users_df = kv_manager.get_users_df()
    
    if users_df.empty:
        st.info("No users available to edit")
        return
    
    selected_user = st.selectbox(
        "Select user to edit",
        options=users_df['username'].tolist(),
        index=None,
        placeholder="Choose a user..."
    )
    
    if selected_user:
        user_data = users_df[users_df['username'] == selected_user].iloc[0]
        
        with st.form("edit_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                email = st.text_input("Email", value=user_data['email'])
                full_name = st.text_input("Full Name", value=user_data['full_name'])
            
            with col2:
                role = st.selectbox(
                    "Role",
                    ["Super Admin", "HR Admin", "Department Manager", "Viewer"],
                    index=["Super Admin", "HR Admin", "Department Manager", "Viewer"].index(user_data['role'])
                )
                department = st.text_input("Department", value=user_data['department'])
                is_active = st.checkbox("Active", value=user_data['is_active'])
            
            submitted = st.form_submit_button("Update User")
            
            if submitted:
                # Update user data
                users_df.loc[users_df['username'] == selected_user, 'email'] = email
                users_df.loc[users_df['username'] == selected_user, 'full_name'] = full_name
                users_df.loc[users_df['username'] == selected_user, 'role'] = role
                users_df.loc[users_df['username'] == selected_user, 'department'] = department
                users_df.loc[users_df['username'] == selected_user, 'is_active'] = is_active
                users_df.loc[users_df['username'] == selected_user, 'last_modified'] = datetime.now().isoformat()
                users_df.loc[users_df['username'] == selected_user, 'permissions'] = ','.join(get_permissions_for_role(role))
                
                # Update Key Vault
                if kv_manager.update_users_df(users_df):
                    st.success(f"User {selected_user} updated successfully!")
                    audit_logger.log_user_action(
                        user_id=st.session_state.get('username', 'unknown'),
                        action="edit_user",
                        target_user=selected_user,
                        details={"role": role, "department": department}
                    )
                    st.rerun()
                else:
                    st.error("Failed to update user in Key Vault")

def deactivate_user(kv_manager: KeyVaultUserManager, audit_logger: AuditLogger, username: str):
    """Deactivate a user"""
    users_df = kv_manager.get_users_df()
    users_df.loc[users_df['username'] == username, 'is_active'] = False
    users_df.loc[users_df['username'] == username, 'last_modified'] = datetime.now().isoformat()
    
    if kv_manager.update_users_df(users_df):
        st.success(f"User {username} deactivated successfully!")
        audit_logger.log_user_action(
            user_id=st.session_state.get('username', 'unknown'),
            action="deactivate_user",
            target_user=username
        )
        st.rerun()
    else:
        st.error("Failed to deactivate user")

def delete_user(kv_manager: KeyVaultUserManager, audit_logger: AuditLogger, username: str):
    """Delete a user"""
    users_df = kv_manager.get_users_df()
    users_df = users_df[users_df['username'] != username]
    
    if kv_manager.update_users_df(users_df):
        st.success(f"User {username} deleted successfully!")
        audit_logger.log_user_action(
            user_id=st.session_state.get('username', 'unknown'),
            action="delete_user",
            target_user=username
        )
        st.rerun()
    else:
        st.error("Failed to delete user")