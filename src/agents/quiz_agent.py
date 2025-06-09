#quiz_agent.py 
import os
import streamlit as st
from datetime import datetime
import google.generativeai as genai
import json
import random

class QuizAgent:
    def __init__(self):
        """Initialize the Quiz Agent with Gemini API."""
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
    
    def create_quiz_prompt(self, topic: str, num_questions: int, difficulty: str, question_types: list) -> str:
        """Create a detailed prompt for generating quiz questions."""
        
        question_type_str = " and ".join(question_types)
        
        prompt = f"""
        You are an expert quiz creator and educator. Generate a comprehensive quiz based on the following specifications:

        **Topic:** {topic}
        **Number of Questions:** {num_questions}
        **Difficulty Level:** {difficulty}
        **Question Types:** {question_type_str}

        **Quiz Requirements:**
        1. Create exactly {num_questions} questions about {topic}
        2. Mix the question types as specified: {question_type_str}
        3. Ensure questions match the {difficulty} difficulty level
        4. Provide clear, unambiguous questions
        5. For multiple choice questions, provide 4 options (A, B, C, D)
        6. For true/false questions, make statements clear and definitive
        7. Include detailed explanations for all correct answers

        **Difficulty Guidelines:**
        - Easy: Basic concepts, definitions, simple recall
        - Intermediate: Application of concepts, analysis, moderate complexity
        - Hard: Complex analysis, synthesis, advanced application, critical thinking

        **Response Format:**
        Please format your response as a structured list where each question follows this exact format:

        Question [number]: [Question text]
        Type: [Multiple Choice/True-False]
        A) [Option A] (for multiple choice only)
        B) [Option B] (for multiple choice only)
        C) [Option C] (for multiple choice only)
        D) [Option D] (for multiple choice only)
        Correct Answer: [Letter or True/False]
        Explanation: [Detailed explanation of why this is correct and why other options are wrong]

        ---

        Generate the quiz now:
        """
        
        return prompt
    
    def generate_quiz_questions(self, prompt: str) -> str:
        """Generate quiz questions using Gemini API."""
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
                raise Exception(f"Error generating quiz: {str(e)}")
    
    def parse_quiz_response(self, response: str) -> list:
        """Parse the AI response into structured quiz data."""
        questions = []
        current_question = {}
        
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('Question'):
                if current_question:
                    questions.append(current_question)
                current_question = {
                    'question': line.split(':', 1)[1].strip() if ':' in line else line,
                    'type': '',
                    'options': [],
                    'correct_answer': '',
                    'explanation': ''
                }
            elif line.startswith('Type:'):
                current_question['type'] = line.split(':', 1)[1].strip()
            elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                current_question['options'].append(line)
            elif line.startswith('Correct Answer:'):
                current_question['correct_answer'] = line.split(':', 1)[1].strip()
            elif line.startswith('Explanation:'):
                current_question['explanation'] = line.split(':', 1)[1].strip()
            elif current_question and line.startswith('Explanation:') == False and '---' not in line:
                # Continue explanation if it spans multiple lines
                if current_question['explanation']:
                    current_question['explanation'] += ' ' + line
        
        # Add the last question
        if current_question:
            questions.append(current_question)
        
        return questions
    
    def create_quiz(self, topic: str, num_questions: int, difficulty: str, question_types: list) -> list:
        """Main method to create quiz questions."""
        try:
            # Step 1: Validate inputs
            if not topic.strip():
                raise Exception("Please enter a valid topic for the quiz")
            
            if num_questions < 1 or num_questions > 50:
                raise Exception("Number of questions must be between 1 and 50")
            
            # Step 2: Create quiz prompt
            st.info("🎯 Preparing quiz questions...")
            prompt = self.create_quiz_prompt(topic, num_questions, difficulty, question_types)
            
            # Step 3: Generate quiz using Gemini
            st.info("❓ Generating quiz questions...")
            quiz_response = self.generate_quiz_questions(prompt)
            
            # Step 4: Parse response into structured data
            st.info("📝 Processing quiz format...")
            questions = self.parse_quiz_response(quiz_response)
            
            if len(questions) == 0:
                raise Exception("Failed to generate quiz questions. Please try again.")
            
            return questions
        
        except Exception as e:
            raise Exception(f"Quiz creation failed: {str(e)}")
    
    def calculate_score(self, questions: list, user_answers: dict) -> dict:
        """Calculate quiz score and generate performance report."""
        total_questions = len(questions)
        correct_answers = 0
        detailed_results = []
        
        for i, question in enumerate(questions):
            question_num = i + 1
            user_answer = user_answers.get(f"q_{question_num}", "")
            correct_answer = question['correct_answer']
            
            is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            if is_correct:
                correct_answers += 1
            
            detailed_results.append({
                'question_num': question_num,
                'question': question['question'],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'explanation': question['explanation']
            })
        
        score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Determine grade
        if score_percentage >= 90:
            grade = "A+"
        elif score_percentage >= 80:
            grade = "A"
        elif score_percentage >= 70:
            grade = "B"
        elif score_percentage >= 60:
            grade = "C"
        elif score_percentage >= 50:
            grade = "D"
        else:
            grade = "F"
        
        return {
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'score_percentage': score_percentage,
            'grade': grade,
            'detailed_results': detailed_results
        }
    
    def save_quiz_performance(self, topic: str, score_data: dict):
        """Save quiz performance to session state for history tracking."""
        if 'quiz_history' not in st.session_state:
            st.session_state.quiz_history = []
        
        performance_record = {
            'topic': topic,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'score_percentage': score_data['score_percentage'],
            'grade': score_data['grade'],
            'total_questions': score_data['total_questions'],
            'correct_answers': score_data['correct_answers']
        }
        
        st.session_state.quiz_history.append(performance_record)
    
    def get_quiz_history(self) -> list:
        """Retrieve quiz performance history."""
        return st.session_state.get('quiz_history', [])
    
    def format_quiz_results(self, topic: str, score_data: dict) -> str:
        """Format quiz results for display or download."""
        current_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        formatted = f"""
### 🎯 Quiz Results

**Topic:** {topic}
**Date:** {current_date}
**Score:** {score_data['correct_answers']}/{score_data['total_questions']} ({score_data['score_percentage']:.1f}%)
**Grade:** {score_data['grade']}

---

### 📊 Detailed Results:

"""
        
        for result in score_data['detailed_results']:
            status_emoji = "✅" if result['is_correct'] else "❌"
            formatted += f"""
**Question {result['question_num']}:** {result['question']}
{status_emoji} **Your Answer:** {result['user_answer']}
**Correct Answer:** {result['correct_answer']}
**Explanation:** {result['explanation']}

---
"""
        
        formatted += "\n*Generated by EduMate AI Assistant*"
        return formatted.strip()