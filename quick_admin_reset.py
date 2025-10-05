#!/usr/bin/env python3
"""
Quick Admin Password Reset
==========================
Simple script to quickly reset admin password to default.

Usage: python quick_admin_reset.py
"""

import sqlite3
import bcrypt
from datetime import datetime

def quick_reset_admin():
    """Quick reset admin password to default"""
    print("🔄 Quick Admin Password Reset")
    print("="*40)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Connect to database
        conn = sqlite3.connect('exam_system.db')
        conn.row_factory = sqlite3.Row
        
        # Check if admin exists
        admin = conn.execute('SELECT * FROM admins WHERE username = ?', ('admin',)).fetchone()
        
        if not admin:
            print("❌ Admin user not found!")
            print("💡 Please run the main application first to create admin user.")
            conn.close()
            return False
        
        print(f"✅ Admin user found: {admin['username']}")
        
        # Hash new password
        default_password = 'admin123'
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(default_password.encode('utf-8'), salt)
        
        # Update admin password
        conn.execute('''
            UPDATE admins 
            SET password_hash = ?, password_change_required = 1 
            WHERE username = ?
        ''', (password_hash.decode('utf-8'), 'admin'))
        
        conn.commit()
        conn.close()
        
        print("✅ Password reset successful!")
        print(f"📝 Username: admin")
        print(f"📝 Password: {default_password}")
        print("⚠️  Password change will be required on next login")
        print("\n🌐 You can now login at: http://localhost:5008/admin/login")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    try:
        quick_reset_admin()
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    
    input("\nPress Enter to exit...")