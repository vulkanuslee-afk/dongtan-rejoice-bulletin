@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 주보 변환

if "%~1"=="" (
  echo.
  echo   ------------------------------------------------------
  echo    주보 워드 파일(.docx)을 이 파일 위로 끌어다 놓으세요.
  echo   ------------------------------------------------------
  echo.
  echo    (파일을 마우스로 잡아서 1_주보변환.bat 아이콘 위에 놓으면 됩니다)
  echo.
  pause
  exit /b
)

echo.
echo   [1/2] 워드 파일을 읽는 중...
echo.
python -I tools\docx_to_bulletin.py "%~1"
if errorlevel 1 (
  echo.
  echo   !! 변환에 실패했습니다. 위 메시지를 확인해 주세요.
  echo.
  pause
  exit /b 1
)

echo.
echo   [2/2] 미리보기를 엽니다. 내용을 확인해 주세요.
echo.
call "0_미리보기.bat"

echo   ------------------------------------------------------
echo    확인 끝나셨으면 2_올리기.bat 을 실행하세요.
echo    고칠 곳이 있으면 data\bulletins.js 를 열어 고치면 됩니다.
echo   ------------------------------------------------------
echo.
pause
