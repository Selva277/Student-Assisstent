# launcher.py
import streamlit as st
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from src.auth.auth_manager import AuthManager

# Page configuration
st.set_page_config(
    page_title="EduMate",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto"
)

def check_authentication():
    """Check user authentication status and return appropriate page"""
    auth_manager = AuthManager()
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    
    # Check for remember me token if not authenticated
    if not st.session_state.authenticated and 'remember_token' in st.session_state:
        token = st.session_state.remember_token
        result = auth_manager.validate_remember_token(token)
        
        if result['success']:
            st.session_state.authenticated = True
            st.session_state.user_data = {
                'user_id': result['user_id'],
                'email': result['email'],
                'is_profile_complete': result['is_profile_complete']
            }
    
    return st.session_state.authenticated, st.session_state.user_data

def load_page(page_name):
    """Dynamically load and execute a page"""
    try:
        if page_name == "auth":
            # Load authentication page
            exec(open("src/auth/auth_app.py").read())
        elif page_name == "profile":
            # Load student profile page
            exec(open("src/auth/student_profile.py").read())
        elif page_name == "main":
            # Load main application
            exec(open("main.py").read())
    except FileNotFoundError as e:
        st.error(f"❌ Error loading page: {e}")
        st.error("Please make sure all required files are in the correct locations.")
    except Exception as e:
        st.error(f"❌ An error occurred: {e}")

def show_loading_screen():
    """Show a loading screen while determining which page to load"""
    st.markdown("""
        <div style='
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 70vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            margin: 2rem;
        '>
            <div style='
                background: rgba(255, 255, 255, 0.95);
                padding: 3rem;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
            '>
                <h1 style='
                    font-size: 3rem;
                    margin-bottom: 1rem;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                '>🎓 EduMate</h1>
                <p style='font-size: 1.2rem; color: #64748b; margin-bottom: 2rem;'>
                    Your AI-Powered Learning Companion
                </p>
                <div style='
                    width: 60px;
                    height: 60px;
                    margin: 0 auto;
                    border: 4px solid #e2e8f0;
                    border-top: 4px solid #6366f1;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                '>
                </div>
            </div>
        </div>
        
        <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    """Main launcher function"""
    
    # Show loading screen briefly
    loading_placeholder = st.empty()
    with loading_placeholder.container():
        show_loading_screen()
    
    # Small delay for better UX
    import time
    time.sleep(0.5)
    
    # Clear loading screen
    loading_placeholder.empty()
    
    # Check authentication status
    is_authenticated, user_data = check_authentication()
    
    # Determine which page to load based on authentication status
    if not is_authenticated:
        # User is not logged in - show authentication page
        st.info("🔐 Please log in to access EduMate")
        load_page("auth")
        
    elif user_data and not user_data.get('is_profile_complete', False):
        # User is logged in but profile is incomplete - show profile setup
        st.info("👨‍🎓 Please complete your profile to get started")
        load_page("profile")
        
    else:
        # User is logged in and profile is complete - show main application
        # Add logout button in sidebar
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"**Welcome, {user_data.get('email', 'User')}!** 👋")
            
            if st.button("🚪 Logout", type="secondary", use_container_width=True):
                auth_manager = AuthManager()
                auth_manager.logout_user(user_data['user_id'])
                st.success("✅ Logged out successfully!")
                st.rerun()
            
            if st.button("⚙️ Edit Profile", type="secondary", use_container_width=True):
                # Temporarily mark profile as incomplete to show profile page
                st.session_state.user_data['is_profile_complete'] = False
                st.rerun()
        
        # Load main application
        load_page("main")

def show_error_page(error_message):
    """Show error page when something goes wrong"""
    st.error("❌ Application Error")
    st.markdown(f"""
        <div style='
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 12px;
            padding: 2rem;
            margin: 2rem 0;
            text-align: center;
        '>
            <h3 style='color: #b91c1c; margin-bottom: 1rem;'>
                🚨 Something went wrong!
            </h3>
            <p style='color: #7f1d1d; margin-bottom: 1rem;'>
                {error_message}
            </p>
            <p style='color: #7f1d1d; font-size: 0.9rem;'>
                Please check your file structure and try again.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Retry", type="primary"):
        st.rerun()

# Debug information (only shown in development)
def show_debug_info():
    """Show debug information for development"""
    if st.checkbox("🔧 Show Debug Info"):
        st.json({
            "authenticated": st.session_state.get('authenticated', False),
            "user_data": st.session_state.get('user_data'),
            "session_keys": list(st.session_state.keys()),
            "current_directory": str(Path.cwd()),
            "files_exist": {
                "main.py": os.path.exists("main.py"),
                "auth_app.py": os.path.exists("src/auth/auth_app.py"),
                "student_profile.py": os.path.exists("src/auth/student_profile.py"),
                "auth_manager.py": os.path.exists("src/auth/auth_manager.py")
            }
        })

if __name__ == "__main__":
    try:
        main()
        
        # Show debug info at the bottom (only in development)
        with st.expander("🔧 Developer Tools", expanded=False):
            show_debug_info()
            
    except Exception as e:
        show_error_page(str(e))
        st.exception(e)  # This will show the full traceback in development