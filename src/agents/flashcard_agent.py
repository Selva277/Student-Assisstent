# flashcard_agent.py

import os
import tempfile
import streamlit as st
from typing import Optional, List, Dict
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import json
import random

class FlashcardAgent:
    def __init__(self):
        """Initialize the Flashcard Agent with Gemini API."""
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
                # Fallback to other available models
                self.model = genai.GenerativeModel('gemini-1.5-pro')
            except Exception:
                try:
                    self.model = genai.GenerativeModel('gemini-pro')
                except Exception:
                    # Get list of available models and use the first generative one
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
    
    def extract_text_from_pdf(self, file) -> str:
        """Extract text from PDF file."""
        try:
            pdf_reader = PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    def extract_text_from_docx(self, file) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")
    
    def extract_text_from_file(self, uploaded_file) -> str:
        """Extract text from uploaded file based on file type."""
        file_type = uploaded_file.type
        
        # Check file size (10MB limit)
        if uploaded_file.size > 10 * 1024 * 1024:
            raise Exception("File size exceeds 10MB limit")
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        
        try:
            if file_type == "application/pdf":
                with open(tmp_file_path, 'rb') as file:
                    text = self.extract_text_from_pdf(file)
            elif file_type == "application/vnd.openxmlformats-officedudlament.wordprocessingml.document":
                text = self.extract_text_from_docx(tmp_file_path)
            else:
                raise Exception(f"Unsupported file type: {file_type}")
            
            if not text.strip():
                raise Exception("No text content found in the document")
            
            return text
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    def create_flashcard_prompt(self, text: str, num_cards: int, difficulty: str) -> str:
        """Create a detailed prompt for Gemini to generate flashcards."""
        
        difficulty_instructions = {
            "Basic": "Focus on simple, fundamental concepts and basic definitions. Use clear, straightforward language.",
            "Intermediate": "Include more detailed concepts and relationships. Use moderate academic vocabulary.",
            "Advanced": "Focus on complex ideas, nuanced concepts, and advanced terminology. Use sophisticated academic language."
        }
        
        difficulty_instruction = difficulty_instructions.get(difficulty, difficulty_instructions["Intermediate"])
        
        prompt = f"""
        You are an expert educational content creator specializing in creating effective flashcards for students.
        
        Please analyze the following document and create {num_cards} high-quality flashcards using Term/Definition format.
        
        **Flashcard Requirements:**
        - Difficulty Level: {difficulty} - {difficulty_instruction}
        - Format: Term/Definition pairs
        - Each flashcard should test important concepts from the document
        - Terms should be key concepts, important vocabulary, or significant ideas
        - Definitions should be clear, concise, and educational (2-4 sentences)
        - Avoid overly simple or overly complex terms based on difficulty level
        - Ensure flashcards cover different sections/topics from the document
        - Make definitions standalone (don't reference "the document" or "as mentioned")
        
        **Output Format (STRICTLY FOLLOW THIS FORMAT):**
        FLASHCARD_1:
        TERM: [Key term or concept]
        DEFINITION: [Clear, educational definition]
        
        FLASHCARD_2:
        TERM: [Key term or concept]
        DEFINITION: [Clear, educational definition]
        
        [Continue for all {num_cards} flashcards...]
        
        **Document Content:**
        {text}
        
        Please generate exactly {num_cards} flashcards now:
        """
        
        return prompt
    
    def generate_flashcards_with_gemini(self, prompt: str) -> str:
        """Generate flashcards using Gemini API."""
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
                raise Exception(f"Error generating flashcards: {str(e)}")
    
    def parse_flashcards(self, response_text: str) -> List[Dict[str, str]]:
        """Parse the Gemini response into structured flashcard data."""
        flashcards = []
        
        try:
            # Split response into individual flashcards
            flashcard_blocks = response_text.split("FLASHCARD_")
            
            for block in flashcard_blocks[1:]:  # Skip the first empty split
                lines = block.strip().split("\n")
                term = ""
                definition = ""
                
                for line in lines:
                    line = line.strip()
                    if line.startswith("TERM:"):
                        term = line.replace("TERM:", "").strip()
                    elif line.startswith("DEFINITION:"):
                        definition = line.replace("DEFINITION:", "").strip()
                    elif definition and not line.startswith("FLASHCARD_"):
                        # Continue definition on next line
                        definition += " " + line
                
                if term and definition:
                    flashcards.append({
                        "term": term,
                        "definition": definition
                    })
            
            return flashcards
        
        except Exception as e:
            raise Exception(f"Error parsing flashcards: {str(e)}")
    
    def shuffle_flashcards(self, flashcards: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Shuffle the order of flashcards."""
        shuffled = flashcards.copy()
        random.shuffle(shuffled)
        return shuffled
    
    def generate_flashcards(self, uploaded_file, num_cards: int, difficulty: str, shuffle: bool = False) -> List[Dict[str, str]]:
        """Main method to generate flashcards from uploaded document."""
        try:
            # Step 1: Extract text from document
            st.info("📄 Extracting text from document...")
            text = self.extract_text_from_file(uploaded_file)
            
            # Check if text is sufficient for flashcard generation
            if len(text.split()) < 100:
                raise Exception("Document too short to generate meaningful flashcards (minimum 100 words required)")
            
            # Step 2: Create flashcard prompt
            st.info("🤖 Preparing flashcard generation request...")
            prompt = self.create_flashcard_prompt(text, num_cards, difficulty)
            
            # Step 3: Generate flashcards using Gemini
            st.info("✨ Generating intelligent flashcards...")
            response = self.generate_flashcards_with_gemini(prompt)
            
            # Step 4: Parse flashcards
            st.info("📝 Processing flashcards...")
            flashcards = self.parse_flashcards(response)
            
            if not flashcards:
                raise Exception("No valid flashcards could be generated from the document")
            
            # Step 5: Shuffle if requested
            if shuffle:
                flashcards = self.shuffle_flashcards(flashcards)
            
            return flashcards
        
        except Exception as e:
            raise Exception(f"Flashcard generation failed: {str(e)}")
    
    def format_flashcards_for_display(self, flashcards: List[Dict[str, str]], filename: str) -> str:
        """Format flashcards for display in the UI."""
        if not flashcards:
            return "No flashcards generated."
        
        formatted = f"""
### 🃏 Generated Flashcards

**Source:** {filename}  
**Total Cards:** {len(flashcards)}  
**Generated:** Now

---
"""
        
        for i, card in enumerate(flashcards, 1):
            formatted += f"""
**Card {i}:**
- **Term:** {card['term']}
- **Definition:** {card['definition']}

---
"""
        
        formatted += "\n*Generated by EduMate AI Assistant*"
        return formatted.strip()
    
    def format_flashcards_for_print(self, flashcards: List[Dict[str, str]], filename: str) -> str:
        """Format flashcards for print-friendly download."""
        if not flashcards:
            return "No flashcards to export."
        
        print_format = f"""
EDUMATE FLASHCARDS
==================

Source Document: {filename}
Total Cards: {len(flashcards)}
Generated: {st.session_state.get('current_time', 'Now')}

"""
        
        for i, card in enumerate(flashcards, 1):
            print_format += f"""
CARD {i}
--------
TERM: {card['term']}

DEFINITION: {card['definition']}


"""
        
        print_format += """
===========================================
Generated by EduMate AI Assistant
Study tip: Cover the definitions and test your knowledge!
"""
        
        return print_format.strip()