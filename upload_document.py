#upload_document.py
#!/usr/bin/env python3
"""
EduMate - Document Upload Script
Simple script to upload documents to FAISS database
"""

import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.document_processor import DocumentProcessor

def main():
    """Main upload function"""
    print("🎓 EduMate - Document Upload Tool")
    print("=" * 40)
    
    # Initialize document processor
    try:
        processor = DocumentProcessor()
        print("✅ Document processor initialized")
    except Exception as e:
        print(f"❌ Error initializing processor: {e}")
        return
    
    # Show current database status
    stats = processor.get_database_summary()
    print(f"\n📊 Current Database Status:")
    print(f"   Documents: {stats['total_documents']}")
    print(f"   Processed files: {stats['processed_files']}")
    print(f"   Database size: {stats['database_size']}")
    
    if stats['courses']:
        print(f"   Courses: {', '.join(stats['courses'].keys())}")
    
    print("\n" + "=" * 40)
    
    # Main menu
    while True:
        print("\n📋 Options:")
        print("1. Scan and process documents folder")
        print("2. Add single document")
        print("3. Monitor folder for changes")
        print("4. View database statistics")
        print("5. Test search")
        print("6. Clear database")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-6): ").strip()
        
        if choice == "1":
            scan_documents(processor)
        elif choice == "2":
            add_single_document(processor)
        elif choice == "3":
            monitor_folder(processor)
        elif choice == "4":
            show_statistics(processor)
        elif choice == "5":
            test_search(processor)
        elif choice == "6":
            clear_database(processor)
        elif choice == "0":
            print("👋 Goodbye!")
            break
        else:
            print("⚠️ Invalid choice. Please try again.")

def scan_documents(processor):
    """Scan and process documents folder"""
    print("\n🔍 Scanning documents folder...")
    
    try:
        count = processor.scan_and_process_documents()
        if count > 0:
            print(f"✅ Successfully processed {count} documents")
        else:
            print("ℹ️ No new documents found")
    except Exception as e:
        print(f"❌ Error during scanning: {e}")

def add_single_document(processor):
    """Add a single document to database"""
    print("\n📄 Add Single Document")
    
    file_path = input("Enter full path to document (PDF/DOCX): ").strip()
    
    if not file_path:
        print("⚠️ No file path provided")
        return
    
    if not os.path.exists(file_path):
        print("❌ File not found")
        return
    
    if not file_path.lower().endswith(('.pdf', '.docx')):
        print("❌ Only PDF and DOCX files are supported")
        return
    
    try:
        print(f"🔄 Processing: {os.path.basename(file_path)}")
        success = processor.process_file(file_path)
        
        if success:
            processor.save_processed_files()
            processor.faiss_manager.save_database()
            print("✅ Document added successfully!")
        else:
            print("❌ Failed to process document")
            
    except Exception as e:
        print(f"❌ Error processing document: {e}")

def monitor_folder(processor):
    """Monitor documents folder for changes"""
    print("\n👀 Starting folder monitoring...")
    print("Press Ctrl+C to stop")
    
    try:
        processor.monitor_folder(check_interval=10)
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")

def show_statistics(processor):
    """Show detailed database statistics"""
    print("\n📊 Database Statistics")
    print("=" * 30)
    
    try:
        stats = processor.get_database_summary()
        
        print(f"Total Documents: {stats['total_documents']}")
        print(f"Processed Files: {stats['processed_files']}")
        print(f"Database Size: {stats['database_size']}")
        
        if stats['courses']:
            print("\nCourses & Document Count:")
            for course, count in stats['courses'].items():
                print(f"  • {course}: {count} chunks")
        else:
            print("\nNo courses found in database")
            
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")

def test_search(processor):
    """Test search functionality"""
    print("\n🔍 Test Search")
    
    query = input("Enter search query: ").strip()
    
    if not query:
        print("⚠️ No query provided")
        return
    
    try:
        print(f"🔄 Searching for: '{query}'")
        
        # Test topic search
        results = processor.faiss_manager.search_by_topic(query, top_k=3)
        
        if results['matches']:
            print(f"\n✅ Found {len(results['matches'])} matches:")
            
            for i, match in enumerate(results['matches'], 1):
                metadata = match['metadata']
                similarity = match['similarity']
                
                print(f"\n{i}. {metadata.get('title', 'Untitled')}")
                print(f"   Course: {metadata.get('course', 'Unknown')}")
                print(f"   Chapter: {metadata.get('chapter', 'Unknown')}")
                print(f"   Similarity: {similarity:.2f}")
                print(f"   Content preview: {match['content'][:100]}...")
        else:
            print("❌ No matches found")
            
    except Exception as e:
        print(f"❌ Error during search: {e}")

def clear_database(processor):
    """Clear entire database"""
    print("\n🗑️ Clear Database")
    print("⚠️ This will delete ALL documents from the database!")
    
    confirm = input("Type 'CONFIRM' to proceed: ").strip()
    
    if confirm == 'CONFIRM':
        try:
            processor.faiss_manager.clear_database()
            # Clear processed files list
            processor.processed_files = {}
            processor.save_processed_files()
            print("✅ Database cleared successfully")
        except Exception as e:
            print(f"❌ Error clearing database: {e}")
    else:
        print("❌ Operation cancelled")

def setup_documents_folder():
    """Create documents folder structure for demo"""
    print("\n📁 Setting up documents folder structure...")
    
    # Create example folder structure
    folders = [
        "documents/Python_Programming/Basics",
        "documents/Python_Programming/Advanced",
        "documents/Data_Science/Introduction",
        "documents/Data_Science/Machine_Learning",
        "documents/Web_Development/Frontend",
        "documents/Web_Development/Backend"
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    
    print("✅ Folder structure created:")
    for folder in folders:
        print(f"   📁 {folder}")
    
    print("\n💡 Now you can:")
    print("   1. Copy your PDF/DOCX files to appropriate folders")
    print("   2. Run option 1 to scan and process them")

if __name__ == "__main__":
    # Quick setup check
    if not os.path.exists("documents"):
        print("📁 Documents folder not found")
        create_folder = input("Create folder structure? (y/n): ").strip().lower()
        if create_folder == 'y':
            setup_documents_folder()
        print()
    
    # Run main program
    main()