# planner_agent.py

import os
import sys
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import google.generativeai as genai
import calendar

# Add src to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir))
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Import FAISS database
try:
    from database.document_processor import DocumentProcessor
except ImportError:
    DocumentProcessor = None
    print("⚠️ FAISS database not available - using Gemini-only mode")

class PlannerAgent:
    def __init__(self):
        """Initialize the Planner Agent with Gemini API and FAISS database."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        
        # Initialize Gemini model
        try:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception:
            try:
                self.model = genai.GenerativeModel('gemini-1.5-pro')
            except Exception:
                try:
                    self.model = genai.GenerativeModel('gemini-pro')
                except Exception:
                    available_models = genai.list_models()
                    generative_models = [
                        model for model in available_models 
                        if 'generateContent' in model.supported_generation_methods
                    ]
                    if generative_models:
                        model_name = generative_models[0].name.replace('models/', '')
                        self.model = genai.GenerativeModel(model_name)
                    else:
                        raise ValueError("No suitable generative models available")
        
        # Initialize FAISS database (optional)
        self.faiss_db = None
        if DocumentProcessor:
            try:
                self.faiss_db = DocumentProcessor()
                print("✅ FAISS database connected")
            except Exception as e:
                print(f"⚠️ FAISS database unavailable: {e}")
                self.faiss_db = None
    
    def search_course_content(self, topic: str) -> Optional[str]:
        """Search for relevant content in FAISS database."""
        if not self.faiss_db:
            return None
        
        try:
            # Search for content related to the topic
            content = self.faiss_db.search_documents(topic, top_k=5)
            return content
        except Exception as e:
            print(f"⚠️ FAISS search error: {e}")
            return None
    
    def get_course_structure(self, topic: str) -> Optional[Dict]:
        """Get course structure and available topics from FAISS database."""
        if not self.faiss_db:
            return None
        
        try:
            # Search for multiple related topics to understand course depth
            results = self.faiss_db.faiss_manager.search_by_topic(topic, top_k=10)
            
            if results['matches']:
                # Extract course structure information
                courses = {}
                chapters = set()
                topics = set()
                
                for match in results['matches']:
                    metadata = match['metadata']
                    course = metadata.get('course', 'Unknown')
                    chapter = metadata.get('chapter', 'Unknown')
                    topic_tags = metadata.get('topics', [])
                    
                    if course not in courses:
                        courses[course] = {'chapters': set(), 'topics': set()}
                    
                    courses[course]['chapters'].add(chapter)
                    courses[course]['topics'].update(topic_tags)
                    chapters.add(chapter)
                    topics.update(topic_tags)
                
                return {
                    'courses': {k: {'chapters': list(v['chapters']), 'topics': list(v['topics'])} 
                              for k, v in courses.items()},
                    'total_matches': len(results['matches']),
                    'has_content': True
                }
            
            return None
        except Exception as e:
            print(f"⚠️ Course structure analysis error: {e}")
            return None
    
    def create_planner_prompt(self, topic: str, duration: str, daily_time: str, 
                            current_level: str, learning_style: str, 
                            course_content: Optional[str] = None, 
                            course_structure: Optional[Dict] = None,
                            user_profile: Optional[Dict] = None) -> str:
        """Create a detailed prompt for generating study plan."""
        
        # Base prompt structure
        prompt = f"""
You are an expert educational planner and learning strategist. Create a comprehensive study plan based on the following requirements:

**Learning Goal:** {topic}
**Study Duration:** {duration}
**Daily Available Time:** {daily_time}
**Current Level:** {current_level}
**Learning Style:** {learning_style}

"""
        
        # Add user profile information if available
        if user_profile:
            prompt += f"""
**User Profile:**
- Name: {user_profile.get('name', 'N/A')}
- Course/Major: {user_profile.get('course', 'N/A')}
- Academic Year: {user_profile.get('year', 'N/A')}
- Interests: {user_profile.get('interests', 'N/A')}
- Goals: {user_profile.get('goals', 'N/A')}
- Learning Style Preference: {user_profile.get('learning_style', 'N/A')}
- Current Skills: {user_profile.get('current_skills', 'N/A')}

