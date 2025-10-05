import sqlite3

conn = sqlite3.connect('exam_system.db')
conn.row_factory = sqlite3.Row

# Check Test User's data
print("=" * 60)
print("Test User's Exam Sessions:")
print("=" * 60)

results = conn.execute('''
    SELECT u.name, u.id as user_id, es.score, e.num_questions, e.title,
           ROUND((CAST(es.score AS FLOAT) / CAST(e.num_questions AS FLOAT)) * 100, 1) as percentage
    FROM exam_sessions es
    JOIN users u ON es.user_id = u.id
    JOIN exams e ON es.exam_id = e.id
    WHERE u.name LIKE '%Test%' AND es.is_completed = 1
''').fetchall()

for row in results:
    print(f"User: {row['name']} (ID: {row['user_id']})")
    print(f"  Exam: {row['title']}")
    print(f"  Score: {row['score']} / {row['num_questions']}")
    print(f"  Percentage: {row['percentage']}%")
    print()

# Check top performers calculation
print("=" * 60)
print("Top Performers Calculation:")
print("=" * 60)

top_performers = conn.execute('''
    SELECT u.id, u.name, 
           AVG(
               CASE 
                   WHEN e.num_questions > 0 THEN (CAST(es.score AS FLOAT) / CAST(e.num_questions AS FLOAT)) * 100
                   ELSE 0
               END
           ) as average_score,
           COUNT(es.id) as exams_taken
    FROM exam_sessions es
    JOIN users u ON es.user_id = u.id
    JOIN exams e ON es.exam_id = e.id
    WHERE es.is_completed = 1 AND e.num_questions > 0
    GROUP BY u.id
    ORDER BY average_score DESC
    LIMIT 5
''').fetchall()

for row in top_performers:
    avg_score = min(round(row['average_score'], 1), 100.0)
    print(f"{row['name']}: {avg_score}% (from {row['exams_taken']} exams)")

conn.close()
