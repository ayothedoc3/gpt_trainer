import streamlit as st
import requests
import json
from typing import Optional

class GPTTrainerAuth:
    def __init__(self, api_endpoint: str):
        """Initialize the GPT-Trainer authentication handler.
        
        Args:
            api_endpoint (str): The GPT-Trainer verification endpoint URL
        """
        self.api_endpoint = api_endpoint
        
    def verify_token(self, token: str) -> tuple[bool, Optional[dict]]:
        """Verify a user token with GPT-Trainer.
        
        Args:
            token (str): The user's authentication token
            
        Returns:
            tuple[bool, Optional[dict]]: (success status, user data if successful)
        """
        try:
            response = requests.post(
                self.api_endpoint,
                json={"token": token},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return True, response.json()
            return False, None
            
        except Exception as e:
            st.error(f"Verification error: {str(e)}")
            return False, None

def init_session_state():
    """Initialize session state variables if they don't exist."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None

def login_page():
    """Render the login page and handle authentication."""
    st.title("Login")
    
    token = st.text_input("Enter your GPT-Trainer token:", type="password")
    
    if st.button("Login"):
        auth_handler = GPTTrainerAuth(st.secrets["gpt_trainer_endpoint"])
        success, user_data = auth_handler.verify_token(token)
        
        if success:
            st.session_state.authenticated = True
            st.session_state.user_data = user_data
            st.success("Successfully authenticated!")
            st.rerun()
        else:
            st.error("Authentication failed. Please check your token.")

def main_app():
    """Render the main application content for authenticated users."""
    st.title("Welcome to the Protected App")
    
    # Display user information
    if st.session_state.user_data:
        st.write("User Information:")
        st.json(st.session_state.user_data)
    
    # Add your main app content here
    st.write("This is your protected content!")
    
    # Logout button
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user_data = None
        st.rerun()

def main():
    # Initialize session state
    init_session_state()
    
    # Show login page or main app based on authentication status
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()