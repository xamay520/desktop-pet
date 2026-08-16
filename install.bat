@echo off
chcp 65001 >nul
title 桌宠一键安装
echo ============================================
echo   桌宠一键安装脚本
echo ============================================
echo.

where python >nul 2>nul
if %errorlevel%==0 (
    echo [1/2] 检测到 Python，正在安装依赖...
    python -m pip install --upgrade pip
    python -m pip install pyperclip requests mss
    echo.
    echo [2/2] 依赖安装完成！
    echo 现在双击 desktop_pet.py 即可运行桌宠
) else (
    echo [错误] 未检测到 Python！
    echo.
    echo 请先到 https://www.python.org/downloads/ 下载安装 Python
    echo 安装时务必勾选 "Add Python to PATH" 选项
    echo 装完后再双击本脚本一次即可
)
echo.
pause
