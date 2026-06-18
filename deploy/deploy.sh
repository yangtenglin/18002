#!/bin/bash

set -e

PROJECT_DIR="/home/ubuntu/hotel-simulation"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"

echo "=========================================="
echo "  酒店模拟经营平台 - 一键部署脚本"
echo "=========================================="
echo ""

echo "[1/8] 检查系统环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python 3.9+"
    exit 1
fi
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js 16+"
    exit 1
fi
if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx 未安装，请先安装 Nginx"
    exit 1
fi
echo "✅ 系统环境检查通过"
echo ""

echo "[2/8] 创建项目目录..."
mkdir -p "$BACKEND_DIR/data"
mkdir -p "$BACKEND_DIR/logs"
mkdir -p "$PROJECT_DIR/logs"
echo "✅ 目录创建完成"
echo ""

echo "[3/8] 安装后端依赖..."
cd "$BACKEND_DIR"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv venv
fi
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ 后端依赖安装完成"
echo ""

echo "[4/8] 配置环境变量..."
if [ ! -f "$BACKEND_DIR/.env" ]; then
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
    sed -i "s|your-secret-key-here-change-this-to-a-long-random-string|$SECRET_KEY|" "$BACKEND_DIR/.env"
    echo "⚠️  请编辑 $BACKEND_DIR/.env 文件，修改域名和IP配置"
else
    echo "✅ 环境变量文件已存在"
fi
echo ""

echo "[5/8] 初始化数据库..."
cd "$BACKEND_DIR"
source "$VENV_DIR/bin/activate"
export DJANGO_SETTINGS_MODULE=backend.settings_prod
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
echo "✅ 数据库初始化完成"
echo ""

echo "[6/8] 构建前端..."
cd "$FRONTEND_DIR"
npm install
npm run build:prod
echo "✅ 前端构建完成"
echo ""

echo "[7/8] 配置 Nginx..."
sudo cp "$PROJECT_DIR/deploy/nginx.conf" /etc/nginx/sites-available/hotel-simulation
sudo ln -sf /etc/nginx/sites-available/hotel-simulation /etc/nginx/sites-enabled/hotel-simulation
sudo nginx -t
sudo systemctl reload nginx
echo "✅ Nginx 配置完成"
echo ""

echo "[8/8] 配置系统服务..."
sudo cp "$PROJECT_DIR/deploy/hotel-simulation.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hotel-simulation
sudo systemctl restart hotel-simulation
echo "✅ 系统服务配置完成"
echo ""

echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "请完成以下步骤："
echo "1. 编辑 $BACKEND_DIR/.env，修改域名和IP配置"
echo "2. 执行: sudo systemctl restart hotel-simulation"
echo ""
echo "常用命令："
echo "  查看服务状态: sudo systemctl status hotel-simulation"
echo "  查看后端日志: sudo journalctl -u hotel-simulation -f"
echo "  重启服务: sudo systemctl restart hotel-simulation"
echo "  创建管理员: cd $BACKEND_DIR && source venv/bin/activate && python manage.py createsuperuser"
echo ""
echo "访问地址："
echo "  前端: http://your-domain.com"
echo "  后台: http://your-domain.com/admin"
echo ""
