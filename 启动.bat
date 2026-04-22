@echo off
chcp 65001 >nul
echo ========================================
echo   在线投票系统 - 一键启动（SQLite版）
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    echo 下载地址：https://www.python.org/downloads/
    pause & exit
)

echo [第一步] 安装依赖包（使用国内镜像）...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 60
if errorlevel 1 (
    echo        清华源失败，尝试阿里云...
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple --timeout 60
)
echo        安装完成 ✓
echo.

echo [第二步] 初始化数据库...
python -c "
from app import create_app
from models import db
import bcrypt

app = create_app()
with app.app_context():
    db.create_all()
    from models import User
    if not User.query.filter_by(username='admin').first():
        pw = bcrypt.hashpw(b'admin123456', bcrypt.gensalt()).decode()
        db.session.add(User(username='admin', email='admin@vote.com', password=pw, is_admin=True))
        db.session.commit()
        print('        默认管理员已创建 ✓')
    else:
        print('        数据库已存在，跳过初始化 ✓')
"
echo.

echo [第三步] 启动 Web 服务...
echo.
echo  ┌─────────────────────────────────────────┐
echo  │  浏览器访问：http://127.0.0.1:5000      │
echo  │  管理员账号：admin / admin123456        │
echo  │  数据库文件：当前目录下的 vote.db       │
echo  │  按 Ctrl+C 可停止服务                   │
echo  └─────────────────────────────────────────┘
echo.
python app.py
pause
