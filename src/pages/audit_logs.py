import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.azure_services.audit_logger import AuditLogger
from src.azure_services.auth_manager import check_permission

def render():
    st.title("📋 Audit Logs")
    
    # Check permissions
    if not check_permission("view_audit_logs"):
        st.error("You don't have permission to view audit logs")
        return
    
    # Initialize audit logger
    try:
        audit_logger = AuditLogger()
    except Exception as e:
        st.error(f"Error initializing audit logger: {e}")
        return
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Recent Activity", "Search Logs", "Export Logs"])
    
    with tab1:
        render_recent_activity(audit_logger)
    
    with tab2:
        render_search_logs(audit_logger)
    
    with tab3:
        render_export_logs(audit_logger)

def render_recent_activity(audit_logger: AuditLogger):
    """Display recent audit activity"""
    st.subheader("Recent Activity")
    
    # Time range selector
    col1, col2 = st.columns(2)
    with col1:
        time_range = st.selectbox(
            "Time Range",
            ["Last 24 hours", "Last 7 days", "Last 30 days", "Custom range"]
        )
    
    # Calculate date range
    end_date = datetime.now()
    if time_range == "Last 24 hours":
        start_date = end_date - timedelta(hours=24)
    elif time_range == "Last 7 days":
        start_date = end_date - timedelta(days=7)
    elif time_range == "Last 30 days":
        start_date = end_date - timedelta(days=30)
    else:  # Custom range
        with col2:
            start_date = st.date_input("Start Date", value=end_date - timedelta(days=7))
            start_date = datetime.combine(start_date, datetime.min.time())
    
    try:
        # Get audit logs
        logs_df = audit_logger.get_audit_logs(start_date, end_date)
        
        if logs_df.empty:
            st.info("No audit logs found for the selected time range")
            return
        
        # Display summary metrics
        st.subheader("Activity Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Actions", len(logs_df))
        with col2:
            unique_users = logs_df['user_id'].nunique()
            st.metric("Active Users", unique_users)
        with col3:
            action_counts = logs_df['action'].value_counts()
            most_common_action = action_counts.index[0] if not action_counts.empty else "N/A"
            st.metric("Most Common Action", most_common_action)
        with col4:
            recent_actions = logs_df[logs_df['timestamp'] >= (end_date - timedelta(hours=1))]
            st.metric("Actions (Last Hour)", len(recent_actions))
        
        # Action breakdown
        st.subheader("Action Breakdown")
        
        action_counts = logs_df['action'].value_counts()
        
        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart(action_counts)
        with col2:
            st.write("**Action Counts:**")
            for action, count in action_counts.items():
                st.write(f"• {action}: {count}")
        
        # Recent logs table
        st.subheader("Recent Logs")
        
        # Sort by timestamp (most recent first)
        logs_df['timestamp'] = pd.to_datetime(logs_df['timestamp'])
        logs_df = logs_df.sort_values('timestamp', ascending=False)
        
        # Display logs
        st.dataframe(
            logs_df.head(50),
            use_container_width=True,
            hide_index=True
        )
        
        if len(logs_df) > 50:
            st.info(f"Showing 50 most recent logs of {len(logs_df)} total")
    
    except Exception as e:
        st.error(f"Error retrieving audit logs: {str(e)}")

def render_search_logs(audit_logger: AuditLogger):
    """Search and filter audit logs"""
    st.subheader("Search Logs")
    
    # Search filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        user_filter = st.text_input("User ID", placeholder="Enter user ID to filter")
    
    with col2:
        action_filter = st.selectbox(
            "Action",
            ["All", "create_user", "edit_user", "delete_user", "bulk_import", "deactivate_user"]
        )
    
    with col3:
        target_user_filter = st.text_input("Target User", placeholder="Enter target user to filter")
    
    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    # Convert dates to datetime
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Search button
    if st.button("Search Logs", type="primary"):
        try:
            # Get all logs for the date range
            logs_df = audit_logger.get_audit_logs(start_datetime, end_datetime)
            
            if logs_df.empty:
                st.info("No logs found for the specified criteria")
                return
            
            # Apply filters
            filtered_logs = logs_df.copy()
            
            if user_filter:
                filtered_logs = filtered_logs[
                    filtered_logs['user_id'].str.contains(user_filter, case=False, na=False)
                ]
            
            if action_filter != "All":
                filtered_logs = filtered_logs[filtered_logs['action'] == action_filter]
            
            if target_user_filter:
                filtered_logs = filtered_logs[
                    filtered_logs['target_user'].str.contains(target_user_filter, case=False, na=False)
                ]
            
            # Display results
            st.subheader("Search Results")
            
            if filtered_logs.empty:
                st.info("No logs match the search criteria")
            else:
                st.success(f"Found {len(filtered_logs)} matching logs")
                
                # Sort by timestamp (most recent first)
                filtered_logs['timestamp'] = pd.to_datetime(filtered_logs['timestamp'])
                filtered_logs = filtered_logs.sort_values('timestamp', ascending=False)
                
                st.dataframe(
                    filtered_logs,
                    use_container_width=True,
                    hide_index=True
                )
        
        except Exception as e:
            st.error(f"Error searching logs: {str(e)}")

def render_export_logs(audit_logger: AuditLogger):
    """Export audit logs"""
    st.subheader("Export Logs")
    
    st.info("Export audit logs for compliance reporting or external analysis.")
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox("Export Format", ["CSV", "JSON"])
    
    with col2:
        export_range = st.selectbox(
            "Time Range",
            ["Last 7 days", "Last 30 days", "Last 90 days", "Custom range"]
        )
    
    # Date range for custom export
    if export_range == "Custom range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now())
    else:
        # Calculate date range
        end_date = datetime.now()
        if export_range == "Last 7 days":
            start_date = end_date - timedelta(days=7)
        elif export_range == "Last 30 days":
            start_date = end_date - timedelta(days=30)
        elif export_range == "Last 90 days":
            start_date = end_date - timedelta(days=90)
        
        start_date = start_date.date()
        end_date = end_date.date()
    
    # Export button
    if st.button("Generate Export", type="primary"):
        try:
            # Convert dates to datetime
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # Get logs
            logs_df = audit_logger.get_audit_logs(start_datetime, end_datetime)
            
            if logs_df.empty:
                st.warning("No logs found for the specified date range")
                return
            
            # Prepare export data
            if export_format == "CSV":
                export_data = logs_df.to_csv(index=False)
                file_name = f"audit_logs_{start_date}_to_{end_date}.csv"
                mime_type = "text/csv"
            else:  # JSON
                export_data = logs_df.to_json(orient='records', date_format='iso', indent=2)
                file_name = f"audit_logs_{start_date}_to_{end_date}.json"
                mime_type = "application/json"
            
            # Display export summary
            st.success(f"Export ready! {len(logs_df)} logs prepared for download.")
            
            # Download button
            st.download_button(
                label=f"Download {export_format}",
                data=export_data,
                file_name=file_name,
                mime=mime_type
            )
            
            # Export statistics
            st.subheader("Export Statistics")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Records", len(logs_df))
            with col2:
                st.metric("Unique Users", logs_df['user_id'].nunique())
            with col3:
                st.metric("Date Range", f"{(end_datetime - start_datetime).days} days")
            
            # Action breakdown
            action_counts = logs_df['action'].value_counts()
            st.write("**Actions in Export:**")
            for action, count in action_counts.items():
                st.write(f"• {action}: {count}")
        
        except Exception as e:
            st.error(f"Error generating export: {str(e)}")