#!/bin/bash
# FastAPI后端部署脚本 - 阿里云ECS报价系统

set -e  # 遇到错误立即退出

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}FastAPI后端部署脚本${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 请使用root用户或sudo运行此脚本${NC}"
    exit 1
fi

# 项目配置
PROJECT_DIR="/root/Quotation_Pipeline"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_FILE="/etc/systemd/system/quotation-api.service"
NGINX_CONF="/etc/nginx/sites-available/quotation-api"

echo -e "${YELLOW}📦 步骤1: 安装系统依赖...${NC}"

# 更新包管理器
apt-get update -y

# 安装Python3和pip
apt-get install -y python3 python3-pip python3-venv

# 安装Nginx
apt-get install -y nginx

echo -e "${GREEN}✅ 系统依赖安装完成${NC}"
echo ""

echo -e "${YELLOW}📁 步骤2: 准备后端目录...${NC}"

# 确保项目目录存在
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ 后端目录不存在: $BACKEND_DIR${NC}"
    exit 1
fi

cd $BACKEND_DIR

echo -e "${GREEN}✅ 后端目录检查完成${NC}"
echo ""

echo -e "${YELLOW}🐍 步骤3: 创建Python虚拟环境...${NC}"

# 创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi

# 激活虚拟环境
source $VENV_DIR/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✅ Python环境配置完成${NC}"
echo ""

echo -e "${YELLOW}⚙️ 步骤4: 配置环境变量...${NC}"

# 检查.env文件
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${RED}⚠️  .env文件不存在${NC}"
    echo -e "${YELLOW}从根目录复制.env文件...${NC}"
    
    if [ -f "$PROJECT_DIR/.env" ]; then
        cp $PROJECT_DIR/.env $BACKEND_DIR/.env
        echo -e "${GREEN}✅ .env文件已复制${NC}"
    else
        echo -e "${RED}❌ 未找到.env文件，请手动创建${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env文件已存在${NC}"
fi

echo ""

echo -e "${YELLOW}🔧 步骤5: 配置Systemd服务...${NC}"

# 复制服务文件
cp $PROJECT_DIR/deploy/quotation-api.service $SERVICE_FILE

# 重新加载systemd
systemctl daemon-reload

# 启用服务
systemctl enable quotation-api.service

echo -e "${GREEN}✅ Systemd服务配置完成${NC}"
echo ""

echo -e "${YELLOW}🌐 步骤6: 配置Nginx...${NC}"

# 复制Nginx配置
cp $PROJECT_DIR/deploy/nginx_fastapi.conf $NGINX_CONF

# 创建符号链接
ln -sf $NGINX_CONF /etc/nginx/sites-enabled/quotation-api

# 删除默认配置（如果存在）
rm -f /etc/nginx/sites-enabled/default

# 测试Nginx配置
nginx -t

# 重启Nginx
systemctl restart nginx
systemctl enable nginx

echo -e "${GREEN}✅ Nginx配置完成${NC}"
echo ""

echo -e "${YELLOW}📁 步骤7: 创建必要目录...${NC}"

# 创建临时上传和输出目录
mkdir -p $BACKEND_DIR/temp_uploads
mkdir -p $BACKEND_DIR/output

# 设置权限
chown -R root:root $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

# 确保日志目录存在
mkdir -p /var/log
touch /var/log/quotation-api.log
touch /var/log/quotation-api-error.log
touch /var/log/quotation-api-access.log
chmod 644 /var/log/quotation-api*.log

echo -e "${GREEN}✅ 目录创建完成${NC}"
echo ""

echo -e "${YELLOW}🚀 步骤8: 启动API服务...${NC}"

# 启动服务
systemctl start quotation-api.service

# 检查服务状态
sleep 3
if systemctl is-active --quiet quotation-api.service; then
    echo -e "${GREEN}✅ API服务启动成功${NC}"
else
    echo -e "${RED}❌ API服务启动失败，请检查日志${NC}"
    echo -e "${YELLOW}查看日志命令：${NC}"
    echo "   journalctl -u quotation-api.service -f"
    exit 1
fi

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}🎉 FastAPI后端部署完成！${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${YELLOW}📊 系统信息：${NC}"
echo "   后端框架: FastAPI + Gunicorn + Uvicorn"
echo "   Worker数量: 3 workers（平衡方案）"
echo "   计费模式: 包年包月"
echo "   推荐策略: NewProductFirst"
echo ""
echo -e "${YELLOW}🌐 访问地址：${NC}"
echo "   API文档: http://$(curl -s ifconfig.me)/api/docs"
echo "   健康检查: http://$(curl -s ifconfig.me)/health"
echo "   API端点: http://$(curl -s ifconfig.me)/api/v1"
echo ""
echo -e "${YELLOW}❓ 常用命令：${NC}"
echo "   启动服务: systemctl start quotation-api.service"
echo "   停止服务: systemctl stop quotation-api.service"
echo "   重启服务: systemctl restart quotation-api.service"
echo "   查看状态: systemctl status quotation-api.service"
echo "   查看日志: journalctl -u quotation-api.service -f"
echo ""
echo -e "${YELLOW}⚠️  重要提示：${NC}"
echo "   1. 确保.env文件配置了所有API密钥"
echo "   2. 确保ECS安全组开放了80端口"
echo "   3. 前端需要单独构建和部署"
echo "   4. 监控内存使用，必要时调整worker数量"
echo ""
