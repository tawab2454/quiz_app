#!/usr/bin/env python3
"""
Migration helper: normalize stored answers in exam_sessions.
- Scans completed exam_sessions
- Loads questions_json and answers/answers_detail
- For numeric answers, tries to map to option letters using 1-based index mapping
- Updates answers and answers_detail with normalized letters where possible

Make a DB backup before running.
"""
import sqlite3
import json
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / 'exam_system.db'

if not DB.exists():
    print(f"Database not found at {DB}")
    raise SystemExit(1)

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def normalize_value(val, options):
    """Try to normalize val to an option letter using heuristics.
    - If val is letter (A/B/...), return upper-letter
    - If val is digit and 1 <= int(val) <= len(options), map to that option's letter (1-based)
    - If val equals option text, return option letter
    - Otherwise return original val and mark as unmapped
    """
    if val is None:
        return None, False
    s = str(val).strip()
    if not s:
        return s, False
    # letter
    if len(s) == 1 and s.upper() in [o[0] for o in options]:
        return s.upper(), True
    # digit -> 1-based index
    if s.isdigit():
        idx = int(s)
        if 1 <= idx <= len(options):
            return options[idx-1][0], True
    # match by exact option text
    for letter, text in options:
        if s == text:
            return letter, True
    return val, False

# Fetch completed sessions
cur.execute("SELECT id, questions_json, answers, answers_detail FROM exam_sessions WHERE is_completed = 1")
sessions = cur.fetchall()
print(f"Found {len(sessions)} completed sessions to inspect")

changed = 0
problems = []
for sess in sessions:
    sid = sess['id']
    try:
        questions = json.loads(sess['questions_json'] or '[]')
    except Exception:
        questions = []
    try:
        answers = json.loads(sess['answers'] or '{}') if sess['answers'] else {}
    except Exception:
        answers = {}
    try:
        answers_detail = json.loads(sess['answers_detail'] or '[]')
    except Exception:
        answers_detail = []

    updated = False

    # Build options map by question id
    q_options = {}
    for q in questions:
        q_options[str(q.get('id'))] = q.get('options', [])

    # Normalize answers dict
    new_answers = dict(answers) if isinstance(answers, dict) else {}
    for qid, val in list(new_answers.items()):
        opts = q_options.get(str(qid), [])
        if not opts:
            continue
        normalized, ok = normalize_value(val, opts)
        if ok and normalized != val:
            new_answers[qid] = normalized
            updated = True
            print(f"Session {sid}: answer for q{qid} normalized {val} -> {normalized}")
        elif not ok and isinstance(val, (int, str)) and str(val).isdigit():
            # couldn't map numeric value
            problems.append((sid, qid, val))

    # Normalize answers_detail list
    new_answers_detail = list(answers_detail)
    for i, ad in enumerate(new_answers_detail):
        if isinstance(ad, dict):
            qid = str(ad.get('question_id') or (i+1))
            opts = q_options.get(qid, [])
            sel = ad.get('selected_answer') or ad.get('user_answer') or ad.get('answer')
            if sel is None:
                continue
            normalized, ok = normalize_value(sel, opts)
            if ok and normalized != sel:
                new_answers_detail[i]['selected_answer'] = normalized
                new_answers_detail[i]['user_answer'] = normalized
                updated = True
                print(f"Session {sid}: answers_detail[{i}] normalized {sel} -> {normalized}")
            elif not ok and isinstance(sel, (int, str)) and str(sel).isdigit():
                problems.append((sid, qid, sel))

    if updated:
        # write back
        cur.execute('UPDATE exam_sessions SET answers = ?, answers_detail = ? WHERE id = ?',
                    (json.dumps(new_answers), json.dumps(new_answers_detail), sid))
        conn.commit()
        changed += 1

print(f"Normalization complete. Sessions updated: {changed}. Problematic entries: {len(problems)}")
if problems:
    print("Examples of problematic entries (session_id, question_id, stored_value):")
    for p in problems[:20]:
        print(p)

conn.close()
print('Done. Please verify by opening a few exam review pages in the app.')
