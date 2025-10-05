#!/usr/bin/env python3
"""
Simple Online Examination System - Complete Working Version
Pure HTML, CSS, JavaScript, and Python Flask
No external dependencies except Flask
"""
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, make_response, send_from_directory
import sqlite3
import hashlib
import secrets
import json
import random
from datetime import datetime, timedelta
import time
import os
import bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_wtf import csrf
import re
import html

# Input validation and sanitization module
class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    @staticmethod
    def sanitize_string(value, max_length=None, allow_html=False):
        """Sanitize string input to prevent XSS"""
        if not value:
            return ""
        
        # Convert to string and strip whitespace
        value = str(value).strip()
        
        # HTML escape if HTML is not allowed
        if not allow_html:
            value = html.escape(value)
        
        # Truncate if max_length specified
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        return value
    
    @staticmethod
    def validate_nsi_id(nsi_id):
        """Validate NSI ID format (a-d dash 4 digits)"""
        if not nsi_id:
            return False, "NSI ID is required"
        
        nsi_id = str(nsi_id).lower().strip()
        
        if not re.match(r'^[a-d]-[0-9]{4}$', nsi_id):
            return False, "NSI ID must be in format: a-1234 (letter a-d, dash, 4 digits)"
        
        return True, nsi_id
    
    @staticmethod
    def validate_password(password, min_length=6):
        """Validate password strength"""
        if not password:
            return False, "Password is required"
        
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters long"
        
        # Check for common weak passwords
        weak_patterns = ['password', '123456', 'admin', 'qwerty', 'abc123']
        if password.lower() in weak_patterns:
            return False, "Password is too weak. Please choose a stronger password"
        
        return True, password
    
    @staticmethod
    def validate_username(username):
        """Validate username format"""
        if not username:
            return False, "Username is required"
        
        username = str(username).strip()
        
        # Allow alphanumeric and underscore, 3-20 characters
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            return False, "Username must be 3-20 characters, letters, numbers and underscore only"
        
        return True, username
    
    @staticmethod
    def validate_name(name):
        """Validate person name"""
        if not name:
            return False, "Name is required"
        
        name = str(name).strip()
        
        # Allow letters, spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-Z\s'-\.]{2,50}$", name):
            return False, "Name must be 2-50 characters, letters and common punctuation only"
        
        return True, name
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email:
            return False, "Email is required"
        
        email = str(email).strip().lower()
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, "Please enter a valid email address"
        
        return True, email
    
    @staticmethod
    def validate_integer(value, min_val=None, max_val=None):
        """Validate integer input"""
        try:
            int_value = int(value)
            if min_val is not None and int_value < min_val:
                return False, f"Value must be at least {min_val}"
            if max_val is not None and int_value > max_val:
                return False, f"Value must be at most {max_val}"
            return True, int_value
        except (ValueError, TypeError):
            return False, "Please enter a valid number"
    
    @staticmethod
    def validate_choice(value, allowed_choices):
        """Validate that value is in allowed choices"""
        if not value:
            return False, "Selection is required"
        
        if value not in allowed_choices:
            return False, f"Invalid choice. Must be one of: {', '.join(allowed_choices)}"
        
        return True, value
    
    @staticmethod
    def detect_sql_injection(value):
        """Detect potential SQL injection attempts"""
        if not value:
            return False
        
        # Common SQL injection patterns
        sql_patterns = [
            r"(\s*(;|'|\"|\-\-|\/\*|\*\/|@@|@|char|nchar|varchar|nvarchar|alter|begin|cast|create|cursor|declare|delete|drop|end|exec|execute|fetch|insert|kill|open|select|sys|sysobjects|syscolumns|table|update)\s*)",
            r"(\s*(union|join|where|order\s+by|group\s+by|having)\s+)",
            r"(\s*(script|javascript|vbscript|onload|onerror|onclick)\s*)",
        ]
        
        value_lower = str(value).lower()
        for pattern in sql_patterns:
            if re.search(pattern, value_lower):
                return True
        
        return False
    
    @staticmethod
    def detect_xss(value):
        """Detect potential XSS attempts"""
        if not value:
            return False
        
        # Common XSS patterns
        xss_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*=',
            r'onmouseover\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
        ]
        
        value_lower = str(value).lower()
        for pattern in xss_patterns:
            if re.search(pattern, value_lower):
                return True
        
        return False

# Input validation decorator
def validate_input(validation_rules):
    """Decorator for input validation"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            if request.method == 'POST':
                errors = []
                
                for field_name, rules in validation_rules.items():
                    value = request.form.get(field_name, '')
                    
                    # Check for malicious content
                    if InputValidator.detect_sql_injection(value):
                        flash('Potential security threat detected. Request blocked.', 'error')
                        return redirect(request.url)
                    
                    if InputValidator.detect_xss(value):
                        flash('Potential security threat detected. Request blocked.', 'error')
                        return redirect(request.url)
                    
                    # Apply validation rules
                    for rule in rules:
                        valid, result = rule(value)
                        if not valid:
                            errors.append(result)
                            break
                
                if errors:
                    for error in errors:
                        flash(error, 'error')
                    return redirect(request.url)
            
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# Register custom adapters for datetime
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
sqlite3.register_converter("TIMESTAMP", lambda s: datetime.fromisoformat(s.decode()))

# Initialize Flask app
app = Flask(__name__)

# Configure Jinja2 for enhanced security
app.jinja_env.autoescape = True  # Ensure autoescape is enabled
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# Use a more secure secret key management
# In production, this should be loaded from environment variables
SECRET_KEY_FILE = 'secret_key.txt'
if os.path.exists(SECRET_KEY_FILE):
    with open(SECRET_KEY_FILE, 'r') as f:
        app.secret_key = f.read().strip()
else:
    # Generate and save secret key for consistency
    secret_key = secrets.token_hex(32)
    with open(SECRET_KEY_FILE, 'w') as f:
        f.write(secret_key)
    app.secret_key = secret_key

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Add custom Jinja2 filters for extra security
@app.template_filter('safe_output')
def safe_output_filter(value):
    """Extra HTML escaping for user-provided content"""
    if not value:
        return ""
    return html.escape(str(value))

@app.template_filter('safe_name')
def safe_name_filter(value):
    """Safe display of names and titles"""
    if not value:
        return ""
    # Allow only letters, spaces, and common punctuation
    cleaned = re.sub(r'[^a-zA-Z0-9\s\-\.\'\,]', '', str(value))
    return html.escape(cleaned[:100])  # Limit length

@app.template_filter('safe_html')
def safe_html_filter(value):
    """Strip all HTML tags and escape content"""
    if not value:
        return ""
    # Remove all HTML tags
    clean_text = re.sub(r'<[^>]+>', '', str(value))
    # HTML escape the result
    return html.escape(clean_text)

@app.template_filter('safe_url')
def safe_url_filter(value):
    """Validate and sanitize URLs and local paths"""
    if not value:
        return ""
    
    value = str(value).strip()
    
    # Allow local paths starting with /static/
    if value.startswith('/static/'):
        # Normalize path separators and remove any dangerous characters
        safe_path = value.replace('\\', '/').replace('..', '')
        return html.escape(safe_path)
    
    # Allow http and https URLs
    if re.match(r'^https?://', value):
        try:
            from urllib.parse import urlparse
            parsed = urlparse(value)
            if not parsed.netloc:
                return ""
            return html.escape(value)
        except:
            return ""
    
    # For other cases, return empty string
    return ""

@app.template_filter('safe_text')
def safe_text_filter(value, max_length=500):
    """Comprehensive text sanitization"""
    if not value:
        return ""
    
    text = str(value)
    
    # Remove potential script content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Limit length
    if max_length and len(text) > max_length:
        text = text[:max_length] + "..."
    
    return html.escape(text)

@app.template_filter('strip_dangerous')
def strip_dangerous_filter(value):
    """Remove dangerous characters and patterns"""
    if not value:
        return ""
    
    text = str(value)
    
    # Remove dangerous patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
        r'on\w+\s*=',
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return html.escape(text)

# Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add comprehensive security headers to all responses"""
    # Basic security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Note: X-Frame-Options removed to avoid conflicts with CSP frame-src
    # response.headers['X-Frame-Options'] = 'DENY'  # This can conflict with iframe embeds
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Enhanced Content Security Policy for XSS prevention (with YouTube support)
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "media-src 'self'; "
        "object-src 'none'; "
        "frame-src 'self' https://www.youtube.com https://youtube.com https://www.youtube-nocookie.com; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )
    response.headers['Content-Security-Policy'] = csp_policy
    
    # Additional XSS protection headers (reduced for iframe compatibility)
    response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
    # Temporarily remove conflicting headers for iframe testing
    # response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    # response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'  # Disabled for YouTube embeds
    
    # Cache-busting headers to force policy refresh
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

# Helper functions for form data
def get_divisions():
    """Get all divisions from database"""
    try:
        conn = get_db_connection()
        divisions = conn.execute('SELECT * FROM divisions ORDER BY name').fetchall()
        conn.close()
        return divisions
    except:
        return []

def get_districts():
    """Get all districts from database"""
    try:
        conn = get_db_connection()
        districts = conn.execute('SELECT * FROM districts ORDER BY name').fetchall()
        conn.close()
        return districts
    except:
        return []

# Custom error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(400)
def bad_request_error(error):
    flash('Invalid request. Please try again.', 'error')
    return redirect(url_for('index'))

# Database configuration
DATABASE = 'exam_system.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_passwords_to_bcrypt():
    """Migrate existing SHA-256 passwords to bcrypt"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Add password_change_required column to admins table if it doesn't exist
    cursor.execute("PRAGMA table_info(admins)")
    admin_columns = [col['name'] for col in cursor.fetchall()]
    if 'password_change_required' not in admin_columns:
        cursor.execute("ALTER TABLE admins ADD COLUMN password_change_required INTEGER DEFAULT 0")
        conn.commit()
        print("Added 'password_change_required' column to admins table")
    
    # Check if admin password is still SHA-256 (64 characters)
    admin = cursor.execute('SELECT id, password_hash FROM admins WHERE username = ?', ('admin',)).fetchone()
    if admin and len(admin['password_hash']) == 64:  # SHA-256 hash length
        print("Migrating admin password from SHA-256 to bcrypt...")
        new_hash = hash_password('admin123')
        cursor.execute('UPDATE admins SET password_hash = ?, password_change_required = 1 WHERE id = ?', 
                      (new_hash, admin['id']))
        print("Admin password migrated to bcrypt and marked for password change")
    
    # Check user passwords and show summary
    users = cursor.execute('SELECT id, password_hash FROM users').fetchall()
    sha256_users = [user for user in users if len(user['password_hash']) == 64]
    
    if sha256_users:
        print(f"⚠️  Found {len(sha256_users)} users with old SHA-256 passwords")
        print("💡 Run 'python migrate_user_passwords.py' to migrate them to bcrypt format")
    else:
        print("✅ All user passwords are in bcrypt format")
    
    conn.commit()
    conn.close()

def migrate_database():
    """Handle database migrations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if division_name column exists in users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'division_name' not in columns:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN division_name TEXT")
            conn.commit()
            print("Added division_name column to users table")
        except sqlite3.Error as e:
            print(f"Error adding division_name column: {e}")
    
    conn.close()

