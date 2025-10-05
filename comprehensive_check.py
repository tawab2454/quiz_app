import sqlite3

conn = sqlite3.connect('exam_system.db')
conn.row_factory = sqlite3.Row

print("=" * 80)
print("COMPREHENSIVE SCORING & RESULT CHECK")
print("=" * 80)

# 1. Check for any score > num_questions (impossible scores)
print("\n1. Checking for impossible scores (score > num_questions)...")
impossible = conn.execute('''
    SELECT es.id, u.name, e.title, es.score, e.num_questions
    FROM exam_sessions es
    JOIN users u ON es.user_id = u.id
    JOIN exams e ON es.exam_id = e.id
    WHERE es.score > e.num_questions AND es.is_completed = 1
''').fetchall()

if impossible:
    print(f"   ❌ Found {len(impossible)} session(s) with impossible scores!")
    for row in impossible:
        print(f"      Session {row['id']}: {row['name']} - {row['score']}/{row['num_questions']}")
else:
    print("   ✅ No impossible scores found!")

# 2. Check for negative scores
print("\n2. Checking for negative scores...")
negative = conn.execute('''
    SELECT es.id, u.name, e.title, es.score
    FROM exam_sessions es
    JOIN users u ON es.user_id = u.id
    JOIN exams e ON es.exam_id = e.id
    WHERE es.score < 0 AND es.is_completed = 1
''').fetchall()

if negative:
    print(f"   ❌ Found {len(negative)} session(s) with negative scores!")
    for row in negative:
        print(f"      Session {row['id']}: {row['name']} - Score: {row['score']}")
else:
    print("   ✅ No negative scores found!")

# 3. Check for NULL scores in completed exams
print("\n3. Checking for NULL scores in completed exams...")
null_scores = conn.execute('''
    SELECT es.id, u.name, e.title, es.score
    FROM exam_sessions es
    JOIN users u ON es.user_id = u.id
    JOIN exams e ON es.exam_id = e.id
    WHERE es.score IS NULL AND es.is_completed = 1
''').fetchall()

if null_scores:
    print(f"   ❌ Found {len(null_scores)} completed session(s) with NULL scores!")
    for row in null_scores:
        print(f"      Session {row['id']}: {row['name']} - {row['title']}")
else:
    print("   ✅ No NULL scores in completed exams!")

# 4. Check for exams with zero or negative num_questions
print("\n4. Checking for exams with invalid num_questions...")
invalid_exams = conn.execute('''
    SELECT id, title, num_questions
    FROM exams
    WHERE num_questions <= 0 OR num_questions IS NULL
''').fetchall()

if invalid_exams:
    print(f"   ❌ Found {len(invalid_exams)} exam(s) with invalid num_questions!")
    for row in invalid_exams:
        print(f"      Exam {row['id']}: {row['title']} - num_questions: {row['num_questions']}")
else:
    print("   ✅ All exams have valid num_questions!")

# 5. Sample percentage calculations for recent exams
print("\n5. Recent exam results with percentage calculations...")
recent = conn.execute('''
    SELECT u.name, e.title, es.score, e.num_questions,
           ROUND((CAST(es.score AS FLOAT) / CAST(e.num_questions AS FLOAT)) * 100, 2) as percentage
    FROM exam_sessions es
    JOIN users u ON es.user_id = u.id
    JOIN exams e ON es.exam_id = e.id
    WHERE es.is_completed = 1
    ORDER BY es.end_time DESC
    LIMIT 10
''').fetchall()

if recent:
    print(f"   Last 10 completed exams:")
    for row in recent:
        print(f"      {row['name']}: {row['score']}/{row['num_questions']} = {row['percentage']}%")
else:
    print("   No completed exams found!")

# 6. Check for duplicate exam sessions (user taking same exam multiple times)
print("\n6. Checking exam attempt counts...")
attempts = conn.execute('''
    SELECT u.name, e.title, COUNT(*) as attempts
    FROM exam_sessions es
    JOIN users u ON es.user_id = u.id
    JOIN exams e ON es.exam_id = e.id
    WHERE es.is_completed = 1
    GROUP BY es.user_id, es.exam_id
    HAVING attempts > 1
    ORDER BY attempts DESC
    LIMIT 5
''').fetchall()

if attempts:
    print(f"   Users with multiple attempts:")
    for row in attempts:
        print(f"      {row['name']} - {row['title']}: {row['attempts']} attempts")
else:
    print("   ✅ No users with multiple attempts!")

# 7. Check pass/fail logic accuracy
print("\n7. Verifying pass/fail logic...")
passfail = conn.execute('''
    SELECT u.name, e.title, es.score, e.num_questions, e.passing_score,
           ROUND((CAST(es.score AS FLOAT) / CAST(e.num_questions AS FLOAT)) * 100, 2) as percentage,
           CASE 
               WHEN (CAST(es.score AS FLOAT) / CAST(e.num_questions AS FLOAT)) * 100 >= e.passing_score 
               THEN 'PASS' 
               ELSE 'FAIL' 
           END as status
    FROM exam_sessions es
    JOIN users u ON es.user_id = u.id
    JOIN exams e ON es.exam_id = e.id
    WHERE es.is_completed = 1
    ORDER BY es.end_time DESC
    LIMIT 10
''').fetchall()

print(f"   Recent results:")
for row in passfail:
    symbol = "✅" if row['status'] == 'PASS' else "❌"
    print(f"      {symbol} {row['name']}: {row['percentage']}% (need {row['passing_score']}%) - {row['status']}")

# 8. Check for incomplete sessions that are too old (potential stuck sessions)
print("\n8. Checking for stuck/incomplete sessions...")
from datetime import datetime, timedelta
cutoff = datetime.now() - timedelta(hours=2)
stuck = conn.execute('''
    SELECT es.id, u.name, e.title, es.start_time
    FROM exam_sessions es
    JOIN users u ON es.user_id = u.id
    JOIN exams e ON es.exam_id = e.id
    WHERE es.is_completed = 0 AND es.start_time < ?
''', (cutoff,)).fetchall()

if stuck:
    print(f"   ⚠️ Found {len(stuck)} incomplete session(s) older than 2 hours:")
    for row in stuck:
        print(f"      Session {row['id']}: {row['name']} - {row['title']} (started: {row['start_time']})")
else:
    print("   ✅ No stuck sessions found!")

# 9. Summary statistics
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

stats = conn.execute('''
    SELECT 
        COUNT(*) as total_sessions,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(DISTINCT exam_id) as unique_exams,
        ROUND(AVG((CAST(score AS FLOAT) / CAST(num_questions AS FLOAT)) * 100), 2) as avg_percentage
    FROM exam_sessions es
    JOIN exams e ON es.exam_id = e.id
    WHERE es.is_completed = 1
''').fetchone()

print(f"   Total completed exams: {stats['total_sessions']}")
print(f"   Unique users: {stats['unique_users']}")
print(f"   Unique exams: {stats['unique_exams']}")
print(f"   Average score: {stats['avg_percentage']}%")

print("\n" + "=" * 80)
print("CHECK COMPLETE!")
print("=" * 80)

conn.close()
