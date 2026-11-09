@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 주보 올리기

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
  echo.
  echo   !! 아직 깃허브에 연결되지 않았습니다.
  echo      docs\깃허브-올리는법.md 의 "처음 한 번" 을 먼저 해 주세요.
  echo.
  pause
  exit /b 1
)

echo.
echo   바뀐 파일:
git --no-pager status --short
echo.

set "MSG="
set /p MSG=  메모 (그냥 엔터 치면 오늘 날짜로):
if "%MSG%"=="" set "MSG=주보 업데이트 %date%"

git add -A
git commit -m "%MSG%"
if errorlevel 1 (
  echo.
  echo   바뀐 내용이 없습니다. 올릴 것이 없네요.
  echo.
  pause
  exit /b
)

git push
if errorlevel 1 (
  echo.
  echo   !! 올리기에 실패했습니다.
  echo      인터넷 연결과 깃허브 로그인(gh auth status)을 확인해 주세요.
  echo.
  pause
  exit /b 1
)

echo.
echo   ------------------------------------------------------
echo    올렸습니다. 2~3분 뒤 교인들 폰에서 새 주보가 보입니다.
echo   ------------------------------------------------------
echo.
pause
