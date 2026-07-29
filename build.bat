@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM 检查虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在，请先运行 run.bat 初始化项目
    pause
    exit /b 1
)

REM 安装打包工具
echo [准备] 检查 PyInstaller...
".venv\Scripts\python.exe" -m pip install pyinstaller --quiet 2>nul

echo [打包] AI电商工具箱 - PyInstaller
".venv\Scripts\python.exe" -m PyInstaller ^
    --noconsole ^
    --name "AI-Ecommerce-Toolkit" ^
    --add-data "config;config" ^
    --add-data "resources;resources" ^
    --add-data "VERSION;." ^
    -m launcher

if errorlevel 1 (
    echo.
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo [完成] 打包结果在 dist\ 目录
pause
