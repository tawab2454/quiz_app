#!/usr/bin/env python3
"""
Admin Password Reset Tool
=========================
This script allows you to manually reset the admin password.

Usage:
    python admin_password_reset.py

Features:
- Reset admin password to default (admin123)
- Set custom password
- Enable/disable password change requirement
- Verify admin credentials
"""

import sqlite3
import bcrypt
import getpass
import sys
from datetime import datetime

class AdminPasswordReset:
    def __init__(self):
        self.db_name = 'exam_system.db'
        self.default_password = 'admin123'
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return None
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        try:
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
            return password_hash.decode('utf-8')
        except Exception as e:
            print(f"❌ Password hashing error: {e}")
            return None
    
    def verify_password(self, password, hash_value):
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hash_value.encode('utf-8'))
        except Exception as e:
            print(f"❌ Password verification error: {e}")
            return False
    
    def check_admin_exists(self):
        """Check if admin user exists"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            admin = conn.execute('SELECT * FROM admins WHERE username = ?', ('admin',)).fetchone()
            conn.close()
            return admin is not None
        except Exception as e:
            print(f"❌ Error checking admin: {e}")
            conn.close()
            return False
    
    def get_admin_info(self):
        """Get current admin information"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        try:
            admin = conn.execute('SELECT * FROM admins WHERE username = ?', ('admin',)).fetchone()
            conn.close()
            return admin
        except Exception as e:
            print(f"❌ Error getting admin info: {e}")
            conn.close()
            return None
    
    def reset_to_default(self):
        """Reset admin password to default"""
        print(f"\n🔄 Resetting admin password to default: '{self.default_password}'")
        
        if not self.check_admin_exists():
            print("❌ Admin user does not exist!")
            return False
        
        password_hash = self.hash_password(self.default_password)
        if not password_hash:
            return False
        
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            conn.execute('''
                UPDATE admins 
                SET password_hash = ?, password_change_required = 1 
                WHERE username = ?
            ''', (password_hash, 'admin'))
            conn.commit()
            conn.close()
            
            print(f"✅ Admin password reset successfully!")
            print(f"📝 Username: admin")
            print(f"📝 Password: {self.default_password}")
            print(f"⚠️  Password change will be required on next login")
            return True
            
        except Exception as e:
            print(f"❌ Error resetting password: {e}")
            conn.close()
            return False
    
    def set_custom_password(self):
        """Set custom admin password"""
        print("\n🔐 Setting custom admin password")
        
        if not self.check_admin_exists():
            print("❌ Admin user does not exist!")
            return False
        
        # Get new password
        while True:
            new_password = getpass.getpass("Enter new password: ")
            if len(new_password) < 6:
                print("❌ Password must be at least 6 characters long")
                continue
            
            confirm_password = getpass.getpass("Confirm new password: ")
            if new_password != confirm_password:
                print("❌ Passwords do not match")
                continue
            
            break
        
        # Ask if password change should be required
        while True:
            require_change = input("Require password change on next login? (y/n): ").lower()
            if require_change in ['y', 'yes']:
                change_required = 1
                break
            elif require_change in ['n', 'no']:
                change_required = 0
                break
            else:
                print("❌ Please enter 'y' or 'n'")
        
        password_hash = self.hash_password(new_password)
        if not password_hash:
            return False
        
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            conn.execute('''
                UPDATE admins 
                SET password_hash = ?, password_change_required = ? 
                WHERE username = ?
            ''', (password_hash, change_required, 'admin'))
            conn.commit()
            conn.close()
            
            print(f"✅ Custom password set successfully!")
            print(f"📝 Username: admin")
            print(f"⚠️  Password change required: {'Yes' if change_required else 'No'}")
            return True
            
        except Exception as e:
            print(f"❌ Error setting password: {e}")
            conn.close()
            return False
    
    def verify_credentials(self):
        """Verify admin credentials"""
        print("\n🔍 Verifying admin credentials")
        
        admin = self.get_admin_info()
        if not admin:
            print("❌ Admin user not found!")
            return False
        
        print(f"📋 Current admin info:")
        print(f"   Username: {admin['username']}")
        print(f"   Password change required: {'Yes' if admin['password_change_required'] else 'No'}")
        
        # Test password
        test_password = getpass.getpass("Enter password to test: ")
        
        if self.verify_password(test_password, admin['password_hash']):
            print("✅ Password is correct!")
            return True
        else:
            print("❌ Password is incorrect!")
            return False
    
    def show_menu(self):
        """Show main menu"""
        print("\n" + "="*50)
        print("🔐 Admin Password Reset Tool")
        print("="*50)
        print("1. Reset password to default (admin123)")
        print("2. Set custom password")
        print("3. Verify current credentials")
        print("4. Show admin info")
        print("5. Exit")
        print("-"*50)
    
    def show_admin_info(self):
        """Show current admin information"""
        print("\n📋 Current Admin Information")
        print("-"*30)
        
        admin = self.get_admin_info()
        if not admin:
            print("❌ Admin user not found!")
            return
        
        print(f"ID: {admin['id']}")
        print(f"Username: {admin['username']}")
        print(f"Password Hash: {admin['password_hash'][:50]}...")
        print(f"Password Change Required: {'Yes' if admin['password_change_required'] else 'No'}")
        
        # Test default password
        if self.verify_password(self.default_password, admin['password_hash']):
            print(f"🔑 Current password is: {self.default_password}")
        else:
            print(f"🔒 Current password is not the default")
    
    def run(self):
        """Run the password reset tool"""
        print("🚀 Starting Admin Password Reset Tool...")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not self.check_admin_exists():
            print("❌ Admin user does not exist in database!")
            print("❌ Please run the main application first to create admin user.")
            return
        
        while True:
            try:
                self.show_menu()
                choice = input("\nEnter your choice (1-5): ").strip()
                
                if choice == '1':
                    self.reset_to_default()
                elif choice == '2':
                    self.set_custom_password()
                elif choice == '3':
                    self.verify_credentials()
                elif choice == '4':
                    self.show_admin_info()
                elif choice == '5':
                    print("\n👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-5.")
                
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                input("Press Enter to continue...")

def main():
    """Main function"""
    try:
        reset_tool = AdminPasswordReset()
        reset_tool.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()