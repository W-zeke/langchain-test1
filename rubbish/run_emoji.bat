@echo off
REM 情绪支持助手启动脚本 —— 设置 UTF-8 编码以避免 GBK 兼容问题
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
python test_deepseek3.py
pause
