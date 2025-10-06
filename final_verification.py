"""
Final Verification: Show what admin will see when creating exams
"""
import sqlite3

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print("="*70)
print("ADMIN EXAM CREATION - QUESTION AVAILABILITY")
print("="*70)
print("\nThis is what you'll see when creating a new exam:\n")

# Simulate the add_exam view
for category in ['easy', 'medium', 'hard', 'image', 'video']:
    if category in ['easy', 'medium', 'hard']:
        cursor.execute('SELECT COUNT(*) FROM questions WHERE difficulty = ?', (category,))
        count = cursor.fetchone()[0]
        
        # Show breakdown
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN question_youtube IS NOT NULL THEN 'video'
                    WHEN question_image IS NOT NULL THEN 'image'
                    ELSE 'text'
                END as type,
                COUNT(*) as cnt
            FROM questions
            WHERE difficulty = ?
            GROUP BY type
        ''', (category,))
        
        breakdown = {row[0]: row[1] for row in cursor.fetchall()}
        text_cnt = breakdown.get('text', 0)
        video_cnt = breakdown.get('video', 0)
        image_cnt = breakdown.get('image', 0)
        
        details = []
        if text_cnt > 0:
            details.append(f"{text_cnt} text")
        if video_cnt > 0:
            details.append(f"{video_cnt} video")
        if image_cnt > 0:
            details.append(f"{image_cnt} image")
        
        detail_str = " + ".join(details)
        
        print(f"  📝 {category.upper():10} : {count:3} questions available ({detail_str})")
    else:
        cursor.execute('SELECT COUNT(*) FROM questions WHERE category = ?', (category,))
        count = cursor.fetchone()[0]
        
        if category == 'image':
            icon = "🖼️"
        else:
            icon = "🎥"
        
        print(f"  {icon} {category.upper():10} : {count:3} questions available")

print("\n" + "="*70)
print("EXAMPLE: Creating 'Test 1' type exam")
print("="*70)
print("\nIf you select:")
print("  - 3 easy questions")
print("  - 4 medium questions")
print("  - 3 hard questions")
print("\nYou'll get a MIX including:")

# Simulate selection
import random
random.seed(42)  # For consistent demo

total_text = 0
total_video = 0
total_image = 0

for category, num_q in [('easy', 3), ('medium', 4), ('hard', 3)]:
    cursor.execute('''
        SELECT 
            CASE 
                WHEN question_youtube IS NOT NULL THEN 'video'
                WHEN question_image IS NOT NULL THEN 'image'
                ELSE 'text'
            END as type
        FROM questions
        WHERE difficulty = ?
        ORDER BY RANDOM()
        LIMIT ?
    ''', (category, num_q))
    
    for row in cursor.fetchall():
        if row[0] == 'text':
            total_text += 1
        elif row[0] == 'video':
            total_video += 1
        else:
            total_image += 1

print(f"  ✓ {total_text} text questions")
print(f"  ✓ {total_video} video questions")
print(f"  ✓ {total_image} image questions")

print("\n" + "="*70)
print("COMPARISON: Old vs New")
print("="*70)

print("\n❌ OLD SYSTEM (Before Fix):")
print("  - Only counted questions where category='easy/medium/hard'")
print("  - Ignored video/image questions with those difficulties")
print("  - Students got same text questions repeatedly")

print("\n✅ NEW SYSTEM (After Fix):")
print("  - Counts ALL questions with difficulty='easy/medium/hard'")
print("  - Includes text, video, AND image questions")
print("  - Students get variety in every exam!")

print("\n" + "="*70)
print("🎉 READY TO USE!")
print("="*70)
print("\nNext steps:")
print("  1. Go to Admin Panel → Add Exam")
print("  2. See updated question counts")
print("  3. Create exam with desired difficulty levels")
print("  4. Students will now get variety of question types!")
print("\n" + "="*70)

conn.close()
