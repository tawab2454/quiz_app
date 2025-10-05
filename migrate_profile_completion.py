"""
Database migration script to add profile completion tracking
and make location fields nullable for security.
"""
import sqlite3
import os

def migrate_database():
    db_path = 'exam_system.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if profile_completed column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'profile_completed' not in columns:
            print("Adding 'profile_completed' column to users table...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN profile_completed INTEGER DEFAULT 0
            """)
            conn.commit()
            print("✅ Added 'profile_completed' column")
            
            # Update existing users to have profile_completed = 1
            # (since they already have all information)
            cursor.execute("""
                UPDATE users 
                SET profile_completed = 1 
                WHERE wing_name IS NOT NULL
            """)
            conn.commit()
            print(f"✅ Updated {cursor.rowcount} existing users to profile_completed = 1")
        else:
            print("'profile_completed' column already exists")
        
        # Note: SQLite doesn't support modifying column constraints directly
        # So wing_name, division_name etc. are already nullable (no NOT NULL constraint)
        # We just need to ensure the application logic handles NULL values
        
        print("\n✅ Migration completed successfully!")
        
        # Show current user count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE profile_completed = 1")
        completed_count = cursor.fetchone()[0]
        
        print(f"\n📊 Database Status:")
        print(f"   Total users: {user_count}")
        print(f"   Complete profiles: {completed_count}")
        print(f"   Incomplete profiles: {user_count - completed_count}")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("  Profile Completion Migration Script")
    print("=" * 60)
    print()
    migrate_database()
