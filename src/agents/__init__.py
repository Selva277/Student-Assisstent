"""
EduMate AI Agents Package

This package contains various AI agents for the EduMate application:
- SummarizerAgent: Document summarization functionality
- Future agents will be added here
"""

from .summarizer_agent import SummarizerAgent
from .flashcard_agent import FlashcardAgent

__all__ = ['SummarizerAgent', 'FlashcardAgent']