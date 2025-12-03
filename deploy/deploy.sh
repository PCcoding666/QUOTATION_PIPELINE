#!/bin/bash
# 阿里云ECS部署脚本 - 为Streamlit极简版前端优化

set -e  # 遇到错误立即退出

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}阿里云ECS报价系统 - 部署脚本${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 请使用root用户或sudo运行此脚本${NC}"
    exit 1
fi

# 项目配置
PROJECT_DIR="/root/Quotation_Pipeline"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_FILE="/etc/systemd/system/quotation-app.service"
NGINX_CONF="/etc/nginx/sites-available/quotation-app"

echo -e "${YELLOW}📦 步骤1: 安装系统依赖...${NC}"

# 更新包管理器
apt-get update -y

# 安装Python3和pip
apt-get install -y python3 python3-pip python3-venv

# 安装Nginx
apt-get install -y nginx

# 安装Git（如果需要从仓库拉取）
apt-get install -y git

echo -e "${GREEN}✅ 系统依赖安装完成${NC}"
echo ""

echo -e "${YELLOW}📁 步骤2: 准备项目目录...${NC}"

# 如果项目目录不存在，从Git克隆
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}正在从GitHub克隆项目...${NC}"
    git clone https://github.com/PCcoding666/QUOTATION_PIPELINE.git $PROJECT_DIR
else
    echo -e "${YELLOW}项目目录已存在，更新代码...${NC}"
    cd $PROJECT_DIR
    git pull
fi

cd $PROJECT_DIR

echo -e "${GREEN}✅ 项目目录准备完成${NC}"
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
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}⚠️  .env文件不存在，请手动创建${NC}"
    echo -e "${YELLOW}创建模板文件...${NC}"
    
    cat > $PROJECT_DIR/.env << 'EOF'
# Alibaba Cloud API Credentials
ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id_here
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret_here

# DashScope API Key
DASHSCOPE_API_KEY=sk-your_dashscope_api_key_here
EOF
    
    echo -e "${YELLOW}💡 请编辑 $PROJECT_DIR/.env 文件填写正确的API密钥${NC}"
    echo -e "${YELLOW}然后重新运行此脚本${NC}"
    exit 1
else
    echo -e "${GREEN}✅ .env文件已存在${NC}"
fi

echo ""

echo -e "${YELLOW}🔧 步骤5: 配置Systemd服务...${NC}"

# 复制服务文件
cp $PROJECT_DIR/deploy/quotation-app.service $SERVICE_FILE

# 重新加载systemd
systemctl daemon-reload

# 启用服务
systemctl enable quotation-app.service

echo -e "${GREEN}✅ Systemd服务配置完成${NC}"
echo ""

echo -e "${YELLOW}🌐 步骤6: 配置Nginx反向代理...${NC}"

# 复制Nginx配置
cp $PROJECT_DIR/deploy/nginx.conf $NGINX_CONF

# 创建符号链接
ln -sf $NGINX_CONF /etc/nginx/sites-enabled/quotation-app

# 删除默认配置（如果存在）
rm -f /etc/nginx/sites-enabled/default

# 测试Nginx配置
nginx -t

# 重启Nginx
systemctl restart nginx
systemctl enable nginx

echo -e "${GREEN}✅ Nginx配置完成${NC}"
echo ""

echo -e "${YELLOW}📁 步骤7: 创建必要目录...。{NC}"

# 为极简版Streamlit创建目录
mkdir -p $PROJECT_DIR/temp_uploads
mkdir -p $PROJECT_DIR/tests/output

# 设置权限
chown -R root:root $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

# 确保日志目录存在
touch /var/log/quotation-app.log
touch /var/log/quotation-app-error.log
chmod 644 /var/log/quotation-app.log
chmod 644 /var/log/quotation-app-error.log

echo -e "${GREEN}✅ 目录创建完成${NC}"
echo ""

echo -e "${YELLOW}🚀 步骤8: 启动应用...${NC}"

# 启动服务
systemctl start quotation-app.service

# 检查服务状态
sleep 3
if systemctl is-active --quiet quotation-app.service; then
    echo -e "${GREEN}✅ 应用启动成功${NC}"
else
    echo -e "${RED}❌ 应用启动失败，请检查日志${NC}"
    echo -e "${YELLOW}查看日志命令：${NC}"
    echo "   journalctl -u quotation-app.service -f"
    exit 1
fi

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}🎉 部署完成！${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${YELLOW}📊 系统信息：${NC}"
echo "   前端框架: Streamlit (极简版)"
echo "   Python版本: $(python3 --version)"
echo "   计费模式: 包年包月"
echo "   推荐策略: NewProductFirst"
echo ""
echo -e "${YELLOW}❓ 常用命令：${NC}"
echo "   启动服务: systemctl start quotation-app.service"
echo "   停止服务: systemctl stop quotation-app.service"
echo "   重启服务: systemctl restart quotation-app.service"
echo ""
echo -e "${YELLOW}👁️ 监控命令：${NC}"
echo "   服务状态: systemctl status quotation-app.service"
echo "   实时日志: journalctl -u quotation-app.service -f"
echo "   应用日志: tail -f /var/log/quotation-app.log"
echo "   错误日志: tail -f /var/log/quotation-app-error.log"
echo ""
echo -e "${YELLOW}🌐 访问地址：${NC}"
echo "   HTTP: http://$(curl -s ifconfig.me)"
echo "   端口: 80"
echo ""
echo ""
echo -e "${YELLOW}⚠️  重要提示：${NC}"
echo "   1. 确保.env文件配置了所有API密钥"
echo "   2. 确保ECS安全组开放了80端口"
echo "   3. 如需HTTPS，请配置SSL证书"
echo "   4. 定期检查应用日志和系统资源"
echo ""
