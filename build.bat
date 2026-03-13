@echo off
chcp 65001 >nul
REM AI Agent 快速打包脚本 (Windows)
REM 适用于 PowerShell 或 CMD

echo ======================================
echo 🚀 AI Agent 打包工具
echo ======================================
echo.

REM 检查是否在项目根目录
if not exist "main.py" (
    echo [错误] 请在项目根目录执行此脚本
    pause
    exit /b 1
)

REM 检查 flet 是否安装
where flet >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 flet 命令，请先安装：pip install flet
    pause
    exit /b 1
)

REM 显示版本信息
echo [信息] Flet 版本:
flet --version
echo.

REM 清理旧的构建文件
echo [信息] 清理旧的构建文件...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul
echo [完成] ✓ 清理完成
echo.

REM 开始打包
echo [信息] 开始打包...
echo 这可能需要 5-10 分钟，请耐心等待...
echo.

REM 设置图标文件（如果不存在则使用默认）
set ICON_FILE=assets\icon.ico
if not exist "%ICON_FILE%" (
    echo [警告] 图标文件不存在：%ICON_FILE%，将使用默认图标
    set ICON_PARAM=
) else (
    set ICON_PARAM=--icon "%ICON_FILE%"
)

REM 执行打包命令
echo [信息] 执行打包命令...
flet pack main.py ^
  --name "AI Agent" ^
  --file-version "1.0.0" ^
  --product-version "1.0.0" ^
  %ICON_PARAM% ^
  --add-data "theme;theme" ^
  --add-data "components;components" ^
  --add-data "views;views" ^
  --add-data "core;core" ^
  --add-data "tools;tools" ^
  --add-data "controllers;controllers" ^
  --add-data "services;services" ^
  --add-data "utils;utils" ^
  --hidden-import langchain ^
  --hidden-import langchain_openai ^
  --hidden-import langchain_deepseek ^
  --hidden-import yaml ^
  --hidden-import aiohttp ^
  --hidden-import dotenv ^
  --hidden-import tree_sitter ^
  --hidden-import tree_sitter_python

REM 检查打包结果
if %errorlevel% equ 0 (
    echo.
    echo ======================================
    echo ✅ 打包成功！
    echo ======================================
    echo.
    
    REM 显示生成的文件
    if exist "dist\AI Agent" (
        echo [信息] 生成的文件:
        dir /b "dist\AI Agent"
        echo.
        
        echo [信息] 运行方式:
        echo cd "dist\AI Agent"
        echo AI Agent.exe
        echo.
    )
    
    echo [提示]
    echo - 可执行文件位于：dist\AI Agent\
    echo - 如需分发，请将整个目录打包
    echo - 首次启动可能需要几秒钟加载
    echo.
    
    REM 询问是否打开输出目录
    set /p OPEN_DIR="是否打开输出目录？(Y/N): "
    if /i "%OPEN_DIR%"=="Y" (
        explorer "dist\AI Agent"
    )
    
) else (
    echo.
    echo ======================================
    echo ❌ 打包失败！
    echo ======================================
    echo.
    echo 请检查以下常见问题：
    echo 1. 确保所有依赖已安装：pip install -r requirements.txt
    echo 2. 检查图标文件是否存在：assets\icon.ico
    echo 3. 查看上方错误信息
    echo.
    pause
    exit /b 1
)

pause
