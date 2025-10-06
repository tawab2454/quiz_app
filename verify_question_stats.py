"""Verify the question stats are correct"""
import sqlite3

conn = sqlite3.connect('exam_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("="*70)
print("QUESTION STATISTICS VERIFICATION")
print("="*70)

# Get all questions
cursor.execute('SELECT * FROM questions')
all_questions = cursor.fetchall()

print(f"\nTotal Questions: {len(all_questions)}")

# Count by difficulty (for easy/medium/hard/unseen)
print("\n" + "-"*70)
print("BY DIFFICULTY (for Easy/Medium/Hard/Unseen):")
print("-"*70)

for difficulty in ['easy', 'medium', 'hard', 'unseen']:
    cursor.execute('SELECT COUNT(*) FROM questions WHERE difficulty = ?', (difficulty,))
    count = cursor.fetchone()[0]
    
    # Show breakdown by category
    cursor.execute('''
        SELECT category, COUNT(*) as cnt
        FROM questions
        WHERE difficulty = ?
        GROUP BY category
    ''', (difficulty,))
    
    breakdown = cursor.fetchall()
    breakdown_str = ', '.join([f"{row['category']}:{row['cnt']}" for row in breakdown]) if breakdown else 'none'
    
    print(f"  {difficulty.upper():10} : {count:3} questions (breakdown: {breakdown_str})")

# Count by category (for image/video)
print("\n" + "-"*70)
print("BY CATEGORY (for Image/Video):")
print("-"*70)

for category in ['image', 'video']:
    cursor.execute('SELECT COUNT(*) FROM questions WHERE category = ?', (category,))
    count = cursor.fetchone()[0]
    
    # Show breakdown by difficulty
    cursor.execute('''
        SELECT difficulty, COUNT(*) as cnt
        FROM questions
        WHERE category = ?
        GROUP BY difficulty
    ''', (category,))
    
    breakdown = cursor.fetchall()
    breakdown_str = ', '.join([f"{row['difficulty']}:{row['cnt']}" for row in breakdown]) if breakdown else 'none'
    
    print(f"  {category.upper():10} : {count:3} questions (difficulty: {breakdown_str})")

# Show the complete picture
print("\n" + "="*70)
print("WHAT ADMIN SHOULD SEE IN admin_questions.html:")
print("="*70)
print("\nTotal Questions: {}".format(len(all_questions)))
print("\nBy Difficulty:")
for difficulty in ['easy', 'medium', 'hard', 'unseen']:
    cursor.execute('SELECT COUNT(*) FROM questions WHERE difficulty = ?', (difficulty,))
    count = cursor.fetchone()[0]
    print(f"  {difficulty.capitalize():10} : {count} questions")

print("\nBy Media Type:")
for category in ['image', 'video']:
    cursor.execute('SELECT COUNT(*) FROM questions WHERE category = ?', (category,))
    count = cursor.fetchone()[0]
    print(f"  {category.capitalize():10} : {count} questions")

print("\n" + "="*70)

conn.close()
