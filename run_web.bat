@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo 재고 웹 입력 페이지: http://127.0.0.1:5000
echo 브라우저에서 위 주소로 접속하세요. 종료하려면 이 창을 닫으세요.
python app.py
pause
