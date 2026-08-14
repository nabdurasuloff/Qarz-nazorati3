@echo off
echo ============================================
echo   Qarz Nazorat Tizimi - .exe yig'ish
echo ============================================

echo [1/3] Kerakli kutubxonalar o'rnatilmoqda...
pip install -r requirements.txt

echo [2/3] .exe yig'ilmoqda (bir necha daqiqa vaqt olishi mumkin)...
pyinstaller --noconfirm --onefile --windowed ^
    --name "QarzNazorat" ^
    --add-data "templates;templates" ^
    --hidden-import "pyxlsb" ^
    --hidden-import "openpyxl" ^
    --collect-submodules "pyxlsb" ^
    main.py

echo [3/3] Tayyor!
echo Natija: dist\QarzNazorat.exe
pause
