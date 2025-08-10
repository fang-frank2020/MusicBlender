import sqlite3

# Match your Flask app's DATABASE path
DATABASE = './database.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        print("Initialized the database.")

if __name__ == '__main__':
    init_db()