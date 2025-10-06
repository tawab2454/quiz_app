import sqlite3
import bcrypt

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

# Create test user
password_hash = bcrypt.hashpw('test123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
cursor.execute('INSERT OR REPLACE INTO users (nsi_id, name, wing_name, district_name, section_name, password_hash, profile_completed) VALUES (?, ?, ?, ?, ?, ?, ?)',
               ('a-1234', 'Test User', 'Test Wing', 'Test District', 'Test Section', password_hash, 1))

conn.commit()
print('Test user created: a-1234 / test123')
conn.close()