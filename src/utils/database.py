import sqlite3
import hashlib
import os
import time

class Database:
    def __init__(self):
        db_path = 'data/engagement_data.db'
        os.makedirs(os.path.dirname(db_path), exist_ok=True)  # Ensure the directory exists
        self.connection = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.connection.cursor()

        # Drop the table if it exists to avoid schema conflicts during testing
        cursor.execute('DROP TABLE IF EXISTS gaze_data')

        # Table for gaze data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gaze_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                timestamp TEXT,
                gaze_direction TEXT
            )
        ''')

        # Table for user data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT
            )
        ''')
        self.connection.commit()

    def log_gaze_data(self, username, gaze_data):
        cursor = self.connection.cursor()
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        for gaze_direction in gaze_data.get('gaze_direction', []):
            cursor.execute('''
                INSERT INTO gaze_data (user, timestamp, gaze_direction) 
                VALUES (?, ?, ?)
            ''', (username, timestamp, str(gaze_direction)))
        self.connection.commit()

    def retrieve_gaze_data(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT user, timestamp, gaze_direction FROM gaze_data')
        data = cursor.fetchall()
        return data

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
    db = Database()
    db.create_user('test_user', 'password123')
    print(db.validate_user('test_user', 'password123'))  # Output: True
    sample_data = {'road_focus': [5.0], 'mirror_check': [1.5]}
    db.log_gaze_data('test_user', sample_data)
    print(db.retrieve_gaze_data())
    db.close()