def init_database():
    """Initialize database with tables and sample data"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create system_settings table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY,
            registration_enabled INTEGER DEFAULT 1,
            maintenance_mode INTEGER DEFAULT 0,
            exams_enabled INTEGER DEFAULT 1,
            exam_window_start TIMESTAMP,
            exam_window_end TIMESTAMP,
            last_backup_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if system_settings has at least one row
    cursor.execute("SELECT COUNT(*) FROM system_settings")
    if cursor.fetchone()[0] == 0:
        # Insert default system settings
        cursor.execute('''
            INSERT INTO system_settings (
                id, registration_enabled, maintenance_mode, exams_enabled,
                created_at, updated_at
            ) VALUES (
                1, 1, 0, 1, datetime('now'), datetime('now')
            )
        ''')
        conn.commit()

    # Check and add category column to questions table
    cursor.execute("PRAGMA table_info(questions)")
    columns = [col['name'] for col in cursor.fetchall()]
    if 'category' not in columns:
        try:
            cursor.execute("ALTER TABLE questions ADD COLUMN category TEXT")
            # Update existing questions with categories based on their properties
            cursor.execute("""
                UPDATE questions 
                SET category = CASE
                    WHEN question_image IS NOT NULL THEN 'image'
                    WHEN question_youtube IS NOT NULL THEN 'video'
                    ELSE difficulty
                END
            """)
            conn.commit()
            print("Added 'category' column to questions table")
        except sqlite3.OperationalError as e:
            print(f"Error adding category column: {e}")

    # Check and add new columns to exams table
    cursor.execute("PRAGMA table_info(exams)")
    columns = [col['name'] for col in cursor.fetchall()]
    if 'category_config' not in columns:
        try:
            cursor.execute("ALTER TABLE exams ADD COLUMN category_config TEXT")
            conn.commit()
            print("Added 'category_config' column to exams table")
        except sqlite3.OperationalError as e:
            print(f"Error adding category_config column: {e}")

    # Add scheduled_start and scheduled_end columns for exam scheduling
    if 'scheduled_start' not in columns:
        try:
            cursor.execute("ALTER TABLE exams ADD COLUMN scheduled_start TIMESTAMP")
            conn.commit()
            print("Added 'scheduled_start' column to exams table")
        except sqlite3.OperationalError as e:
            print(f"Error adding scheduled_start column: {e}")
    if 'scheduled_end' not in columns:
        try:
            cursor.execute("ALTER TABLE exams ADD COLUMN scheduled_end TIMESTAMP")
            conn.commit()
            print("Added 'scheduled_end' column to exams table")
        except sqlite3.OperationalError as e:
            print(f"Error adding scheduled_end column: {e}")

    # Check and add exam_controls table
    cursor.execute("PRAGMA table_info(exam_controls)")
    columns = [col['name'] for col in cursor.fetchall()]
    if not columns:
        cursor.executescript('''
            -- Exam controls table
            CREATE TABLE IF NOT EXISTS exam_controls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                show_result_immediately BOOLEAN DEFAULT 1,
                show_result_history BOOLEAN DEFAULT 1,
                show_rankings BOOLEAN DEFAULT 1,
                enable_copy_protection BOOLEAN DEFAULT 1,
                enable_screenshot_block BOOLEAN DEFAULT 1,
                enable_tab_switch_detect BOOLEAN DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        # Initialize default exam controls
        controls_count = conn.execute('SELECT COUNT(*) FROM exam_controls').fetchone()[0]
        if controls_count == 0:
            conn.execute('''
                INSERT INTO exam_controls 
                (show_result_immediately, show_result_history, show_rankings, enable_copy_protection, enable_screenshot_block, enable_tab_switch_detect) 
                VALUES (1, 1, 1, 1, 1, 1)
            ''')
            print("Initialized exam_controls with default values")
        conn.commit()
    else:
        # Check if show_rankings column exists and add it if missing
        if 'show_rankings' not in columns:
            try:
                cursor.execute("ALTER TABLE exam_controls ADD COLUMN show_rankings BOOLEAN DEFAULT 1")
                conn.commit()
                print("Added 'show_rankings' column to exam_controls table")
            except sqlite3.OperationalError:
                pass
        
        # Check if allow_answer_review column exists and add it if missing
        if 'allow_answer_review' not in columns:
            try:
                cursor.execute("ALTER TABLE exam_controls ADD COLUMN allow_answer_review BOOLEAN DEFAULT 1")
                conn.commit()
                print("Added 'allow_answer_review' column to exam_controls table")
            except sqlite3.OperationalError:
                pass
        
    # Check and add system_settings table
    cursor.execute("PRAGMA table_info(system_settings)")
    columns = [col['name'] for col in cursor.fetchall()]
    if not columns:
        cursor.executescript('''
            -- System settings table
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                registration_enabled INTEGER DEFAULT 1,
                maintenance_mode INTEGER DEFAULT 0,
                db_backup_path TEXT DEFAULT 'backups/',
                last_backup_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        # Initialize default system settings
        settings_count = conn.execute('SELECT COUNT(*) FROM system_settings').fetchone()[0]
        if settings_count == 0:
            conn.execute('''
                INSERT INTO system_settings 
                (registration_enabled, maintenance_mode, updated_at) 
                VALUES (1, 0, ?)
            ''', (datetime.now(),))
            print("Initialized system_settings with default values")
        conn.commit()

    # Check and add missing columns to system_settings
    cursor.execute("PRAGMA table_info(system_settings)")
    columns = [col['name'] for col in cursor.fetchall()]
    if 'exams_enabled' not in columns:
        try:
            cursor.execute("ALTER TABLE system_settings ADD COLUMN exams_enabled INTEGER DEFAULT 1")
            conn.commit()
            print("Added 'exams_enabled' column to system_settings table")
            # Update existing row
            cursor.execute("UPDATE system_settings SET exams_enabled = 1 WHERE id = 1")
            conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Error adding exams_enabled column: {e}")
    if 'exam_window_start' not in columns:
        try:
            cursor.execute("ALTER TABLE system_settings ADD COLUMN exam_window_start TIMESTAMP")
            conn.commit()
            print("Added 'exam_window_start' column to system_settings table")
        except sqlite3.OperationalError as e:
            print(f"Error adding exam_window_start column: {e}")
    if 'exam_window_end' not in columns:
        try:
            cursor.execute("ALTER TABLE system_settings ADD COLUMN exam_window_end TIMESTAMP")
            conn.commit()
            print("Added 'exam_window_end' column to system_settings table")
        except sqlite3.OperationalError as e:
            print(f"Error adding exam_window_end column: {e}")

    # Check if answers_detail column exists in exam_sessions
    cursor.execute("PRAGMA table_info(exam_sessions)")
    columns = [col['name'] for col in cursor.fetchall()]
    
    # Add answers_detail column if it doesn't exist
    if 'answers_detail' not in columns:
        try:
            cursor.execute("ALTER TABLE exam_sessions ADD COLUMN answers_detail TEXT")
            conn.commit()
            print("Added 'answers_detail' column to exam_sessions table")
        except sqlite3.OperationalError:
            pass  # Column might have been added by another process
    
    # Check if answers_detail column exists in exam_sessions
    cursor.execute("PRAGMA table_info(exam_sessions)")
    columns = [col['name'] for col in cursor.fetchall()]
    
    # Add answers_detail column if it doesn't exist
    if 'answers_detail' not in columns:
        try:
            cursor.execute("ALTER TABLE exam_sessions ADD COLUMN answers_detail TEXT")
            conn.commit()
            print("Added 'answers_detail' column to exam_sessions table")
        except sqlite3.OperationalError:
            pass  # Column might have been added by another process

    conn.executescript('''
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nsi_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            wing_name TEXT,
            internal_type TEXT,
            border_type TEXT,
            external_type TEXT,
            country_name TEXT,
            division_name TEXT,
            district_name TEXT,
            section_name TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Admin table
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Questions table
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            option_e TEXT,
            option_f TEXT,
            correct_option TEXT NOT NULL,
            difficulty TEXT DEFAULT 'medium',
            subject TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Exams table
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            duration_minutes INTEGER NOT NULL,
            num_questions INTEGER NOT NULL,
            passing_score INTEGER DEFAULT 60,
            max_attempts INTEGER DEFAULT 1,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Exam sessions table
        CREATE TABLE IF NOT EXISTS exam_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exam_id INTEGER NOT NULL,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            score INTEGER,
            answers TEXT,
            answers_detail TEXT,
            is_completed BOOLEAN DEFAULT 0,
            questions_json TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (exam_id) REFERENCES exams (id)
        );
    ''')
    
    # Check if required columns exist in questions table
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(questions)")
    columns = [col['name'] for col in cursor.fetchall()]
    
    required_columns = {
        'question_text': {'type': 'TEXT', 'not_null': True, 'default': "''"},
        'option_a': {'type': 'TEXT', 'not_null': True, 'default': "''"},
        'option_b': {'type': 'TEXT', 'not_null': True, 'default': "''"},
        'option_c': {'type': 'TEXT', 'not_null': True, 'default': "''"},
        'option_d': {'type': 'TEXT', 'not_null': True, 'default': "''"},
        'option_e': {'type': 'TEXT', 'not_null': False, 'default': None},
        'option_f': {'type': 'TEXT', 'not_null': False, 'default': None},
        'correct_option': {'type': 'TEXT', 'not_null': True, 'default': "'A'"},
        'difficulty': {'type': 'TEXT', 'not_null': False, 'default': "'medium'"},
        'subject': {'type': 'TEXT', 'not_null': False, 'default': "'general'"}
    }
    
    for col_name, col_info in required_columns.items():
        if col_name not in columns:
            col_def = f"{col_info['type']}"
            if col_info['not_null']:
                col_def += f" NOT NULL DEFAULT {col_info['default']}"
            elif col_info['default']:
                col_def += f" DEFAULT {col_info['default']}"
            cursor.execute(f"ALTER TABLE questions ADD COLUMN {col_name} {col_def}")
            conn.commit()
            print(f"Added '{col_name}' column to questions table")
    
    # Ensure no NULL values in required columns
    cursor.execute('''
        UPDATE questions 
        SET 
            question_text = COALESCE(question_text, ''),
            option_a = COALESCE(option_a, ''),
            option_b = COALESCE(option_b, ''),
            option_c = COALESCE(option_c, ''),
            option_d = COALESCE(option_d, ''),
            correct_option = COALESCE(correct_option, 'A'),
            difficulty = COALESCE(difficulty, 'medium'),
            subject = COALESCE(subject, 'general')
        WHERE 
            question_text IS NULL OR 
            option_a IS NULL OR 
            option_b IS NULL OR 
            option_c IS NULL OR 
            option_d IS NULL OR 
            correct_option IS NULL OR 
            difficulty IS NULL OR 
            subject IS NULL
    ''')
    conn.commit()
    
    # Normalize correct_option to uppercase string
    cursor.execute("UPDATE questions SET correct_option = UPPER(correct_option)")
    conn.commit()
    
    # Check for questions_json in exam_sessions
    cursor.execute("PRAGMA table_info(exam_sessions)")
    es_columns = [col['name'] for col in cursor.fetchall()]
    if 'questions_json' not in es_columns:
        cursor.execute("ALTER TABLE exam_sessions ADD COLUMN questions_json TEXT")
        conn.commit()
        print("Added 'questions_json' column to exam_sessions table")
    
    # Check for duration_minutes in exam_sessions
    if 'duration_minutes' not in es_columns:
        cursor.execute("ALTER TABLE exam_sessions ADD COLUMN duration_minutes REAL")
        conn.commit()
        print("Added 'duration_minutes' column to exam_sessions table")
        
        # Update existing records with calculated duration
        cursor.execute('''
            UPDATE exam_sessions 
            SET duration_minutes = CASE 
                WHEN start_time IS NOT NULL AND end_time IS NOT NULL 
                THEN ROUND((julianday(end_time) - julianday(start_time)) * 24 * 60, 2)
                ELSE NULL 
            END
            WHERE is_completed = 1
        ''')
        conn.commit()
        print("Updated existing exam sessions with calculated durations")
    
    # Check if internal_type column exists in users table
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [col['name'] for col in cursor.fetchall()]
    if 'internal_type' not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN internal_type TEXT")
        conn.commit()
        print("Added 'internal_type' column to users table")
    
    # Check if border_type column exists in users table
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [col['name'] for col in cursor.fetchall()]
    if 'border_type' not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN border_type TEXT")
        conn.commit()
        print("Added 'border_type' column to users table")
    
    # Check if external_type column exists in users table
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [col['name'] for col in cursor.fetchall()]
    if 'external_type' not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN external_type TEXT")
        conn.commit()
        print("Added 'external_type' column to users table")
    
    # Check if country_name column exists in users table
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [col['name'] for col in cursor.fetchall()]
    if 'country_name' not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN country_name TEXT")
        conn.commit()
        print("Added 'country_name' column to users table")
    
    # Check if admin exists
    admin_exists = conn.execute('SELECT COUNT(*) FROM admins').fetchone()[0]
    if admin_exists == 0:
        admin_password = hash_password('admin123')
        conn.execute('INSERT INTO admins (username, password_hash) VALUES (?, ?)', 
                    ('admin', admin_password))
        print("Admin user created: admin / admin123")
    
    # Check if questions exist
    question_count = conn.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
    if question_count == 0:
        sample_questions = [
            ("What is the capital of Bangladesh?", "Dhaka", "Chittagong", "Sylhet", "Rajshahi", "", "", "A", "easy", "geography"),
            ("Which programming language is known for web development?", "Python", "JavaScript", "C++", "Java", "PHP", "Ruby", "B", "medium", "programming"),
            ("What is 2 + 2?", "3", "4", "5", "6", "", "", "B", "easy", "mathematics"),
            ("Who wrote 'Romeo and Juliet'?", "Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain", "", "", "B", "medium", "literature"),
            ("What is the largest planet in our solar system?", "Earth", "Mars", "Jupiter", "Saturn", "", "", "C", "medium", "science"),
            ("Which year did Bangladesh gain independence?", "1970", "1971", "1972", "1973", "", "", "B", "medium", "history"),
            ("What is the chemical symbol for water?", "H2O", "CO2", "NaCl", "O2", "", "", "A", "easy", "chemistry"),
            ("Which is the longest river in the world?", "Amazon", "Nile", "Ganges", "Mississippi", "", "", "B", "hard", "geography"),
            ("What does CPU stand for?", "Central Processing Unit", "Computer Personal Unit", "Central Program Unit", "Computer Processing Unit", "", "", "A", "medium", "technology"),
            ("Which country has the most time zones?", "USA", "Russia", "China", "Canada", "", "", "B", "hard", "geography")
        ]
        
        for q in sample_questions:
            conn.execute('''INSERT INTO questions 
                           (question_text, option_a, option_b, option_c, option_d, option_e, option_f, correct_option, difficulty, subject) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', q)
        
        print("Sample questions created")
    
    # Check if exam exists
    exam_count = conn.execute('SELECT COUNT(*) FROM exams').fetchone()[0]
    if exam_count == 0:
        conn.execute('''INSERT INTO exams 
                       (title, description, duration_minutes, num_questions, passing_score, max_attempts, is_active) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    ('General Knowledge Test', 'A comprehensive test covering various topics', 30, 10, 60, 1, 1))
        print("Sample exam created")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

def hash_password(password):
    """Hash password using bcrypt with salt"""
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

def verify_password(password, hash_value):
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hash_value.encode('utf-8'))
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def is_admin_logged_in():
    """Check if admin is logged in"""
    return session.get('admin_logged_in', False)

def requires_password_change():
    """Check if admin requires password change"""
    return session.get('password_change_required', False)

def admin_access_check():
    """Check admin access and password change requirement"""
    if not is_admin_logged_in():
        return False
    if requires_password_change():
        return 'password_change'
    return True

def is_user_logged_in():
    """Check if user is logged in"""
    return session.get('user_logged_in', False)

def get_current_user():
    """Get current logged in user"""
    if is_user_logged_in():
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        return user
    return None

# Routes
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
@csrf.exempt  # Exempt CSRF for user registration
def register():
    """User registration with comprehensive input validation"""
    # Check system settings for registration flag
    conn_check = get_db_connection()
    try:
        sys_row = conn_check.execute('SELECT registration_enabled FROM system_settings WHERE id = 1').fetchone()
        registration_open = True if (sys_row and sys_row['registration_enabled']) else False
    except Exception:
        registration_open = True
    finally:
        conn_check.close()

    # If registration is disabled, show a clear message to users
    if not registration_open:
        # If POST was attempted while disabled, inform the user
        if request.method == 'POST':
            flash('Registration is currently disabled by the administrator.', 'error')
        return render_template('register.html', registration_open=False)

    if request.method == 'POST':
        # Get and sanitize inputs
        nsi_id = request.form.get('nsi_id', '').lower().strip()
        name = request.form.get('name', '').strip()
        wing_name = request.form.get('wing_name', '').strip()
        internal_type = request.form.get('internal_type', '').strip()
        border_type = request.form.get('border_type', '').strip()
        external_type = request.form.get('external_type', '').strip()
        country_name = request.form.get('country_name', '').strip()
        district_name = request.form.get('district_name', '').strip()
        section_name = request.form.get('section_name', '').strip()
        password = request.form.get('password', '')
        division_name = request.form.get('division_name', '').strip()
        
        # Security checks for malicious content
        all_inputs = [nsi_id, name, wing_name, internal_type, border_type, 
                     external_type, country_name, district_name, section_name, division_name]
        
        for input_value in all_inputs:
            if InputValidator.detect_sql_injection(input_value):
                flash('Potential security threat detected. Request blocked.', 'error')
                return render_template('register.html')
            
            if InputValidator.detect_xss(input_value):
                flash('Potential security threat detected. Request blocked.', 'error')
                return render_template('register.html')
        
        # Validate NSI ID
        valid, result = InputValidator.validate_nsi_id(nsi_id)
        if not valid:
            flash(result, 'error')
            return render_template('register.html')
        nsi_id = result
        
        # Validate name
        valid, result = InputValidator.validate_name(name)
        if not valid:
            flash(result, 'error')
            return render_template('register.html')
        name = InputValidator.sanitize_string(result, max_length=100)
        
        # Validate password
        valid, result = InputValidator.validate_password(password, min_length=6)
        if not valid:
            flash(result, 'error')
            return render_template('register.html')
        
        # Validate wing selection
        allowed_wings = [
            'Technical Intelligence Wing', 'Admin Wing', 'External Affairs & Liasons Wing',
            'Political Wing', 'Research Wing', 'Special Affairs Wing', 'DG Secretariat',
            'DG Coordination', 'Economic Security Wing', 'Internal Wing', 'Border Wing',
            'Counter Terrorism Wing', 'Dhaka Wing', 'Media Wing', 'Training Institute Wing', 'CTcell'
        ]
        valid, result = InputValidator.validate_choice(wing_name, allowed_wings)
        if not valid:
            flash(result, 'error')
            return render_template('register.html')
        wing_name = result
        
        # Sanitize other inputs
        internal_type = InputValidator.sanitize_string(internal_type, max_length=50)
        border_type = InputValidator.sanitize_string(border_type, max_length=50)
        external_type = InputValidator.sanitize_string(external_type, max_length=50)
        country_name = InputValidator.sanitize_string(country_name, max_length=50)
        district_name = InputValidator.sanitize_string(district_name, max_length=50)
        section_name = InputValidator.sanitize_string(section_name, max_length=50)
        division_name = InputValidator.sanitize_string(division_name, max_length=50)
        
        # Basic validation
        if not nsi_id or not name or not password or not wing_name:
            flash('All required fields must be filled', 'error')
            return render_template('register.html')
        
        # Additional validation for Internal Wing
        if wing_name == 'Internal Wing':
            if not internal_type:
                flash('Internal Wing Type is required for Internal Wing', 'error')
                return render_template('register.html')
            
            if internal_type == 'Others':
                if not division_name or not district_name:
                    flash('Division and District are required for Internal Wing - Others', 'error')
                    return render_template('register.html')
        
        # Additional validation for Border Wing
        if wing_name == 'Border Wing':
            if not border_type:
                flash('Border Wing Type is required for Border Wing', 'error')
                return render_template('register.html')
            
            if border_type == 'Others':
                if not division_name or not district_name:
                    flash('Division and District are required for Border Wing - Others', 'error')
                    return render_template('register.html')
        
        # Additional validation for External Affairs & Liaisons Wing
        if wing_name == 'External Affairs & Liasons Wing':
            if not external_type:
                flash('Office Location is required for External Affairs & Liaisons Wing', 'error')
                return render_template('register.html')
            
            if external_type == 'Outside BD':
                if not country_name:
                    flash('Country is required for External Affairs Wing - Outside BD', 'error')
                    return render_template('register.html')
        
        # Validate NSI ID format
        import re
        if not re.match(r'^[a-d]-[0-9]{4}$', nsi_id):
            flash('NSI ID must be in format: a-1234 (letter a-d, dash, 4 digits)', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        conn = get_db_connection()
        existing_user = conn.execute('SELECT id FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
        
        if existing_user:
            flash('This NSI ID is already registered', 'error')
            conn.close()
            return render_template('register.html')
        
        # Create user
        password_hash = hash_password(password)
        try:
            # Handle field clearing based on wing type
            if wing_name == 'Internal Wing':
                border_type = None
                external_type = None
                country_name = None
                if internal_type == 'HQ':
                    # For Internal HQ users, clear division and district
                    division_name = None
                    district_name = None
            elif wing_name == 'Border Wing':
                internal_type = None
                external_type = None
                country_name = None
                if border_type == 'HQ':
                    # For Border HQ users, clear division and district
                    division_name = None
                    district_name = None
            elif wing_name == 'External Affairs & Liasons Wing':
                internal_type = None
                border_type = None
                division_name = None
                district_name = None
                if external_type == 'Inside BD':
                    # For Inside BD users, clear country
                    country_name = None
                elif external_type == 'Outside BD':
                    # For Outside BD users, clear section
                    section_name = None
            else:
                # For other wings, clear all wing-specific fields
                internal_type = None
                border_type = None
                external_type = None
                country_name = None
                division_name = None
                district_name = None
            
            conn.execute('''INSERT INTO users (nsi_id, name, wing_name, internal_type, border_type, external_type, country_name, division_name, district_name, section_name, password_hash) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (nsi_id, name, wing_name, internal_type, border_type, external_type, country_name, division_name, district_name, section_name, password_hash))
            conn.commit()
            flash('Registration successful! You can now login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed. Please try again.', 'error')
            return render_template('register.html')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@csrf.exempt  # Exempt CSRF for user login
def login():
    """User login with input validation"""
    if request.method == 'POST':
        nsi_id = request.form.get('nsi_id', '').lower().strip()
        password = request.form.get('password', '')
        
        # Security checks for malicious content
        if InputValidator.detect_sql_injection(nsi_id) or InputValidator.detect_sql_injection(password):
            flash('Potential security threat detected. Request blocked.', 'error')
            return render_template('login.html')
        
        if InputValidator.detect_xss(nsi_id) or InputValidator.detect_xss(password):
            flash('Potential security threat detected. Request blocked.', 'error')
            return render_template('login.html')
        
        # Validate NSI ID format
        valid, result = InputValidator.validate_nsi_id(nsi_id)
        if not valid:
            flash('Invalid NSI ID format', 'error')
            return render_template('login.html')
        nsi_id = result
        
        if not password:
            flash('Password is required', 'error')
            return render_template('login.html')
        
        # Sanitize password (but don't validate strength for login)
        password = InputValidator.sanitize_string(password, max_length=200)
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
        conn.close()
        
        if user and verify_password(password, user['password_hash']):
            # Regenerate session to prevent session fixation
            session.clear()
            session['user_logged_in'] = True
            session['user_id'] = user['id']
            session['user_name'] = InputValidator.sanitize_string(user['name'])
            session['nsi_id'] = user['nsi_id']
            flash(f'Welcome, {InputValidator.sanitize_string(user["name"])}!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid NSI ID or password', 'error')
    
    return render_template('login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
@csrf.exempt  # Exempt CSRF for admin login
def admin_login():
    """Admin login with input validation"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Security checks for malicious content
        if InputValidator.detect_sql_injection(username) or InputValidator.detect_sql_injection(password):
            flash('Potential security threat detected. Request blocked.', 'error')
            return render_template('admin_login.html')
        
        if InputValidator.detect_xss(username) or InputValidator.detect_xss(password):
            flash('Potential security threat detected. Request blocked.', 'error')
            return render_template('admin_login.html')
        
        # Validate username
        valid, result = InputValidator.validate_username(username)
        if not valid:
            flash('Invalid username format', 'error')
            return render_template('admin_login.html')
        username = result
        
        if not password:
            flash('Password is required', 'error')
            return render_template('admin_login.html')
        
        # Sanitize password
        password = InputValidator.sanitize_string(password, max_length=200)
        
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if admin and verify_password(password, admin['password_hash']):
            # Regenerate session to prevent session fixation
            session.clear()
            session['admin_logged_in'] = True
            session['admin_id'] = admin['id']
            session['admin_username'] = InputValidator.sanitize_string(admin['username'])
            
            # Check if password change is required
            if admin['password_change_required'] == 1:
                session['password_change_required'] = True
                flash('You must change your password before continuing', 'warning')
                return redirect(url_for('admin_change_password'))
            
            flash(f'Welcome, Admin {admin["username"]}!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/change-password', methods=['GET', 'POST'])
