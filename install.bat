@echo off
chcp 65001 >nul
title 桌宠一键安装
echo ============================================
echo   桌宠一键安装脚本
echo ============================================
echo.

REM 依次检测 py / python / python3
set "PYCMD="
where py >nul 2>nul && set "PYCMD=py -3"
if not defined PYCMD (
    where python >nul 2>nul && set "PYCMD=python"
)
if not defined PYCMD (
    where python3 >nul 2>nul && set "PYCMD=python3"
)

if defined PYCMD (
    echo [1/2] 使用 %PYCMD% 安装依赖...
    %PYCMD% -m pip install --upgrade pip
    %PYCMD% -m pip install pyperclip requests mss
    echo.
    echo [2/2] 依赖安装完成！
    echo 现在双击 desktop_pet.py 即可运行桌宠
    goto :end
)

REM 尝试用 uv 修复 Python 环境
where uv >nul 2>nul
if %errorlevel%==0 (
    echo 检测到 uv，正在安装 Python 3.12...
    uv python install 3.12
    echo 正在安装依赖...
    uv pip install --python 3.12 pyperclip requests mss
    echo.
    echo 依赖安装完成！
    echo 以后运行桌宠请用命令： uv run --python 3.12 desktop_pet.py
    goto :end
)

echo [错误] 未检测到 Python 或 uv！
echo.
echo 请先到 https://www.python.org/downloads/ 下载安装 Python
echo 安装时务必勾选 "Add Python to PATH" 选项
echo 装完后再双击本脚本一次即可

:end
echo.
pause
