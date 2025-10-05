import sqlite3
import bcrypt

def reset_admin_password():
    conn = sqlite3.connect('exam_system.db')
    
    # Hash the password
    password = 'admin123'
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    # Update admin password
    conn.execute('UPDATE admins SET password_hash = ?, password_change_required = 1 WHERE username = ?',
                (password_hash.decode('utf-8'), 'admin'))
    conn.commit()
    
    print("Admin password reset to: admin123")
    print("Password change will be required on next login")
    
    # Verify the update
    admin = conn.execute('SELECT * FROM admins WHERE username = ?', ('admin',)).fetchone()
    if admin:
        print(f"Updated admin hash: {admin[2][:50]}...")
        print(f"Change required: {admin[3]}")
    
    conn.close()

if __name__ == "__main__":
    reset_admin_password()