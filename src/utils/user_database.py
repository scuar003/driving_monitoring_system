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
        self.connection.commit()

    def create_user(self, username, password):
        cursor = self.connection.cursor()
        password_hash = self.hash_password(password)
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash) 
                VALUES (?, ?)
            ''', (username, password_hash))
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

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password, stored_password_hash):
        return self.hash_password(password) == stored_password_hash

    def close(self):
        self.connection.close()

if __name__ == "__main__":
    db = UserDatabase()
    db.create_user('test_user', 'password123')
    print(db.validate_user('test_user', 'password123'))  # Output: True
    db.close()
