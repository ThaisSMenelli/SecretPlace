import sqlite3
from config import Config

conn = sqlite3.connect(Config.DATABASE)
with open("schema.sql") as f:
    conn.executescript(f.read())
conn.close()

print("Database initialized successfully!")