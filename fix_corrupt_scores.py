import sqlite3

conn = sqlite3.connect('exam_system.db')

# Find and fix corrupt exam_sessions where score > num_questions
print("Finding corrupt exam sessions...")

corrupt_sessions = conn.execute('''
    SELECT es.id, es.user_id, es.score, e.num_questions, u.name, e.title
    FROM exam_sessions es
    JOIN exams e ON es.exam_id = e.id
    JOIN users u ON es.user_id = u.id
    WHERE es.score > e.num_questions AND es.is_completed = 1
''').fetchall()

if corrupt_sessions:
    print(f"\nFound {len(corrupt_sessions)} corrupt session(s):\n")
    for session in corrupt_sessions:
        print(f"Session ID: {session[0]}")
        print(f"  User: {session[4]}")
        print(f"  Exam: {session[5]}")
        print(f"  Score: {session[2]} (should be max {session[3]})")
        
        # Cap the score at num_questions
        new_score = min(session[2], session[3])
        conn.execute('UPDATE exam_sessions SET score = ? WHERE id = ?', (new_score, session[0]))
        print(f"  ✅ Fixed: Score capped to {new_score}")
        print()
    
    conn.commit()
    print(f"✅ All corrupt sessions fixed!")
else:
    print("✅ No corrupt sessions found!")

conn.close()
