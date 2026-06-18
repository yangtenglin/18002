# 酒店模拟经营教学平台 - 部署操作文档

## 目录
1. [部署架构说明](#1-部署架构说明)
2. [服务器环境要求](#2-服务器环境要求)
3. [部署前准备](#3-部署前准备)
4. [一键部署（推荐）](#4-一键部署推荐)
5. [手动部署步骤](#5-手动部署步骤)
6. [部署后配置](#6-部署后配置)
7. [访问方式](#7-访问方式)
8. [日常运维](#8-日常运维)
9. [代码更新流程](#9-代码更新流程)
10. [常见问题排查](#10-常见问题排查)

---

## 1. 部署架构说明

### 1.1 技术栈
| 层级 | 技术 | 说明 |
|---|---|---|
| 前端 | Vue 3 + Vite + Element Plus | 打包为静态文件 |
| 后端 | Django 4 + DRF + SQLite | RESTful API 服务 |
| Web服务器 | Nginx | 反向代理 + 静态文件服务 |
| 应用服务器 | Gunicorn | WSGI 服务器，运行 Django |
| 进程管理 | Systemd | 服务自动重启、日志管理 |

### 1.2 同服务器部署架构

**前后端完全可以部署在同一台服务器上**，推荐架构如下：

```
                    用户浏览器
                         │
                         ▼
                    Nginx (监听 80/443 端口)
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
    静态文件请求                 API 请求(/api/*)
  (前端 dist 目录)           ┌──────────────────┐
                             │  Gunicorn:8000   │
                             │  (Django 后端)   │
                             └──────────────────┘
                                       │
                                       ▼
                                SQLite 数据库
                            (backend/data/db.sqlite3)
```

**部署优势**：
- ✅ 成本低：仅需一台服务器
- ✅ 配置简单：Nginx 统一处理所有请求
- ✅ 无跨域问题：前后端同域名
- ✅ 维护方便：单服务器管理

### 1.3 请求流转
1. 用户访问 `http://your-domain.com` → Nginx 返回前端 `index.html`
2. 前端 JS 加载后，调用 `/api/xxx` 接口 → Nginx 转发给 `127.0.0.1:8000`
3. Django 处理 API 请求，操作 SQLite 数据库
4. 结果原路返回给前端

---

## 2. 服务器环境要求

### 2.1 硬件配置
| 规模 | CPU | 内存 | 硬盘 | 推荐服务器 |
|---|---|---|---|---|
| 测试/小规模（<50人） | 2核 | 2GB | 40GB SSD | 阿里云/腾讯云 轻量应用服务器 |
| 中等规模（50-200人） | 4核 | 4GB | 80GB SSD | 标准型 S6/CVM |
| 大规模（>200人） | 8核 | 8GB | 160GB SSD | 计算型或通用型 |

### 2.2 软件环境
| 软件 | 版本要求 | 说明 |
|---|---|---|
| 操作系统 | Ubuntu 20.04/22.04 LTS | 推荐使用 Ubuntu |
| Python | ≥ 3.9 | 运行 Django 后端 |
| Node.js | ≥ 16.0 | 构建前端 Vue 项目 |
| npm | ≥ 8.0 | Node 包管理器 |
| Nginx | ≥ 1.18 | Web 服务器 / 反向代理 |
| Git | 最新版 | 代码拉取 |

---

## 3. 部署前准备

### 3.1 域名解析（可选但推荐）
如果有域名，在 DNS 服务商添加解析：
- 主机记录：`@` 或 `www`
- 记录类型：`A`
- 记录值：服务器公网 IP 地址

### 3.2 服务器安全组配置
在云服务器控制台开放以下端口：
| 端口 | 协议 | 说明 |
|---|---|---|
| 22 | TCP | SSH 远程连接 |
| 80 | TCP | HTTP 访问 |
| 443 | TCP | HTTPS 访问（配置 SSL 后需要） |

### 3.3 连接服务器
```bash
# 使用 SSH 连接服务器
ssh ubuntu@your-server-ip

# 或使用 root 用户（不推荐）
ssh root@your-server-ip
```

### 3.4 更新系统软件包
```bash
sudo apt update
sudo apt upgrade -y
```

---

## 4. 一键部署（推荐）

项目提供了自动化部署脚本，可一键完成全部部署。

### 4.1 上传代码到服务器
```bash
# 在服务器上克隆代码（推荐）
cd ~
git clone <your-git-repo-url> hotel-simulation

# 或者使用 scp 上传本地代码（开发机执行）
scp -r /path/to/project ubuntu@your-server-ip:~/hotel-simulation
```

### 4.2 安装系统依赖
```bash
# 安装 Python、Node.js、Nginx
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y python3 python3-venv python3-pip nodejs nginx git

# 验证安装
python3 --version
node --version
nginx -v
```

### 4.3 执行一键部署脚本
```bash
cd ~/hotel-simulation
bash deploy/deploy.sh
```

脚本会自动完成以下操作：
1. ✅ 检查系统环境
2. ✅ 创建必要目录
3. ✅ 创建 Python 虚拟环境
4. ✅ 安装后端依赖
5. ✅ 生成并配置环境变量
6. ✅ 初始化数据库
7. ✅ 构建前端静态文件
8. ✅ 配置 Nginx 反向代理
9. ✅ 配置 Systemd 服务

### 4.4 配置环境变量
部署脚本运行后，需要编辑环境变量文件：
```bash
nano ~/hotel-simulation/backend/.env
```

修改以下内容：
```dotenv
DJANGO_SECRET_KEY=自动生成的随机密钥（无需修改）
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com,123.45.67.89
DJANGO_CORS_ORIGINS=http://your-domain.com,https://your-domain.com
DJANGO_CSRF_ORIGINS=http://your-domain.com,https://your-domain.com
```

重启服务使配置生效：
```bash
sudo systemctl restart hotel-simulation
```

---

## 5. 手动部署步骤

如果需要自定义部署，可按以下步骤手动操作。

### 5.1 创建项目目录
```bash
mkdir -p ~/hotel-simulation/{backend/data,backend/logs,logs}
cd ~/hotel-simulation
```

### 5.2 部署后端

#### 5.2.1 创建虚拟环境
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

#### 5.2.2 安装依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5.2.3 配置环境变量
```bash
cp .env.example .env

# 生成随机密钥
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# 编辑环境变量
nano .env
```

#### 5.2.4 初始化数据库
```bash
export DJANGO_SETTINGS_MODULE=backend.settings_prod
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
```

#### 5.2.5 创建管理员账号
```bash
python manage.py createsuperuser
```

#### 5.2.6 配置 Gunicorn 服务
```bash
sudo cp ~/hotel-simulation/deploy/hotel-simulation.service /etc/systemd/system/

# 如果服务器用户名不是 ubuntu，需要修改 service 文件中的用户
sudo nano /etc/systemd/system/hotel-simulation.service

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable hotel-simulation
sudo systemctl start hotel-simulation

# 验证服务状态
sudo systemctl status hotel-simulation
```

### 5.3 部署前端

#### 5.3.1 安装依赖并构建
```bash
cd ~/hotel-simulation/frontend
npm install
npm run build:prod
```

构建完成后，静态文件会生成在 `dist/` 目录。

#### 5.3.2 验证构建结果
```bash
ls -la dist/
# 应该看到 index.html 和 assets 目录
```

### 5.4 配置 Nginx

#### 5.4.1 复制配置文件
```bash
sudo cp ~/hotel-simulation/deploy/nginx.conf /etc/nginx/sites-available/hotel-simulation
```

#### 5.4.2 修改域名配置
```bash
sudo nano /etc/nginx/sites-available/hotel-simulation
```

将 `server_name` 改为你的域名或服务器 IP：
```nginx
server_name your-domain.com www.your-domain.com 123.45.67.89;
```

#### 5.4.3 启用站点
```bash
# 启用站点
sudo ln -sf /etc/nginx/sites-available/hotel-simulation /etc/nginx/sites-enabled/

# 删除默认站点（可选）
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

---

## 6. 部署后配置

### 6.1 创建管理员账号
```bash
cd ~/hotel-simulation/backend
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=backend.settings_prod
python manage.py createsuperuser
```

按照提示输入用户名、邮箱、密码。

### 6.2 初始化测试数据（可选）
```bash
# 先通过注册页面创建 teacher1 和 4 个学生账号，然后执行：
python setup_testdata.py
```

### 6.3 配置 HTTPS（可选但推荐）

使用 Let's Encrypt 免费证书：

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取并配置证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Certbot 会自动修改 Nginx 配置，启用 HTTPS 并设置自动续期。

### 6.4 修改前端 API 配置（如需要）

如果前后端部署在不同服务器，需要修改前端 API 地址：

```bash
nano ~/hotel-simulation/frontend/src/api/index.js
```

修改 `baseURL`：
```javascript
const api = axios.create({
  baseURL: 'https://api.your-domain.com/api',  // 修改为实际后端地址
  // ...
})
```

然后重新构建前端：
```bash
npm run build:prod
sudo systemctl reload nginx
```

---

## 7. 访问方式

### 7.1 部署成功后访问地址

| 功能 | 地址 | 说明 |
|---|---|---|
| 前端首页 | `http://your-domain.com` | 用户登录、注册、使用系统 |
| 管理后台 | `http://your-domain.com/admin` | Django 后台管理，使用超级管理员登录 |
| API 接口 | `http://your-domain.com/api/*` | 后端 API 接口 |

### 7.2 测试验证

1. **访问前端**：在浏览器打开 `http://your-domain.com`，应该看到登录页面
2. **注册账号**：注册一个教师账号和几个学生账号
3. **登录测试**：使用注册的账号登录
4. **后台登录**：访问 `http://your-domain.com/admin`，使用超级管理员登录
5. **功能测试**：创建班级、团队、模拟游戏，提交决策等

---

## 8. 日常运维

### 8.1 服务管理命令

```bash
# 查看服务状态
sudo systemctl status hotel-simulation

# 启动服务
sudo systemctl start hotel-simulation

# 停止服务
sudo systemctl stop hotel-simulation

# 重启服务
sudo systemctl restart hotel-simulation

# 设置开机自启
sudo systemctl enable hotel-simulation

# 取消开机自启
sudo systemctl disable hotel-simulation
```

### 8.2 日志查看

```bash
# 查看后端服务实时日志
sudo journalctl -u hotel-simulation -f

# 查看最近 100 行日志
sudo journalctl -u hotel-simulation -n 100

# 查看 Nginx 访问日志
sudo tail -f /var/log/nginx/hotel-simulation.access.log

# 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/hotel-simulation.error.log

# 查看 Django 应用日志
tail -f ~/hotel-simulation/backend/logs/django.log

# 查看 Gunicorn 日志
tail -f ~/hotel-simulation/logs/gunicorn.access.log
tail -f ~/hotel-simulation/logs/gunicorn.error.log
```

### 8.3 数据库备份

```bash
# 备份数据库（推荐每天执行一次）
cd ~/hotel-simulation
cp backend/data/db.sqlite3 backups/db_$(date +%Y%m%d_%H%M%S).sqlite3

# 恢复数据库
cp backups/db_20240101_120000.sqlite3 backend/data/db.sqlite3
sudo systemctl restart hotel-simulation
```

### 8.4 定时备份（Crontab）

```bash
# 编辑 crontab
crontab -e

# 添加以下内容（每天凌晨 2 点备份）
0 2 * * * cd ~/hotel-simulation && cp backend/data/db.sqlite3 backups/db_$(date +\%Y\%m\%d_\%H\%M\%S).sqlite3

# 只保留最近 7 天的备份
0 3 * * * find ~/hotel-simulation/backups -name "db_*.sqlite3" -mtime +7 -delete
```

---

## 9. 代码更新流程

### 9.1 使用更新脚本（推荐）

```bash
cd ~/hotel-simulation
bash deploy/update.sh
```

### 9.2 手动更新步骤

```bash
# 1. 拉取最新代码
cd ~/hotel-simulation
git pull

# 2. 更新后端依赖
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 3. 数据库迁移
export DJANGO_SETTINGS_MODULE=backend.settings_prod
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

# 4. 重新构建前端
cd ../frontend
npm install
npm run build:prod

# 5. 重启服务
sudo systemctl restart hotel-simulation
sudo systemctl reload nginx

# 6. 验证服务
sudo systemctl status hotel-simulation
```

---

## 10. 常见问题排查

### 10.1 前端页面显示 403 Forbidden
**原因**：Nginx 没有前端文件的读取权限

**解决**：
```bash
sudo chmod -R 755 ~/hotel-simulation/frontend/dist
sudo systemctl reload nginx
```

### 10.2 API 请求返回 502 Bad Gateway
**原因**：后端服务未启动或崩溃

**排查**：
```bash
# 查看服务状态
sudo systemctl status hotel-simulation

# 查看错误日志
sudo journalctl -u hotel-simulation -n 50

# 重启服务
sudo systemctl restart hotel-simulation
```

### 10.3 API 请求返回 403 CORS 错误
**原因**：跨域配置不正确

**解决**：
检查 `backend/.env` 中的 `DJANGO_CORS_ORIGINS` 和 `DJANGO_CSRF_ORIGINS` 是否包含前端域名。

### 10.4 数据库被锁定（SQLite）
**原因**：SQLite 是文件型数据库，高并发时可能出现锁等待

**解决**：
1. 增加超时时间（已在配置中设置 30 秒）
2. 如果用户量较大（>100 人），建议迁移到 PostgreSQL

### 10.5 静态资源加载失败
**原因**：静态文件路径配置错误

**排查**：
```bash
# 检查静态文件是否存在
ls -la ~/hotel-simulation/backend/staticfiles/

# 重新收集静态文件
cd ~/hotel-simulation/backend
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=backend.settings_prod
python manage.py collectstatic --noinput
```

### 10.6 上传文件大小限制
**原因**：Nginx 默认限制上传文件大小为 1MB

**解决**：
在 Nginx 配置中已设置 `client_max_body_size 10M;`，如需更大可修改此值。

### 10.7 服务启动后无法访问
**排查清单**：
1. 检查安全组是否开放 80/443 端口
2. 检查防火墙状态：`sudo ufw status`
3. 检查 Nginx 是否运行：`sudo systemctl status nginx`
4. 检查后端服务：`sudo systemctl status hotel-simulation`
5. 查看 Nginx 错误日志：`sudo tail -f /var/log/nginx/error.log`

### 10.8 Django admin 无法登录
**原因**：CSRF 配置问题

**解决**：
确保 `DJANGO_CSRF_ORIGINS` 包含正确的域名，并且包含 `http://` 或 `https://` 前缀。

---

## 附录 A：配置文件位置速查表

| 文件 | 位置 | 说明 |
|---|---|---|
| Django 生产配置 | [backend/backend/settings_prod.py](file:///Users/linyile/projects/new/2/backend/backend/settings_prod.py) | 后端生产环境配置 |
| 环境变量 | `backend/.env` | 敏感配置（密钥、域名等） |
| Gunicorn 配置 | [deploy/gunicorn.conf.py](file:///Users/linyile/projects/new/2/deploy/gunicorn.conf.py) | Gunicorn 服务器参数 |
| Systemd 服务 | [deploy/hotel-simulation.service](file:///Users/linyile/projects/new/2/deploy/hotel-simulation.service) | 系统服务配置 |
| Nginx 配置 | [deploy/nginx.conf](file:///Users/linyile/projects/new/2/deploy/nginx.conf) | Nginx 反向代理配置 |
| 数据库文件 | `backend/data/db.sqlite3` | SQLite 数据库文件 |
| Django 日志 | `backend/logs/django.log` | 应用日志 |
| Gunicorn 日志 | `logs/gunicorn.*.log` | 服务器日志 |
| Nginx 日志 | `/var/log/nginx/hotel-simulation.*.log` | Web 服务器日志 |

---

## 附录 B：端口使用说明

| 端口 | 服务 | 监听地址 | 说明 |
|---|---|---|---|
| 80 | Nginx | 0.0.0.0 | HTTP 访问（对外） |
| 443 | Nginx | 0.0.0.0 | HTTPS 访问（配置 SSL 后，对外） |
| 8000 | Gunicorn | 127.0.0.1 | Django 后端（仅对内，不对外暴露） |

> **重要**：8000 端口仅监听本地 127.0.0.1，不会直接对外暴露，所有请求通过 Nginx 转发。

---

## 附录 C：性能优化建议

1. **启用 Gzip 压缩**：在 Nginx 配置中添加 gzip 压缩
2. **配置浏览器缓存**：已配置静态资源 30 天缓存
3. **升级数据库**：用户量 > 100 时，建议迁移到 PostgreSQL
4. **添加 CDN**：静态资源可使用 CDN 加速
5. **连接池**：可考虑使用 `pgBouncer` 等连接池（使用 PostgreSQL 时）

---

如有其他问题，请查看项目文档或提交 Issue。
