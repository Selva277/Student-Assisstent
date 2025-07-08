# src/auth/database.py
import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="edumate_users.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize all database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_profile_complete BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Student profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                year INTEGER NOT NULL CHECK(year >= 1 AND year <= 4),
                course TEXT NOT NULL,
                interests TEXT,
                goals TEXT,
                hobbies TEXT,
                learning_style TEXT,
                current_skills TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Remember me tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS remember_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Quiz performance table (for integration with existing quiz feature)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic TEXT NOT NULL,
                score_percentage REAL NOT NULL,
                total_questions INTEGER NOT NULL,
                correct_answers INTEGER NOT NULL,
                grade TEXT NOT NULL,
                date_taken TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
            )
        ''')
        
        # Study plans table (for integration with existing planner feature)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic TEXT NOT NULL,
                duration TEXT NOT NULL,
                daily_time TEXT NOT NULL,
                level TEXT NOT NULL,
                learning_style TEXT NOT NULL,
                plan_content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Database initialized successfully at {self.db_path}")
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            conn.commit()
            conn.close()
            return {"success": True, "data": results}
        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}
    
    def backup_database(self, backup_path=None):
        """Create a backup of the database"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"edumate_backup_{timestamp}.db"
        
        try:
            # Simple file copy for SQLite
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return {"success": True, "backup_path": backup_path}
        except Exception as e:
            return {"success": False, "error": str(e)}