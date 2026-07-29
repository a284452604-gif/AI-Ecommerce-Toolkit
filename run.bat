@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PYTHON=C:\Users\ZHANG\.workbuddy\binaries\python\versions\3.13.12\python.exe

REM 检查 Python 是否存在
if not exist "%PYTHON%" (
    echo [错误] 找不到 Python: %PYTHON%
    echo 请确认 Python 3.13.12 已安装
    pause
    exit /b 1
)

REM 首次运行：创建虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo [初始化] 首次运行，正在创建虚拟环境...
    "%PYTHON%" -m venv .venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo [初始化] 正在安装依赖...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo [初始化] 完成！
    echo.
)

echo [启动] AI电商工具箱
".venv\Scripts\python.exe" -m launcher
if errorlevel 1 (
    echo.
    echo [错误] 应用异常退出
    pause
)
