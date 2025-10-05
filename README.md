# quiz_app

Simple Online Examination System - local copy.

How to push this project to GitHub (Windows PowerShell):

1. Install Git: https://git-scm.com/download/win
2. Open PowerShell and run:

```powershell
cd "C:\Users\User\Desktop\QUIZ-04-10-2025"
git init
git add -A
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/tawab2454/quiz_app.git
# Use your GitHub username and a personal access token (PAT) when prompted for password
git push -u origin main
```

If you want to avoid interactive credential prompts, create a GitHub PAT with repo scope and use it via:

```powershell
# Replace <USERNAME> and <PAT>
git remote set-url origin https://<USERNAME>:<PAT>@github.com/tawab2454/quiz_app.git
git push -u origin main
```

Security: Do not commit `exam_system.db`, backups, or `secret_key.txt`. `.gitignore` is included to prevent that.
