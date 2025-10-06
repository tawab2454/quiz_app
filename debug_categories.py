import sqlite3

conn = sqlite3.connect('exam_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Find video questions with wrong category
cursor.execute('''
    SELECT id, category, question_youtube, question_image, 
           option_a_image, option_b_image, option_c_image, 
           option_d_image, option_e_image, option_f_image
    FROM questions 
    WHERE question_youtube IS NOT NULL
''')

print("Questions with YouTube links:")
print("="*70)

for row in cursor.fetchall():
    has_images = any([
        row['question_image'],
        row['option_a_image'], row['option_b_image'], 
        row['option_c_image'], row['option_d_image'],
        row['option_e_image'], row['option_f_image']
    ])
    
    print(f"ID {row['id']:3}: category={row['category']:8}, has_youtube=True, has_images={has_images}")

conn.close()
