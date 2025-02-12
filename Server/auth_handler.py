import sqlite3
import hashlib
from datetime import datetime
from urllib.parse import parse_qs

class AuthHandler:
    @staticmethod
    def hash_password(password):
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def setup_database():
        """Initialize the SQLite database."""
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            conn.commit()

    @staticmethod
    def register_user(username, password, email):
        """Register a new user."""
        try:
            with sqlite3.connect('users.db') as conn:
                # TODO: CHECK IF THE USER ALREADY EXISTS AND THROW ERROR
                cursor = conn.cursor()
                password_hash = AuthHandler.hash_password(password)
                cursor.execute(
                    'INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
                    (username, password_hash, email)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return "ERROR§Username already exists"
        except Exception as e:
            return f"ERROR§Registration failed: {str(e)}"

    @staticmethod
    def authenticate_user(username, password):
        """Authenticate user login."""
        try:
            with sqlite3.connect('users.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
                result = cursor.fetchone()
                
                if result and result[0] == AuthHandler.hash_password(password):
                    cursor.execute(
                        'UPDATE users SET last_login = ? WHERE username = ?',
                        (datetime.now(), username)
                    )
                    conn.commit()
                    return True
                return "ERROR§Invalid username or password"
        except Exception as e:
            return f"ERROR§Authentication failed: {str(e)}"