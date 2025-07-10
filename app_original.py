import streamlit as st
from src.azure_services.auth_manager import authenticate_user
from src.pages import user_management, bulk_import, audit_logs

def main():
    st.set_page_config(
        page_title="Backoffice User Manager",
        page_icon="👥",
        layout="wide"
    )
    
    # Authentication
    if not authenticate_user():
        st.stop()
    
    # Navigation
    pages = {
        "User Management": user_management,
        "Bulk Import": bulk_import,
        "Audit Logs": audit_logs
    }
    
    # Sidebar navigation
    selected_page = st.sidebar.selectbox("Navigate", list(pages.keys()))
    pages[selected_page].render()

if __name__ == "__main__":
    main()