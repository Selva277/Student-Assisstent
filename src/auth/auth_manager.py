# src/auth/auth_manager.py
import hashlib
import sqlite3
import os
from datetime import datetime, timedelta
import streamlit as st

class AuthManager:
    def __init__(self):
        self.db_path = "edumate_users.db"
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with users and student_profiles tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
                FOREIGN KEY (user_id) REFERENCES users (id)
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
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, email, password):
        """Register a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return {"success": True, "user_id": user_id, "message": "User registered successfully!"}
        except sqlite3.IntegrityError:
            conn.close()
            return {"success": False, "message": "Email already exists!"}
        except Exception as e:
            conn.close()
            return {"success": False, "message": f"Registration failed: {str(e)}"}
    
    def login_user(self, email, password):
        """Authenticate user login"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute(
            "SELECT id, email, is_profile_complete FROM users WHERE email = ? AND password_hash = ?",
            (email, password_hash)
        )
        
        user = cursor.fetchone()
        
        if user:
            # Update last login
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user[0],)
            )
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "user_id": user[0],
                "email": user[1],
                "is_profile_complete": bool(user[2]),
                "message": "Login successful!"
            }
        else:
            conn.close()
            return {"success": False, "message": "Invalid email or password!"}
    
    def create_remember_token(self, user_id):
        """Create a remember me token"""
        import secrets
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=30)  # Token valid for 30 days
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Remove old tokens for this user
        cursor.execute("DELETE FROM remember_tokens WHERE user_id = ?", (user_id,))
        
        # Insert new token
        cursor.execute(
            "INSERT INTO remember_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
            (user_id, token, expires_at)
        )
        
        conn.commit()
        conn.close()
        return token
    
    def validate_remember_token(self, token):
        """Validate remember me token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.email, u.is_profile_complete 
            FROM users u 
            JOIN remember_tokens rt ON u.id = rt.user_id 
            WHERE rt.token = ? AND rt.expires_at > CURRENT_TIMESTAMP
        ''', (token,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                "success": True,
                "user_id": user[0],
                "email": user[1],
                "is_profile_complete": bool(user[2])
            }
        return {"success": False}
    
    def save_student_profile(self, user_id, profile_data):
        """Save or update student profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if profile exists
            cursor.execute("SELECT id FROM student_profiles WHERE user_id = ?", (user_id,))
            existing_profile = cursor.fetchone()
            
            if existing_profile:
                # Update existing profile
                cursor.execute('''
                    UPDATE student_profiles 
                    SET name = ?, year = ?, course = ?, interests = ?, goals = ?, 
                        hobbies = ?, learning_style = ?, current_skills = ?, 
                        updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                ''', (
                    profile_data['name'], profile_data['year'], profile_data['course'],
                    profile_data['interests'], profile_data['goals'], profile_data['hobbies'],
                    profile_data['learning_style'], profile_data['current_skills'], user_id
                ))
            else:
                # Insert new profile
                cursor.execute('''
                    INSERT INTO student_profiles 
                    (user_id, name, year, course, interests, goals, hobbies, learning_style, current_skills) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, profile_data['name'], profile_data['year'], profile_data['course'],
                    profile_data['interests'], profile_data['goals'], profile_data['hobbies'],
                    profile_data['learning_style'], profile_data['current_skills']
                ))
            
            # Mark profile as complete
            cursor.execute(
                "UPDATE users SET is_profile_complete = TRUE WHERE id = ?",
                (user_id,)
            )
            
            conn.commit()
            conn.close()
            return {"success": True, "message": "Profile saved successfully!"}
        
        except Exception as e:
            conn.close()
            return {"success": False, "message": f"Failed to save profile: {str(e)}"}
    
    def get_student_profile(self, user_id):
        """Get student profile by user ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, year, course, interests, goals, hobbies, learning_style, current_skills
            FROM student_profiles WHERE user_id = ?
        ''', (user_id,))
        
        profile = cursor.fetchone()
        conn.close()
        
        if profile:
            return {
                "success": True,
                "profile": {
                    "name": profile[0],
                    "year": profile[1],
                    "course": profile[2],
                    "interests": profile[3],
                    "goals": profile[4],
                    "hobbies": profile[5],
                    "learning_style": profile[6],
                    "current_skills": profile[7]
                }
            }
        return {"success": False, "message": "Profile not found"}
    
    def logout_user(self, user_id):
        """Logout user and remove remember token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Remove remember tokens
        cursor.execute("DELETE FROM remember_tokens WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        return {"success": True, "message": "Logged out successfully!"}