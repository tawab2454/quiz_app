"""Check Test 1 exam configuration and questions"""
import sqlite3
import json

conn = sqlite3.connect('exam_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Find Test 1 exam
exam = cursor.execute('SELECT * FROM exams WHERE title LIKE ?', ('%Test 1%',)).fetchone()

if not exam:
    print("❌ No exam found with 'Test 1' in the title")
    
    # Show all exams
    print("\nAvailable exams:")
    all_exams = cursor.execute('SELECT id, title, num_questions, is_active FROM exams').fetchall()
    for e in all_exams:
        print(f"  ID {e['id']}: {e['title']} ({e['num_questions']} questions, active={e['is_active']})")
else:
    print("="*70)
    print("EXAM DETAILS: Test 1")
    print("="*70)
    print(f"  ID: {exam['id']}")
    print(f"  Title: {exam['title']}")
    print(f"  Description: {exam['description'] if 'description' in exam.keys() else 'N/A'}")
    print(f"  Num Questions: {exam['num_questions']}")
    print(f"  Duration: {exam['duration_minutes']} minutes")
    print(f"  Passing Score: {exam['passing_score']}")
    print(f"  Is Active: {exam['is_active']}")
    
    category_config = exam['category_config']
    print(f"\n  Category Config (raw): {category_config}")
    
    if category_config:
        try:
            config = json.loads(category_config)
            print("\n  Category Breakdown:")
            for cat, count in config.items():
                print(f"    {cat:10} : {count} questions")
        except:
            print("  (Invalid JSON)")
    
    # Check what questions are available for this exam's categories
    print("\n" + "="*70)
    print("AVAILABLE QUESTIONS BY CATEGORY")
    print("="*70)
    
    if category_config:
        try:
            config = json.loads(category_config)
            for cat, requested in config.items():
                cursor.execute('SELECT COUNT(*) FROM questions WHERE category = ?', (cat,))
                available = cursor.fetchone()[0]
                status = "✅" if available >= requested else "❌"
                print(f"  {status} {cat:10} : Requested {requested}, Available {available}")
        except:
            pass
    
    # Check exam sessions to see what questions were actually used
    print("\n" + "="*70)
    print("EXAM SESSIONS (Most Recent)")
    print("="*70)
    
    sessions = cursor.execute('''
        SELECT es.id, es.user_id, es.is_completed, es.questions_json, u.name
        FROM exam_sessions es
        LEFT JOIN users u ON es.user_id = u.id
        WHERE es.exam_id = ?
        ORDER BY es.start_time DESC
        LIMIT 3
    ''', (exam['id'],)).fetchall()
    
    if not sessions:
        print("  No exam sessions found")
    else:
        for session in sessions:
            print(f"\n  Session ID {session['id']} - User: {session['name']} - Completed: {session['is_completed']}")
            
            if session['questions_json']:
                try:
                    questions = json.loads(session['questions_json'])
                    print(f"    Total Questions: {len(questions)}")
                    
                    # Show first 3 questions
                    print("    Sample questions:")
                    for i, q in enumerate(questions[:3], 1):
                        q_id = q.get('id', 'N/A')
                        q_text = q.get('question_text', 'N/A')[:50]
                        print(f"      {i}. ID {q_id}: {q_text}...")
                    
                    # Check categories of questions used
                    q_ids = [q.get('id') for q in questions if q.get('id')]
                    if q_ids:
                        placeholders = ','.join(['?' for _ in q_ids])
                        cursor.execute(f'''
                            SELECT category, COUNT(*) as count
                            FROM questions
                            WHERE id IN ({placeholders})
                            GROUP BY category
                        ''', q_ids)
                        
                        print("    Question categories used:")
                        for row in cursor.fetchall():
                            print(f"      {row['category']:10} : {row['count']} questions")
                except Exception as e:
                    print(f"    Error parsing questions: {e}")

# Check current question database state
print("\n" + "="*70)
print("CURRENT QUESTION DATABASE STATE")
print("="*70)

cursor.execute('''
    SELECT category, difficulty, COUNT(*) as count
    FROM questions
    GROUP BY category, difficulty
    ORDER BY category, difficulty
''')

print("\nQuestions by Category and Difficulty:")
for row in cursor.fetchall():
    cat = row['category'] or 'NULL'
    diff = row['difficulty'] or 'NULL'
    print(f"  Category: {cat:10} | Difficulty: {diff:10} | Count: {row['count']}")

cursor.execute('SELECT category, COUNT(*) as count FROM questions GROUP BY category')
print("\nQuestions by Category (Summary):")
for row in cursor.fetchall():
    cat = row['category'] or 'NULL'
    print(f"  {cat:10} : {row['count']} questions")

conn.close()
