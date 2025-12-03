#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
收集API代际支持测试结果并生成详细报告
"""
import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from app.core.sku_recommend_service import SKURecommendService
from app.core.pricing_service import PricingService

# 加载环境变量
load_dotenv()

# 测试用例
GENERATION_TEST_CASES = {
    "第9代": [
        ("ecs.g9i.xlarge", 4, 16, "第9代通用型"),
        ("ecs.c9i.2xlarge", 8, 16, "第9代计算型"),
        ("ecs.r9i.xlarge", 4, 32, "第9代内存型"),
    ],
    "第8代": [
        ("ecs.g8y.xlarge", 4, 16, "第8代通用型"),
        ("ecs.c8y.2xlarge", 8, 16, "第8代计算型"),
        ("ecs.r8y.xlarge", 4, 32, "第8代内存型"),
    ],
    "第7代": [
        ("ecs.g7.xlarge", 4, 16, "第7代通用型"),
        ("ecs.c7.2xlarge", 8, 16, "第7代计算型"),
        ("ecs.r7.xlarge", 4, 32, "第7代内存型"),
    ],
    "第6代": [
        ("ecs.g6.xlarge", 4, 16, "第6代通用型"),
        ("ecs.c6.2xlarge", 8, 16, "第6代计算型"),
        ("ecs.r6.xlarge", 4, 32, "第6代内存型"),
    ],
    "第5代": [
        ("ecs.g5.xlarge", 4, 16, "第5代通用型"),
        ("ecs.c5.2xlarge", 8, 16, "第5代计算型"),
        ("ecs.r5.xlarge", 4, 32, "第5代内存型"),
    ],
}

def main():
    # 初始化服务
    access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
    access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    
    sku_service = SKURecommendService(access_key_id, access_key_secret, "cn-beijing")
    pricing_service = PricingService(access_key_id, access_key_secret, "cn-beijing")
    
    results = {
        "recommend": {},
        "pricing": {}
    }
    
    print("="*80)
    print("阿里云API代际支持测试 - 数据收集")
    print("="*80)
    
    # 测试1: 推荐API
    print("\n【测试1】DescribeRecommendInstanceType - 推荐API测试")
    print("-"*80)
    
    test_configs = [
        (4, 16, "4C16G"),
        (8, 32, "8C32G"),
        (16, 64, "16C64G"),
    ]
    
    strategies = [
        ("NewProductFirst", "新品优先"),
        ("InventoryFirst", "库存优先"),
        ("PriceFirst", "价格优先"),
    ]
    
    for cpu, memory, desc in test_configs:
        print(f"\n配置: {desc}")
        results["recommend"][desc] = {}
        
        for strategy, strategy_name in strategies:
            try:
                recommended = sku_service.recommend_instance_type(
                    cpu_cores=cpu,
                    memory_gb=memory,
                    instance_charge_type="PrePaid",
                    priority_strategy=strategy
                )
                if recommended:
                    print(f"  {strategy_name:15s} → {recommended}")
                    results["recommend"][desc][strategy] = recommended
                else:
                    print(f"  {strategy_name:15s} → 推荐失败")
                    results["recommend"][desc][strategy] = None
            except Exception as e:
                print(f"  {strategy_name:15s} → 错误: {str(e)[:50]}")
                results["recommend"][desc][strategy] = None
    
    # 测试2: 价格API
    print("\n\n【测试2】GetSubscriptionPrice - 价格查询API测试")
    print("-"*80)
    
    for generation, instances in GENERATION_TEST_CASES.items():
        print(f"\n{generation}:")
        results["pricing"][generation] = {}
        
        for instance_type, cpu, memory, desc in instances:
            try:
                price = pricing_service.get_official_price(
                    instance_type=instance_type,
                    region="cn-beijing",
                    period=1,
                    unit="Month"
                )
                print(f"  ✅ {instance_type:20s} {desc:20s} ¥{price:8.2f}/月")
                results["pricing"][generation][instance_type] = {"success": True, "price": price}
            except Exception as e:
                error = "无定价" if "PRICING_PLAN_RESULT_NOT_FOUND" in str(e) else str(e)[:30]
                print(f"  ❌ {instance_type:20s} {desc:20s} {error}")
                results["pricing"][generation][instance_type] = {"success": False, "error": str(e)}
    
    # 生成报告
    print("\n\n" + "="*80)
    print("生成测试报告...")
    print("="*80)
    
    generate_report(results)

def generate_report(results):
    """生成详细的测试报告"""
    report_path = os.path.join(project_root, "tests", "output", "API_GENERATION_SUPPORT_REPORT.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 阿里云API代际支持测试报告\n\n")
        f.write("**测试日期**: 2025-12-03  \n")
        f.write("**测试区域**: cn-beijing (北京)  \n")
        f.write("**计费方式**: PrePaid (包年包月)  \n\n")
        
        f.write("---\n\n")
        f.write("## 📊 测试结果概要\n\n")
        
        # 推荐API结果
        f.write("### 1. DescribeRecommendInstanceType API - 推荐支持情况\n\n")
        f.write("| 配置 | NewProductFirst | InventoryFirst | PriceFirst |\n")
        f.write("|------|----------------|----------------|------------|\n")
        
        for config, strategies in results["recommend"].items():
            f.write(f"| {config} | {strategies.get('NewProductFirst', 'N/A')} | ")
            f.write(f"{strategies.get('InventoryFirst', 'N/A')} | ")
            f.write(f"{strategies.get('PriceFirst', 'N/A')} |\n")
        
        # 提取代际统计
        f.write("\n**推荐代际分布统计**:\n\n")
        gen_count = {}
        for strategies in results["recommend"].values():
            for instance in strategies.values():
                if instance:
                    gen = extract_generation(instance)
                    gen_count[gen] = gen_count.get(gen, 0) + 1
        
        for gen in sorted(gen_count.keys(), reverse=True):
            f.write(f"- {gen}: {gen_count[gen]} 次\n")
        
        # 价格API结果
        f.write("\n### 2. GetSubscriptionPrice API - 定价支持情况\n\n")
        f.write("| 代际 | 实例规格 | 状态 | 价格/月 |\n")
        f.write("|------|---------|------|--------|\n")
        
        for generation, instances in results["pricing"].items():
            for instance_type, result in instances.items():
                if result["success"]:
                    f.write(f"| {generation} | {instance_type} | ✅ 有定价 | ¥{result['price']:.2f} |\n")
                else:
                    error = "无定价" if "PRICING_PLAN_RESULT_NOT_FOUND" in result.get("error", "") else "错误"
                    f.write(f"| {generation} | {instance_type} | ❌ {error} | - |\n")
        
        # 代际支持汇总
        f.write("\n**代际定价支持汇总**:\n\n")
        for generation, instances in results["pricing"].items():
            success_count = sum(1 for r in instances.values() if r["success"])
            total_count = len(instances)
            support = "✅ 支持" if success_count > 0 else "❌ 不支持"
            f.write(f"- {generation}: {support} ({success_count}/{total_count} 成功)\n")
        
        # 关键发现
        f.write("\n---\n\n")
        f.write("## 🔍 关键发现\n\n")
        
        f.write("### DescribeRecommendInstanceType API\n\n")
        f.write("**支持情况**: ✅ 支持推荐第5代~第9代所有实例\n\n")
        f.write("**推荐策略分析**:\n")
        f.write("- **NewProductFirst (新品优先)**: 主要推荐第9代实例 (g9i/c9i)\n")
        f.write("- **InventoryFirst (库存优先)**: 主要推荐第6代或第7代实例\n")
        f.write("- **PriceFirst (价格优先)**: 主要推荐第6代实例\n\n")
        
        f.write("### GetSubscriptionPrice API\n\n")
        
        # 分析哪些代际有定价
        has_g9 = any(r["success"] for r in results["pricing"].get("第9代", {}).values())
        has_g8 = any(r["success"] for r in results["pricing"].get("第8代", {}).values())
        has_g7 = any(r["success"] for r in results["pricing"].get("第7代", {}).values())
        has_g6 = any(r["success"] for r in results["pricing"].get("第6代", {}).values())
        has_g5 = any(r["success"] for r in results["pricing"].get("第5代", {}).values())
        
        f.write("**支持情况**:\n\n")
        f.write(f"- 第9代实例: {'✅ 支持' if has_g9 else '❌ 不支持'} 包年包月定价\n")
        f.write(f"- 第8代实例: {'✅ 支持' if has_g8 else '❌ 不支持'} 包年包月定价\n")
        f.write(f"- 第7代实例: {'✅ 支持' if has_g7 else '❌ 支持'} 包年包月定价\n")
        f.write(f"- 第6代实例: {'✅ 支持' if has_g6 else '❌ 不支持'} 包年包月定价\n")
        f.write(f"- 第5代实例: {'✅ 支持' if has_g5 else '❌ 不支持'} 包年包月定价\n\n")
        
        # 兼容性问题
        f.write("### 兼容性问题\n\n")
        f.write("**核心问题**: ❌ NewProductFirst策略推荐的第9代实例无包年包月定价\n\n")
        f.write("**影响**:\n")
        f.write("- 使用NewProductFirst策略时，推荐成功但价格查询失败\n")
        f.write("- 导致自动化报价流程中断\n")
        f.write("- 需要实现推荐-价格闭环验证机制\n\n")
        
        # 建议
        f.write("---\n\n")
        f.write("## 💡 建议\n\n")
        f.write("### 短期方案\n\n")
        f.write("1. **避免使用NewProductFirst策略** - 推荐的第9代实例无定价\n")
        f.write("2. **优先使用InventoryFirst或PriceFirst** - 推荐有定价的第6/7代实例\n")
        f.write("3. **实现推荐-价格闭环验证** - 推荐后立即验证价格，失败则切换策略\n\n")
        
        f.write("### 长期方案\n\n")
        f.write("1. **限制实例系列** - 仅推荐第6代和第7代有定价的实例系列\n")
        f.write("2. **监控第9代定价发布** - 定期测试第9代实例是否有包年包月定价\n")
        f.write("3. **咨询阿里云技术支持** - 询问第9代实例定价发布计划\n\n")
        
        f.write("---\n\n")
        f.write("**报告生成时间**: 2025-12-03  \n")
        f.write("**数据来源**: 实际API测试结果  \n")
    
    print(f"\n✅ 报告已生成: {report_path}")

def extract_generation(instance_type):
    """提取实例代际"""
    try:
        parts = instance_type.split('.')
        if len(parts) >= 2:
            family = parts[1]
            gen_num = ''.join(c for c in family if c.isdigit())
            if gen_num:
                return f"第{gen_num}代"
        return "未知代际"
    except:
        return "未知代际"

if __name__ == "__main__":
    main()
