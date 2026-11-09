@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 주보 미리보기

rem 이미 켜져 있으면 다시 안 켭니다
powershell -NoProfile -Command "try{(New-Object Net.Sockets.TcpClient('127.0.0.1',8792)).Close();exit 0}catch{exit 1}" >nul 2>&1
if errorlevel 1 (
  start /min "주보 미리보기 서버 - 다 보시면 이 창을 닫으세요" cmd /c "python -m http.server 8792 --directory ."
  powershell -NoProfile -Command "Start-Sleep -Milliseconds 900" >nul
)

start "" http://localhost:8792/?v=%RANDOM%

echo.
echo   브라우저에서 주보를 확인하세요.
echo   작업 표시줄에 작게 내려간 "주보 미리보기 서버" 창은
echo   다 보신 뒤에 닫으시면 됩니다.
echo.
