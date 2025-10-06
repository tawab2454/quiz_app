"""Analyze the category vs difficulty field usage"""
import sqlite3

conn = sqlite3.connect('exam_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get table schema
cursor.execute("PRAGMA table_info(questions)")
columns = cursor.fetchall()

print("="*70)
print("QUESTIONS TABLE SCHEMA")
print("="*70)
for col in columns:
    print(f"  {col['name']:20} | Type: {col['type']:10} | Nullable: {not col['notnull']}")

print("\n" + "="*70)
print("CATEGORY vs DIFFICULTY ANALYSIS")
print("="*70)

# Show all unique combinations
cursor.execute('''
    SELECT 
        category,
        difficulty,
        COUNT(*) as count,
        MIN(id) as sample_id
    FROM questions
    GROUP BY category, difficulty
    ORDER BY category, difficulty
''')

print("\nAll Category/Difficulty Combinations:")
for row in cursor.fetchall():
    cat = row['category'] or 'NULL'
    diff = row['difficulty'] or 'NULL'
    print(f"  Category: {cat:10} | Difficulty: {diff:10} | Count: {row['count']:3} | Sample ID: {row['sample_id']}")

# Check a sample question from each category
print("\n" + "="*70)
print("SAMPLE QUESTIONS FROM EACH CATEGORY")
print("="*70)

categories = ['easy', 'medium', 'hard', 'image', 'video']
for cat in categories:
    cursor.execute('''
        SELECT id, category, difficulty, 
               CASE WHEN question_image IS NOT NULL THEN 'YES' ELSE 'NO' END as has_image,
               CASE WHEN question_youtube IS NOT NULL THEN 'YES' ELSE 'NO' END as has_video,
               question_text
        FROM questions
        WHERE category = ?
        LIMIT 1
    ''', (cat,))
    
    row = cursor.fetchone()
    if row:
        print(f"\nCategory: {cat}")
        print(f"  ID: {row['id']}")
        print(f"  Difficulty: {row['difficulty']}")
        print(f"  Has Image: {row['has_image']}")
        print(f"  Has Video: {row['has_video']}")
        print(f"  Text: {row['question_text'][:60]}...")

conn.close()
