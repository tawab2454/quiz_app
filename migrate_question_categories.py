"""
Migration Script: Update Question Categories
This script updates the category field for all questions in the database.
"""

import sqlite3
import os

def get_db_connection():
    db_path = 'exam_system.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def update_question_categories():
    """Update category field for all questions based on their properties"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if category column exists
        cursor.execute("PRAGMA table_info(questions)")
        columns = [col['name'] for col in cursor.fetchall()]
        
        if 'category' not in columns:
            print("Adding 'category' column to questions table...")
            cursor.execute("ALTER TABLE questions ADD COLUMN category TEXT")
            conn.commit()
            print("✅ Category column added successfully!")
        
        # Update all questions to have proper category values
        print("\nUpdating question categories...")
        
        # First, update all questions with the correct category logic
        # This will fix both NULL categories AND mismatched categories
        cursor.execute("""
            UPDATE questions 
            SET category = CASE
                WHEN question_image IS NOT NULL OR 
                     option_a_image IS NOT NULL OR 
                     option_b_image IS NOT NULL OR 
                     option_c_image IS NOT NULL OR 
                     option_d_image IS NOT NULL OR 
                     option_e_image IS NOT NULL OR 
                     option_f_image IS NOT NULL THEN 'image'
                WHEN question_youtube IS NOT NULL THEN 'video'
                WHEN difficulty IS NOT NULL THEN difficulty
                ELSE 'medium'
            END
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ Updated {updated_count} questions with category values")
        
        # Show category distribution
        print("\n" + "="*60)
        print("Question Category Distribution:")
        print("="*60)
        
        cursor.execute("""
            SELECT 
                category, 
                COUNT(*) as count 
            FROM questions 
            GROUP BY category 
            ORDER BY count DESC
        """)
        
        for row in cursor.fetchall():
            category = row['category'] or 'NULL'
            count = row['count']
            print(f"  {category:15} : {count:5} questions")
        
        # Show total count
        cursor.execute("SELECT COUNT(*) as total FROM questions")
        total = cursor.fetchone()['total']
        print("="*60)
        print(f"  {'TOTAL':15} : {total:5} questions")
        print("="*60)
        
        # Check for any NULL categories (should be none now)
        cursor.execute("SELECT COUNT(*) FROM questions WHERE category IS NULL")
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            print(f"\n⚠️  Warning: {null_count} questions still have NULL category")
        else:
            print("\n✅ All questions have valid categories!")
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("="*60)
    print("Question Category Migration Script")
    print("="*60)
    print("\nThis script will update all questions with proper category values.")
    print("Categories are determined by:")
    print("  - 'image' if question has any images")
    print("  - 'video' if question has YouTube link")
    print("  - difficulty value (easy/medium/hard) otherwise")
    print("="*60)
    
    response = input("\nDo you want to proceed? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\nStarting migration...\n")
        update_question_categories()
    else:
        print("\nMigration cancelled.")
