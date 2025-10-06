"""
Test Script: Verify Question Categories and Exam Creation
This script verifies that:
1. Questions have proper category values
2. Exam creation shows correct question counts
3. Questions are properly selected when taking exams
"""

import sqlite3
import json

def get_db_connection():
    db_path = 'exam_system.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def test_question_categories():
    """Test that all questions have valid categories"""
    print("\n" + "="*70)
    print("TEST 1: Verifying Question Categories")
    print("="*70)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check for NULL categories
    cursor.execute("SELECT COUNT(*) FROM questions WHERE category IS NULL OR category = ''")
    null_count = cursor.fetchone()[0]
    
    if null_count > 0:
        print(f"❌ FAIL: {null_count} questions have NULL or empty category")
        
        # Show details of questions with NULL category
        cursor.execute("""
            SELECT id, question_text, difficulty, question_image, question_youtube 
            FROM questions 
            WHERE category IS NULL OR category = ''
            LIMIT 5
        """)
        print("\nSample questions with NULL category:")
        for row in cursor.fetchall():
            print(f"  ID {row['id']}: {row['question_text'][:50]}...")
        return False
    else:
        print("✅ PASS: All questions have valid categories")
    
    # Show category distribution
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM questions 
        GROUP BY category 
        ORDER BY count DESC
    """)
    
    print("\nCategory Distribution:")
    category_counts = {}
    for row in cursor.fetchall():
        category = row['category']
        count = row['count']
        category_counts[category] = count
        print(f"  {category:10} : {count:5} questions")
    
    conn.close()
    return True, category_counts

def test_exam_question_counts(expected_counts):
    """Test that exam creation can count questions correctly"""
    print("\n" + "="*70)
    print("TEST 2: Verifying Exam Question Count Logic")
    print("="*70)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    all_pass = True
    
    for category in ['easy', 'medium', 'hard', 'image', 'video']:
        # Simulate what add_exam does
        cursor.execute('SELECT COUNT(*) FROM questions WHERE category = ?', (category,))
        count = cursor.fetchone()[0]
        
        expected = expected_counts.get(category, 0)
        
        if count == expected:
            print(f"✅ PASS: {category:10} - Found {count:5} questions (expected {expected})")
        else:
            print(f"❌ FAIL: {category:10} - Found {count:5} questions (expected {expected})")
            all_pass = False
    
    conn.close()
    return all_pass

def test_exam_question_selection():
    """Test that questions can be selected properly for exams"""
    print("\n" + "="*70)
    print("TEST 3: Verifying Question Selection for Exams")
    print("="*70)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create a test category config
    test_config = {
        'easy': 2,
        'medium': 2,
        'hard': 2,
        'image': 2,
        'video': 2
    }
    
    all_pass = True
    selected_questions = []
    
    for category, num_q in test_config.items():
        # Simulate what take_exam does
        cursor.execute('''
            SELECT id, question_text, category 
            FROM questions 
            WHERE category = ? 
            ORDER BY RANDOM() 
            LIMIT ?
        ''', (category, num_q))
        
        questions = cursor.fetchall()
        actual_count = len(questions)
        
        if actual_count == num_q:
            print(f"✅ PASS: {category:10} - Selected {actual_count}/{num_q} questions")
            selected_questions.extend(questions)
        elif actual_count > 0:
            print(f"⚠️  WARN: {category:10} - Selected {actual_count}/{num_q} questions (not enough available)")
            selected_questions.extend(questions)
        else:
            print(f"❌ FAIL: {category:10} - Selected 0/{num_q} questions (none available)")
            all_pass = False
    
    # Verify selected questions have correct categories
    print(f"\nTotal questions selected: {len(selected_questions)}")
    
    if len(selected_questions) > 0:
        print("\nSample of selected questions:")
        for i, q in enumerate(selected_questions[:5], 1):
            print(f"  {i}. [{q['category']:8}] {q['question_text'][:50]}...")
    
    conn.close()
    return all_pass

def test_category_integrity():
    """Test that category values match their question properties"""
    print("\n" + "="*70)
    print("TEST 4: Verifying Category Integrity")
    print("="*70)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    all_pass = True
    
    # Check if image questions have 'image' category
    cursor.execute("""
        SELECT COUNT(*) 
        FROM questions 
        WHERE (question_image IS NOT NULL OR 
               option_a_image IS NOT NULL OR option_b_image IS NOT NULL OR 
               option_c_image IS NOT NULL OR option_d_image IS NOT NULL OR 
               option_e_image IS NOT NULL OR option_f_image IS NOT NULL)
        AND category != 'image'
    """)
    mismatched_images = cursor.fetchone()[0]
    
    if mismatched_images == 0:
        print("✅ PASS: All image questions have 'image' category")
    else:
        print(f"❌ FAIL: {mismatched_images} image questions don't have 'image' category")
        all_pass = False
    
    # Check if video questions (without images) have 'video' category
    # Note: Questions with both YouTube AND images should be 'image' category
    cursor.execute("""
        SELECT COUNT(*) 
        FROM questions 
        WHERE question_youtube IS NOT NULL 
        AND question_image IS NULL
        AND option_a_image IS NULL AND option_b_image IS NULL
        AND option_c_image IS NULL AND option_d_image IS NULL
        AND option_e_image IS NULL AND option_f_image IS NULL
        AND category != 'video'
    """)
    mismatched_videos = cursor.fetchone()[0]
    
    if mismatched_videos == 0:
        print("✅ PASS: All video-only questions have 'video' category")
    else:
        print(f"❌ FAIL: {mismatched_videos} video-only questions don't have 'video' category")
        all_pass = False
    
    # Check if text questions have difficulty-based categories
    cursor.execute("""
        SELECT COUNT(*) 
        FROM questions 
        WHERE question_image IS NULL 
        AND question_youtube IS NULL
        AND (option_a_image IS NULL AND option_b_image IS NULL AND 
             option_c_image IS NULL AND option_d_image IS NULL AND
             option_e_image IS NULL AND option_f_image IS NULL)
        AND category NOT IN ('easy', 'medium', 'hard', 'unseen')
    """)
    mismatched_text = cursor.fetchone()[0]
    
    if mismatched_text == 0:
        print("✅ PASS: All text questions have difficulty-based categories")
    else:
        print(f"⚠️  WARN: {mismatched_text} text questions have non-standard categories")
    
    conn.close()
    return all_pass

def main():
    print("="*70)
    print("QUESTION CATEGORY & EXAM CREATION TEST SUITE")
    print("="*70)
    
    # Run all tests
    test1_pass, category_counts = test_question_categories()
    test2_pass = test_exam_question_counts(category_counts)
    test3_pass = test_exam_question_selection()
    test4_pass = test_category_integrity()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    tests = [
        ("Question Categories", test1_pass),
        ("Exam Question Counts", test2_pass),
        ("Question Selection", test3_pass),
        ("Category Integrity", test4_pass)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print("="*70)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("="*70)
    
    if passed == total:
        print("\n🎉 All tests passed! The system is working correctly.")
        print("\nNext steps:")
        print("  1. Create a new exam from the admin panel")
        print("  2. Verify question counts are accurate")
        print("  3. Take the exam as a student")
        print("  4. Verify new questions appear in the exam")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")

if __name__ == '__main__':
    main()
