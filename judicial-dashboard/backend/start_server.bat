@echo off
cd /d "c:\xampp\htdocs\Frank work\judicial-dashboard\backend"
set DATABASE_URL=mysql+pymysql://root:@localhost:3306/judicial_dashboard
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
pause
