# src/auth/student_profile.py
import streamlit as st
from src.auth.auth_manager import AuthManager

# Page configuration
st.set_page_config(
    page_title="EduMate - Complete Your Profile",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS (same styling as auth_app.py for consistency)
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
    
    /* Profile container */
    .profile-container {
        background: rgba(255, 255, 255, 0.95);
        padding: 3rem 2rem;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        max-width: 600px;
        margin: 2rem auto;
    }
    
    /* Header styling */
    .profile-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .profile-header h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .profile-header p {
        color: #64748b;
        font-size: 1.1rem;
        margin: 0;
    }
    
    /* Form styling */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div > select {
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        background: rgba(255, 255, 255, 0.8);
    }
    
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus, .stSelectbox > div > div > select:focus {
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
    
    /* Section styling */
    .profile-section {
        background: rgba(248, 250, 252, 0.8);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        border-left: 4px solid #6366f1;
    }
    
    .section-title {
        color: #1e293b;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
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
    
    /* Progress bar */
    .progress-container {
        background: rgba(248, 250, 252, 0.8);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 2rem;
    }
    
    .progress-bar {
        background: #e2e8f0;
        border-radius: 8px;
        height: 8px;
        overflow: hidden;
    }
    
    .progress-fill {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        height: 100%;
        border-radius: 8px;
        transition: width 0.3s ease;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

def calculate_progress(profile_data):
    """Calculate profile completion progress"""
    required_fields = ['name', 'year', 'course', 'interests', 'goals', 'hobbies', 'learning_style', 'current_skills']
    filled_fields = sum(1 for field in required_fields if profile_data.get(field))
    return (filled_fields / len(required_fields)) * 100

def main():
    # Check if user is authenticated
    if not st.session_state.get('authenticated', False):
        st.error("❌ Access denied! Please login first.")
        st.stop()
    
    # Check if profile is already complete
    user_data = st.session_state.get('user_data')
    if user_data and user_data.get('is_profile_complete'):
        st.success("✅ Your profile is already complete!")
        st.info("Redirecting to EduMate...")
        st.stop()
    
    auth_manager = AuthManager()
    
    # Initialize profile data in session state
    if 'profile_data' not in st.session_state:
        st.session_state.profile_data = {
            'name': '',
            'year': 1,
            'course': '',
            'interests': '',
            'goals': '',
            'hobbies': '',
            'learning_style': '',
            'current_skills': ''
        }
    
    # Main profile container
    st.markdown("<div class='profile-container'>", unsafe_allow_html=True)
    
    # Header
    st.markdown("""
        <div class='profile-header'>
            <h1>👨‍🎓 Complete Your Profile</h1>
            <p>Help us personalize your learning experience</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    progress = calculate_progress(st.session_state.profile_data)
    st.markdown(f"""
        <div class='progress-container'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                <span style='font-weight: 600; color: #1e293b;'>Profile Completion</span>
                <span style='font-weight: 600; color: #6366f1;'>{progress:.0f}%</span>
            </div>
            <div class='progress-bar'>
                <div class='progress-fill' style='width: {progress}%;'></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Profile form
    with st.form("profile_form", clear_on_submit=False):
        # Basic Information Section
        st.markdown("""
            <div class='profile-section'>
                <div class='section-title'>
                    📝 Basic Information
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            name = st.text_input(
                "Full Name *", 
                value=st.session_state.profile_data['name'],
                placeholder="Enter your full name"
            )
        with col2:
            year = st.selectbox(
                "Academic Year *",
                options=[1, 2, 3, 4],
                index=st.session_state.profile_data['year'] - 1,
                help="Select your current year of study"
            )
        
        course = st.text_input(
            "Course/Major *",
            value=st.session_state.profile_data['course'],
            placeholder="e.g., Computer Science, Mathematics, Biology"
        )
        
        # Learning Preferences Section
        st.markdown("""
            <div class='profile-section'>
                <div class='section-title'>
                    🧠 Learning Preferences
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        learning_style = st.selectbox(
            "Preferred Learning Style *",
            options=["", "Visual", "Auditory", "Kinesthetic", "Reading/Writing", "Mixed"],
            index=0 if not st.session_state.profile_data['learning_style'] else 
                  ["", "Visual", "Auditory", "Kinesthetic", "Reading/Writing", "Mixed"].index(st.session_state.profile_data['learning_style']),
            help="How do you learn best?"
        )
        
        # Interests and Goals Section
        st.markdown("""
            <div class='profile-section'>
                <div class='section-title'>
                    🎯 Interests & Goals
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        interests = st.text_area(
            "Academic Interests *",
            value=st.session_state.profile_data['interests'],
            placeholder="e.g., Artificial Intelligence, Data Science, Web Development",
            help="What subjects or topics are you most interested in?"
        )
        
        goals = st.text_area(
            "Learning Goals *",
            value=st.session_state.profile_data['goals'],
            placeholder="e.g., Master Python programming, Understand machine learning concepts",
            help="What do you want to achieve in your studies?"
        )
        
        # Personal Information Section
        st.markdown("""
            <div class='profile-section'>
                <div class='section-title'>
                    🌟 Personal Information
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        hobbies = st.text_area(
            "Hobbies & Activities *",
            value=st.session_state.profile_data['hobbies'],
            placeholder="e.g., Reading, Coding, Sports, Music",
            help="What do you enjoy doing in your free time?"
        )
        
        current_skills = st.text_area(
            "Current Skills *",
            value=st.session_state.profile_data['current_skills'],
            placeholder="e.g., Python, JavaScript, Problem Solving, Team Leadership",
            help="What skills do you currently possess?"
        )
        
        # Update session state with current values
        st.session_state.profile_data.update({
            'name': name,
            'year': year,
            'course': course,
            'interests': interests,
            'goals': goals,
            'hobbies': hobbies,
            'learning_style': learning_style,
            'current_skills': current_skills
        })
        
        # Submit button
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 Complete Profile Setup", use_container_width=True)
        
        if submitted:
            # Validation
            required_fields = {
                'name': name,
                'course': course,
                'interests': interests,
                'goals': goals,
                'hobbies': hobbies,
                'learning_style': learning_style,
                'current_skills': current_skills
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value.strip()]
            
            if missing_fields:
                st.error(f"❌ Please fill in all required fields: {', '.join(missing_fields)}")
            else:
                with st.spinner("Saving your profile..."):
                    # Save profile to database
                    user_id = st.session_state.user_data['user_id']
                    result = auth_manager.save_student_profile(user_id, st.session_state.profile_data)
                    
                    if result['success']:
                        # Update session state
                        st.session_state.user_data['is_profile_complete'] = True
                        
                        st.success("🎉 Profile completed successfully!")
                        st.balloons()
                        st.info("Welcome to EduMate! Redirecting to your dashboard...")
                        
                        # Add a small delay for better UX
                        import time
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Skip option (optional)
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⏭️ Skip for now (Complete later)", use_container_width=True):
            st.warning("You can complete your profile later from settings.")
            st.info("Redirecting to EduMate...")
            # In a real app, you might want to set a flag for incomplete profile
            import time
            time.sleep(1)
            st.rerun()
    
    # Footer
    st.markdown("""
        <div style='text-align: center; margin-top: 2rem; color: rgba(255,255,255,0.8);'>
            <p>🎓 EduMate - Personalized Learning Experience</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()