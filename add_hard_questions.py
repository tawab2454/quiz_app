import sqlite3

conn = sqlite3.connect('exam_system.db')

# Add some hard category questions
hard_questions = [
    {
        'question_text': 'What is the time complexity of the merge sort algorithm in the worst case?',
        'option_a': 'O(n)',
        'option_b': 'O(n log n)',
        'option_c': 'O(n²)',
        'option_d': 'O(log n)',
        'correct_option': 'B',
        'category': 'hard',
        'difficulty': 'hard'
    },
    {
        'question_text': 'Which design pattern is used to ensure a class has only one instance?',
        'option_a': 'Factory Pattern',
        'option_b': 'Observer Pattern', 
        'option_c': 'Singleton Pattern',
        'option_d': 'Strategy Pattern',
        'correct_option': 'C',
        'category': 'hard',
        'difficulty': 'hard'
    },
    {
        'question_text': 'What is the space complexity of quicksort algorithm?',
        'option_a': 'O(1)',
        'option_b': 'O(log n)',
        'option_c': 'O(n)',
        'option_d': 'O(n log n)',
        'correct_option': 'B',
        'category': 'hard',
        'difficulty': 'hard'
    }
]

for q in hard_questions:
    conn.execute('''
        INSERT INTO questions (question_text, option_a, option_b, option_c, option_d, 
                             correct_option, category, difficulty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (q['question_text'], q['option_a'], q['option_b'], q['option_c'], 
          q['option_d'], q['correct_option'], q['category'], q['difficulty']))

conn.commit()

# Check updated categories
print('Updated categories:')
result = conn.execute('SELECT category, COUNT(*) as count FROM questions GROUP BY category ORDER BY count DESC').fetchall()
for row in result:
    print(f'{row[0]}: {row[1]}')

conn.close()
print('\nAdded hard category questions successfully!')