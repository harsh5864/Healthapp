@echo off
echo ===================================================
echo Starting AI Health Companion Full-Stack Application
echo ===================================================

REM 1. Verify / Start MySQL
echo [1/4] Checking MySQL Database...
docker compose up -d mysql

REM 2. Start Python AI Service
echo [2/4] Starting AI Service on port 8000...
start "AI Health Companion - AI Service" cmd /k "cd /d %~dp0ai-service && set AI_MODE=production&& python -m uvicorn main:app --port 8000"

REM 3. Start Spring Boot Backend
echo [3/4] Starting Spring Boot Backend on port 8080...
start "AI Health Companion - Backend API" cmd /k "cd /d %~dp0backend && set AI_MODE=production&& ..\.tools\apache-maven-3.9.16\bin\mvn.cmd -Dmaven.repo.local=..\.tools\m2 spring-boot:run"

REM 4. Start React Frontend
echo [4/4] Starting React Frontend on port 5173...
start "AI Health Companion - Frontend Web" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ===================================================
echo All services launched!
echo Access the application at: http://localhost:5173
echo Backend API Swagger/Status: http://localhost:8080/api/status
echo AI Service Health: http://localhost:8000/health
echo ===================================================
pause
