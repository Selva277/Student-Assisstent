# src/database/document_processor.py
import os
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
import PyPDF2
import docx
from .faiss_manager import FAISSManager

class DocumentProcessor:
    def __init__(self, documents_folder: str = "documents", db_path: str = "faiss_db"):
        """Initialize Document Processor."""
        self.documents_folder = documents_folder
        self.faiss_manager = FAISSManager(db_path)
        self.processed_files = self.load_processed_files()
        
        # Create documents folder if it doesn't exist
        os.makedirs(documents_folder, exist_ok=True)
        print(f"📁 Monitoring folder: {documents_folder}")
    
    def load_processed_files(self) -> Dict:
        """Load list of already processed files with their hashes."""
        processed_file_path = os.path.join(self.faiss_manager.db_path, "processed_files.txt")
        processed_files = {}
        
        if os.path.exists(processed_file_path):
            try:
                with open(processed_file_path, 'r') as f:
                    for line in f:
                        if '|' in line:
                            file_path, file_hash = line.strip().split('|', 1)
                            processed_files[file_path] = file_hash
            except Exception as e:
                print(f"⚠️ Error loading processed files: {e}")
        
        return processed_files
    
    def save_processed_files(self):
        """Save list of processed files."""
        processed_file_path = os.path.join(self.faiss_manager.db_path, "processed_files.txt")
        try:
            with open(processed_file_path, 'w') as f:
                for file_path, file_hash in self.processed_files.items():
                    f.write(f"{file_path}|{file_hash}\n")
        except Exception as e:
            print(f"❌ Error saving processed files: {e}")
    
    def get_file_hash(self, file_path: str) -> str:
        """Get hash of file for change detection."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"❌ Error reading PDF {file_path}: {e}")
            # Try alternative method
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e2:
                print(f"❌ Alternative PDF method failed: {e2}")
                return ""
        
        return text.strip()
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            print(f"❌ Error reading DOCX {file_path}: {e}")
            return ""
    
    def extract_metadata_from_path(self, file_path: str) -> Dict:
        """Extract course/chapter/topic from folder structure."""
        # Convert to Path object for easier manipulation
        path = Path(file_path)
        parts = path.parts
        
        # Extract metadata from folder structure
        # documents/Course/Chapter/file.pdf
        metadata = {
            'id': hashlib.md5(file_path.encode()).hexdigest()[:8],
            'file_path': file_path,
            'title': path.stem,  # filename without extension
            'course': 'General',
            'chapter': 'General',
            'topics': []
        }
        
        # Extract from folder structure
        documents_idx = -1
        for i, part in enumerate(parts):
            if part == 'documents':
                documents_idx = i
                break
        
        if documents_idx != -1:
            if len(parts) > documents_idx + 1:
                metadata['course'] = parts[documents_idx + 1].replace('_', ' ')
            if len(parts) > documents_idx + 2:
                metadata['chapter'] = parts[documents_idx + 2].replace('_', ' ')
            
            # Add folder names as topics
            metadata['topics'] = [part.replace('_', ' ') for part in parts[documents_idx + 1:-1]]
        
        return metadata
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into chunks with overlap."""
        if not text:
            return []
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def process_file(self, file_path: str) -> bool:
        """Process a single file and add to FAISS database."""
        try:
            print(f"🔄 Processing: {file_path}")
            
            # Extract text based on file type
            if file_path.lower().endswith('.pdf'):
                text = self.extract_text_from_pdf(file_path)
            elif file_path.lower().endswith('.docx'):
                text = self.extract_text_from_docx(file_path)
            else:
                print(f"⚠️ Unsupported file type: {file_path}")
                return False
            
            if not text:
                print(f"⚠️ No text extracted from: {file_path}")
                return False
            
            # Extract metadata
            metadata = self.extract_metadata_from_path(file_path)
            
            # Chunk the text
            chunks = self.chunk_text(text)
            
            # Add each chunk to FAISS database
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_id'] = i
                chunk_metadata['total_chunks'] = len(chunks)
                
                self.faiss_manager.add_document(chunk, chunk_metadata)
            
            # Mark file as processed
            file_hash = self.get_file_hash(file_path)
            self.processed_files[file_path] = file_hash
            
            print(f"✅ Processed {len(chunks)} chunks from: {os.path.basename(file_path)}")
            return True
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return False
    
    def scan_and_process_documents(self):
        """Scan documents folder and process new/updated files."""
        print("🔍 Scanning for documents...")
        
        processed_count = 0
        
        # Walk through all files in documents folder
        for root, dirs, files in os.walk(self.documents_folder):
            for file in files:
                if file.lower().endswith(('.pdf', '.docx')):
                    file_path = os.path.join(root, file)
                    file_hash = self.get_file_hash(file_path)
                    
                    # Check if file is new or updated
                    if (file_path not in self.processed_files or 
                        self.processed_files[file_path] != file_hash):
                        
                        if self.process_file(file_path):
                            processed_count += 1
        
        # Save updated processed files list
        if processed_count > 0:
            self.save_processed_files()
            self.faiss_manager.save_database()
            print(f"✅ Processed {processed_count} new/updated documents")
        else:
            print("ℹ️ No new documents to process")
        
        return processed_count
    
    def monitor_folder(self, check_interval: int = 10):
        """Continuously monitor folder for new documents."""
        print(f"👀 Monitoring documents folder (checking every {check_interval} seconds)")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                self.scan_and_process_documents()
                time.sleep(check_interval)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped")
    
    def get_database_summary(self) -> Dict:
        """Get summary of processed documents."""
        stats = self.faiss_manager.get_database_stats()
        
        # Count documents by course
        courses = {}
        for metadata in self.faiss_manager.metadata:
            course = metadata.get('course', 'Unknown')
            courses[course] = courses.get(course, 0) + 1
        
        return {
            **stats,
            'courses': courses,
            'processed_files': len(self.processed_files)
        }
    
    def search_documents(self, query: str, top_k: int = 3) -> Optional[str]:
        """Search documents and return best match content."""
        results = self.faiss_manager.search_by_topic(query, top_k)
        
        if results['matches']:
            # Return the best match content
            best_match = results['matches'][0]
            return best_match['content']
        
        return None