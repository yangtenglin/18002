#!/bin/bash

set -e

PROJECT_DIR="/home/ubuntu/hotel-simulation"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"

echo "=========================================="
echo "  酒店模拟经营平台 - 代码更新脚本"
echo "=========================================="
echo ""

echo "[1/5] 拉取最新代码..."
cd "$PROJECT_DIR"
git pull
echo "✅ 代码拉取完成"
echo ""

echo "[2/5] 更新后端依赖..."
cd "$BACKEND_DIR"
source "$VENV_DIR/bin/activate"
pip install -r requirements.txt
echo "✅ 后端依赖更新完成"
echo ""

echo "[3/5] 数据库迁移..."
export DJANGO_SETTINGS_MODULE=backend.settings_prod
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
echo "✅ 数据库迁移完成"
echo ""

echo "[4/5] 重新构建前端..."
cd "$FRONTEND_DIR"
npm install
npm run build:prod
echo "✅ 前端构建完成"
echo ""

echo "[5/5] 重启服务..."
sudo systemctl restart hotel-simulation
sudo systemctl reload nginx
echo "✅ 服务重启完成"
echo ""

echo "=========================================="
echo "  更新完成！"
echo "=========================================="
echo ""
echo "查看服务状态: sudo systemctl status hotel-simulation"
echo "查看后端日志: sudo journalctl -u hotel-simulation -f"
echo ""