**Personalization Instructions:**
- Tailor the study plan to align with the user's course, interests, and academic goals.
- Adjust the complexity and focus based on the user's current skills and academic year.
- Incorporate the user's preferred learning style where possible.
"""
        
        # Add course content if available from FAISS
        if course_content and course_structure:
            prompt += f"""
**Available Course Content (Use as primary reference):**
{course_content}

**Course Structure Analysis:**
- Total courses available: {len(course_structure['courses'])}
- Available topics: {course_structure['total_matches']} content pieces found
- Course breakdown: {', '.join(course_structure['courses'].keys())}

**IMPORTANT:** Base your study plan on the available course content above. Structure the daily activities around the topics and chapters identified in the course content.

"""
        elif course_content:
            prompt += f"""
**Available Course Content:**
{course_content}

**IMPORTANT:** Use the course content above as the primary reference for creating the study plan.

"""
        
        prompt += f"""
**Plan Requirements:**
1. Create a day-by-day breakdown for the specified duration
2. Each day should have specific learning objectives and activities
3. Gradually increase complexity based on the current level
4. Align activities with the specified learning style
5. Include variety in daily activities (reading, practice, projects, review)
6. Add weekly milestone checkpoints
7. Ensure realistic time allocation per activity
8. Focus on scheduling TOPICS and CONCEPTS for each day/week (not specific documents)

**Format the response as a structured calendar view:**
- Use clear day headers (Day 1, Day 2, etc.) or Week headers for longer durations
- List specific topics/concepts to study with estimated time duration
- Include learning objectives for each day/week
- Add weekly summary/milestone sections
- Provide brief explanations for topic progression

**Learning Style Guidelines:**
- Theory-focused: Emphasize concept understanding, theoretical frameworks, reading-heavy topics
- Hands-on/Project-based: Focus on practical exercises, implementation, project-based learning
- Mixed approach: Balance theory and practice equally

**Topic Scheduling Focus:**
- Schedule specific topics/concepts for each study session
- Progress from foundational concepts to advanced topics
- Ensure logical learning progression
- Include review sessions for complex topics

Please generate a detailed, actionable study plan now:
"""
        
        return prompt
    
    def generate_study_plan(self, prompt: str) -> str:
        """Generate study plan using Gemini API."""
        try:
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise Exception("Empty response from Gemini API")
            
            return response.text.strip()
        
        except Exception as e:
            if "API_KEY" in str(e):
                raise Exception("Invalid API key. Please check your Gemini API key.")
            elif "quota" in str(e).lower():
                raise Exception("API quota exceeded. Please try again later.")
            else:
                raise Exception(f"Error generating study plan: {str(e)}")
    
    def create_study_plan(self, topic: str, duration: str, daily_time: str, 
                         current_level: str, learning_style: str, 
                         user_profile: Optional[Dict] = None) -> str:
        """Main method to create personalized study plan with FAISS integration."""
        try:
            # Step 1: Validate inputs
            if not topic.strip():
                raise Exception("Please enter a valid learning topic/goal")
            
            # Step 2: Search for course content in FAISS database
            st.info("🔍 Searching course database for related content...")
            course_content = self.search_course_content(topic)
            course_structure = self.get_course_structure(topic)
            
            # Step 3: Create planner prompt with course content and user profile
            if course_content:
                st.success("✅ Found relevant course content!")
                if course_structure:
                    st.info(f"📚 Analyzing {course_structure['total_matches']} content pieces from {len(course_structure['courses'])} course(s)")
                st.info("🎯 Creating enhanced study plan with course materials...")
            else:
                st.info("📚 No course content found, creating general study plan...")
            
            prompt = self.create_planner_prompt(topic, duration, daily_time, 
                                              current_level, learning_style, 
                                              course_content, course_structure, 
                                              user_profile)
            
            # Step 4: Generate study plan using Gemini
            st.info("📅 Generating your personalized study plan...")
            study_plan = self.generate_study_plan(prompt)
            
            # Step 5: Format study plan
            formatted_plan = self.format_study_plan(study_plan, topic, duration, 
                                                  daily_time, course_content is not None)
            
            return formatted_plan
        
        except Exception as e:
            raise Exception(f"Study plan creation failed: {str(e)}")
    
    def create_topic_study_plan(self, topic: str, duration: str, daily_time: str, 
                               current_level: str, learning_style: str) -> str:
        """Generate study plan for a specific topic using FAISS database."""
        try:
            # Search for course content
            st.info("🔍 Searching course database...")
            course_content = self.search_course_content(topic)
            course_structure = self.get_course_structure(topic)
            
            if course_content:
                st.success("✅ Found relevant course content!")
                if course_structure:
                    st.info(f"📚 Found content from: {', '.join(course_structure['courses'].keys())}")
                
                # Create enhanced prompt with course content
                prompt = f"""
