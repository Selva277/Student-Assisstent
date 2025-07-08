# auth_app.py
import streamlit as st
import re
from src.auth.auth_manager import AuthManager

# Page configuration
st.set_page_config(
    page_title="EduMate - Login",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for authentication pages
st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styling */
    .main {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Auth container */
    .auth-container {
        background: rgba(255, 255, 255, 0.95);
        padding: 3rem 2rem;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        max-width: 450px;
        margin: 2rem auto;
    }
    
    /* Header styling */
    .auth-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .auth-header h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .auth-header p {
        color: #64748b;
        font-size: 1.1rem;
        margin: 0;
    }
    
    /* Form styling */
    .stTextInput > div > div > input {
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        background: rgba(255, 255, 255, 0.8);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        background: white;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(99, 102, 241, 0.4);
    }
    
    /* Checkbox styling */
    .stCheckbox {
        margin: 1rem 0;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(248, 250, 252, 0.8);
        padding: 8px;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #64748b;
        padding: 12px 24px;
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        border-left: 4px solid #059669;
        border-radius: 8px;
    }
    
    .stError {
        background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
        border-left: 4px solid #dc2626;
        border-radius: 8px;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, "Password is valid"

def main():
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    
    # Check for remember me token
    auth_manager = AuthManager()
    
    # Check if user is already authenticated
    if st.session_state.authenticated:
        st.success("You are already logged in!")
        st.info("Redirecting to EduMate...")
        st.stop()
    
    # Main authentication container
    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
    
    # Header
    st.markdown("""
        <div class='auth-header'>
            <h1>🎓 EduMate</h1>
            <p>Your AI-Powered Learning Companion</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Authentication tabs
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
    
    with tab1:
        st.markdown("### Welcome Back!")
        
        # Login form
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("📧 Email Address", placeholder="Enter your email")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            remember_me = st.checkbox("Remember me for 30 days")
            
            login_submitted = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if login_submitted:
                if not email or not password:
                    st.error("Please fill in both email and password!")
                elif not validate_email(email):
                    st.error("Please enter a valid email address!")
                else:
                    with st.spinner("Logging in..."):
                        result = auth_manager.login_user(email, password)
                        
                        if result['success']:
                            # Set session state
                            st.session_state.authenticated = True
                            st.session_state.user_data = {
                                'user_id': result['user_id'],
                                'email': result['email'],
                                'is_profile_complete': result['is_profile_complete']
                            }
                            
                            # Handle remember me
                            if remember_me:
                                token = auth_manager.create_remember_token(result['user_id'])
                                # In a real app, you'd set this as a secure cookie
                                st.session_state.remember_token = token
                            
                            st.success(result['message'])
                            st.success("🎉 Login successful! Redirecting to EduMate...")
                            
                            # Add a small delay for better UX
                            import time
                            time.sleep(1)
                            st.rerun()
                            
                        else:
                            st.error(result['message'])
    
    with tab2:
        st.markdown("### Join EduMate Today!")
        
        # Registration form
        with st.form("register_form", clear_on_submit=False):
            new_email = st.text_input("📧 Email Address", placeholder="Enter your email")
            new_password = st.text_input("🔒 Password", type="password", placeholder="Create a password (min 6 characters)")
            confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
            
            terms_accepted = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            register_submitted = st.form_submit_button("✨ Create Account", use_container_width=True)
            
            if register_submitted:
                # Validation
                if not new_email or not new_password or not confirm_password:
                    st.error("Please fill in all fields!")
                elif not validate_email(new_email):
                    st.error("Please enter a valid email address!")
                elif new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif not terms_accepted:
                    st.error("Please accept the Terms of Service and Privacy Policy!")
                else:
                    # Validate password strength
                    is_valid, message = validate_password(new_password)
                    if not is_valid:
                        st.error(message)
                    else:
                        with st.spinner("Creating your account..."):
                            result = auth_manager.register_user(new_email, new_password)
                            
                            if result['success']:
                                st.success(result['message'])
                                st.info("🎉 Account created successfully! Please login to continue.")
                                
                                # Switch to login tab (this is more of a visual cue)
                                st.balloons()
                                
                            else:
                                st.error(result['message'])
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
        <div style='text-align: center; margin-top: 2rem; color: rgba(255,255,255,0.8);'>
            <p>🎓 EduMate - Empowering Students with AI</p>
            <p style='font-size: 0.9rem;'>© 2024 EduMate. All rights reserved.</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()