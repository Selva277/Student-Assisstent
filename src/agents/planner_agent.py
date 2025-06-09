#planner_agent.py
import os
import streamlit as st
from datetime import datetime, timedelta
import google.generativeai as genai
import calendar

class PlannerAgent:
    def __init__(self):
        """Initialize the Planner Agent with Gemini API."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        
        # Try to initialize with the best available model
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
    
    def create_planner_prompt(self, topic: str, duration: str, daily_time: str, current_level: str, learning_style: str) -> str:
        """Create a detailed prompt for generating study plan."""
        
        prompt = f"""
        You are an expert educational planner and learning strategist. Create a comprehensive study plan based on the following requirements:

        **Learning Goal:** {topic}
        **Study Duration:** {duration}
        **Daily Available Time:** {daily_time}
        **Current Level:** {current_level}
        **Learning Style:** {learning_style}

        **Plan Requirements:**
        1. Create a day-by-day breakdown for the specified duration
        2. Each day should have specific learning objectives and activities
        3. Gradually increase complexity based on the current level
        4. Align activities with the specified learning style
        5. Include variety in daily activities (reading, practice, projects, review)
        6. Add weekly milestone checkpoints
        7. Ensure realistic time allocation per activity

        **Format the response as a structured calendar view:**
        - Use clear day headers (Day 1, Day 2, etc.)
        - List specific tasks with estimated time duration
        - Include learning objectives for each day
        - Add weekly summary/milestone sections
        - Provide brief explanations for activity choices

        **Learning Style Guidelines:**
        - Theory-focused: Emphasize reading, concept understanding, theoretical frameworks
        - Hands-on/Project-based: Focus on practical exercises, coding, building projects
        - Mixed approach: Balance theory and practice equally

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
    
    def create_study_plan(self, topic: str, duration: str, daily_time: str, current_level: str, learning_style: str) -> str:
        """Main method to create personalized study plan."""
        try:
            # Step 1: Validate inputs
            if not topic.strip():
                raise Exception("Please enter a valid learning topic/goal")
            
            # Step 2: Create planner prompt
            st.info("🎯 Analyzing your learning requirements...")
            prompt = self.create_planner_prompt(topic, duration, daily_time, current_level, learning_style)
            
            # Step 3: Generate study plan using Gemini
            st.info("📅 Creating your personalized study plan...")
            study_plan = self.generate_study_plan(prompt)
            
            # Step 4: Format study plan
            formatted_plan = self.format_study_plan(study_plan, topic, duration, daily_time)
            
            return formatted_plan
        
        except Exception as e:
            raise Exception(f"Study plan creation failed: {str(e)}")
    
    def format_study_plan(self, plan: str, topic: str, duration: str, daily_time: str) -> str:
        """Format the study plan with header and metadata."""
        current_date = datetime.now().strftime("%B %d, %Y")
        
        formatted = f"""
### 📚 Personalized Study Plan

**Learning Goal:** {topic}  
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

*Generated by EduMate AI Assistant*
        """
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