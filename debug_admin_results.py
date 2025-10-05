import sqlite3

conn = sqlite3.connect('exam_system.db')
conn.row_factory = sqlite3.Row

print("=" * 80)
print("CHECKING ADMIN RESULTS CALCULATION")
print("=" * 80)

# Simulate the admin_results query
print("\n1. Raw data from database:")
raw_results = conn.execute('''
    SELECT 
        es.id, es.score, u.name, u.nsi_id,
        e.title as exam_title, e.passing_score, e.num_questions
    FROM exam_sessions es
    JOIN users u ON es.user_id = u.id
    JOIN exams e ON es.exam_id = e.id
    WHERE es.is_completed = 1
    ORDER BY es.score DESC
    LIMIT 5
''').fetchall()

print(f"\n{'Name':<15} {'NSI ID':<10} {'Exam':<25} {'Raw Score':<10} {'Questions':<10} {'Percentage'}")
print("-" * 90)
for r in raw_results:
    percentage = round((r['score'] / r['num_questions']) * 100, 1) if r['num_questions'] > 0 else 0
    print(f"{r['name']:<15} {r['nsi_id']:<10} {r['exam_title']:<25} {r['score']:<10} {r['num_questions']:<10} {percentage}%")

# Check top performers calculation
print("\n2. Top Performers calculation:")
top_performers = conn.execute('''
    SELECT 
        u.name,
        u.nsi_id,
        AVG(
            CASE 
                WHEN e.num_questions > 0 
                THEN (CAST(es.score AS FLOAT) / CAST(e.num_questions AS FLOAT)) * 100
                ELSE 0
            END
        ) as avg_score,
        COUNT(es.id) as completed_exams
    FROM users u
    LEFT JOIN exam_sessions es ON u.id = es.user_id AND es.is_completed = 1
    LEFT JOIN exams e ON es.exam_id = e.id
    WHERE e.num_questions > 0
    GROUP BY u.id, u.name, u.nsi_id
    HAVING completed_exams > 0
    ORDER BY avg_score DESC
    LIMIT 5
''').fetchall()

print(f"\n{'Name':<15} {'NSI ID':<10} {'Avg Score %':<12} {'Exams'}")
print("-" * 50)
for p in top_performers:
    avg = round(p['avg_score'], 1)
    print(f"{p['name']:<15} {p['nsi_id']:<10} {avg:<12} {p['completed_exams']}")

conn.close()

print("\n" + "=" * 80)
print("If percentages above are correct, then the issue is in template rendering")
print("=" * 80)
