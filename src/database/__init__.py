# src/database/__init__.py
"""
Database module for EduMate - AI Student Assistant
Handles document processing and FAISS vector database operations
"""

from .faiss_manager import FAISSManager
from .document_processor import DocumentProcessor

__all__ = ['FAISSManager', 'DocumentProcessor']