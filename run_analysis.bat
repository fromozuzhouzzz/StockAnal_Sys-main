@echo off
echo 批量股票分析程序
echo ==================

echo 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo Python未找到，尝试使用py命令...
    py --version
    if %errorlevel% neq 0 (
        echo 错误: 未找到Python环境
        pause
        exit /b 1
    )
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

echo 使用Python命令: %PYTHON_CMD%

echo.
echo 运行批量分析程序...
%PYTHON_CMD% final_batch_analyzer.py

echo.
echo 程序执行完成
pause
