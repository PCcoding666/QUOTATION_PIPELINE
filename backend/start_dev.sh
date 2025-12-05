#!/bin/bash
# FastAPI开发服务器快速启动脚本

echo "🚀 启动FastAPI开发服务器..."
echo ""
echo "📋 配置信息："
echo "   - Host: 0.0.0.0"
echo "   - Port: 8000"
echo "   - 热重载: 启用"
echo ""
echo "📚 访问地址："
echo "   - API文档: http://localhost:8000/api/docs"
echo "   - ReDoc: http://localhost:8000/api/redoc"
echo "   - 健康检查: http://localhost:8000/health"
echo ""

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  未检测到虚拟环境，尝试激活..."
    if [ -f "../venv/bin/activate" ]; then
        source ../venv/bin/activate
        echo "✅ 虚拟环境已激活"
    else
        echo "❌ 未找到虚拟环境，请先创建: python3 -m venv ../venv"
        exit 1
    fi
fi

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
