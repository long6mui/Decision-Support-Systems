@echo off
chcp 65001 >nul
echo ===========================================================================
echo   HUST CareerDSS - Hệ Trợ Giúp Quyết Định Tìm Việc Làm Cho SV Tốt Nghiệp
echo   Đang khởi chạy Máy chủ Mô hình AHP-TOPSIS & CSDL SQLite tại cổng 8000...
echo ===========================================================================
start "" "http://127.0.0.1:8000"
python backend\main.py
pause

