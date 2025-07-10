import streamlit as st
import pandas as pd
from datetime import datetime

def main():
    st.set_page_config(
        page_title="Backoffice User Manager",
        page_icon="👥",
        layout="wide"
    )
    
    # Check if Azure configuration is available
    azure_configured = check_azure_config()
    
    # Authentication
    if not authenticate_user():
        st.stop()
    
    # Show configuration status
    display_config_status(azure_configured)
    
    # Navigation
    pages = {
        "User Management": render_user_management,
        "Bulk Import": render_bulk_import,
        "Audit Logs": render_audit_logs
    }
    
    # Sidebar navigation
    selected_page = st.sidebar.selectbox("Navigate", list(pages.keys()))
    pages[selected_page](azure_configured)

def check_azure_config():
    """Check if Azure configuration is available"""
    try:
        # Check if secrets are configured
        if hasattr(st, 'secrets') and 'azure' in st.secrets:
            keyvault_url = st.secrets['azure'].get('keyvault_url', '')
            if keyvault_url and keyvault_url != "https://your-keyvault.vault.azure.net/":
                return True
        return False
    except Exception:
        return False

def display_config_status(azure_configured):
    """Display configuration status in sidebar"""
    st.sidebar.markdown("---")
    if azure_configured:
        st.sidebar.success("🔗 Azure Connected")
    else:
        st.sidebar.warning("⚠️ Demo Mode")
        st.sidebar.info("Configure Azure secrets to use live data")

def authenticate_user():
    """Handle user authentication"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 Authentication")
        
        with st.form("auth_form"):
            username = st.text_input("Username", value="demo")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if username and password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("Successfully authenticated!")
                    st.rerun()
                else:
                    st.error("Please enter both username and password")
        
        st.info("Enter any username and password to continue")
        return False
    
    # Add logout button to sidebar
    st.sidebar.success(f"Logged in as: {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
    
    return True

def get_sample_users():
    """Return sample user data"""
    return pd.DataFrame({
        'username': ['john.doe', 'jane.smith', 'admin', 'hr.manager'],
        'email': ['john@company.com', 'jane@company.com', 'admin@company.com', 'hr@company.com'],
        'full_name': ['John Doe', 'Jane Smith', 'Admin User', 'HR Manager'],
        'role': ['HR Admin', 'Department Manager', 'Super Admin', 'HR Admin'],
        'department': ['Human Resources', 'Engineering', 'IT', 'Human Resources'],
        'is_active': [True, True, True, False],
        'created_date': [datetime.now(), datetime.now(), datetime.now(), datetime.now()],
        'last_modified': [datetime.now(), datetime.now(), datetime.now(), datetime.now()],
        'permissions': ['create_user,edit_user,view_users', 'view_users', 'all_permissions', 'create_user,view_users']
    })

def render_user_management(azure_configured):
    """User management page"""
    st.title("👥 User Management")
    
    if not azure_configured:
        st.info("🚧 Running in demo mode with sample data. Configure Azure Key Vault for live data.")
    
    # Get users data
    if azure_configured:
        users_df = get_users_from_azure()
    else:
        users_df = get_sample_users()
    
    # Tabs for different operations
    tab1, tab2, tab3 = st.tabs(["View Users", "Add User", "Edit User"])
    
    with tab1:
        render_users_table(users_df, azure_configured)
    
    with tab2:
        render_add_user_form(users_df, azure_configured)
    
    with tab3:
        render_edit_user_form(users_df, azure_configured)

def render_users_table(users_df, azure_configured):
    """Display users in a table"""
    st.subheader("Current Users")
    
    if users_df.empty:
        st.info("No users found.")
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
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    
    if not azure_configured:
        st.info("💡 This is sample data. Configure Azure to manage real users.")

def render_add_user_form(users_df, azure_configured):
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
            if username and email and full_name and department:
                if azure_configured:
                    st.success(f"User {username} would be added to Azure Key Vault!")
                    st.info("Azure integration: User would be saved to Key Vault")
                else:
                    st.success(f"User {username} added successfully! (Demo mode)")
                    st.info("💡 In production, this would save to Azure Key Vault")
            else:
                st.error("Please fill in all required fields.")

def render_edit_user_form(users_df, azure_configured):
    """Form for editing existing users"""
    st.subheader("Edit User")
    
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
                if azure_configured:
                    st.success(f"User {selected_user} would be updated in Azure Key Vault!")
                else:
                    st.success(f"User {selected_user} updated successfully! (Demo mode)")

def render_bulk_import(azure_configured):
    """Bulk import page"""
    st.title("📂 Bulk Import Users")
    
    if not azure_configured:
        st.info("🚧 Running in demo mode. Configure Azure Key Vault for live imports.")
    
    # Tabs for different import options
    tab1, tab2 = st.tabs(["Upload CSV", "Download Template"])
    
    with tab1:
        st.subheader("Upload CSV File")
        
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.success("CSV file uploaded successfully!")
                
                st.subheader("Data Preview")
                st.dataframe(df.head(10), use_container_width=True)
                
                if azure_configured:
                    st.info("🔄 Would validate and import to Azure Key Vault")
                else:
                    st.info("💡 In production, this would import to Azure Key Vault")
                
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
    
    with tab2:
        st.subheader("Download CSV Template")
        
        # Generate sample CSV
        sample_data = {
            'username': ['john.doe', 'jane.smith'],
            'email': ['john@company.com', 'jane@company.com'],
            'full_name': ['John Doe', 'Jane Smith'],
            'role': ['HR Admin', 'Department Manager'],
            'department': ['Human Resources', 'Engineering'],
            'is_active': [True, True],
            'created_date': [datetime.now().isoformat(), datetime.now().isoformat()],
            'last_modified': [datetime.now().isoformat(), datetime.now().isoformat()],
            'permissions': ['create_user,edit_user,view_users', 'view_users']
        }
        
        sample_df = pd.DataFrame(sample_data)
        csv_data = sample_df.to_csv(index=False)
        
        st.download_button(
            label="Download Template",
            data=csv_data,
            file_name="user_template.csv",
            mime="text/csv"
        )
        
        st.dataframe(sample_df, use_container_width=True)

def render_audit_logs(azure_configured):
    """Audit logs page"""
    st.title("📋 Audit Logs")
    
    if not azure_configured:
        st.info("🚧 Running in demo mode with sample audit data.")
    
    # Sample audit data
    sample_logs = pd.DataFrame({
        'timestamp': [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ],
        'user_id': ['admin@company.com', 'hr@company.com', 'admin@company.com'],
        'action': ['create_user', 'edit_user', 'bulk_import'],
        'target_user': ['john.doe', 'jane.smith', 'multiple_users'],
        'details': ['Created new HR Admin user', 'Updated user role', 'Imported 5 users from CSV']
    })
    
    st.dataframe(sample_logs, use_container_width=True)
    
    if azure_configured:
        st.info("🔄 Would retrieve real audit data from Azure Log Analytics")
    else:
        st.info("💡 In production, this would show real audit data from Azure Log Analytics")

def get_users_from_azure():
    """Get users from Azure Key Vault (placeholder)"""
    try:
        # This would implement actual Azure Key Vault integration
        # For now, return sample data
        return get_sample_users()
    except Exception as e:
        st.error(f"Error connecting to Azure: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    main()