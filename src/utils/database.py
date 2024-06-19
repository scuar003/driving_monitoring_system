import sqlite3
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gaze_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                timestamp TEXT,
                gaze_direction TEXT
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
            ''', (username, timestamp, gaze_direction))
        self.connection.commit()

    def retrieve_gaze_data(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT user, timestamp, gaze_direction FROM gaze_data')
        data = cursor.fetchall()
        return data

    def close(self):
        self.connection.close()

if __name__ == "__main__":
    db = Database()
    sample_data = {'gaze_direction': ['Right, UP', 'Left, DOWN']}
    db.log_gaze_data('test_user', sample_data)
    print(db.retrieve_gaze_data())
    db.close()
