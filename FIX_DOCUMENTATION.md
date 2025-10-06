# Fix for "Potential Security Threat Detected" Error

## Problem
When adding questions through the admin portal's add_question form, the system was blocking legitimate quiz questions with the error: **"Potential Security Threat Detected, Request Block"**

## Root Cause
The security validation functions `detect_sql_injection()` and `detect_xss()` were too aggressive. They were blocking:

1. **SQL Keywords**: Questions about databases/SQL (containing words like "SELECT", "WHERE", "INSERT", "UPDATE", "JOIN", "ORDER BY", etc.)
2. **Quotes**: Questions with apostrophes or quotation marks (e.g., "What's the difference...")
3. **HTML/JavaScript Terms**: Questions about web development (containing words like "onclick", "onload", "script", "javascript")

These are legitimate educational content but were being flagged as security threats.

## Solution Implemented

### 1. Updated `detect_sql_injection()` function
- Added a `strict` parameter (default=True)
- **Strict mode** (for user inputs): Blocks all SQL-related patterns
- **Relaxed mode** (for admin question content): Only blocks dangerous SQL injection patterns like:
  - `; DROP TABLE`
  - `UNION SELECT`
  - `EXEC(...)` with suspicious context
  - SQL comments with destructive commands

### 2. Updated `detect_xss()` function
- Added a `strict` parameter (default=True)
- **Strict mode** (for user inputs): Blocks all XSS-related patterns
- **Relaxed mode** (for admin question content): Only blocks active script injections like:
  - Complete `<script>` tags with code
  - `javascript:` protocol with code
  - Event handlers with suspicious functions
  - Embedded iframes/objects with sources

### 3. Modified `add_question()` route
- Changed validation calls to use `strict=False` for admin content
- This allows SQL/HTML keywords in question text while still blocking actual attacks

## Files Modified
- `new.py`: Lines 141-194 (InputValidator class methods)
- `new.py`: Lines 3028-3037 (add_question security checks)

## Testing
Created `test_validation.py` to verify the fix:
- ✅ Legitimate questions with SQL keywords: ALLOWED in relaxed mode
- ✅ Questions with quotes/apostrophes: ALLOWED in relaxed mode
- ✅ Questions about JavaScript events: ALLOWED in relaxed mode
- ✅ Actual SQL injection attempts: BLOCKED in both modes
- ✅ Actual XSS attempts: BLOCKED in both modes

## Security Impact
- **No security reduction**: Actual malicious payloads are still blocked
- **Improved usability**: Admins can now create educational content about security topics
- **Context-aware**: Strict validation still applies to user authentication and other sensitive areas

## How to Test
1. Login to admin portal
2. Navigate to Add Question form
3. Try adding questions with:
   - SQL keywords: "What does SELECT do in SQL?"
   - Quotes: "What's the difference between 'var' and 'let'?"
   - JavaScript events: "Explain the onclick event handler"
4. All should save successfully without security errors

## Additional Notes
- User registration, login, and other forms still use strict validation
- Only admin question management uses relaxed validation
- The `@csrf.exempt` decorator is already in place for the add_question route
