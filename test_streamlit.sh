#!/bin/bash
# 快速测试Streamlit应用

echo "🧪 测试Streamlit应用启动..."
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

# 检查.env
if [ ! -f ".env" ]; then
    echo "❌ .env文件不存在"
    exit 1
fi

# 检查Streamlit
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "⚠️  Streamlit未安装，安装中..."
    pip3 install streamlit
fi

echo "✅ 环境检查通过"
echo ""
echo "🚀 启动测试服务器..."
echo "📍 访问地址: http://localhost:8501"
echo "⏹️  按 Ctrl+C 停止服务"
echo ""

# 启动应用（仅用于测试，不在后台运行）
streamlit run streamlit_app.py --server.headless=true
