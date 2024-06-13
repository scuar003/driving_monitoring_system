import sqlite3
import time

class Database:
    def __init__(self):
        self.connection = sqlite3.connect('data/engagement_data.db')
        self.create_table()

    def create_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gaze_data (
                timestamp TEXT,
                gaze_direction TEXT,
                duration REAL
            )
        ''')
        self.connection.commit()

    def log_gaze_data(self, gaze_data):
        cursor = self.connection.cursor()
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        for gaze_direction, durations in gaze_data.items():
            if not isinstance(durations, list):
                durations = [durations]
            for duration in durations:
                cursor.execute('''
                    INSERT INTO gaze_data (timestamp, gaze_direction, duration) 
                    VALUES (?, ?, ?)
                ''', (timestamp, gaze_direction, float(duration)))
        self.connection.commit()

    def retrieve_gaze_data(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT timestamp, gaze_direction, duration FROM gaze_data')
        data = cursor.fetchall()
        return data

    def close(self):
        self.connection.close()

if __name__ == "__main__":
    db = Database()
    # Example usage
    sample_data = {'road_focus': [5.0], 'mirror_check': [1.5]}
    db.log_gaze_data(sample_data)
    print(db.retrieve_gaze_data())
    db.close()
