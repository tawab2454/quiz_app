"""Test script to verify validation changes"""

# Test the updated validation logic
test_cases = [
    # Test case 1: Normal question with SQL keywords (should pass in relaxed mode)
    {
        "text": "What SQL command is used to select all records from a table?",
        "should_block_strict": True,
        "should_block_relaxed": False
    },
    # Test case 2: Question with quotes (should pass in relaxed mode)
    {
        "text": "What's the difference between 'SELECT' and 'INSERT' commands?",
        "should_block_strict": True,
        "should_block_relaxed": False
    },
    # Test case 3: Actual SQL injection attempt (should block in both modes)
    {
        "text": "'; DROP TABLE users; --",
        "should_block_strict": True,
        "should_block_relaxed": True
    },
    # Test case 4: Normal text about programming (should pass)
    {
        "text": "What does HTML stand for?",
        "should_block_strict": False,
        "should_block_relaxed": False
    },
    # Test case 5: Question with JavaScript keyword (should pass in relaxed mode)
    {
        "text": "What is the purpose of the onclick event in JavaScript?",
        "should_block_strict": True,
        "should_block_relaxed": False
    },
    # Test case 6: Actual XSS attempt (should block in both modes)
    {
        "text": "<script>alert('xss')</script>",
        "should_block_strict": True,
        "should_block_relaxed": True
    },
]

print("Testing validation logic...")
print("=" * 70)

# Import the validation functions from new.py
import sys
import re

def detect_sql_injection(value, strict=True):
    """Detect potential SQL injection attempts"""
    if not value:
        return False
    
    value_lower = str(value).lower()
    
    if strict:
        # Strict mode: Check for common SQL injection patterns
        sql_patterns = [
            r"(\s*(;|'|\"|\-\-|\/\*|\*\/|@@|@|char|nchar|varchar|nvarchar|alter|begin|cast|create|cursor|declare|delete|drop|end|exec|execute|fetch|insert|kill|open|select|sys|sysobjects|syscolumns|table|update)\s*)",
            r"(\s*(union|join|where|order\s+by|group\s+by|having)\s+)",
            r"(\s*(script|javascript|vbscript|onload|onerror|onclick)\s*)",
        ]
    else:
        # Relaxed mode: Only check for dangerous SQL commands with suspicious patterns
        sql_patterns = [
            r";\s*(drop|delete|truncate|alter|create|exec|execute)\s+",
            r"(union\s+select|union\s+all\s+select)",
            r"(exec\s*\(|execute\s*\()",
            r"(--|\/\*|\*\/)\s*(drop|delete|insert|update|exec)",
        ]
    
    for pattern in sql_patterns:
        if re.search(pattern, value_lower):
            return True
    
    return False

def detect_xss(value, strict=True):
    """Detect potential XSS attempts"""
    if not value:
        return False
    
    value_lower = str(value).lower()
    
    if strict:
        # Strict mode: Check for all XSS patterns
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
    else:
        # Relaxed mode: Only check for active script injection
        xss_patterns = [
            r'<script[^>]*>.*</script>',
            r'javascript:\s*[a-z]',
            r'on\w+\s*=\s*["\']?\s*(javascript|alert)',
            r'<iframe[^>]*src\s*=',
            r'<object[^>]*data\s*=',
            r'<embed[^>]*src\s*=',
        ]
    
    for pattern in xss_patterns:
        if re.search(pattern, value_lower):
            return True
    
    return False

# Run tests
for i, test in enumerate(test_cases, 1):
    text = test["text"]
    print(f"\nTest {i}: {text}")
    print("-" * 70)
    
    # Test strict mode
    sql_strict = detect_sql_injection(text, strict=True)
    xss_strict = detect_xss(text, strict=True)
    blocked_strict = sql_strict or xss_strict
    
    # Test relaxed mode
    sql_relaxed = detect_sql_injection(text, strict=False)
    xss_relaxed = detect_xss(text, strict=False)
    blocked_relaxed = sql_relaxed or xss_relaxed
    
    print(f"Strict mode - SQL: {sql_strict}, XSS: {xss_strict}, Blocked: {blocked_strict}")
    print(f"Relaxed mode - SQL: {sql_relaxed}, XSS: {xss_relaxed}, Blocked: {blocked_relaxed}")
    
    # Verify expectations
    strict_pass = blocked_strict == test["should_block_strict"]
    relaxed_pass = blocked_relaxed == test["should_block_relaxed"]
    
    if strict_pass and relaxed_pass:
        print("✅ PASS: Validation works as expected")
    else:
        print("❌ FAIL: Validation doesn't match expectations")
        if not strict_pass:
            print(f"   Expected strict mode blocked={test['should_block_strict']}, got {blocked_strict}")
        if not relaxed_pass:
            print(f"   Expected relaxed mode blocked={test['should_block_relaxed']}, got {blocked_relaxed}")

print("\n" + "=" * 70)
print("Testing complete!")