@csrf.exempt  # Exempt CSRF for admin password change
def admin_change_password():
    """Force admin password change"""
    if not session.get('admin_logged_in') or not session.get('password_change_required'):
        flash('Access denied', 'error')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('admin_change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('admin_change_password.html')
        
        if len(new_password) < 8:
            flash('New password must be at least 8 characters long', 'error')
            return render_template('admin_change_password.html')
        
        if new_password == 'admin123':
            flash('Cannot use default password. Please choose a different password.', 'error')
            return render_template('admin_change_password.html')
        
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admins WHERE id = ?', (session['admin_id'],)).fetchone()
        
        if admin and verify_password(current_password, admin['password_hash']):
            new_hash = hash_password(new_password)
            conn.execute('UPDATE admins SET password_hash = ?, password_change_required = 0 WHERE id = ?', 
                        (new_hash, session['admin_id']))
            conn.commit()
            conn.close()
            
            # Clear password change requirement from session
            session.pop('password_change_required', None)
            flash('Password changed successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Current password is incorrect', 'error')
            conn.close()
    
    return render_template('admin_change_password.html')

@app.route('/logout')
def logout():
    """Logout (both user and admin)"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))


@app.route('/student/dashboard')
def student_dashboard():
    """Student dashboard"""
    user_logged_in = is_user_logged_in()
    
    if not user_logged_in:
        flash('Please login to access student dashboard', 'error')
        return redirect(url_for('login'))
    
    user = get_current_user()
    
    if not user:
        return redirect(url_for('logout'))
    
    conn = get_db_connection()
    
    # Get active exam
    active_exam = conn.execute('SELECT * FROM exams WHERE is_active = 1').fetchone()

    # Get next scheduled exam
    now = datetime.now()
    next_exam = conn.execute('SELECT * FROM exams WHERE scheduled_start IS NOT NULL AND scheduled_start > ? ORDER BY scheduled_start ASC LIMIT 1', (now,)).fetchone()

    # Get user's exam history with calculated percentages
    exam_history_raw = conn.execute('''
        SELECT es.*, e.title, e.passing_score, e.num_questions, e.duration_minutes as exam_duration, es.duration_minutes
        FROM exam_sessions es
        JOIN exams e ON es.exam_id = e.id
        WHERE es.user_id = ? AND es.is_completed = 1
        ORDER BY es.end_time DESC
    ''', (user['id'],)).fetchall()
    
    # Convert to list of dicts and calculate percentage scores
    exam_history = []
    for exam in exam_history_raw:
        exam_dict = dict(exam)
        # Calculate percentage: (correct_count / total_questions) * 100
        correct_count = exam_dict['score'] if exam_dict['score'] else 0
        total_questions = exam_dict['num_questions'] if exam_dict['num_questions'] else 1
        percentage = round((correct_count / total_questions) * 100, 2) if total_questions > 0 else 0
        exam_dict['score'] = percentage  # Replace raw score with percentage
        exam_dict['correct_count'] = correct_count  # Keep raw count for reference
        exam_history.append(exam_dict)

    # Check if user has ongoing session
    ongoing_session = None
    if active_exam:
        ongoing_session = conn.execute('''
            SELECT * FROM exam_sessions 
            WHERE user_id = ? AND exam_id = ? AND is_completed = 0
        ''', (user['id'], active_exam['id'])).fetchone()

    # Get global controls
    controls = conn.execute('SELECT * FROM exam_controls WHERE id = 1').fetchone()
    show_result_history = bool(controls['show_result_history']) if controls and 'show_result_history' in controls.keys() else True
    show_rankings = bool(controls['show_rankings']) if controls and 'show_rankings' in controls.keys() else True
    
    # More conservative approach for answer review - default to False if column doesn't exist
    allow_answer_review = False
    if controls and 'allow_answer_review' in controls.keys():
        allow_answer_review = bool(controls['allow_answer_review'])
    else:
        # If column doesn't exist, check if it exists in the table structure
        try:
            test_query = conn.execute('SELECT allow_answer_review FROM exam_controls WHERE id = 1').fetchone()
            allow_answer_review = bool(test_query['allow_answer_review']) if test_query else False
        except:
            # Column doesn't exist, default to False for security
            allow_answer_review = False
    
    # Calculate user rankings for each completed exam
    rankings = {}
    top_performers = []
    
    if show_rankings:
        # Get exams with rankings data - for exams user has completed
        for exam in exam_history:
            exam_id = exam['exam_id']
            # Get all results for this exam with percentage scores, ordered by percentage DESC then by duration ASC
            # Note: exam_history already has percentage in 'score' field after our conversion above
            all_results_raw = conn.execute('''
                SELECT es.user_id, es.score as raw_score, e.num_questions, u.name, u.nsi_id, u.wing_name, es.end_time, es.duration_minutes
                FROM exam_sessions es
                JOIN users u ON es.user_id = u.id
                JOIN exams e ON es.exam_id = e.id
                WHERE es.exam_id = ? AND es.is_completed = 1
                ORDER BY es.score DESC, es.duration_minutes ASC, es.end_time ASC
            ''', (exam_id,)).fetchall()
            
            # Calculate percentage for each result for proper ranking
            all_results = []
            for result in all_results_raw:
                result_dict = dict(result)
                total_q = result_dict['num_questions'] if result_dict['num_questions'] else 1
                percentage = round((result_dict['raw_score'] / total_q) * 100, 2) if total_q > 0 else 0
                result_dict['score'] = percentage
                all_results.append(result_dict)
            
            # Re-sort by percentage
            all_results.sort(key=lambda x: (-x['score'], x['duration_minutes'], x['end_time']))
            
            # Find user's rank with percentage and duration-based tiebreaker
            user_rank = 1
            for idx, result in enumerate(all_results):
                if result['user_id'] == user['id']:
                    user_rank = idx + 1
                    break
            
            total_participants = len(all_results)
            # Calculate percentile: if you're rank 1 out of 12, you're better than 11 others (11/11 = 100%)
            # Formula: ((total - rank) / (total - 1)) * 100
            if total_participants > 1:
                percentile = round(((total_participants - user_rank) / (total_participants - 1)) * 100)
            elif total_participants == 1:
                percentile = 100  # Only participant gets 100th percentile
            else:
                percentile = 0
            
            rankings[exam_id] = {
                'rank': user_rank,
                'total_participants': total_participants,
                'percentile': percentile
            }
        
        # Get top 10 performers across all exams (based on average percentage scores with duration tiebreaker)
        # Calculate percentage: (score / num_questions) * 100 for each session, then average
        top_performers_raw = conn.execute('''
            SELECT u.id, u.name, u.nsi_id, u.wing_name, 
                   AVG(
                       CASE 
                           WHEN e.num_questions > 0 THEN (CAST(es.score AS FLOAT) / CAST(e.num_questions AS FLOAT)) * 100
                           ELSE 0
                       END
                   ) as average_score,
                   COUNT(es.id) as exams_taken,
                   ROUND(AVG(es.duration_minutes), 2) as average_duration
            FROM exam_sessions es
            JOIN users u ON es.user_id = u.id
            JOIN exams e ON es.exam_id = e.id
            WHERE es.is_completed = 1 AND e.num_questions > 0
            GROUP BY u.id
            HAVING exams_taken > 0
            ORDER BY average_score DESC, average_duration ASC, MIN(es.end_time) ASC
            LIMIT 10
        ''').fetchall()
        
        # Round the average_score to 1 decimal place and cap at 100%
        top_performers = []
        for performer in top_performers_raw:
            performer_dict = dict(performer)
            avg_score = performer_dict['average_score'] if performer_dict['average_score'] else 0
            # Cap at 100% in case of any data anomalies
            performer_dict['average_score'] = min(round(avg_score, 1), 100.0)
            top_performers.append(performer_dict)

    conn.close()

    return render_template('student_dashboard.html', 
                         user=user, 
                         active_exam=active_exam, 
                         exam_history=exam_history,
                         ongoing_session=ongoing_session,
                         next_exam=next_exam,
                         now=now,
                         now_str=now.isoformat(),
                         show_result_history=show_result_history,
                         show_rankings=show_rankings,
                         allow_answer_review=allow_answer_review,
                         rankings=rankings,
                         top_performers=top_performers)

@app.route('/admin/exam_controls', methods=['GET', 'POST'])
@csrf.exempt  # Exempt CSRF for this route since we handle auth manually
def admin_exam_controls():
    """Admin exam controls management"""
    if not is_admin_logged_in():
        # Handle AJAX requests when not authenticated
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': 'Admin authentication required'
            }), 401
        flash('Please login as admin', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = request.get_json()
            action = data.get('action') if data else None
            
            if action == 'update_setting':
                setting = data.get('setting')
                value = data.get('value')
                
                if setting in ['registration_enabled', 'maintenance_mode', 'exams_enabled']:
                    # Boolean settings
                    value_to_store = 1 if value else 0
                    conn.execute(
                        f'UPDATE system_settings SET {setting} = ?, updated_at = ? WHERE id = 1', 
                        (value_to_store, datetime.now())
                    )
                elif setting in ['exam_window_start', 'exam_window_end']:
                    # Date/time settings
                    conn.execute(
                        f'UPDATE system_settings SET {setting} = ?, updated_at = ? WHERE id = 1', 
                        (value, datetime.now())
                    )
                else:
                    return jsonify({
                        'success': False,
                        'message': f"Unknown setting: {setting}"
                    })
                
                conn.commit()
                return jsonify({
                    'success': True,
                    'message': f"{setting.replace('_', ' ').title()} updated successfully"
                })
            
            elif action == 'get_stats':
                # Get system statistics
                stats = {}
                
                # Total users
                stats['total_users'] = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
                
                # Total exams
                stats['total_exams'] = conn.execute('SELECT COUNT(*) as count FROM exams').fetchone()['count']
                
                # Total questions
                stats['total_questions'] = conn.execute('SELECT COUNT(*) as count FROM questions').fetchone()['count']
                
                # Total attempts
                stats['total_attempts'] = conn.execute('SELECT COUNT(*) as count FROM exam_sessions').fetchone()['count']
                
                # Pass rate
                pass_rate_result = conn.execute('''
                    SELECT 
                        CASE 
                            WHEN COUNT(*) = 0 THEN 0
                            ELSE ROUND((SUM(CASE WHEN er.score >= e.passing_score THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 1)
                        END as pass_rate
                    FROM exam_sessions er
                    JOIN exams e ON er.exam_id = e.id
                ''').fetchone()
                stats['pass_rate'] = pass_rate_result['pass_rate']
                
                # Average score
                avg_score_result = conn.execute('''
                    SELECT 
                        CASE 
                            WHEN COUNT(*) = 0 THEN 0
                            ELSE ROUND(AVG(score), 1)
                        END as avg_score
                    FROM exam_sessions
                ''').fetchone()
                stats['avg_score'] = avg_score_result['avg_score']
                
                # Add timestamp
                stats['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                return jsonify({
                    'success': True,
                    'stats': stats
                })
                
            elif action == 'toggle_registration':
                enabled = data.get('enabled', True)
                status = 1 if enabled else 0
                conn.execute(
                    'UPDATE system_settings SET registration_enabled = ?, updated_at = ? WHERE id = 1', 
                    (status, datetime.now())
                )
                conn.commit()
                return jsonify({
                    'success': True,
                    'message': f"Registration {'enabled' if enabled else 'disabled'} successfully"
                })
                
            elif action == 'backup':
                # Create backup directory if it doesn't exist
                import shutil
                import os
                
                backup_dir = 'backups'
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                backup_name = f"backup_{timestamp}.db"
                backup_path = os.path.join(backup_dir, backup_name)
                
                # Create a copy of the database file
                try:
                    shutil.copy2('exam_system.db', backup_path)
                    
                    # Update last backup time in system_settings
                    conn.execute(
                        'UPDATE system_settings SET last_backup_time = ?, updated_at = ? WHERE id = 1',
                        (datetime.now(), datetime.now())
                    )
                    conn.commit()
                    
                    return jsonify({
                        'success': True,
                        'download_link': url_for('download_backup', filename=backup_name),
                        'message': f"Database backup created successfully"
                    })
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'message': f"Backup failed: {str(e)}"
                    })
                
            elif action == 'reset_results':
                # Delete all exam results
                conn.execute("DELETE FROM exam_sessions")
                conn.execute("UPDATE system_settings SET updated_at = ? WHERE id = 1", (datetime.now(),))
                conn.commit()
                return jsonify({
                    'success': True,
                    'message': "All exam results have been reset successfully"
                })
                
            elif action == 'truncate':
                # Delete users (except admin) and all exam results
                conn.execute("DELETE FROM users WHERE nsi_id != 'admin'")
                conn.execute("DELETE FROM exam_sessions")
                conn.execute("UPDATE system_settings SET updated_at = ? WHERE id = 1", (datetime.now(),))
                conn.commit()
                return jsonify({
                    'success': True,
                    'message': "Database truncated successfully. All users and exam results have been removed."
                })
                
            elif action == 'reset_all_attempts':
                # Delete all exam sessions
                conn.execute("DELETE FROM exam_sessions")
                conn.commit()
                return jsonify({
                    'success': True,
                    'message': "All exam attempts have been reset"
                })
                
            elif action == 'optimize_database':
                # Optimize SQLite database with VACUUM
                conn.execute("VACUUM")
                conn.commit()
                return jsonify({
                    'success': True,
                    'message': "Database optimized successfully"
                })
                
            elif action == 'clear_cache':
                # Clear any temporary files or cache (for now, just return success)
                import os
                import glob
                
                # Remove any .pyc files
                for pyc_file in glob.glob('**/*.pyc', recursive=True):
                    try:
                        os.remove(pyc_file)
                    except:
                        pass
                
                # Remove __pycache__ directories
                for cache_dir in glob.glob('**/__pycache__', recursive=True):
                    try:
                        import shutil
                        shutil.rmtree(cache_dir)
                    except:
                        pass
                
                return jsonify({
                    'success': True,
                    'message': "Cache cleared successfully"
                })
                
            elif action == 'get_system_stats':
                # Get various stats from the database
                stats = {
                    'total_users': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
                    'total_questions': conn.execute('SELECT COUNT(*) FROM questions').fetchone()[0],
                    'total_exams': conn.execute('SELECT COUNT(*) FROM exams').fetchone()[0],
                    'active_exams': conn.execute('SELECT COUNT(*) FROM exams WHERE is_active = 1').fetchone()[0],
                    'completed_sessions': conn.execute('SELECT COUNT(*) FROM exam_sessions WHERE is_completed = 1').fetchone()[0],
                }
                
                # Get the last backup time
                last_backup = conn.execute('SELECT last_backup_time FROM system_settings WHERE id = 1').fetchone()
                stats['last_backup'] = last_backup[0] if last_backup and last_backup[0] else 'Never'
                
                # Get database size (approximate)
                import os
                try:
                    stats['db_size'] = f"{os.path.getsize('exam_system.db') / (1024 * 1024):.2f} MB"
                except:
                    stats['db_size'] = 'Unknown'
                    
                return jsonify({
                    'success': True,
                    'stats': stats
                })
                
            elif action == 'update_security_setting':
                setting = data.get('setting')
                enabled = data.get('enabled', False)
                
                if setting in ['enable_copy_protection', 'enable_screenshot_block', 'enable_tab_switch_detect']:
                    value = 1 if enabled else 0
                    conn.execute(
                        f'UPDATE exam_controls SET {setting} = ?, updated_at = ? WHERE id = 1',
                        (value, datetime.now())
                    )
                    conn.commit()
                    
                    setting_name = setting.replace('enable_', '').replace('_', ' ').title()
                    return jsonify({
                        'success': True,
                        'message': f"{setting_name} {'enabled' if enabled else 'disabled'} successfully"
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f"Invalid security setting: {setting}"
                    })
            
            elif action == 'update_visibility_setting':
                # Handle result visibility toggles via AJAX
                setting = data.get('setting')
                enabled = data.get('enabled', False)
                
                if setting in ['show_result_history', 'show_result_immediately', 'show_rankings', 'allow_answer_review']:
                    value = 1 if enabled else 0
                    conn.execute(
                        f'UPDATE exam_controls SET {setting} = ?, updated_at = ? WHERE id = 1',
                        (value, datetime.now())
                    )
                    conn.commit()
                    
                    setting_name = setting.replace('_', ' ').title()
                    return jsonify({
                        'success': True,
                        'message': f"{setting_name} {'enabled' if enabled else 'disabled'} successfully"
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f"Invalid visibility setting: {setting}"
                    })
                
            else:
                return jsonify({
                    'success': False,
                    'message': "Unknown action"
                })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            })
        finally:
            conn.close()
    
    # Handle regular form submissions
    if request.method == 'POST' and request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        show_result_immediately = 1 if request.form.get('show_result_immediately') == 'on' else 0
        show_result_history = 1 if request.form.get('show_result_history') == 'on' else 0
        show_rankings = 1 if request.form.get('show_rankings') == 'on' else 0
        allow_answer_review = 1 if request.form.get('allow_answer_review') == 'on' else 0
        enable_copy_protection = 1 if request.form.get('enable_copy_protection') == 'on' else 0
        enable_screenshot_block = 1 if request.form.get('enable_screenshot_block') == 'on' else 0
        enable_tab_switch_detect = 1 if request.form.get('enable_tab_switch_detect') == 'on' else 0

        conn.execute('''
            UPDATE exam_controls 
            SET show_result_immediately = ?, show_result_history = ?, show_rankings = ?, allow_answer_review = ?, 
                enable_copy_protection = ?, enable_screenshot_block = ?, enable_tab_switch_detect = ?, 
                updated_at = ?
            WHERE id = 1
        ''', (show_result_immediately, show_result_history, show_rankings, allow_answer_review, 
              enable_copy_protection, enable_screenshot_block, enable_tab_switch_detect, datetime.now()))
        conn.commit()
        flash('Exam controls updated successfully!', 'success')
    
    controls = conn.execute('SELECT * FROM exam_controls WHERE id = 1').fetchone()
    system_settings = conn.execute('SELECT * FROM system_settings WHERE id = 1').fetchone()
    
    # Get system statistics
    stats = {}
    
    # Total users
    stats['total_users'] = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    
    # Total exams
    stats['total_exams'] = conn.execute('SELECT COUNT(*) as count FROM exams').fetchone()['count']
    
    # Total questions
    stats['total_questions'] = conn.execute('SELECT COUNT(*) as count FROM questions').fetchone()['count']
    
    # Total attempts
    stats['total_attempts'] = conn.execute('SELECT COUNT(*) as count FROM exam_sessions').fetchone()['count']
    
    # Pass rate
    pass_rate_result = conn.execute('''
        SELECT 
            CASE 
                WHEN COUNT(*) = 0 THEN 0
                ELSE ROUND((SUM(CASE WHEN er.score >= e.passing_score THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 1)
            END as pass_rate
        FROM exam_sessions er
        JOIN exams e ON er.exam_id = e.id
    ''').fetchone()
    stats['pass_rate'] = pass_rate_result['pass_rate']
    
    # Average score
    avg_score_result = conn.execute('''
        SELECT 
            CASE 
                WHEN COUNT(*) = 0 THEN 0
                ELSE ROUND(AVG(score), 1)
            END as avg_score
        FROM exam_sessions
    ''').fetchone()
    stats['avg_score'] = avg_score_result['avg_score']
    
    # Add timestamp
    stats['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Convert system_settings to dict for template
    settings = {
        'registration_enabled': bool(system_settings['registration_enabled']),
        'maintenance_mode': bool(system_settings['maintenance_mode']),
        'exams_enabled': bool(system_settings['exams_enabled']),
        'exam_window_start': system_settings['exam_window_start'],
        'exam_window_end': system_settings['exam_window_end'],
        'last_backup_time': system_settings['last_backup_time']
    }
    
    conn.close()
    
    return render_template('admin_exam_controls.html', controls=controls, settings=settings, system_settings=system_settings, stats=stats)

@app.route('/exam/<int:exam_id>/start')
def start_exam(exam_id):
    """Start exam"""
    if not is_user_logged_in():
        flash('Please login to take exam', 'error')
        return redirect(url_for('login'))
    
    user = get_current_user()
    if not user:
        return redirect(url_for('logout'))
    
    conn = get_db_connection()
    
    # Get exam details
    exam = conn.execute('SELECT * FROM exams WHERE id = ? AND is_active = 1', (exam_id,)).fetchone()
    if not exam:
        flash('Exam not found or not active', 'error')
        conn.close()
        return redirect(url_for('student_dashboard'))
    
    # Check if exam has started
    scheduled_start = exam['scheduled_start']
    if scheduled_start:
        if not isinstance(scheduled_start, str):
            scheduled_start = scheduled_start.isoformat() if isinstance(scheduled_start, datetime) else None
        
        if scheduled_start:
            scheduled_start = datetime.fromisoformat(scheduled_start)
            if datetime.now() < scheduled_start:
                flash(f'Exam cannot be started yet. It is scheduled to start at {exam["scheduled_start"]}.', 'error')
                conn.close()
                return redirect(url_for('student_dashboard'))
    
    # Check if user already has completed sessions
    completed_sessions = conn.execute('''
        SELECT COUNT(*) FROM exam_sessions 
        WHERE user_id = ? AND exam_id = ? AND is_completed = 1
    ''', (user['id'], exam_id)).fetchone()[0]
    
    if completed_sessions >= exam['max_attempts']:
        flash(f'You have already completed this exam {exam["max_attempts"]} time(s)', 'error')
        conn.close()
        return redirect(url_for('student_dashboard'))
    
    # Check for ongoing session
    ongoing_session = conn.execute('''
        SELECT * FROM exam_sessions 
        WHERE user_id = ? AND exam_id = ? AND is_completed = 0
    ''', (user['id'], exam_id)).fetchone()
    
    shuffled_questions = None
    processed_questions = []
    
    if ongoing_session and ongoing_session['questions_json']:
        try:
            processed_questions = json.loads(ongoing_session['questions_json'])
            session_id = ongoing_session['id']
        except (TypeError, json.JSONDecodeError):
            processed_questions = []
            session_id = ongoing_session['id']
    else:
        session_id = None  # Will be set below
    
    # If we don't have questions yet (new session or corrupted session), generate them
    if not processed_questions:
        shuffled_questions = []
        
        # New logic for category-based question selection
        category_config_json = exam['category_config']
        if category_config_json:
            try:
                category_config = json.loads(category_config_json)
                
                # Fetch questions based on category config
                for category, num_q in category_config.items():
                    if num_q > 0:
                        cat_questions = conn.execute('''
                            SELECT * FROM questions 
                            WHERE category = ? 
                            ORDER BY RANDOM() 
                            LIMIT ?
                        ''', (category, num_q)).fetchall()
                        shuffled_questions.extend(cat_questions)
                
                # Shuffle the combined list of questions
                random.shuffle(shuffled_questions)

            except (json.JSONDecodeError, TypeError):
                # Fallback if config is invalid
                shuffled_questions = conn.execute('''
                    SELECT * FROM questions ORDER BY RANDOM() LIMIT ?
                ''', (exam['num_questions'],)).fetchall()
        else:
            # Fallback for exams without category config
            shuffled_questions = conn.execute('''
                SELECT * FROM questions ORDER BY RANDOM() LIMIT ?
            ''', (exam['num_questions'],)).fetchall()

        processed_questions = []
        for q in shuffled_questions:
            qd = dict(q)
            
            required_fields = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']
            if not all(qd.get(field) is not None for field in required_fields):
                print(f"Skipping invalid question ID {qd.get('id')}: missing required fields")
                continue
            
            options = [
                ('A', qd.get('option_a', '')),
                ('B', qd.get('option_b', '')),
                ('C', qd.get('option_c', '')),
                ('D', qd.get('option_d', ''))
            ]
            if qd.get('option_e'):
                options.append(('E', qd.get('option_e')))
            if qd.get('option_f'):
                options.append(('F', qd.get('option_f')))
            
            correct_opt_letter = str(qd.get('correct_option', '')).upper()
            if correct_opt_letter not in ['A','B','C','D','E','F']:
                print(f"Skipping question ID {qd.get('id')}: invalid correct_option {qd.get('correct_option')}")
                continue
            
            # Find the text of the correct option before shuffling
            correct_text = None
            for opt_letter, opt_text in [('A', 'option_a'), ('B', 'option_b'), ('C', 'option_c'), ('D', 'option_d'), ('E', 'option_e'), ('F', 'option_f')]:
                if opt_letter == correct_opt_letter:
                    correct_text = qd.get(opt_text)
                    break

            if correct_text is None:
                print(f"Skipping question ID {qd.get('id')}: correct option text missing")
                continue
            
            random.shuffle(options)
            
            new_correct_option = None
            # Find the new letter of the correct option after shuffling
            for i, (original_letter, text) in enumerate(options):
                if text == correct_text:
                    new_correct_option = chr(ord('A') + i)
                    break
            
            if new_correct_option is None:
                print(f"Skipping question ID {qd.get('id')}: could not determine new correct option")
                continue

            # Re-assign options with new letters and preserve image mappings
            final_options = []
            option_images_shuffled = {}
            
            for i, (original_letter, text) in enumerate(options):
                new_letter = chr(ord('A') + i)
                final_options.append((new_letter, text))
                
                # Map the shuffled option letter to the original image
                original_image_key = f'option_{original_letter.lower()}_image'
                if qd.get(original_image_key):
                    option_images_shuffled[new_letter] = (qd.get(original_image_key, '') or '').replace('\\', '/')

            processed_questions.append({
                'id': qd.get('id'),
                'question_text': qd.get('question_text', ''),
                'options': final_options,
                'correct_option': new_correct_option,
                'difficulty': qd.get('difficulty', 'medium') or 'medium',
                'question_image': (qd.get('question_image', '') or '').replace('\\', '/'),
                'question_youtube': qd.get('question_youtube', '') or '',
                'option_images': option_images_shuffled
            })
        
        if not processed_questions:
            flash('No valid questions available for this exam. Please contact the administrator.', 'error')
            conn.close()
            return redirect(url_for('student_dashboard'))
        
        questions_json = json.dumps(processed_questions)
        
        cursor = conn.cursor()
        if session_id is None:  # New session
            cursor.execute('''
                INSERT INTO exam_sessions (user_id, exam_id, start_time, questions_json) 
                VALUES (?, ?, ?, ?)
            ''', (user['id'], exam_id, datetime.now(), questions_json))
            session_id = cursor.lastrowid
        else:  # Update existing session with new questions
            cursor.execute('''
                UPDATE exam_sessions 
                SET questions_json = ? 
                WHERE id = ?
            ''', (questions_json, session_id))
        
        conn.commit()
    
    # Get global exam controls
    controls = conn.execute('SELECT * FROM exam_controls WHERE id = 1').fetchone()
    toggles = {
        'show_result_immediately': controls['show_result_immediately'] if controls else 1,
        'enable_copy_protection': controls['enable_copy_protection'] if controls else 1,
        'enable_screenshot_block': controls['enable_screenshot_block'] if controls else 1,
        'enable_tab_switch_detect': controls['enable_tab_switch_detect'] if controls else 1
    }
    
    conn.close()
    
    return render_template('take_exam.html', 
                         exam=exam, 
                         questions=processed_questions,
                         session_id=session_id,
                         user=user,
                         toggles=toggles)

@app.route('/exam/<int:session_id>/submit', methods=['POST'])
@csrf.exempt
def submit_exam(session_id):
    """Submit exam"""
    if not is_user_logged_in():
        if request.is_json:
            return jsonify({'success': False, 'message': 'Authentication required.'}), 401
        return redirect(url_for('login'))
    
    user = get_current_user()
    if not user:
        if request.is_json:
            return jsonify({'success': False, 'message': 'User not found.'}), 401
        return redirect(url_for('logout'))
    
    conn = get_db_connection()
    
    exam_session = conn.execute('''
        SELECT es.*, e.num_questions, e.passing_score
        FROM exam_sessions es
        JOIN exams e ON es.exam_id = e.id
        WHERE es.id = ? AND es.user_id = ?
    ''', (session_id, user['id'])).fetchone()
    
    if not exam_session:
        conn.close()
        if request.is_json:
            return jsonify({'success': False, 'message': 'Exam session not found.'}), 404
        flash('Exam session not found.', 'error')
        return redirect(url_for('student_dashboard'))
    
    if exam_session['is_completed']:
        conn.close()
        if request.is_json:
            return jsonify({'success': False, 'message': 'Exam already submitted.'}), 400
        flash('You have already submitted this exam.', 'warning')
        return redirect(url_for('exam_results', session_id=session_id))

    try:
        # Debug: Print all form data for troubleshooting
        print(f"🔍 Form submission debug for session {session_id}:")
        print(f"Request method: {request.method}")
        print(f"Request content type: {request.content_type}")
        print(f"Is JSON: {request.is_json}")
        print(f"Form data keys: {list(request.form.keys())}")
        print(f"Form data: {dict(request.form)}")
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            if not data or 'answers' not in data:
                raise ValueError("Missing 'answers' in request payload")
            answers = data['answers']
            if not isinstance(answers, dict):
                raise ValueError("Invalid 'answers' format")
        else:
            # Handle form data (backward compatibility)
            answers = {}
            for key, value in request.form.items():
                if key.startswith('question_'):
                    question_id = key.split('_')[1]
                    answers[question_id] = value
            
            print(f"📝 Extracted answers: {answers}")
            
            # Allow submission even with no answers (all questions left blank)
            # This is valid - user might choose not to answer some questions
                
    except Exception as e:
        print(f"❌ Error processing form data: {e}")
        conn.close()
        if request.is_json:
            return jsonify({'success': False, 'message': f'Invalid request data: {e}'}), 400
        flash(f'Invalid request. Please try again. Error: {str(e)}', 'error')
        return redirect(url_for('student_dashboard'))

    try:
        questions = json.loads(exam_session['questions_json'])
    except (TypeError, json.JSONDecodeError):
        conn.close()
        if request.is_json:
            return jsonify({'success': False, 'message': 'Could not load exam questions.'}), 500
        flash('An error occurred while processing your submission.', 'error')
        return redirect(url_for('student_dashboard'))

    score = 0
    answers_detail = {}
    
    for question in questions:
        q_id = str(question['id'])
        user_answer = answers.get(q_id)
        correct_option = question['correct_option']
        
        is_correct = (user_answer == correct_option)
        if is_correct:
            score += 1
        
        answers_detail[q_id] = {
            'user_answer': user_answer,
            'correct_answer': correct_option,
            'is_correct': is_correct
        }

    end_time = datetime.now()
    start_time = exam_session['start_time']
    
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time)
        
    duration_minutes = round((end_time - start_time).total_seconds() / 60, 2)

    try:
        conn.execute('''
            UPDATE exam_sessions 
            SET end_time = ?, score = ?, answers = ?, answers_detail = ?, is_completed = 1, duration_minutes = ?
            WHERE id = ?
        ''', (end_time, score, json.dumps(answers), json.dumps(answers_detail), duration_minutes, session_id))
        conn.commit()
    except Exception as e:
        conn.close()
        if request.is_json:
            return jsonify({'success': False, 'message': f'Database error: {e}'}), 500
        flash('An error occurred while saving your results.', 'error')
        return redirect(url_for('student_dashboard'))
    finally:
        conn.close()

    if request.is_json:
        return jsonify({
            'success': True, 
            'message': 'Exam submitted successfully!',
            'redirect_url': url_for('exam_results', session_id=session_id)
        })
    
    flash('Exam submitted successfully!', 'success')
    return redirect(url_for('exam_results', session_id=session_id))

@app.route('/exam/result')
def exam_result():
    """Show exam result"""
    if not is_user_logged_in():
        return redirect(url_for('login'))
    
    result = session.get('exam_result')
    if not result:
        flash('No exam result found', 'error')
        return redirect(url_for('student_dashboard'))

    # Get last exam_id for user
    user = get_current_user()
    conn = get_db_connection()
    last_session = conn.execute('SELECT * FROM exam_sessions WHERE user_id = ? ORDER BY end_time DESC LIMIT 1', (user['id'],)).fetchone()
    exam = None
    if last_session:
        exam = conn.execute('SELECT * FROM exams WHERE id = ?', (last_session['exam_id'],)).fetchone()
    
    # Get global exam controls
    controls = conn.execute('SELECT * FROM exam_controls WHERE id = 1').fetchone()
    show_result = bool(controls['show_result_immediately']) if controls else True
    
    conn.close()

    if not show_result:
        flash('Results for this exam are not available immediately. Please check back later.', 'info')
        session.pop('exam_result', None)
        return redirect(url_for('student_dashboard'))

    session.pop('exam_result', None)

    return render_template('exam_results.html', result=result, toggles={
        'show_result_immediately': controls['show_result_immediately'] if controls else 1,
        'enable_copy_protection': controls['enable_copy_protection'] if controls else 1,
        'enable_screenshot_block': controls['enable_screenshot_block'] if controls else 1,
        'enable_tab_switch_detect': controls['enable_tab_switch_detect'] if controls else 1
    })

@app.route('/exam/<int:session_id>/results')
def exam_results(session_id):
    """Show exam results for a specific session"""
    if not is_user_logged_in():
        return redirect(url_for('login'))
    
    user = get_current_user()
    if not user:
        return redirect(url_for('logout'))
    
    conn = get_db_connection()
    
    # Get exam session with results
    exam_session = conn.execute('''
        SELECT es.*, e.title as exam_title, e.description as exam_description, e.passing_score
        FROM exam_sessions es
        JOIN exams e ON es.exam_id = e.id
        WHERE es.id = ? AND es.user_id = ? AND es.is_completed = 1
    ''', (session_id, user['id'])).fetchone()
    
    if not exam_session:
        conn.close()
        flash('Exam session not found or not completed.', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Get exam controls
    controls = conn.execute('SELECT * FROM exam_controls LIMIT 1').fetchone()
    
    exam = conn.execute('SELECT * FROM exams WHERE id = ?', (exam_session['exam_id'],)).fetchone()
    
    # Calculate total questions based on exam configuration
    total_q = 0
    if exam:
        total_q = exam['num_questions']
    else:
        # Fallback: count all questions for this exam
        total_q = conn.execute('SELECT COUNT(*) as count FROM questions WHERE exam_id = ?', 
                              (exam_session['exam_id'],)).fetchone()['count']
    show_result = controls['show_result_immediately'] if controls else 1
    
    conn.close()
    
    if not show_result:
        flash('Results for this exam are not available immediately. Please check back later.', 'info')
        return redirect(url_for('student_dashboard'))
    
    # Prepare result data
    correct_count = exam_session['score'] if exam_session['score'] else 0
    total_questions = total_q
    percentage = round((correct_count / total_questions) * 100, 2) if total_questions > 0 else 0
    
    result = {
        'session_id': exam_session['id'],
        'exam_title': exam_session['exam_title'],
        'exam_description': exam_session['exam_description'],
        'score': percentage,  # Fixed: Now passing percentage instead of raw score
        'correct_count': correct_count,
        'total_questions': total_questions,
        'percentage': percentage,
        'passing_score': exam_session['passing_score'],
        'status': 'Passed' if percentage >= exam_session['passing_score'] else 'Failed',
        'passed': percentage >= exam_session['passing_score'],
        'time_taken': exam_session['duration_minutes'],
        'end_time': exam_session['end_time']
    }
    
    conn.close()
    
    return render_template('exam_results.html', result=result, toggles={
        'show_result_immediately': controls['show_result_immediately'] if controls else 1,
        'enable_copy_protection': controls['enable_copy_protection'] if controls else 1,
        'enable_screenshot_block': controls['enable_screenshot_block'] if controls else 1,
        'enable_tab_switch_detect': controls['enable_tab_switch_detect'] if controls else 1
    })

@app.route('/student/exam/<int:session_id>/review')
def student_exam_review(session_id):
    """Allow students to review their exam answers and see correct answers"""
    if not is_user_logged_in():
        return redirect(url_for('login'))
    
    user = get_current_user()
    if not user:
        return redirect(url_for('logout'))
    
    conn = get_db_connection()
    
    # Check if answer review is allowed by admin
    controls = conn.execute('SELECT * FROM exam_controls WHERE id = 1').fetchone()
    allow_review = bool(controls['allow_answer_review']) if controls else True
    
    if not allow_review:
        flash('Answer review is currently disabled by the administrator.', 'error')
        conn.close()
        return redirect(url_for('student_dashboard'))
    
    # Get exam session with exam details - ONLY for current user (security)
    exam_session = conn.execute('''
        SELECT 
            es.*, 
            e.title as exam_title, 
            e.description as exam_description,
            e.passing_score
        FROM exam_sessions es
        JOIN exams e ON es.exam_id = e.id
        WHERE es.id = ? AND es.user_id = ? AND es.is_completed = 1
    ''', (session_id, user['id'])).fetchone()
    
    if not exam_session:
        flash('Exam session not found or you do not have permission to view it.', 'error')
        conn.close()
        return redirect(url_for('student_dashboard'))
    
    # Get detailed answers
    try:
        answers_detail = json.loads(exam_session['answers_detail'] or '[]')
    except (json.JSONDecodeError, TypeError):
        answers_detail = []
    
    # Get questions with correct answers from the stored questions_json
    try:
        questions_data = json.loads(exam_session['questions_json'] or '[]')
    except (json.JSONDecodeError, TypeError):
        questions_data = []
    
    # Combine answers with full question details
    detailed_review = []
    for i, answer_detail in enumerate(answers_detail):
        # Find matching question from stored questions
        question_data = None
        if i < len(questions_data):
            question_data = questions_data[i]
        
        # Handle case where answer_detail might be a string or dict
        if isinstance(answer_detail, dict):
            review_item = {
                'question_number': i + 1,
                'question_text': answer_detail.get('question', 'Question not found'),
                'user_answer': answer_detail.get('selected_answer', 'No answer selected'),
                'is_correct': answer_detail.get('is_correct', False),
                'correct_answer': '',
                'explanation': '',
                'options': []
            }
        else:
            # If answer_detail is a string, create a basic structure
            review_item = {
                'question_number': i + 1,
                'question_text': 'Question not found',
                'user_answer': str(answer_detail) if answer_detail else 'No answer selected',
                'is_correct': False,
                'correct_answer': '',
                'explanation': '',
                'options': []
            }
        
        # If we have the full question data, add more details
        if question_data:
            review_item['question_text'] = question_data.get('question_text', review_item['question_text'])
            review_item['explanation'] = question_data.get('explanation', '')
            review_item['options'] = question_data.get('options', [])
            
            # Find the correct answer text
            correct_option = question_data.get('correct_option', '')
            if correct_option and review_item['options']:
                for option in review_item['options']:
                    if option[0] == correct_option:
                        review_item['correct_answer'] = option[1]
                        break
        
        detailed_review.append(review_item)
    
    conn.close()
    
    return render_template('exam_review.html', 
                         exam_session=exam_session,
                         detailed_review=detailed_review,
                         user=user)

@app.route('/admin/dashboard')
def admin_dashboard():
    """Enhanced Admin dashboard with comprehensive statistics and top performers"""
    access_check = admin_access_check()
    if access_check == False:
        flash('Please login as admin', 'error')
        return redirect(url_for('admin_login'))
    elif access_check == 'password_change':
        flash('You must change your password before accessing admin features', 'warning')
        return redirect(url_for('admin_change_password'))
    
    conn = get_db_connection()
    
    # Enhanced statistics
    stats = {
        'total_users': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'total_questions': conn.execute('SELECT COUNT(*) FROM questions').fetchone()[0],
        'total_exams': conn.execute('SELECT COUNT(*) FROM exams').fetchone()[0],
        'active_exams': conn.execute('SELECT COUNT(*) FROM exams WHERE is_active = 1').fetchone()[0],
        'completed_sessions': conn.execute('SELECT COUNT(*) FROM exam_sessions WHERE is_completed = 1').fetchone()[0]
    }
    
    # Calculate average score
    avg_score = conn.execute('SELECT AVG(score) FROM exam_sessions WHERE is_completed = 1').fetchone()[0]
    stats['average_score'] = round(avg_score, 1) if avg_score else 0
    
    # Get recent users (last 5 registrations)
    recent_users = conn.execute('''
        SELECT * FROM users 
        ORDER BY created_at DESC 
        LIMIT 5
    ''').fetchall()
    
    # Get active exam
    active_exam = conn.execute('SELECT * FROM exams WHERE is_active = 1').fetchone()
    
    # Get available exams (inactive ones that can be activated)
    available_exams = conn.execute('SELECT * FROM exams WHERE is_active = 0 ORDER BY created_at DESC').fetchall()
    
    # Get all exams
    exams = conn.execute('SELECT * FROM exams ORDER BY created_at DESC').fetchall()
    
    # Get top 10 performers across all exams (based on average scores with time tiebreaker)
    top_performers = conn.execute('''
        SELECT u.id, u.name, u.nsi_id, u.wing_name, 
               ROUND(AVG(es.score), 1) as average_score,
               COUNT(es.id) as exams_taken,
               MIN(es.end_time) as earliest_submission
        FROM users u
        JOIN exam_sessions es ON u.id = es.user_id
        WHERE es.is_completed = 1
        GROUP BY u.id
        HAVING exams_taken > 0
        ORDER BY average_score DESC, earliest_submission ASC
        LIMIT 10
    ''').fetchall()
    
    # Get exam controls
    controls = conn.execute('SELECT * FROM exam_controls WHERE id = 1').fetchone()
    
    # Get system settings
    system_settings_row = conn.execute('SELECT * FROM system_settings WHERE id = 1').fetchone()
    
    # Create system settings dict with defaults if table doesn't exist yet
    system_settings = {
        'registration_enabled': system_settings_row['registration_enabled'] if system_settings_row else 1,
        'maintenance_mode': system_settings_row['maintenance_mode'] if system_settings_row else 0,
        'show_result_immediately': controls['show_result_immediately'] if controls else 1,
        'enable_copy_protection': controls['enable_copy_protection'] if controls else 1,
    }
    
    # Create enhanced system stats
    import os
    db_path = os.path.join(os.path.dirname(__file__), 'exam_system.db')
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    
    system_stats = {
        'db_size': f"{db_size / (1024 * 1024):.2f} MB",
        'last_backup': system_settings_row['last_backup_time'] if system_settings_row and system_settings_row['last_backup_time'] else 'Never',
        'table_count': len(conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
    }
    
    # Handle AJAX refresh requests
    if request.args.get('refresh') == 'true' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        conn.close()
        return jsonify({
            'success': True,
            'stats': stats,
            'system_stats': system_stats,
            'top_performers': [dict(p) for p in top_performers]
        })

    conn.close()

    return render_template('admin_dashboard.html', 
                         stats=stats, 
                         recent_users=recent_users,
                         active_exam=active_exam,
                         available_exams=available_exams,
                         exams=exams,
                         top_performers=top_performers,
                         system_settings=system_settings,
                         system_stats=system_stats)

@app.route('/admin/activate-exam', methods=['POST'])
@csrf.exempt  # Exempt CSRF for admin activation routes
def admin_activate_exam():
    """Activate an exam from admin dashboard"""
    access_check = admin_access_check()
    if access_check == False:
        return jsonify({'success': False, 'message': 'Admin access required'})
    elif access_check == 'password_change':
        return jsonify({'success': False, 'message': 'Password change required'})
    
    try:
        data = request.get_json()
        exam_id = data.get('exam_id')
        
        if not exam_id:
            return jsonify({'success': False, 'message': 'Exam ID required'})
        
        conn = get_db_connection()
        
        # First deactivate all other exams (only one can be active at a time)
        conn.execute('UPDATE exams SET is_active = 0')
        
        # Activate the selected exam
        result = conn.execute(
            'UPDATE exams SET is_active = 1 WHERE id = ?',
            (exam_id,)
        )
        
        if result.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Exam not found'})
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Exam activated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error activating exam: {str(e)}'})

@app.route('/admin/deactivate-exam', methods=['POST'])
@csrf.exempt  # Exempt CSRF for admin deactivation routes
def admin_deactivate_exam():
    """Deactivate an exam from admin dashboard"""
    access_check = admin_access_check()
    if access_check == False:
        return jsonify({'success': False, 'message': 'Admin access required'})
    elif access_check == 'password_change':
        return jsonify({'success': False, 'message': 'Password change required'})
    
    try:
        data = request.get_json()
        exam_id = data.get('exam_id')
        
        if not exam_id:
            return jsonify({'success': False, 'message': 'Exam ID required'})
        
        conn = get_db_connection()
        
        # Deactivate the exam
        result = conn.execute(
            'UPDATE exams SET is_active = 0 WHERE id = ?',
            (exam_id,)
        )
        
        if result.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Exam not found'})
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Exam deactivated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deactivating exam: {str(e)}'})

@app.route('/admin/questions')
def admin_questions():
    """Admin questions management"""
    if not is_admin_logged_in():
        flash('Please login as admin', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    category_filter = request.args.get('category', '').strip().lower()
    if category_filter == 'image':
        questions = conn.execute('SELECT * FROM questions WHERE difficulty = "image" ORDER BY created_at DESC').fetchall()
    elif category_filter == 'video':
        questions = conn.execute('SELECT * FROM questions WHERE difficulty = "video" ORDER BY created_at DESC').fetchall()
    elif category_filter:
        questions = conn.execute('SELECT * FROM questions WHERE difficulty = ? ORDER BY created_at DESC', (category_filter,)).fetchall()
    else:
        questions = conn.execute('SELECT * FROM questions ORDER BY created_at DESC').fetchall()

    stats = {
        'total': len(questions),
        'easy': len([q for q in questions if q['difficulty'] == 'easy']),
        'medium': len([q for q in questions if q['difficulty'] == 'medium']),
        'hard': len([q for q in questions if q['difficulty'] == 'hard']),
        'unseen': len([q for q in questions if q['difficulty'] == 'unseen']),
        'image': len([q for q in questions if q['difficulty'] == 'image']),
        'video': len([q for q in questions if q['difficulty'] == 'video'])
    }

    conn.close()

    return render_template('admin_questions.html', questions=questions, stats=stats)

@app.route('/admin/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    """Get question details for editing (AJAX)"""
    if not is_admin_logged_in():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    try:
        question = conn.execute('SELECT * FROM questions WHERE id = ?', (question_id,)).fetchone()
        if not question:
            return jsonify({'success': False, 'error': 'Question not found'}), 404
        
        question_data = {
            'id': question['id'],
            'question_text': question['question_text'],
            'option_a': question['option_a'],
            'option_b': question['option_b'],
            'option_c': question['option_c'],
            'option_d': question['option_d'],
            'option_e': question['option_e'] or '',
            'option_f': question['option_f'] or '',
            'correct_option': question['correct_option'],
            'difficulty': question['difficulty'],
            'subject': question['subject'],
            'question_image': question['question_image'] or '',
            'question_youtube': question['question_youtube'] or '',
            'option_a_image': question['option_a_image'] or '',
            'option_b_image': question['option_b_image'] or '',
            'option_c_image': question['option_c_image'] or '',
            'option_d_image': question['option_d_image'] or '',
            'option_e_image': question['option_e_image'] or '',
            'option_f_image': question['option_f_image'] or ''
        }
        return jsonify({'success': True, 'question': question_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/questions/<int:question_id>/edit', methods=['POST'])
@csrf.exempt  # Exempt CSRF for question editing
def edit_question(question_id):
    """Edit an existing question (admin only)"""
    if not is_admin_logged_in():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    question_text = request.form.get('question_text', '').strip()
    option_a = request.form.get('option_1', '').strip()
    option_b = request.form.get('option_2', '').strip()
    option_c = request.form.get('option_3', '').strip()
    option_d = request.form.get('option_4', '').strip()
    option_e = request.form.get('option_5', '').strip()
    option_f = request.form.get('option_6', '').strip()
    correct_option_num = request.form.get('correct_option', '').strip()
    difficulty = request.form.get('difficulty_level', 'medium')
    subject = request.form.get('subject', 'general').strip()
    question_youtube = request.form.get('question_youtube', '').strip()
    
    option_map = {'1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E', '6': 'F'}
    correct_option = option_map.get(correct_option_num, '')
    
    if not all([question_text, option_a, option_b, option_c, option_d, correct_option]):
        return jsonify({'success': False, 'error': 'Please fill all required fields'}), 400
    
    if correct_option not in ['A', 'B', 'C', 'D', 'E', 'F']:
        return jsonify({'success': False, 'error': 'Please select a valid correct option'}), 400
    
    options = {'A': option_a, 'B': option_b, 'C': option_c, 'D': option_d, 'E': option_e, 'F': option_f}
    if not options[correct_option]:
        return jsonify({'success': False, 'error': f'Option {correct_option} cannot be empty if it\'s the correct answer'}), 400
    
    question_image = None
    if 'question_image' in request.files:
        file = request.files['question_image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # Normalize path separators for URL
            question_image = f"/{file_path}".replace('\\', '/')
    
    # Handle option images upload: loop over letter-based fields
    option_images = {}
    for opt in ['a', 'b', 'c', 'd', 'e', 'f']:
        field = f'option_{opt}_image'
        if field in request.files:
            file = request.files[field]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                # Store using uppercase letter key for frontend
                option_images[opt.upper()] = f"/{file_path}".replace('\\', '/')
    
    if question_image or any(option_images.values()):
        difficulty = 'image'
    elif question_youtube:
        difficulty = 'video'
    
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE questions 
            SET question_text = ?, option_a = ?, option_b = ?, option_c = ?, option_d = ?, 
                option_e = ?, option_f = ?, correct_option = ?, difficulty = ?, subject = ?,
                question_image = ?, question_youtube = ?,
                option_a_image = ?, option_b_image = ?, option_c_image = ?, 
                option_d_image = ?, option_e_image = ?, option_f_image = ?
            WHERE id = ?
        ''', (question_text, option_a, option_b, option_c, option_d, option_e, option_f, 
              correct_option, difficulty, subject, question_image, question_youtube,
              option_images.get('1'), option_images.get('2'), option_images.get('3'),
              option_images.get('4'), option_images.get('5'), option_images.get('6'), 
              question_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/questions/<int:question_id>/delete', methods=['POST'])
@csrf.exempt  # Exempt CSRF for question deletion
def delete_question(question_id):
    """Delete a question (admin only, AJAX)"""
    print(f"Delete request received for question ID: {question_id}")
    if not is_admin_logged_in():
        print("Unauthorized access attempt")
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    try:
        print(f"Executing DELETE for question ID: {question_id}")
        conn.execute('DELETE FROM questions WHERE id = ?', (question_id,))
        conn.commit()
        print(f"Question {question_id} deleted successfully")
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error deleting question {question_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/questions/add', methods=['GET', 'POST'])
@csrf.exempt  # Exempt CSRF for question creation
def add_question():
    """Add new question with input validation"""
    if not is_admin_logged_in():
        flash('Please login as admin', 'error')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        question_text = request.form.get('question_text', '').strip()
        option_a = request.form.get('option_1', '').strip()
        option_b = request.form.get('option_2', '').strip()
        option_c = request.form.get('option_3', '').strip()
        option_d = request.form.get('option_4', '').strip()
        option_e = request.form.get('option_5', '').strip()
        option_f = request.form.get('option_6', '').strip()
        correct_option_num = request.form.get('correct_option', '').strip()
        difficulty = request.form.get('difficulty_level', 'medium')
        subject = request.form.get('subject', 'general').strip()
        question_youtube = request.form.get('question_youtube', '').strip()
        
        # Security checks for malicious content
        all_inputs = [question_text, option_a, option_b, option_c, option_d, 
                     option_e, option_f, subject, question_youtube]
        
        for input_value in all_inputs:
            if InputValidator.detect_sql_injection(input_value):
                flash('Potential security threat detected. Request blocked.', 'error')
                return render_template('add_question.html')
            
            if InputValidator.detect_xss(input_value):
                flash('Potential security threat detected. Request blocked.', 'error')
                return render_template('add_question.html')
        
        # Sanitize inputs
        question_text = InputValidator.sanitize_string(question_text, max_length=1000)
        option_a = InputValidator.sanitize_string(option_a, max_length=500)
        option_b = InputValidator.sanitize_string(option_b, max_length=500)
        option_c = InputValidator.sanitize_string(option_c, max_length=500)
        option_d = InputValidator.sanitize_string(option_d, max_length=500)
        option_e = InputValidator.sanitize_string(option_e, max_length=500)
        option_f = InputValidator.sanitize_string(option_f, max_length=500)
        subject = InputValidator.sanitize_string(subject, max_length=100)
        question_youtube = InputValidator.sanitize_string(question_youtube, max_length=200)
        
        # Validate correct option
        allowed_options = ['1', '2', '3', '4', '5', '6']
        valid, result = InputValidator.validate_choice(correct_option_num, allowed_options)
        if not valid:
            flash('Please select a valid correct option', 'error')
            return render_template('add_question.html')
        
        # Validate difficulty
        allowed_difficulty = ['easy', 'medium', 'hard']
        valid, result = InputValidator.validate_choice(difficulty, allowed_difficulty)
        if not valid:
            difficulty = 'medium'  # Default fallback
        
        option_map = {'1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E', '6': 'F'}
        correct_option = option_map.get(correct_option_num, '')
        
        if not all([question_text, option_a, option_b, option_c, option_d, correct_option]):
            flash('Please fill all required fields', 'error')
            return render_template('add_question.html')
        
        if correct_option not in ['A', 'B', 'C', 'D', 'E', 'F']:
            flash('Please select a valid correct option', 'error')
            return render_template('add_question.html')
        
        options = {'A': option_a, 'B': option_b, 'C': option_c, 'D': option_d, 'E': option_e, 'F': option_f}
        if not options[correct_option]:
            flash(f'Option {correct_option} cannot be empty if it\'s the correct answer', 'error')
            return render_template('add_question.html')
        
        question_image = None
        if 'question_image' in request.files:
            file = request.files['question_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                question_image = f"/{file_path}"
    
        option_images = {}
        for opt in ['1', '2', '3', '4', '5', '6']:
            field = f'option_{opt}_image'
            if field in request.files:
                file = request.files[field]
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    option_images[opt] = f"/{file_path}"
    
        if question_image or any(option_images.values()):
            difficulty = 'image'
        elif question_youtube:
            difficulty = 'video'
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO questions 
                (question_text, option_a, option_b, option_c, option_d, option_e, option_f, 
                 correct_option, difficulty, subject, question_image, question_youtube,
                 option_a_image, option_b_image, option_c_image, option_d_image, 
                 option_e_image, option_f_image) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (question_text, option_a, option_b, option_c, option_d, option_e, option_f, 
                  correct_option, difficulty, subject, question_image, question_youtube,
                  option_images.get('1'), option_images.get('2'), option_images.get('3'),
                  option_images.get('4'), option_images.get('5'), option_images.get('6')))
            conn.commit()
            flash('Question added successfully!', 'success')
            return redirect(url_for('admin_questions'))
        except Exception as e:
            flash(f'Failed to add question: {str(e)}', 'error')
            return render_template('add_question.html')
        finally:
            conn.close()
    
    return render_template('add_question.html')

@app.route('/admin/exams')
def admin_exams():
    """Admin exams management"""
    if not is_admin_logged_in():
        flash('Please login as admin', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    exams = conn.execute('SELECT * FROM exams ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('admin_exams.html', exams=exams)
@app.route('/admin/exams/add', methods=['GET', 'POST'])
@csrf.exempt  # Exempt CSRF for exam creation
def add_exam():
    """Add new exam with category-based question selection"""
    if not is_admin_logged_in():
        flash('Please login as admin', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    category_counts = {}
    for category in ['easy', 'medium', 'hard', 'image', 'video']:
        count = conn.execute('SELECT COUNT(*) FROM questions WHERE category = ?', (category,)).fetchone()[0]
        category_counts[category] = count
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        duration_minutes = request.form.get('duration')
        passing_score = request.form.get('passing_score')
        max_attempts = request.form.get('max_attempts')
        scheduled_start = request.form.get('scheduled_start')
        scheduled_end = request.form.get('scheduled_end')
        
        category_config = {}
        total_questions = 0
        for category in ['easy', 'medium', 'hard', 'image', 'video']:
            try:
                count = int(request.form.get(f'{category}_questions', 0))
                if count > 0:
                    if count > category_counts[category]:
                        flash(f'Not enough {category} questions available. Maximum: {category_counts[category]}', 'error')
                        return render_template('add_exam.html', category_counts=category_counts)
                    category_config[category] = count
                    total_questions += count
            except (ValueError, TypeError):
                continue
        
        try:
            duration_minutes = int(duration_minutes)
            passing_score = int(passing_score)
            max_attempts = int(max_attempts)
        except (ValueError, TypeError):
            flash('Please enter valid numeric values for duration, passing score, and maximum attempts', 'error')
            return render_template('add_exam.html', category_counts=category_counts)
        
        if not title:
            flash('Please enter an exam title', 'error')
            return render_template('add_exam.html', category_counts=category_counts)
        
        if total_questions == 0:  # Fixed: Changed '=' to '=='
            flash('Please select at least one question from any category', 'error')
            return render_template('add_exam.html', category_counts=category_counts)
        
        if duration_minutes < 5 or duration_minutes > 300:
            flash('Duration must be between 5 and 300 minutes', 'error')
            return render_template('add_exam.html', category_counts=category_counts)
        
        if total_questions < 1 or total_questions > 100:
            flash('Total number of questions must be between 1 and 100', 'error')
            return render_template('add_exam.html', category_counts=category_counts)
        
        try:
            conn.execute('''
                INSERT INTO exams 
                (title, description, duration_minutes, num_questions, passing_score, max_attempts, category_config,
                 scheduled_start, scheduled_end)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title,
                description,
                duration_minutes,
                total_questions,
                passing_score,
                max_attempts,
                json.dumps(category_config),
                scheduled_start,
                scheduled_end
            ))
            conn.commit()
            flash('Exam created successfully!', 'success')
            return redirect(url_for('admin_exams'))
        except Exception as e:
            print(f"Error creating exam: {e}")
            flash('Failed to create exam. Please try again.', 'error')
        finally:
            conn.close()
    
    return render_template('add_exam.html', category_counts=category_counts)

# @app.route('/admin/exams/<int:exam_id>/activate')
# def activate_exam(exam_id):
#     """Activate exam"""
#     if not is_admin_logged_in():
#         flash('Please login as admin', 'error')
#         return redirect(url_for('admin_login'))
        
#     conn = get_db_connection()
#     try:
#         conn.execute('UPDATE exams SET is_active = 1 WHERE id = ?', (exam_id,))
#         conn.commit()
        
#         exam = conn.execute('SELECT title FROM exams WHERE id = ?', (exam_id,)).fetchone()
        
#         if exam:
#             flash(f'Exam "{exam["title"]}" has been activated!', 'success')
#         else:
#             flash('Exam not found', 'error')
#     except Exception as e:
#         flash('Failed to activate exam. Please try again.', 'error')
#         conn.rollback()
#     finally:
#         conn.close()
    
#     return redirect(url_for('admin_exams'))

@app.route('/admin/exams/<int:exam_id>/deactivate')
def deactivate_exam(exam_id):
    """Deactivate exam"""
    if not is_admin_logged_in():
        flash('Please login as admin', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    conn.execute('UPDATE exams SET is_active = 0 WHERE id = ?', (exam_id,))
    conn.commit()
    
    exam = conn.execute('SELECT title FROM exams WHERE id = ?', (exam_id,)).fetchone()
    conn.close()
    
    if exam:
        flash(f'Exam "{exam["title"]}" has been deactivated!', 'success')
    
    return redirect(url_for('admin_exams'))

@app.route('/admin/results')
def admin_results():
    """Admin results management with AJAX support for statistics refresh"""
    if not is_admin_logged_in():
        flash('Please login as admin', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    exam_filter = request.args.get('exam', '').strip()
    wing_filter = request.args.get('wing', '').strip()
    division_filter = request.args.get('division', '').strip()
    district_filter = request.args.get('district', '').strip()
    section_filter = request.args.get('section', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    query = '''
        SELECT 
            es.id, es.score, es.start_time, es.end_time, es.duration_minutes, es.answers, es.user_id,
            u.nsi_id, u.name, u.wing_name, u.division_name, u.district_name, u.section_name,
            e.title as exam_title, e.passing_score, e.num_questions
        FROM exam_sessions es
        JOIN users u ON es.user_id = u.id
        JOIN exams e ON es.exam_id = e.id
        WHERE es.is_completed = 1
    '''
    params = []
    
    if exam_filter and exam_filter.lower() != 'all':
        query += ' AND e.title = ?'
        params.append(exam_filter)
    # Wing, Division, District, Section filters are handled client-side in JavaScript
    # This allows NULL/empty values to be displayed and filtered properly
    if status_filter and status_filter.lower() != 'all':
        if status_filter == 'passed':
            query += ' AND es.score >= e.passing_score'
        elif status_filter == 'failed':
            query += ' AND es.score < e.passing_score'
    
    query += ' ORDER BY es.score DESC, es.duration_minutes ASC, es.end_time ASC'
    
    raw_results = conn.execute(query, params).fetchall()
    
    # Get user rankings with percentage score and duration-based tiebreaker  
    user_rankings = {}
    rankings_data = conn.execute('''
        SELECT 
            u.id as user_id,
            COALESCE(AVG(
                CASE 
                    WHEN es.score > 0 AND e.num_questions > 0 
                    THEN (CAST(es.score AS FLOAT) / CAST(e.num_questions AS FLOAT)) * 100
                    ELSE 0
                END
            ), 0) as avg_score,
            COUNT(CASE WHEN es.is_completed = 1 THEN 1 END) as completed_exams,
            COALESCE(AVG(CASE WHEN es.duration_minutes > 0 THEN es.duration_minutes END), 0) as avg_duration,
            MIN(es.end_time) as earliest_submission,
            ROW_NUMBER() OVER (
                ORDER BY 
                    AVG(
                        CASE 
                            WHEN es.score > 0 AND e.num_questions > 0 
                            THEN (CAST(es.score AS FLOAT) / CAST(e.num_questions AS FLOAT)) * 100
                            ELSE 0
                        END
                    ) DESC, 
                    AVG(CASE WHEN es.duration_minutes > 0 THEN es.duration_minutes END) ASC,
                    MIN(es.end_time) ASC,
                    COUNT(CASE WHEN es.is_completed = 1 THEN 1 END) DESC
            ) as user_rank
        FROM users u
        LEFT JOIN exam_sessions es ON u.id = es.user_id AND es.is_completed = 1
        LEFT JOIN exams e ON es.exam_id = e.id
        GROUP BY u.id
        HAVING completed_exams > 0
    ''').fetchall()
    
    for ranking in rankings_data:
        user_rankings[ranking['user_id']] = {
            'rank': ranking['user_rank'],
            'avg_score': ranking['avg_score'],
            'avg_duration': ranking['avg_duration'],
            'completed_exams': ranking['completed_exams']
        }
    
    # Add ranking information to each result and convert scores to percentages
    results = []
    for result in raw_results:
        result_dict = dict(result)
        
        # Calculate percentage for this individual exam
        raw_score = result_dict['score'] if result_dict['score'] else 0
        num_questions = result_dict['num_questions'] if result_dict['num_questions'] else 1
        percentage = round((raw_score / num_questions) * 100, 1) if num_questions > 0 else 0
        result_dict['score'] = percentage  # Replace raw score with percentage
        result_dict['raw_score'] = raw_score  # Keep raw score for reference
        
        user_id = result['user_id']
        if user_id in user_rankings:
            result_dict['user_rank'] = user_rankings[user_id]['rank']
            result_dict['user_avg_score'] = round(user_rankings[user_id]['avg_score'], 1)
            result_dict['user_avg_duration'] = user_rankings[user_id]['avg_duration']
            result_dict['user_completed_exams'] = user_rankings[user_id]['completed_exams']
        else:
            result_dict['user_rank'] = None
            result_dict['user_avg_score'] = None
            result_dict['user_avg_duration'] = None
            result_dict['user_completed_exams'] = 0
        results.append(result_dict)
    
    filtered_results = results
    search_filter = request.args.get('search', '').lower()
    if search_filter:
        filtered_results = [r for r in filtered_results 
                          if search_filter in r['name'].lower() 
                          or search_filter in r['nsi_id'].lower()]
    
    total_submissions = len(filtered_results)
    if total_submissions > 0:
        passed = sum(1 for r in filtered_results if r['score'] >= r['passing_score'])
        failed = total_submissions - passed
        avg_score = sum(r['score'] for r in filtered_results) / total_submissions
    else:
        passed = failed = 0
        avg_score = 0
    
    stats = {
        'total': total_submissions,
        'passed': passed,
        'failed': failed,
        'average': round(avg_score, 1)
    }
    
    # Get exams dynamically from database
    exams = [dict(row) for row in conn.execute('SELECT DISTINCT title FROM exams ORDER BY title').fetchall()]
    
    # Static wings list from registration form
    wings = [
        {'wing_name': 'Technical Intelligence Wing'},
        {'wing_name': 'Admin Wing'},
        {'wing_name': 'External Affairs & Liasons Wing'},
        {'wing_name': 'Political Wing'},
        {'wing_name': 'Research Wing'},
        {'wing_name': 'Special Affairs Wing'},
        {'wing_name': 'DG Secretariat'},
        {'wing_name': 'DG Coordination'},
        {'wing_name': 'Economic Security Wing'},
        {'wing_name': 'Internal Wing'},
        {'wing_name': 'Border Wing'},
        {'wing_name': 'Counter Terrorism Wing'},
        {'wing_name': 'Dhaka Wing'},
        {'wing_name': 'Media Wing'},
        {'wing_name': 'Training Institute Wing'},
        {'wing_name': 'CTcell'}
    ]
    
    # Static districts list from registration form (all districts from all divisions)
    districts = [
        {'district_name': 'Rajshahi'}, {'district_name': 'Naogaon'}, {'district_name': 'Natore'}, 
        {'district_name': 'Chapai Nawabganj'}, {'district_name': 'Pabna'}, {'district_name': 'Bogura'}, 
        {'district_name': 'Sirajganj'}, {'district_name': 'Joypurhat'},
        {'district_name': 'Dhaka'}, {'district_name': 'Tangail'}, {'district_name': 'Narsingdi'}, 
        {'district_name': 'Gazipur'}, {'district_name': 'Munshiganj'}, {'district_name': 'Narayanganj'}, 
        {'district_name': 'Manikganj'}, {'district_name': 'Kishoreganj'},
        {'district_name': 'Chattogram'}, {'district_name': 'Cumilla'}, {'district_name': 'Brahmanbaria'}, 
        {'district_name': 'Chandpur'}, {'district_name': 'Noakhali'}, {'district_name': 'Feni'}, 
        {'district_name': 'Lakshmipur'},
        {'district_name': 'Khulna'}, {'district_name': 'Bagerhat'}, {'district_name': 'Satkhira'}, 
        {'district_name': 'Jashore (Jessore)'}, {'district_name': 'Narail'}, {'district_name': 'Jhenaidah'}, 
        {'district_name': 'Magura'}, {'district_name': 'Kushtia'}, {'district_name': 'Chuadanga'}, 
        {'district_name': 'Meherpur'},
        {'district_name': 'Rangpur'}, {'district_name': 'Kurigram'}, {'district_name': 'Lalmonirhat'}, 
        {'district_name': 'Nilphamari'}, {'district_name': 'Gaibandha'}, {'district_name': 'Dinajpur'}, 
        {'district_name': 'Thakurgaon'}, {'district_name': 'Panchagarh'},
        {'district_name': 'Barishal'}, {'district_name': 'Patuakhali'}, {'district_name': 'Bhola'}, 
        {'district_name': 'Pirojpur'}, {'district_name': 'Barguna'}, {'district_name': 'Jhalokathi'},
        {'district_name': 'Mymensingh'}, {'district_name': 'Jamalpur'}, {'district_name': 'Sherpur'}, 
        {'district_name': 'Netrokona'},
        {'district_name': 'Sylhet'}, {'district_name': 'Sunamganj'}, {'district_name': 'Moulvibazar'}, 
        {'district_name': 'Habiganj'},
        {'district_name': 'Faridpur'}, {'district_name': 'Rajbari'}, {'district_name': 'Shariatpur'}, 
        {'district_name': 'Gopalganj'}, {'district_name': 'Madaripur'},
        {'district_name': 'Rangamati'}, {'district_name': 'Bandarban'}, {'district_name': 'Khagrachhari'}, 
        {'district_name': "Cox's Bazar"}
    ]
    
    # Static divisions list from registration form
    divisions = [
        {'division_name': 'Rajshahi'},
        {'division_name': 'Dhaka'},
        {'division_name': 'Chattogram'},
        {'division_name': 'Khulna'},
        {'division_name': 'Rangpur'},
        {'division_name': 'Barishal'},
        {'division_name': 'Mymensingh'},
        {'division_name': 'Sylhet'},
        {'division_name': 'Faridpur'},
        {'division_name': 'Chittagong Hill Tracts (Parbatya Chattagram)'}
    ]
    
    # Dynamic sections list from database (users who have registered)
    sections = [dict(row) for row in conn.execute('''
        SELECT DISTINCT section_name 
        FROM users 
        WHERE section_name IS NOT NULL AND section_name != ''
        ORDER BY section_name
    ''').fetchall()]
    
    # Get top performers for rankings section with percentage-based ranking
    top_performers_raw = conn.execute('''
        SELECT 
            u.id,
            u.name,
            u.nsi_id,
            u.wing_name,
            AVG(
                CASE 
                    WHEN e.num_questions > 0 
                    THEN (CAST(es.score AS FLOAT) / CAST(e.num_questions AS FLOAT)) * 100
                    ELSE 0
                END
            ) as avg_score,
            COUNT(CASE WHEN es.is_completed = 1 THEN 1 END) as completed_exams,
            COALESCE(AVG(CASE WHEN es.duration_minutes > 0 THEN es.duration_minutes END), 0) as avg_duration,
            MIN(es.end_time) as earliest_submission
        FROM users u
        LEFT JOIN exam_sessions es ON u.id = es.user_id AND es.is_completed = 1
        LEFT JOIN exams e ON es.exam_id = e.id
        WHERE e.num_questions > 0
        GROUP BY u.id, u.name, u.nsi_id, u.wing_name
        HAVING completed_exams > 0
        ORDER BY avg_score DESC, avg_duration ASC, earliest_submission ASC, completed_exams DESC
        LIMIT 15
    ''').fetchall()
    
    # Round percentages and cap at 100%
    top_performers = []
    for performer in top_performers_raw:
        performer_dict = dict(performer)
        avg_score = performer_dict['avg_score'] if performer_dict['avg_score'] else 0
        performer_dict['avg_score'] = min(round(avg_score, 1), 100.0)
        top_performers.append(performer_dict)
    
    conn.close()
    
    selected_filters = {
        'exam': exam_filter or '',
        'wing': wing_filter or '',
        'division': division_filter or '',
        'district': district_filter or '',
        'section': section_filter or '',
        'status': status_filter or ''
    }
    
    return render_template('admin_results.html', 
                         results=results,
                         rankings=top_performers,
                         stats=stats,
                         exams=exams,
                         wings=wings,
                         divisions=divisions,
                         districts=districts,
                         sections=sections,
                         filters=selected_filters)

@app.route('/admin/results/stats')
def admin_results_stats():
    """Return JSON statistics for admin results based on filters"""
    if not is_admin_logged_in():
        return jsonify({'error': 'unauthorized'}), 401
    
    conn = get_db_connection()
    exam_filter = request.args.get('exam', '')
    wing_filter = request.args.get('wing', '')
    district_filter = request.args.get('district', '')
    section_filter = request.args.get('section', '')
    status_filter = request.args.get('status', '')
    search_filter = request.args.get('search', '').lower()
    
    query = '''
        SELECT 
            es.id, es.score, e.passing_score, u.name, u.nsi_id
        FROM exam_sessions es
        JOIN users u ON es.user_id = u.id
        JOIN exams e ON es.exam_id = e.id
        WHERE es.is_completed = 1
    '''
    params = []
    if exam_filter:
        query += ' AND e.title = ?'
        params.append(exam_filter)
    if wing_filter:
        query += ' AND u.wing_name = ?'
        params.append(wing_filter)
    if district_filter:
        query += ' AND u.district_name = ?'
        params.append(district_filter)
    if section_filter:
        query += ' AND u.section_name = ?'
        params.append(section_filter)
    if status_filter:
        if status_filter == 'passed':
            query += ' AND es.score >= e.passing_score'
        elif status_filter == 'failed':
            query += ' AND es.score < e.passing_score'
    
    query += ' ORDER BY es.end_time DESC'
    
    rows = conn.execute(query, params).fetchall()
    
    if search_filter:
        rows = [r for r in rows if search_filter in r['name'].lower() or search_filter in r['nsi_id'].lower()]
    
    total = len(rows)
    passed = sum(1 for r in rows if r['score'] >= r['passing_score']) if total > 0 else 0
    failed = total - passed
    average = round(sum(r['score'] for r in rows) / total, 1) if total > 0 else 0
    
    conn.close()
    return jsonify({'total': total, 'passed': passed, 'failed': failed, 'average': average})

@app.route('/admin/results/export')
def export_results():
    """Export results to CSV with all dashboard columns and detailed answers"""
    if not is_admin_logged_in():
        flash('Please login as admin', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    # Get all results with ranking calculation (same query as admin_results)
    results = conn.execute('''
        WITH RankedResults AS (
            SELECT 
                es.id, es.user_id, es.exam_id, es.score, es.start_time, es.end_time, 
                es.answers_detail, es.duration_minutes,
                u.nsi_id, u.name, u.wing_name, u.district_name, u.section_name,
                e.title as exam_title, e.passing_score,
                RANK() OVER (
                    PARTITION BY es.exam_id 
                    ORDER BY es.score DESC, es.duration_minutes ASC
                ) as user_rank
            FROM exam_sessions es
            JOIN users u ON es.user_id = u.id
            JOIN exams e ON es.exam_id = e.id
            WHERE es.is_completed = 1
        ),
        UserAvgScores AS (
            SELECT 
                user_id,
                AVG(score) as user_avg_score
            FROM exam_sessions 
            WHERE is_completed = 1 
            GROUP BY user_id
        )
        SELECT 
            rr.*,
            uas.user_avg_score
        FROM RankedResults rr
        LEFT JOIN UserAvgScores uas ON rr.user_id = uas.user_id
        ORDER BY rr.end_time DESC
    ''').fetchall()
    
    # CSV header with all dashboard columns
    csv_content = "Rank,NSI ID,Name,Exam,Score,Avg Score,Start Time,End Time,Duration,Status,Wing,District,Completed,Questions and Answers\n"
    
    for result in results:
        # Calculate status
        status = "Passed" if result['score'] >= result['passing_score'] else "Failed"
        
        # Format duration
        if result['duration_minutes']:
            duration_minutes = result['duration_minutes']
            hours = int(duration_minutes // 60)
            minutes = int(duration_minutes % 60)
            seconds = int((duration_minutes % 1) * 60)
            
            if hours > 0:
                duration_str = f"{hours}h {minutes}m"
            elif minutes > 0:
                duration_str = f"{minutes}m {seconds}s"
            else:
                duration_str = f"{duration_minutes:.1f}m"
        else:
            duration_str = "-"
        
        # Format times
        start_time_str = result['start_time'].strftime('%Y-%m-%d %H:%M:%S') if result['start_time'] else '-'
        end_time_str = result['end_time'].strftime('%Y-%m-%d %H:%M:%S') if result['end_time'] else '-'
        completed_str = result['end_time'].strftime('%Y-%m-%d %H:%M:%S') if result['end_time'] else '-'
        
        # Format average score
        avg_score_str = f"{result['user_avg_score']:.1f}%" if result['user_avg_score'] else "Pending"
        
        # Process detailed answers
        answers_detail = json.loads(result['answers_detail'] or '{}')
        questions_answers = []
        for q in answers_detail:
            questions_answers.append(f"Q: {q['question']} | A: {q['selected_answer']}")
        questions_answers_str = '; '.join(questions_answers)
        
        # Build CSV row with all columns
        csv_content += f'#{result["user_rank"] or "-"},'
        csv_content += f'"{result["nsi_id"]}",'
        csv_content += f'"{result["name"]}",'
        csv_content += f'"{result["exam_title"]}",'
        csv_content += f'{result["score"]}%,'
        csv_content += f'"{avg_score_str}",'
        csv_content += f'"{start_time_str}",'
        csv_content += f'"{end_time_str}",'
        csv_content += f'"{duration_str}",'
        csv_content += f'"{status}",'
        csv_content += f'"{result["wing_name"] or "-"}",'
        csv_content += f'"{result["district_name"] or "-"}",'
        csv_content += f'"{completed_str}",'
        csv_content += f'"{questions_answers_str}"\n'
    
    conn.close()
    
    response = make_response(csv_content)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=exam_results_complete.csv'
    
    return response

@app.route('/admin/results/<int:result_id>/details')
def get_result_details(result_id):
    """Get detailed result information including questions and answers"""
    if not is_admin_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    
    result = conn.execute('''
        SELECT 
            es.*, u.nsi_id, u.name,
            e.title as exam_title
        FROM exam_sessions es
        JOIN users u ON es.user_id = u.id
        JOIN exams e ON es.exam_id = e.id
        WHERE es.id = ? AND es.is_completed = 1
    ''', (result_id,)).fetchone()
    
    if not result:
        return jsonify({'error': 'Result not found'}), 404
    
    try:
        answers = json.loads(result['answers_detail'] or '[]')
    except (KeyError, json.JSONDecodeError):
        answers = []
    
    response_data = {
        'id': result['id'],
        'nsi_id': result['nsi_id'],
        'name': result['name'],
        'exam_title': result['exam_title'],
        'score': result['score'],
        'start_time': result['start_time'],
        'end_time': result['end_time'],
        'answers': answers
    }
    
    conn.close()
    return jsonify(response_data)


@app.route('/admin/exams/edit/<int:exam_id>', methods=['GET', 'POST'])
@csrf.exempt  # Exempt CSRF for exam editing
def edit_exam(exam_id):
    """Edit an existing exam"""
    if not is_admin_logged_in():
        return jsonify({'error': 'Unauthorized access'}), 401
    
    conn = get_db_connection()
    
    if request.method == 'GET':
        exam = conn.execute('SELECT * FROM exams WHERE id = ?', (exam_id,)).fetchone()
        if not exam:
            conn.close()
            return jsonify({'error': 'Exam not found'}), 404
        
        exam_dict = dict(exam)
        exam_dict['category_config'] = json.loads(exam_dict['category_config']) if exam_dict['category_config'] else {}
        conn.close()
        return jsonify(exam_dict)
    
    if request.method == 'POST':
        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        duration_minutes = data.get('duration_minutes')
        num_questions = data.get('num_questions')
        passing_score = data.get('passing_score')
        max_attempts = data.get('max_attempts')
        scheduled_start = data.get('scheduled_start')
        scheduled_end = data.get('scheduled_end')
        
        try:
            duration_minutes = int(duration_minutes)
            num_questions = int(num_questions)
            passing_score = int(passing_score)
            max_attempts = int(max_attempts)
        except (ValueError, TypeError):
            conn.close()
            return jsonify({'error': 'Invalid numeric values'}), 400
        
        if not title:
            conn.close()
            return jsonify({'error': 'Exam title is required'}), 400
        
        if duration_minutes < 5 or duration_minutes > 300:
            conn.close()
            return jsonify({'error': 'Duration must be between 5 and 300 minutes'}), 400
        
        if num_questions < 1 or num_questions > 100:
            conn.close()
            return jsonify({'error': 'Number of questions must be between 1 and 100'}), 400
        
        try:
            conn.execute('''
                UPDATE exams 
                SET title = ?, description = ?, duration_minutes = ?, num_questions = ?, 
                    passing_score = ?, max_attempts = ?, scheduled_start = ?, scheduled_end = ?
                WHERE id = ?
            ''', (title, description, duration_minutes, num_questions, passing_score, 
                  max_attempts, scheduled_start, scheduled_end, exam_id))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            conn.close()
            return jsonify({'error': f'Failed to update exam: {str(e)}'}), 500

@app.route('/admin/exams/activate/<int:exam_id>', methods=['POST'])
@csrf.exempt  # Exempt CSRF for admin activation routes
def activate_exam(exam_id):
    """Activate an exam with optional delay"""
    if not is_admin_logged_in():
        return jsonify({'error': 'Unauthorized access'}), 401
    
    conn = get_db_connection()
    
    exam = conn.execute('SELECT * FROM exams WHERE id = ?', (exam_id,)).fetchone()
    if not exam:
        conn.close()
        return jsonify({'error': 'Exam not found'}), 404
    
    data = request.get_json()
    delay_minutes = int(data.get('delay_minutes', 0))
    
    try:
        # Deactivate all other exams
        conn.execute('UPDATE exams SET is_active = 0 WHERE is_active = 1')
        
        # Calculate scheduled start time
        scheduled_start = None
        if delay_minutes > 0:
            scheduled_start = (datetime.now() + timedelta(minutes=delay_minutes)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Activate the selected exam
        conn.execute('UPDATE exams SET is_active = 1, scheduled_start = ? WHERE id = ?', 
                     (scheduled_start, exam_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Failed to activate exam: {str(e)}'}), 500

@app.route('/admin/exams/delete/<int:exam_id>', methods=['POST'])
@csrf.exempt  # Exempt CSRF for admin delete routes
def delete_exam(exam_id):
    """Delete an exam and its associated sessions"""
    if not is_admin_logged_in():
        return jsonify({'error': 'Unauthorized access'}), 401
    
    conn = get_db_connection()
    
    exam = conn.execute('SELECT * FROM exams WHERE id = ?', (exam_id,)).fetchone()
    if not exam:
        conn.close()
        return jsonify({'error': 'Exam not found'}), 404
    
    try:
        # Delete associated exam sessions
        conn.execute('DELETE FROM exam_sessions WHERE exam_id = ?', (exam_id,))
        # Delete the exam
        conn.execute('DELETE FROM exams WHERE id = ?', (exam_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Failed to delete exam: {str(e)}'}), 500
    


@app.route('/admin/users', methods=['GET', 'POST'])
@csrf.exempt  # Exempt CSRF for user management
def admin_users():
    """Admin users management"""
    if not is_admin_logged_in():
        flash('Please login as admin', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    # Handle user view action
    if request.args.get('action') == 'view' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user_id = request.args.get('user_id')
        try:
            user_id = int(user_id)
            user = conn.execute('''
                SELECT u.*, 
                       COUNT(DISTINCT er.exam_id) as total_exams_taken,
                       SUM(CASE WHEN er.score >= e.passing_score THEN 1 ELSE 0 END) as exams_passed
                FROM users u
                LEFT JOIN exam_sessions er ON u.id = er.user_id
                LEFT JOIN exams e ON er.exam_id = e.id
                WHERE u.id = ?
                GROUP BY u.id
            ''', (user_id,)).fetchone()
            
            if user:
                # Format user details as HTML
                exam_history = conn.execute('''
                    SELECT er.*, e.title, e.passing_score
                    FROM exam_sessions er
                    JOIN exams e ON er.exam_id = e.id
                    WHERE er.user_id = ?
                    ORDER BY er.start_time DESC
                ''', (user_id,)).fetchall()
                
                html = f'''
                <div class="user-details">
                    <div class="user-header">
                        <h2>{user['name']} ({user['nsi_id']})</h2>
                        <div class="user-meta">
                            <div class="meta-item"><strong>Wing:</strong> {user['wing_name'] or 'N/A'}</div>
                            <div class="meta-item"><strong>District:</strong> {user['district_name'] or 'N/A'}</div>
                            <div class="meta-item"><strong>Section:</strong> {user['section_name'] or 'N/A'}</div>
                            <div class="meta-item"><strong>Registered:</strong> {user['created_at']}</div>
                        </div>
                    </div>
                    
                    <div class="user-stats">
                        <div class="stat-card">
                            <div class="stat-number">{user['total_exams_taken'] or 0}</div>
                            <div class="stat-label">Exams Taken</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{user['exams_passed'] or 0}</div>
                            <div class="stat-label">Exams Passed</div>
                        </div>
                    </div>
                    
                    <h3>Exam History</h3>
                '''
                
                if exam_history:
                    html += '''
                    <table class="exam-history-table">
                        <thead>
                            <tr>
                                <th>Exam Title</th>
                                <th>Score</th>
                                <th>Status</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                    '''
                    
                    for result in exam_history:
                        score_val = result['score'] if result['score'] is not None else 0
                        status = "Passed" if score_val >= result['passing_score'] else "Failed"
                        status_class = "passed" if status == "Passed" else "failed"
                        date_display = result['end_time'] or result['start_time'] or '-'
                        
                        html += f'''
                        <tr>
                            <td>{result['title']}</td>
                            <td>{score_val}%</td>
                            <td><span class="status-badge {status_class}">{status}</span></td>
                            <td>{date_display}</td>
                        </tr>
                        '''
                    
                    html += '''
                        </tbody>
                    </table>
                    '''
                else:
                    html += '<p>No exam history available for this user.</p>'
                
                html += '</div>'
                
                return jsonify({
                    'success': True,
                    'html': html
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error retrieving user details: {str(e)}'
            })
    
    # Handle the export action
    elif request.args.get('action') == 'export':
        # Get all users
        users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
        
        # Create CSV content
        import io
        import csv
        from flask import Response
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['NSI ID', 'Name', 'Wing', 'District', 'Section', 'Created At'])
        
        # Write user data
        for user in users:
            writer.writerow([
                user['nsi_id'],
                user['name'],
                user['wing_name'] or '',
                user['district_name'] or '',
                user['section_name'] or '',
                user['created_at']
            ])
        
        # Create response
        conn.close()
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=users.csv"}
        )
    
    # Handle add_new action to show the add user form
    elif request.args.get('action') == 'add_new':
        conn.close()
        return render_template('admin_users.html', show_add_form=True)
    
    # Handle bulk delete action via AJAX
    elif request.args.get('action') == 'bulk_delete' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user_ids = request.json.get('user_ids', [])
        if user_ids:
            # Convert string IDs to integers
            try:
                user_ids = [int(uid) for uid in user_ids]
                # Get NSI IDs to report in success message
                nsi_ids = [row['nsi_id'] for row in conn.execute(
                    f"SELECT nsi_id FROM users WHERE id IN ({','.join(['?'] * len(user_ids))}) AND nsi_id != 'admin'", 
                    user_ids
                ).fetchall()]
                
                # Delete the users
                placeholders = ','.join(['?'] * len(user_ids))
                conn.execute(f"DELETE FROM users WHERE id IN ({placeholders}) AND nsi_id != 'admin'", user_ids)
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f"Successfully deleted {len(nsi_ids)} users: {', '.join(nsi_ids)}"
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f"Error deleting users: {str(e)}"
                })
        else:
            return jsonify({
                'success': False,
                'message': "No users selected for deletion"
            })
    
    # Handle bulk reset attempts action via AJAX
    elif request.args.get('action') == 'bulk_reset_attempts' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user_ids = request.json.get('user_ids', [])
        if user_ids:
            try:
                user_ids = [int(uid) for uid in user_ids]
                # Get NSI IDs to report in success message
                nsi_ids = [row['nsi_id'] for row in conn.execute(
                    f"SELECT nsi_id FROM users WHERE id IN ({','.join(['?'] * len(user_ids))})", 
                    user_ids
                ).fetchall()]
                
                # Reset attempts for these users
                placeholders = ','.join(['?'] * len(user_ids))
                conn.execute(f"DELETE FROM exam_sessions WHERE user_id IN ({placeholders})", user_ids)
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': f"Successfully reset exam attempts for {len(nsi_ids)} users: {', '.join(nsi_ids)}"
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f"Error resetting attempts: {str(e)}"
                })
        else:
            return jsonify({
                'success': False,
                'message': "No users selected"
            })
    
    # Handle individual reset attempts
    elif 'reset' in request.args:
        user_id = request.args.get('reset')
        try:
            user_id = int(user_id)
            user = conn.execute("SELECT nsi_id FROM users WHERE id = ?", (user_id,)).fetchone()
            if user:
                conn.execute("DELETE FROM exam_sessions WHERE user_id = ?", (user_id,))
                conn.commit()
                flash(f"Exam attempts reset for user {user['nsi_id']}", 'success')
            else:
                flash("User not found", 'error')
        except Exception as e:
            flash(f"Error resetting attempts: {str(e)}", 'error')
        return redirect(url_for('admin_users'))
    
    # Handle user deletion
    elif 'delete' in request.args:
        nsi_id = request.args.get('delete')
        if nsi_id != 'admin':
            conn.execute('DELETE FROM users WHERE nsi_id = ?', (nsi_id,))
            conn.commit()
            flash(f'User {nsi_id} deleted successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        nsi_id = request.form.get('nsi_id')
        name = request.form.get('name', '').strip()
        wing_name = request.form.get('wing_name', '').strip()
        district_name = request.form.get('district_name', '').strip()
        section_name = request.form.get('section_name', '').strip()
        password = request.form.get('password', '')
        
        # Check if this is a new user submission
        is_new_user = request.form.get('action') == 'add_user'
        
        if is_new_user:
            # Get additional fields for new user
            division_name = request.form.get('division_name', '').strip()
            country_name = request.form.get('country_name', '').strip()
            internal_type = request.form.get('internal_type', '').strip()
            border_type = request.form.get('border_type', '').strip()
            external_type = request.form.get('external_type', '').strip()
            
            # Validate required fields for new user
            if not (nsi_id and name and password and wing_name and section_name):
                flash('NSI ID, Name, Password, Wing and Section are required!', 'error')
                users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
                conn.close()
                return render_template('admin_users.html', users=users, show_add_form=True)
            
            # Wing-specific validation
            if wing_name == 'External' and not country_name:
                flash('Country name is required for External wing!', 'error')
                users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
                conn.close()
                return render_template('admin_users.html', users=users, show_add_form=True)
            
            # Clear irrelevant fields based on wing selection
            if wing_name != 'External':
                country_name = ''
                external_type = ''
            if wing_name != 'Internal':
                internal_type = ''
            if wing_name != 'Border':
                border_type = ''
            
            # Check if user already exists
            existing_user = conn.execute('SELECT id FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
            if existing_user:
                flash('User with this NSI ID already exists!', 'error')
                users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
                conn.close()
                return render_template('admin_users.html', users=users, show_add_form=True)
            
            # Validate password
            is_valid, validation_message = InputValidator.validate_password(password)
            if not is_valid:
                flash(f'Password validation failed: {validation_message}', 'error')
                users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
                conn.close()
                return render_template('admin_users.html', users=users, show_add_form=True)
            
            # Insert new user with all fields
            password_hash = hash_password(password)
            conn.execute('''
                INSERT INTO users (nsi_id, name, wing_name, district_name, section_name, password_hash,
                                 division_name, internal_type, border_type, external_type, country_name) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nsi_id, name, wing_name, district_name, section_name, password_hash,
                  division_name, internal_type, border_type, external_type, country_name))
            conn.commit()
            flash('User added successfully!', 'success')
            return redirect(url_for('admin_users'))
            
        # Handle existing user update
        elif nsi_id != 'admin':
            if password:
                password_hash = hash_password(password)
                conn.execute('UPDATE users SET name=?, wing_name=?, district_name=?, section_name=?, password_hash=? WHERE nsi_id=?',
                           (name, wing_name, district_name, section_name, password_hash, nsi_id))
            else:
                conn.execute('UPDATE users SET name=?, wing_name=?, district_name=?, section_name=? WHERE nsi_id=?',
                           (name, wing_name, district_name, section_name, nsi_id))
            conn.commit()
            flash(f'User {nsi_id} updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
    
    edit_user = None
    if 'edit' in request.args:
        nsi_id = request.args.get('edit')
        edit_user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
    
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    conn.close()
    
    if edit_user:
        return render_template('edit_user.html', user=edit_user)
    
    show_add_form = request.args.get('action') == 'add_new'
    return render_template('admin_users.html', users=users, show_add_form=show_add_form)

@app.route('/admin/users/delete/<nsi_id>')
def delete_user(nsi_id):
    if not is_admin_logged_in():
        flash('Please login as admin', 'error')
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE nsi_id = ?', (nsi_id,))
    conn.commit()
    conn.close()
    flash(f'User {nsi_id} deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/users/edit/<nsi_id>', methods=['GET', 'POST'])
@csrf.exempt  # Exempt CSRF for user editing
def edit_user(nsi_id):
    if not is_admin_logged_in():
        flash('Please login as admin', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        try:
            # Get form data
            new_nsi_id = request.form.get('nsi_id', '').strip()
            name = request.form.get('name', '').strip()
            wing_name = request.form.get('wing_name', '').strip()
            section_name = request.form.get('section_name', '').strip()
            division_name = request.form.get('division_name', '').strip()
            district_name = request.form.get('district_name', '').strip()
            country_name = request.form.get('country_name', '').strip()
            internal_type = request.form.get('internal_type', '').strip()
            border_type = request.form.get('border_type', '').strip()
            external_type = request.form.get('external_type', '').strip()
            password = request.form.get('password', '')
            
            # Validate required fields
            if not new_nsi_id:
                flash('NSI ID is required', 'error')
                user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
                conn.close()
                return render_template('edit_user.html', user=user)
                
            if not name:
                flash('Name is required', 'error')
                user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
                conn.close()
                return render_template('edit_user.html', user=user)
            
            if not wing_name:
                flash('Wing is required', 'error')
                user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
                conn.close()
                return render_template('edit_user.html', user=user)
            
            # Wing-specific validation based on new structure
            if wing_name == 'Internal Wing':
                if not internal_type:
                    flash('Internal Wing type is required', 'error')
                    user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
                    conn.close()
                    return render_template('edit_user.html', user=user)
                
                if internal_type == 'HQ':
                    if not section_name:
                        flash('Section name is required for Internal Wing HQ', 'error')
                        user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
                        conn.close()
                        return render_template('edit_user.html', user=user)
                    # Clear division/district for HQ
                    division_name = ''
                    district_name = ''
                elif internal_type == 'Others':
                    if not division_name or not district_name:
                        flash('Division and District are required for Internal Wing Others', 'error')
                        user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
                        conn.close()
                        return render_template('edit_user.html', user=user)
                    # Clear section for Others
                    section_name = ''
                    
            elif wing_name == 'Border Wing':
                if not border_type:
                    flash('Border Wing type is required', 'error')
                    user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
                    conn.close()
                    return render_template('edit_user.html', user=user)
                    
                if border_type == 'HQ':
                    if not section_name:
                        flash('Section name is required for Border Wing HQ', 'error')
                        user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
                        conn.close()
                        return render_template('edit_user.html', user=user)
                    # Clear division/district for HQ
                    division_name = ''
                    district_name = ''
                elif border_type == 'Others':
                    if not division_name or not district_name:
                        flash('Division and District are required for Border Wing Others', 'error')
                        user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
                        conn.close()
                        return render_template('edit_user.html', user=user)
                    # Clear section for Others
                    section_name = ''
                    
            elif wing_name == 'External Affairs & Liasons Wing':
                if not external_type:
                    flash('External Affairs Wing type is required', 'error')
                    user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
                    conn.close()
                    return render_template('edit_user.html', user=user)
                    
                if external_type == 'Outside BD':
                    if not country_name:
                        flash('Country name is required for External Affairs Wing Outside BD', 'error')
                        user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
                        conn.close()
                        return render_template('edit_user.html', user=user)
                else:
                    # Clear country for Inside BD
                    country_name = ''
                    
                # External Affairs Wing doesn't use section
                section_name = ''
                division_name = ''
                district_name = ''
                
            else:
                # For all other wings (Technical Intelligence, Admin, Political, Research, etc.)
                if not section_name:
                    flash('Section name is required', 'error')
                    user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
                    conn.close()
                    return render_template('edit_user.html', user=user)
                # Clear wing-specific fields for other wings
                division_name = ''
                district_name = ''
                country_name = ''
                internal_type = ''
                border_type = ''
                external_type = ''
            
            # Check if NSI ID is being changed and if new one already exists
            if new_nsi_id != nsi_id:
                existing_user = conn.execute('SELECT nsi_id FROM users WHERE nsi_id = ?', (new_nsi_id,)).fetchone()
                if existing_user:
                    flash(f'NSI ID {new_nsi_id} already exists', 'error')
                    user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
                    conn.close()
                    return render_template('edit_user.html', user=user)
            
            # Validate password if provided
            if password:
                is_valid, validation_message = InputValidator.validate_password(password)
                if not is_valid:
                    flash(f'Password validation failed: {validation_message}', 'error')
                    user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
                    conn.close()
                    return render_template('edit_user.html', user=user)
                
                # Update with password
                password_hash = hash_password(password)
                conn.execute('''UPDATE users SET nsi_id=?, name=?, wing_name=?, section_name=?, 
                               division_name=?, district_name=?, country_name=?, 
                               internal_type=?, border_type=?, external_type=?, password_hash=? 
                               WHERE nsi_id=?''',
                           (new_nsi_id, name, wing_name, section_name, division_name, district_name, 
                            country_name, internal_type, border_type, external_type, password_hash, nsi_id))
            else:
                # Update without password
                conn.execute('''UPDATE users SET nsi_id=?, name=?, wing_name=?, section_name=?, 
                               division_name=?, district_name=?, country_name=?, 
                               internal_type=?, border_type=?, external_type=? 
                               WHERE nsi_id=?''',
                           (new_nsi_id, name, wing_name, section_name, division_name, district_name, 
                            country_name, internal_type, border_type, external_type, nsi_id))
            
            conn.commit()
            flash(f'User {new_nsi_id} updated successfully!', 'success')
            return redirect(url_for('admin_users'))
            
        except Exception as e:
            flash(f'Error updating user: {str(e)}', 'error')
            user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
            conn.close()
            return render_template('edit_user.html', user=user)
        finally:
            if conn:
                conn.close()
    else:
        # GET request - display form
        user = conn.execute('SELECT * FROM users WHERE nsi_id = ?', (nsi_id,)).fetchone()
        if not user:
            flash('User not found!', 'error')
            conn.close()
            return redirect(url_for('admin_users'))
        
        conn.close()
        return render_template('edit_user.html', user=user)

# Error handlers
@app.route('/admin/download_backup/<filename>')
def download_backup(filename):
    """Download a database backup file"""
    if not is_admin_logged_in():
        flash('Please login as admin', 'error')
        return redirect(url_for('admin_login'))
        
    # Validate filename to prevent directory traversal attacks
    import os
    import re
    
    if not re.match(r'^backup_\d{8}_\d{6}\.db$', filename):
        flash('Invalid backup filename', 'error')
        return redirect(url_for('admin_dashboard'))
        
    backup_dir = 'backups'
    return send_from_directory(
        directory=os.path.abspath(backup_dir),
        path=filename,
        as_attachment=True
    )

# Mobile Test Route
@app.route('/test-mobile')
def test_mobile():
    """Mobile responsiveness test page"""
    return send_from_directory('.', 'test_mobile_responsive.html')

# Mobile diagnostics route
@app.route('/mobile-check')
def mobile_check():
    """Mobile compatibility diagnostics"""
    user_agent = request.headers.get('User-Agent', '')
    
    # Detect mobile device
    mobile_indicators = ['Mobile', 'Android', 'iPhone', 'iPad', 'Windows Phone']
    is_mobile = any(indicator in user_agent for indicator in mobile_indicators)
    
    # Return JSON with mobile info
    mobile_info = {
        'is_mobile': is_mobile,
        'user_agent': user_agent,
        'headers': dict(request.headers),
        'method': request.method,
        'url': request.url,
        'remote_addr': request.remote_addr,
        'static_url_test': url_for('static', filename='css/style.css'),
        'login_url': url_for('login'),
        'register_url': url_for('register'),
        'admin_login_url': url_for('admin_login')
    }
    
    response = make_response(jsonify(mobile_info))
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/test-youtube')
def test_youtube():
    """Test page for YouTube embed functionality"""
    return render_template('test_youtube.html')

@app.route('/youtube-debug')
def youtube_debug():
    """Standalone YouTube debugging page"""
    return render_template('youtube_test_standalone.html')

if __name__ == '__main__':
    migrate_database()  # Run migrations first
    migrate_passwords_to_bcrypt()  # Migrate passwords to bcrypt
    init_database()
    
    print("=" * 50)
    print("Simple Online Examination System")
    print("=" * 50)
    print("Admin Login: admin / [Default Password - Change Required]")
    print("URL: http://localhost:5008")
    print("🧪 Test YouTube: http://localhost:5008/test-youtube")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5008, debug=False)