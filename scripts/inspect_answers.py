#!/usr/bin/env python3
import sqlite3
import json
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / 'exam_system.db'
if not DB.exists():
    print('DB not found:', DB)
    raise SystemExit(1)

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, questions_json, answers, answers_detail FROM exam_sessions WHERE is_completed=1 ORDER BY id DESC LIMIT 10")
sessions = cur.fetchall()
if not sessions:
    print('No completed sessions found')
    conn.close()
    raise SystemExit(0)

for sess in sessions:
    sid = sess['id']
    print('\n=== Session', sid, '===')
    try:
        q_json = json.loads(sess['questions_json'] or '[]')
    except Exception as e:
        q_json = []
        print('  questions_json parse error:', e)
    print(' Questions count:', len(q_json))
    for q in q_json[:5]:
        print('  Q id:', q.get('id'), 'text:', q.get('question_text')[:50])
        print('   options:', q.get('options'))
        if q.get('option_images'):
            print('   option_images keys:', list(q.get('option_images').keys()))

    try:
        answers = json.loads(sess['answers'] or '{}') if sess['answers'] else {}
    except Exception as e:
        answers = sess['answers']
        print('  answers parse error:', e)
    print(' Answers raw:', answers)

    # print answers_detail safely
    raw_ad = sess['answers_detail']
    print(' Answers_detail raw type:', type(raw_ad))
    try:
        ad = json.loads(raw_ad or '[]') if raw_ad else []
    except Exception as e:
        ad = raw_ad
        print('  answers_detail parse error:', e)

    print(' Answers_detail (safe preview):')
    if isinstance(ad, list):
        for i, a in enumerate(ad[:10]):
            print('   ', i+1, type(a), a)
    else:
        # print repr of whatever it is
        print('   ', repr(ad))

conn.close()
print('\nInspection finished')
