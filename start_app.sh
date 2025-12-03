#!/bin/bash
# 启动Streamlit应用 - 极简版前端

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}阿里云ECS智能报价系统${NC}"
echo -e "${GREEN}Streamlit极简版前端${NC}"
echo -e "${GREEN}=================================${NC}"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3未安装，请先安装Python3${NC}"
    exit 1
fi

echo -e "${YELLOW}🔍 检查环境...${NC}"

# 检查.env文件
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env文件不存在${NC}"
    echo -e "${YELLOW}💡 请创建.env文件并配置以下环境变量：${NC}"
    echo "   ALIBABA_CLOUD_ACCESS_KEY_ID=your_key_id"
    echo "   ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_key_secret"
    echo "   DASHSCOPE_API_KEY=your_dashscope_key"
    exit 1
fi

# 检查Streamlit是否安装
if ! python3 -c "import streamlit" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Streamlit未安装，正在安装依赖...。{NC}"
    pip3 install -r requirements.txt
fi

# 检查LLMDrivenExcelLoader所需的包
if ! python3 -c "import dashscope" &> /dev/null; then
    echo -e "${YELLOW}⚠️  dashscope未安装，正在安装...。{NC}"
    pip3 install dashscope
fi

# 创建必要的目录
echo -e "${YELLOW}📁 创建必要目录...${NC}"
mkdir -p temp_uploads
mkdir -p tests/output

echo -e "${GREEN}✅ 环境检查完成${NC}"
echo ""
echo -e "${YELLOW}🚀 启动应用...。{NC}"
echo -e "${YELLOW}📍 访问地址: http://localhost:8501${NC}"
echo -e "${YELLOW}💡 提示: 按Ctrl+C停止应用${NC}"
echo ""

# 启动Streamlit
streamlit run streamlit_app.py
