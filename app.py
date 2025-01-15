import streamlit as st
import requests
import json
from typing import Optional

class GPTTrainerAuth:
    def __init__(self):
        """Initialize the GPT-Trainer authentication handler."""
        # Using GPT-Trainer's standard authentication endpoint
        self.api_endpoint = "https://app.gpt-trainer.com/api/v1/verify-token"
        
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
            elif response.status_code == 401:
                st.error("Invalid token. Please check your token and try again.")
            else:
                st.error(f"Verification failed. Status code: {response.status_code}")
            return False, None
            
        except requests.exceptions.ConnectionError:
            st.error("Failed to connect to GPT-Trainer. Please check your internet connection.")
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
    st.title("Login with GPT-Trainer")
    
    st.markdown("""
    ### How to get your token:
    1. Go to your GPT-Trainer dashboard
    2. Find your chatbot configuration
    3. Copy your authentication token
    """)
    
    token = st.text_input("Enter your GPT-Trainer token:", type="password")
    
    if st.button("Login"):
        auth_handler = GPTTrainerAuth()
        success, user_data = auth_handler.verify_token(token)
        
        if success:
            st.session_state.authenticated = True
            st.session_state.user_data = user_data
            st.success("Successfully authenticated!")
            st.rerun()

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