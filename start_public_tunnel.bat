@echo off
echo ========================================================
echo Starting Cloudflare High-Speed Public Tunnel
echo ========================================================
echo Routing traffic to local frontend on port 5173...
"%~dp0.tools\cloudflared.exe" tunnel --url http://localhost:5173
pause