You are an expert educational planner. Create a {duration} study plan for "{topic}".

**Study Parameters:**
- Duration: {duration}
- Daily Time: {daily_time}
- Current Level: {current_level}
- Learning Style: {learning_style}

**Available Course Content:**
{course_content}

**Course Structure:**
{course_structure['courses'] if course_structure else 'General content available'}

Create a detailed day-by-day study schedule focusing on the topics and concepts from the course content. 
Structure the plan to progress logically through the available materials.

**Format:** Day-by-day breakdown with specific topics, learning objectives, and time allocation.
"""
            else:
                st.info("📚 No course content found, using general knowledge...")
                
                # Fallback to general topic study plan
                prompt = f"""
Create a comprehensive {duration} study plan for "{topic}".

**Study Parameters:**
- Duration: {duration}
- Daily Time: {daily_time}
- Current Level: {current_level}
- Learning Style: {learning_style}

Focus on the most important concepts and create a logical learning progression.
**Format:** Day-by-day breakdown with specific topics and learning objectives.
"""
            
            # Generate study plan
            st.info("📅 Creating your study plan...")
            study_plan = self.generate_study_plan(prompt)
            
            # Format with metadata
            formatted_plan = self.format_study_plan(study_plan, topic, duration, 
                                                  daily_time, course_content is not None)
            
            return formatted_plan
        
        except Exception as e:
            raise Exception(f"Topic study plan creation failed: {str(e)}")
    
    def format_study_plan(self, plan: str, topic: str, duration: str, 
                         daily_time: str, has_course_content: bool = False) -> str:
        """Format the study plan with header and metadata."""
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Determine source information
        source_info = f"**Learning Goal:** {topic}"
        if has_course_content:
            source_info += " (Enhanced with course database)"
        
        formatted = f"""
### 📚 Personalized Study Plan

{source_info}  
**Plan Duration:** {duration}  
**Daily Study Time:** {daily_time}  
**Created:** {current_date}

---

{plan}

---

### 📝 Study Tips:
- **Consistency is key:** Stick to your daily schedule as much as possible
- **Take breaks:** Use the Pomodoro technique (25 min study, 5 min break)
- **Track progress:** Check off completed tasks to stay motivated
- **Be flexible:** Adjust the plan if needed based on your progress
- **Review regularly:** Spend time reviewing previous topics to reinforce learning

"""
        
        if has_course_content:
            formatted += """
### 🎯 Course Database Integration:
- This plan is enhanced with content from your course database
- Topics are organized based on available course materials
- Follow the suggested progression for optimal learning

"""
        
        formatted += "*Generated by EduMate AI Assistant*"
        return formatted.strip()
    
    def get_calendar_view(self, duration: str) -> dict:
        """Generate calendar structure for the study plan duration."""
        today = datetime.now()
        duration_days = {
            "1 Week": 7,
            "2 Weeks": 14,
            "1 Month": 30,
            "3 Months": 90,
            "6 Months": 180
        }
        
        days = duration_days.get(duration, 30)
        calendar_data = {}
        
        for i in range(days):
            current_date = today + timedelta(days=i)
            week_number = (i // 7) + 1
            day_key = f"Week {week_number} - Day {(i % 7) + 1}"
            calendar_data[day_key] = {
                "date": current_date.strftime("%B %d, %Y"),
                "day_name": current_date.strftime("%A"),
                "tasks": []
            }
        
        return calendar_data
    
    def get_database_summary(self) -> Dict:
        """Get summary of available course content."""
        if not self.faiss_db:
            return {"status": "unavailable", "message": "FAISS database not connected"}
        
        try:
            stats = self.faiss_db.get_database_summary()
            return {
                "status": "available",
                "total_documents": stats.get('total_documents', 0),
                "courses": stats.get('courses', {}),
                "database_size": stats.get('database_size', '0 KB')
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}