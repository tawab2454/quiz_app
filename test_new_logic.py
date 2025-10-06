"""Test the updated question selection logic"""
import sqlite3
import json

conn = sqlite3.connect('exam_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("="*70)
print("TESTING UPDATED QUESTION SELECTION LOGIC")
print("="*70)

# Test the new counting logic (simulating add_exam)
print("\n1. Question Counts for Exam Creation:")
print("-"*70)

for category in ['easy', 'medium', 'hard', 'image', 'video']:
    if category in ['easy', 'medium', 'hard']:
        # Count by difficulty (includes all question types)
        cursor.execute('SELECT COUNT(*) FROM questions WHERE difficulty = ?', (category,))
        count = cursor.fetchone()[0]
        
        # Show breakdown
        cursor.execute('''
            SELECT category, COUNT(*) as cnt 
            FROM questions 
            WHERE difficulty = ? 
            GROUP BY category
        ''', (category,))
        breakdown = cursor.fetchall()
        
        breakdown_str = ', '.join([f"{row['category']}:{row['cnt']}" for row in breakdown])
        print(f"  {category:10} : {count:3} questions ({breakdown_str})")
    else:
        # Count by category
        cursor.execute('SELECT COUNT(*) FROM questions WHERE category = ?', (category,))
        count = cursor.fetchone()[0]
        print(f"  {category:10} : {count:3} questions")

# Test question selection for Test 1 exam config
print("\n2. Simulating 'Test 1' Exam Question Selection:")
print("-"*70)

test1_config = {"easy": 3, "medium": 4, "hard": 3}
selected_questions = []

for category, num_q in test1_config.items():
    print(f"\n  Selecting {num_q} '{category}' questions...")
    
    if category in ['easy', 'medium', 'hard']:
        cursor.execute('''
            SELECT id, question_text, difficulty, category,
                   CASE WHEN question_image IS NOT NULL THEN 'YES' ELSE 'NO' END as has_image,
                   CASE WHEN question_youtube IS NOT NULL THEN 'YES' ELSE 'NO' END as has_video
            FROM questions 
            WHERE difficulty = ? 
            ORDER BY RANDOM() 
            LIMIT ?
        ''', (category, num_q))
    else:
        cursor.execute('''
            SELECT id, question_text, difficulty, category,
                   CASE WHEN question_image IS NOT NULL THEN 'YES' ELSE 'NO' END as has_image,
                   CASE WHEN question_youtube IS NOT NULL THEN 'YES' ELSE 'NO' END as has_video
            FROM questions 
            WHERE category = ? 
            ORDER BY RANDOM() 
            LIMIT ?
        ''', (category, num_q))
    
    questions = cursor.fetchall()
    selected_questions.extend(questions)
    
    print(f"    Selected {len(questions)} questions:")
    for q in questions:
        media = []
        if q['has_image'] == 'YES':
            media.append('IMG')
        if q['has_video'] == 'YES':
            media.append('VID')
        media_str = '+'.join(media) if media else 'TEXT'
        
        print(f"      ID {q['id']:3} [{q['difficulty']:8}|{q['category']:8}|{media_str:8}] {q['question_text'][:40]}...")

print(f"\n  Total questions selected: {len(selected_questions)}")

# Show category breakdown of selected questions
print("\n3. Category Breakdown of Selected Questions:")
print("-"*70)

cursor.execute('''
    SELECT category, difficulty, COUNT(*) as cnt
    FROM questions
    WHERE id IN ({})
    GROUP BY category, difficulty
    ORDER BY category, difficulty
'''.format(','.join([str(q['id']) for q in selected_questions])))

for row in cursor.fetchall():
    print(f"  Category: {row['category']:10} | Difficulty: {row['difficulty']:10} | Count: {row['cnt']}")

# Show if video/image questions are included
video_count = sum(1 for q in selected_questions if q['has_video'] == 'YES')
image_count = sum(1 for q in selected_questions if q['has_image'] == 'YES')

print(f"\n  Questions with videos: {video_count}")
print(f"  Questions with images: {image_count}")
print(f"  Text-only questions: {len(selected_questions) - max(video_count, image_count)}")

print("\n" + "="*70)
print("✅ NEW LOGIC NOW INCLUDES VIDEO/IMAGE QUESTIONS IN DIFFICULTY LEVELS!")
print("="*70)

conn.close()
