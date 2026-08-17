@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 马维斯桌宠
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
where uv >nul 2>nul
if %errorlevel%==0 (
    uv run --python 3.12 desktop_pet.py
    goto :end
)
echo 未找到 Python，请先运行 install.bat 安装依赖
pause
:end
