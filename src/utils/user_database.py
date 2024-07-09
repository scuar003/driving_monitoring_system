# src/utils/user_database.py
import sqlite3
import hashlib
import os

class UserDatabase:
    def __init__(self):
        db_path = 'data/engagement_data.db'
        os.makedirs(os.path.dirname(db_path), exist_ok=True)  # Ensure the directory exists
        self.connection = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT
            )
        ''')

        cursor.execute('PRAGMA table_info(users)')
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'first_name' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN first_name TEXT')
        if 'last_name' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN last_name TEXT')
        if 'email' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')

        self.connection.commit()

    def create_user(self, username, password, first_name, last_name, email):
        cursor = self.connection.cursor()
        password_hash = self.hash_password(password)
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, first_name, last_name, email) 
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, first_name, last_name, email))
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def validate_user(self, username, password):
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT password_hash FROM users WHERE username = ?
        ''', (username,))
        result = cursor.fetchone()
        if result:
            stored_password_hash = result[0]
            return self.verify_password(password, stored_password_hash)
        return False

    def get_user_info(self, username):
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT first_name, last_name, email FROM users WHERE username = ?
        ''', (username,))
        return cursor.fetchone()

    def delete_user(self, username):
        cursor = self.connection.cursor()
        cursor.execute('''
            DELETE FROM users WHERE username = ?
        ''', (username,))
        self.connection.commit()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password, stored_password_hash):
        return self.hash_password(password) == stored_password_hash

    def change_password(self, username, new_password):
        cursor = self.connection.cursor()
        password_hash = self.hash_password(new_password)
        cursor.execute('''
            UPDATE users SET password_hash = ? WHERE username = ?
        ''', (password_hash, username))
        self.connection.commit()

    def close(self):
        self.connection.close()

