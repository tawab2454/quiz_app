import sqlite3

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

# Check total users
total_users = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
print(f'Total users: {total_users}')

# Check users with division_name
with_division = cursor.execute('SELECT COUNT(*) FROM users WHERE division_name IS NOT NULL AND division_name != ""').fetchone()[0]
print(f'Users with division: {with_division}')

# Check distinct divisions
divisions = cursor.execute('SELECT DISTINCT division_name FROM users WHERE division_name IS NOT NULL AND division_name != ""').fetchall()
print(f'Distinct divisions: {[d[0] for d in divisions]}')

# Check results with division data
results_with_div = cursor.execute('''
    SELECT COUNT(*) FROM exam_sessions es
    JOIN users u ON es.user_id = u.id
    WHERE es.is_completed = 1 AND u.division_name IS NOT NULL AND u.division_name != ""
''').fetchone()[0]
print(f'Completed exams with division data: {results_with_div}')

conn.close()
