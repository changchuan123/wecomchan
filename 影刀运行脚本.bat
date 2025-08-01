@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 影刀数据库上传脚本启动器
echo ========================================
echo 📅 时间: %date% %time%
echo 🖥️ 系统: Windows
echo 📁 工作目录: %CD%
echo ========================================

REM 设置Node.js优化参数（适用于影刀环境）
set NODE_OPTIONS=--max-old-space-size=2048 --expose-gc --optimize-for-size
echo 🔧 Node.js参数: %NODE_OPTIONS%

REM 检查Node.js是否安装
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

echo ✅ Node.js版本检查通过

REM 检查脚本文件是否存在
if not exist "数据库上传_影刀版.js" (
    echo ❌ 错误: 未找到数据库上传脚本文件
    pause
    exit /b 1
)

echo ✅ 脚本文件检查通过

REM 显示内存信息
echo 📊 系统内存信息:
wmic computersystem get TotalPhysicalMemory /value | find "TotalPhysicalMemory"
echo.

REM 启动脚本
echo 🚀 开始执行影刀数据库上传脚本...
echo ⏰ 开始时间: %date% %time%
echo ========================================

REM 运行脚本并捕获输出
node 数据库上传_影刀版.js

REM 检查执行结果
if %errorlevel% equ 0 (
    echo ========================================
    echo ✅ 脚本执行成功完成
    echo ⏰ 结束时间: %date% %time%
    echo 📱 请检查企业微信是否收到推送消息
    echo ========================================
) else (
    echo ========================================
    echo ❌ 脚本执行失败
    echo ⏰ 结束时间: %date% %time%
    echo 💥 错误代码: %errorlevel%
    echo ========================================
)

echo.
echo 按任意键退出...
pause >nul 