@echo off
cd /d "%~dp0"
where pyw >nul 2>nul
if %errorlevel%==0 (
    pyw -3 desktop_pet.py
    goto :end
)
where pythonw >nul 2>nul
if %errorlevel%==0 (
    pythonw desktop_pet.py
    goto :end
)
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 desktop_pet.py
    goto :end
)
where python >nul 2>nul
if %errorlevel%==0 (
    python desktop_pet.py
    goto :end
)
echo Python not found. Please run install.bat first.
pause
:end
