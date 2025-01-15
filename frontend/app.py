# app.py
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
from typing import Optional

class AuthSystem:
    def __init__(self):
        self.api_endpoint = st.secrets["api_endpoint"]
        self.admin_key = st.secrets.get("admin_api_key")
    
    def verify_token(self, token: str) -> tuple[bool, Optional[dict]]:
        try:
            response = requests.post(
                f"{self.api_endpoint}/verify-token",
                json={"token": token},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                st.error("Invalid token. Please check your token and try again.")
            else:
                st.error(f"Verification failed. Status code: {response.status_code}")
            return False, None
            
        except Exception as e:
            st.error(f"Verification error: {str(e)}")
            return False, None
    
    def get_token_usage(self) -> Optional[pd.DataFrame]:
        if not self.admin_key:
            return None
            
        try:
            response = requests.get(
                f"{self.api_endpoint}/admin/tokens/usage",
                headers={"X-Admin-Key": self.admin_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                return pd.DataFrame(data)
            return None
            
        except Exception:
            return None

def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "main"

def render_sidebar():
    with st.sidebar:
        st.title("Navigation")
        
        if st.session_state.authenticated:
            if st.button("Dashboard"):
                st.session_state.current_page = "main"
            if st.button("Profile"):
                st.session_state.current_page = "profile"
            if "admin" in st.session_state.user_data.get("roles", []):
                if st.button("Admin Panel"):
                    st.session_state.current_page = "admin"
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.user_data = None
                st.session_state.current_page = "main"
                st.rerun()

def login_page():
    st.title("GPT-Trainer Authentication Demo")
    
    st.markdown("""
    ### Welcome to the Demo
    This application demonstrates secure token-based authentication with GPT-Trainer.
    
    Features:
    - Secure token verification
    - Role-based access control
    - Usage analytics
    - Admin dashboard
    """)
    
    token = st.text_input("Enter your token:", type="password")
    
    if st.button("Login"):
        auth_handler = AuthSystem()
        success, user_data = auth_handler.verify_token(token)
        
        if success:
            st.session_state.authenticated = True
            st.session_state.user_data = user_data
            st.success("Successfully authenticated!")
            st.rerun()

def profile_page():
    st.title("User Profile")
    
    user_data = st.session_state.user_data
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Basic Information")
        st.write(f"Username: {user_data['userName']}")
        st.write(f"User ID: {user_data['userId']}")
        st.write(f"Roles: {', '.join(user_data['roles'])}")
    
    with col2:
        st.write("### Profile Details")
        if "profile" in user_data:
            for key, value in user_data["profile"].items():
                st.write(f"{key}: {value}")

def admin_page():
    st.title("Admin Dashboard")
    
    auth_handler = AuthSystem()
    usage_data = auth_handler.get_token_usage()
    
    if usage_data is not None:
        st.write("### Token Usage Analytics")
        
        # Convert timestamp to datetime
        usage_data['timestamp'] = pd.to_datetime(usage_data['timestamp'])
        
        # Usage over time
        fig = px.line(
            usage_data,
            x='timestamp',
            title='Token Usage Over Time'
        )
        st.plotly_chart(fig)
        
        # Success rate
        success_rate = (usage_data['success'].sum() / len(usage_data)) * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Raw data
        st.write("### Raw Usage Data")
        st.dataframe(usage_data)
    else:
        st.error("Unable to fetch usage data. Make sure you have admin access.")

def main_app():
    render_sidebar()
    
    if st.session_state.current_page == "profile":
        profile_page()
    elif st.session_state.current_page == "admin":
        if "admin" in st.session_state.user_data.get("roles", []):
            admin_page()
        else:
            st.error("Access denied. Admin privileges required.")
    else:
        st.title("Welcome to Protected Content")
        st.write(f"Welcome back, {st.session_state.user_data['userName']}!")
        
        # Display user roles and permissions
        st.write("### Your Access Level")
        roles = st.session_state.user_data.get("roles", [])
        for role in roles:
            st.write(f"- {role}")

def main():
    st.set_page_config(
        page_title="GPT-Trainer Auth Demo",
        page_icon="🔒",
        layout="wide"
    )
    
    init_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()