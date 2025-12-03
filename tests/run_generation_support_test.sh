#!/bin/bash
# 阿里云API代际支持测试脚本
# 
# 功能：测试 DescribeRecommendInstanceType 和 GetSubscriptionPrice 
#       API 对不同代际实例的支持情况
#
# 输出：
#   - 控制台日志（详细测试过程）
#   - tests/output/api_generation_support_report.md（Markdown报告）
#   - tests/output/api_generation_support_report.html（HTML报告）

echo "========================================"
echo "阿里云API代际支持测试"
echo "========================================"
echo ""

# 检查环境变量
if [ -z "$ALIBABA_CLOUD_ACCESS_KEY_ID" ] || [ -z "$ALIBABA_CLOUD_ACCESS_KEY_SECRET" ]; then
    echo "❌ 错误: 未配置阿里云凭证环境变量"
    echo "请在 .env 文件中配置:"
    echo "  ALIBABA_CLOUD_ACCESS_KEY_ID=your_key_id"
    echo "  ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_key_secret"
    exit 1
fi

echo "✅ 环境变量检查通过"
echo ""

# 创建输出目录
mkdir -p tests/output
mkdir -p tests/data

echo "开始执行测试..."
echo ""

# 运行测试
python -m pytest tests/unit/test_api_generation_support.py \
    -v \
    -s \
    --tb=short \
    --color=yes \
    | tee tests/output/api_generation_support_test.log

TEST_EXIT_CODE=$?

echo ""
echo "========================================"
echo "测试完成"
echo "========================================"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ 测试执行成功"
else
    echo "⚠️  测试执行完成（部分失败）"
fi

echo ""
echo "输出文件："
echo "  - 测试日志: tests/output/api_generation_support_test.log"
echo "  - Markdown报告: tests/output/api_generation_support_report.md"

if [ -f "tests/output/api_generation_support_report.html" ]; then
    echo "  - HTML报告: tests/output/api_generation_support_report.html"
fi

echo ""
echo "查看报告："
echo "  cat tests/output/api_generation_support_report.md"
echo ""

exit $TEST_EXIT_CODE
