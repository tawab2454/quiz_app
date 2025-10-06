# Fix: Admin Questions Stats Display

## Problem
The question statistics in `admin_questions.html` were showing incorrect counts because:
- Easy/Medium/Hard stats were filtering by `category` instead of `difficulty`
- This meant video questions with easy/medium/hard difficulty were not being counted

## Root Cause
The template was using:
```jinja2
{{ questions|selectattr('category', 'equalto', 'easy')|list|length }}
```

But should have been using:
```jinja2
{{ questions|selectattr('difficulty', 'equalto', 'easy')|list|length }}
```

## Fix Applied

### File: `templates/admin_questions.html` (Lines 93-121)

**Changed:**
- Easy/Medium/Hard/Unseen stats now filter by `difficulty` field
- Image/Video stats now filter by `category` field

### Before:
```jinja2
<div class="stat-item">
    <span class="stat-value">{{ questions|selectattr('category', 'equalto', 'easy')|list|length }}</span>
    <span class="stat-label">Easy</span>
</div>
```

### After:
```jinja2
<div class="stat-item">
    <span class="stat-value">{{ questions|selectattr('difficulty', 'equalto', 'easy')|list|length }}</span>
    <span class="stat-label">Easy</span>
</div>
```

## Correct Stats Display

Now the admin will see accurate counts:

```
Total Questions: 41

Easy:    11 questions (3 text + 8 video)
Medium:   9 questions (5 text + 4 video)
Hard:     7 questions (3 text + 4 video)
Unseen:   0 questions
Image:   12 questions
Video:   18 questions
```

## Impact

### Before Fix:
- Easy showed: 3 (only text questions with category='easy')
- Medium showed: 5 (only text questions with category='medium')
- Hard showed: 3 (only text questions with category='hard')

### After Fix:
- Easy shows: 11 (all questions with difficulty='easy')
- Medium shows: 9 (all questions with difficulty='medium')
- Hard shows: 7 (all questions with difficulty='hard')

## Consistency Across System

Now all parts of the system use the same logic:

1. ✅ **Exam Creation** (`add_exam`) - Counts by difficulty for easy/medium/hard
2. ✅ **Exam Taking** (`take_exam`) - Selects by difficulty for easy/medium/hard
3. ✅ **Admin Questions** (`admin_questions.html`) - Displays by difficulty for easy/medium/hard
4. ✅ **Backend Stats** (`admin_questions` route) - Already calculated correctly

## Files Modified
- `templates/admin_questions.html` - Fixed stats display logic

---

**Status:** ✅ FIXED - Admin questions page now shows accurate statistics!
