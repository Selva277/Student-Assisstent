#  flashcard_agent.py

import os
import sys
import tempfile
import streamlit as st
from typing import Optional, List, Dict
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import json
import random

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

class FlashcardAgent:
    def __init__(self):
        """Initialize the Flashcard Agent with Gemini API and FAISS database."""
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
        
        # Define suggested course topics
        self.suggested_topics = [
            "Artificial Intelligence", "Machine Learning", "Deep Learning", "Neural Networks",
            "Python Programming", "Data Structures", "Algorithms", "Object-Oriented Programming",
            "Probability", "Statistics", "Linear Algebra", "Calculus",
            "Database Systems", "SQL", "Data Science", "Big Data",
            "Web Development", "HTML/CSS", "JavaScript", "React",
            "Computer Networks", "Operating Systems", "Software Engineering",
            "Cybersecurity", "Cryptography", "Information Security",
            "Physics", "Chemistry", "Biology", "Mathematics",
            "Economics", "Finance", "Marketing", "Management"
        ]
    
    def search_course_content(self, topic: str) -> Optional[str]:
        """Search for relevant content in FAISS database."""
        if not self.faiss_db:
            return None
        
        try:
            # Search for content related to the topic
            content = self.faiss_db.search_documents(topic, top_k=3)
            return content
        except Exception as e:
            print(f"⚠️ FAISS search error: {e}")
            return None
    
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
        
        if uploaded_file.size > 10 * 1024 * 1024:
            raise Exception("File size exceeds 10MB limit")
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        
        try:
            if file_type == "application/pdf":
                with open(tmp_file_path, 'rb') as file:
                    text = self.extract_text_from_pdf(file)
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text = self.extract_text_from_docx(tmp_file_path)
            else:
                raise Exception(f"Unsupported file type: {file_type}")
            
            if not text.strip():
                raise Exception("No text content found in the document")
            
            return text
        
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    def create_flashcard_prompt(self, text: str, num_cards: int, difficulty: str, course_content: Optional[str] = None) -> str:
        """Create a detailed prompt for Gemini to generate flashcards."""
        
        difficulty_instructions = {
            "Basic": "Focus on simple, fundamental concepts and basic definitions. Use clear, straightforward language.",
            "Intermediate": "Include more detailed concepts and relationships. Use moderate academic vocabulary.",
            "Advanced": "Focus on complex ideas, nuanced concepts, and advanced terminology. Use sophisticated academic language."
        }
        
        difficulty_instruction = difficulty_instructions.get(difficulty, difficulty_instructions["Intermediate"])
        
        # Base prompt
        prompt = f"""
You are an expert educational content creator specializing in creating effective flashcards for students.

Please create {num_cards} high-quality flashcards using Term/Definition format.

**Flashcard Requirements:**
- Difficulty Level: {difficulty} - {difficulty_instruction}
- Format: Term/Definition pairs
- Each flashcard should test important concepts
- Terms should be key concepts, important vocabulary, or significant ideas
- Definitions should be clear, concise, and educational (2-4 sentences)
- Make definitions standalone (don't reference "the document")

**Output Format (STRICTLY FOLLOW THIS FORMAT):**
FLASHCARD_1:
TERM: [Key term or concept]
DEFINITION: [Clear, educational definition]

FLASHCARD_2:
TERM: [Key term or concept]
DEFINITION: [Clear, educational definition]

[Continue for all {num_cards} flashcards...]

"""
        
        # Add course content if available from FAISS
        if course_content:
            prompt += f"""
**Primary Course Content (Use as main reference):**
{course_content}

**Additional Context:**
{text[:2000]}...

Focus primarily on the course content above, and use the additional context to enhance understanding.
"""
        else:
            prompt += f"""
**Document Content:**
{text}
"""
        
        prompt += f"\nPlease generate exactly {num_cards} flashcards now:"
        
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
            flashcard_blocks = response_text.split("FLASHCARD_")
            
            for block in flashcard_blocks[1:]:
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
                        definition += " " + line
                
                if term and definition:
                    flashcards.append({
                        "term": term,
                        "definition": definition
                    })
            
            return flashcards
        
        except Exception as e:
            raise Exception(f"Error parsing flashcards: {str(e)}")
    
    def generate_topic_flashcards(self, topic: str, num_cards: int, difficulty: str, shuffle: bool = False) -> List[Dict[str, str]]:
        """Generate flashcards for a specific topic using FAISS database."""
        try:
            # Search for course content
            st.info("🔍 Searching course database...")
            course_content = self.search_course_content(topic)
            
            if course_content:
                st.success("✅ Found relevant course content!")
                
                # Create prompt with course content
                prompt = f"""
You are an expert educational content creator. Create {num_cards} flashcards about "{topic}".

**Difficulty Level:** {difficulty}
**Format:** Term/Definition pairs

**Course Content:**
{course_content}

**Output Format:**
FLASHCARD_1:
TERM: [Key term or concept]
DEFINITION: [Clear, educational definition]

FLASHCARD_2:
TERM: [Key term or concept]  
DEFINITION: [Clear, educational definition]

Generate exactly {num_cards} flashcards focusing on the most important concepts from the course content:
"""
            else:
                st.info("📚 No course content found, using general knowledge...")
                
                # Fallback to general topic flashcards
                difficulty_instructions = {
                    "Basic": "Focus on simple, fundamental concepts and basic definitions. Use clear, straightforward language.",
                    "Intermediate": "Include more detailed concepts and relationships. Use moderate academic vocabulary.",
                    "Advanced": "Focus on complex ideas, nuanced concepts, and advanced terminology. Use sophisticated academic language."
                }
                
                difficulty_instruction = difficulty_instructions.get(difficulty, difficulty_instructions["Intermediate"])
                
                prompt = f"""
You are an expert educational content creator. Create {num_cards} flashcards about "{topic}".

**Difficulty Level:** {difficulty} - {difficulty_instruction}
**Topic:** {topic}

Focus on the most important concepts, terms, and definitions related to {topic}.
Create comprehensive flashcards that cover key vocabulary, fundamental principles, and important concepts.

**Output Format:**
FLASHCARD_1:
TERM: [Key term or concept]
DEFINITION: [Clear, educational definition]

FLASHCARD_2:
TERM: [Key term or concept]
DEFINITION: [Clear, educational definition]

Generate exactly {num_cards} flashcards covering the essential knowledge for {topic}:
"""
            
            # Generate flashcards
            st.info("✨ Generating flashcards...")
            response = self.generate_flashcards_with_gemini(prompt)
            
            # Parse flashcards
            flashcards = self.parse_flashcards(response)
            
            if not flashcards:
                raise Exception("No valid flashcards could be generated")
            
            # Shuffle if requested
            if shuffle:
                flashcards = self.shuffle_flashcards(flashcards)
            
            return flashcards
        
        except Exception as e:
            raise Exception(f"Topic flashcard generation failed: {str(e)}")
    
    def shuffle_flashcards(self, flashcards: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Shuffle the order of flashcards."""
        shuffled = flashcards.copy()
        random.shuffle(shuffled)
        return shuffled
    
    def generate_flashcards(self, uploaded_file, num_cards: int, difficulty: str, shuffle: bool = False) -> List[Dict[str, str]]:
        """Main method to generate flashcards from uploaded document."""
        try:
            # Extract text from document
            st.info("📄 Extracting text from document...")
            text = self.extract_text_from_file(uploaded_file)
            
            if len(text.split()) < 100:
                raise Exception("Document too short to generate meaningful flashcards (minimum 100 words required)")
            
            # Try to identify topic from document
            topic_keywords = text[:500].split()[:10]  # First 10 words as topic hint
            topic_hint = " ".join(topic_keywords)
            
            # Search for related course content
            st.info("🔍 Searching for related course content...")
            course_content = self.search_course_content(topic_hint)
            
            # Create flashcard prompt
            st.info("🤖 Preparing flashcard generation...")
            prompt = self.create_flashcard_prompt(text, num_cards, difficulty, course_content)
            
            # Generate flashcards
            st.info("✨ Generating intelligent flashcards...")
            response = self.generate_flashcards_with_gemini(prompt)
            
            # Parse flashcards
            st.info("📝 Processing flashcards...")
            flashcards = self.parse_flashcards(response)
            
            if not flashcards:
                raise Exception("No valid flashcards could be generated from the document")
            
            # Shuffle if requested
            if shuffle:
                flashcards = self.shuffle_flashcards(flashcards)
            
            return flashcards
        
        except Exception as e:
            raise Exception(f"Flashcard generation failed: {str(e)}")
    
    def format_flashcards_for_display(self, flashcards: List[Dict[str, str]], source: str = "Topic") -> str:
        """Format flashcards for display in the UI."""
        if not flashcards:
            return "No flashcards generated."
        
        # Check if using course content
        source_info = f"**Source:** {source}"
        if self.faiss_db and source == "Topic":
            source_info += " (Enhanced with course database)"
        
        formatted = f"""
### 🃏 Generated Flashcards

{source_info}  
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
    
    def format_flashcards_for_print(self, flashcards: List[Dict[str, str]], source: str = "Topic") -> str:
        """Format flashcards for print-friendly download."""
        if not flashcards:
            return "No flashcards to export."
        
        print_format = f"""
EDUMATE FLASHCARDS
==================

Source: {source}
Total Cards: {len(flashcards)}
Generated: Now

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
    
    def render_flashcard_interface(self):
        """Render the complete flashcard interface with tabs."""
        st.title("🃏 Flashcard Generator")
        st.markdown("Generate intelligent flashcards from documents or topics using AI")
        
        # Create tabs
        tab1, tab2 = st.tabs(["📄 Upload Document", "📚 Enter Topic"])
        
        # Shared settings
        with st.sidebar:
            st.header("⚙️ Flashcard Settings")
            num_cards = st.slider("Number of Flashcards", min_value=5, max_value=50, value=10)
            difficulty = st.selectbox("Difficulty Level", ["Basic", "Intermediate", "Advanced"])
            shuffle = st.checkbox("Shuffle Cards", value=False)
        
        # Tab 1: Document Upload
        with tab1:
            st.header("📄 Generate from Document")
            st.markdown("Upload a PDF or Word document to generate flashcards")
            
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['pdf', 'docx'],
                help="Upload PDF or Word documents (max 10MB)"
            )
            
            if uploaded_file is not None:
                st.success(f"✅ File uploaded: {uploaded_file.name}")
                
                if st.button("🚀 Generate Flashcards from Document", key="doc_generate"):
                    try:
                        with st.spinner("Processing document..."):
                            flashcards = self.generate_flashcards(
                                uploaded_file, num_cards, difficulty, shuffle
                            )
                        
                        # Store in session state
                        st.session_state.flashcards = flashcards
                        st.session_state.flashcard_source = uploaded_file.name
                        
                        st.success(f"✅ Generated {len(flashcards)} flashcards!")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        # Tab 2: Topic Input
        with tab2:
            st.header("📚 Generate from Topic")
            st.markdown("Enter a topic to generate flashcards using course content and general knowledge")
            
            # Topic input with suggestions
            col1, col2 = st.columns([3, 1])
            
            with col1:
                topic = st.text_input(
                    "Enter Topic",
                    placeholder="e.g., Machine Learning, Python Programming, Statistics...",
                    help="Enter any academic topic or subject"
                )
            
            with col2:
                st.markdown("**Suggested Topics:**")
                selected_topic = st.selectbox(
                    "Quick Select",
                    [""] + self.suggested_topics,
                    help="Select from common course topics"
                )
                
                if selected_topic and selected_topic != topic:
                    topic = selected_topic
                    st.rerun()
            
            # Display some suggested topics as buttons
            st.markdown("**Popular Topics:**")
            topic_cols = st.columns(4)
            popular_topics = ["AI", "Python", "Statistics", "Database"]
            
            for i, pop_topic in enumerate(popular_topics):
                with topic_cols[i]:
                    if st.button(pop_topic, key=f"topic_{pop_topic}"):
                        topic = pop_topic
                        st.rerun()
            
            if topic:
                st.info(f"🎯 Topic selected: **{topic}**")
                
                if st.button("🚀 Generate Flashcards from Topic", key="topic_generate"):
                    try:
                        with st.spinner(f"Generating flashcards for {topic}..."):
                            flashcards = self.generate_topic_flashcards(
                                topic, num_cards, difficulty, shuffle
                            )
                        
                        # Store in session state
                        st.session_state.flashcards = flashcards
                        st.session_state.flashcard_source = topic
                        
                        st.success(f"✅ Generated {len(flashcards)} flashcards for {topic}!")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        # Display generated flashcards
        if 'flashcards' in st.session_state and st.session_state.flashcards:
            st.divider()
            
            # Display options
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.subheader("📋 Generated Flashcards")
            
            with col2:
                if st.button("🔄 Shuffle Cards", key="shuffle_display"):
                    st.session_state.flashcards = self.shuffle_flashcards(st.session_state.flashcards)
                    st.rerun()
            
            with col3:
                # Download button
                flashcard_text = self.format_flashcards_for_print(
                    st.session_state.flashcards, 
                    st.session_state.get('flashcard_source', 'Unknown')
                )
                st.download_button(
                    "📥 Download",
                    data=flashcard_text,
                    file_name=f"flashcards_{st.session_state.get('flashcard_source', 'topic')}.txt",
                    mime="text/plain"
                )
            
            # Display flashcards
            formatted_cards = self.format_flashcards_for_display(
                st.session_state.flashcards,
                st.session_state.get('flashcard_source', 'Topic')
            )
            st.markdown(formatted_cards)


# Main execution function for Streamlit
def main():
    """Main function to run the flashcard agent."""
    try:
        agent = FlashcardAgent()
        agent.render_flashcard_interface()
        
    except ValueError as e:
        st.error(f"❌ Configuration Error: {str(e)}")
        st.info("Please ensure your GOOGLE_API_KEY is set in the environment variables.")
    
    except Exception as e:
        st.error(f"❌ Application Error: {str(e)}")
        st.info("Please check your configuration and try again.")


if __name__ == "__main__":
    main()