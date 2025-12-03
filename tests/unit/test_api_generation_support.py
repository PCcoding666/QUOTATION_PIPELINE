# -*- coding: utf-8 -*-
"""
单元测试：验证阿里云API对不同代际实例的支持情况

测试目标：
1. DescribeRecommendInstanceType API 支持到哪个代际的推荐
2. GetSubscriptionPrice API 支持到哪些代际的哪些实例的价格查询

测试方法：
- 测试第5代到第9代的典型实例规格
- 测试通用型(g系列)、计算型(c系列)、内存型(r系列)
- 记录推荐成功和价格查询成功的实例

创建日期：2025-12-03
"""

import os
import sys
import pytest
import logging
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app.core.sku_recommend_service import SKURecommendService
from app.core.pricing_service import PricingService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


# 测试用例定义：不同代际的典型实例规格
# 格式：{代际: [(实例规格, CPU核数, 内存GB, 实例类型说明), ...]}
GENERATION_TEST_CASES = {
    "第9代": [
        ("ecs.g9i.xlarge", 4, 16, "第9代通用型"),
        ("ecs.c9i.2xlarge", 8, 16, "第9代计算型"),
        ("ecs.r9i.xlarge", 4, 32, "第9代内存型"),
        ("ecs.c9ae.2xlarge", 8, 16, "第9代ARM计算型"),
    ],
    "第8代": [
        ("ecs.g8y.xlarge", 4, 16, "第8代通用型"),
        ("ecs.c8y.2xlarge", 8, 16, "第8代计算型"),
        ("ecs.r8y.xlarge", 4, 32, "第8代内存型"),
        ("ecs.g8i.xlarge", 4, 16, "第8代Intel通用型"),
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


@pytest.fixture(scope="module")
def sku_service():
    """初始化 SKU 推荐服务"""
    access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
    access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    
    if not access_key_id or not access_key_secret:
        pytest.skip("未配置阿里云凭证，跳过测试")
    
    return SKURecommendService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id="cn-beijing"
    )


@pytest.fixture(scope="module")
def pricing_service():
    """初始化价格查询服务"""
    access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
    access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    
    if not access_key_id or not access_key_secret:
        pytest.skip("未配置阿里云凭证，跳过测试")
    
    return PricingService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id="cn-beijing"
    )


class TestDescribeRecommendInstanceTypeSupport:
    """测试 DescribeRecommendInstanceType API 对不同代际的支持"""
    
    def test_recommend_by_generation(self, sku_service):
        """
        测试：通过CPU和内存规格推荐，验证API能推荐到哪个代际的实例
        
        测试策略：
        - 使用不同的推荐策略（NewProductFirst, InventoryFirst, PriceFirst）
        - 测试典型的CPU/内存配置
        - 记录实际推荐的实例代际
        """
        logger.info("\n" + "="*80)
        logger.info("测试1：DescribeRecommendInstanceType API - 代际支持情况")
        logger.info("="*80)
        
        # 测试配置
        test_configs = [
            (4, 16, "4C16G - 小规格"),
            (8, 32, "8C32G - 中规格"),
            (16, 64, "16C64G - 大规格"),
        ]
        
        strategies = [
            ("NewProductFirst", "新品优先"),
            ("InventoryFirst", "库存优先"),
            ("PriceFirst", "价格优先"),
        ]
        
        results = {}
        
        for cpu, memory, desc in test_configs:
            logger.info(f"\n{'─'*60}")
            logger.info(f"📊 测试配置: {desc}")
            logger.info(f"{'─'*60}")
            
            config_results = {}
            
            for strategy, strategy_name in strategies:
                logger.info(f"\n🔍 策略: {strategy_name} ({strategy})")
                
                try:
                    recommended = sku_service.recommend_instance_type(
                        cpu_cores=cpu,
                        memory_gb=memory,
                        instance_charge_type="PrePaid",
                        priority_strategy=strategy
                    )
                    
                    if recommended:
                        # 提取代际信息
                        generation = self._extract_generation(recommended)
                        logger.info(f"✅ 推荐成功: {recommended} ({generation})")
                        config_results[strategy] = {
                            "success": True,
                            "instance": recommended,
                            "generation": generation
                        }
                    else:
                        logger.warning(f"⚠️  未返回推荐结果")
                        config_results[strategy] = {
                            "success": False,
                            "error": "未返回推荐结果"
                        }
                        
                except Exception as e:
                    logger.error(f"❌ 推荐失败: {str(e)}")
                    config_results[strategy] = {
                        "success": False,
                        "error": str(e)
                    }
            
            results[desc] = config_results
        
        # 汇总结果
        self._print_recommend_summary(results)
        
        # 至少应该有一些配置推荐成功
        assert any(
            any(r.get("success", False) for r in config.values())
            for config in results.values()
        ), "所有配置的所有策略都推荐失败"
    
    def _extract_generation(self, instance_type: str) -> str:
        """从实例规格中提取代际信息"""
        # 示例: "ecs.g7.xlarge" -> "第7代"
        # 示例: "ecs.g9i.xlarge" -> "第9代"
        try:
            parts = instance_type.split('.')
            if len(parts) >= 2:
                family = parts[1]  # g7, g9i, c8y等
                # 提取数字
                gen_num = ''.join(c for c in family if c.isdigit())
                if gen_num:
                    return f"第{gen_num}代"
            return "未知代际"
        except:
            return "未知代际"
    
    def _print_recommend_summary(self, results: Dict):
        """打印推荐结果汇总"""
        logger.info("\n" + "="*80)
        logger.info("📊 DescribeRecommendInstanceType API 代际支持汇总")
        logger.info("="*80)
        
        # 统计各代际推荐次数
        generation_count = {}
        
        for config_name, strategies in results.items():
            logger.info(f"\n配置: {config_name}")
            for strategy, result in strategies.items():
                if result.get("success"):
                    gen = result.get("generation", "未知")
                    instance = result.get("instance", "N/A")
                    logger.info(f"  {strategy:20s} → {instance:20s} ({gen})")
                    
                    # 统计
                    generation_count[gen] = generation_count.get(gen, 0) + 1
                else:
                    error = result.get("error", "未知错误")
                    logger.info(f"  {strategy:20s} → ❌ {error}")
        
        # 打印代际统计
        logger.info("\n" + "─"*60)
        logger.info("代际推荐统计:")
        for gen in sorted(generation_count.keys(), reverse=True):
            count = generation_count[gen]
            logger.info(f"  {gen}: {count} 次")
        logger.info("─"*60)


class TestGetSubscriptionPriceSupport:
    """测试 GetSubscriptionPrice API 对不同代际实例的支持"""
    
    def test_price_query_by_generation(self, pricing_service):
        """
        测试：查询不同代际实例的包年包月价格
        
        测试目标：
        - 验证哪些代际的哪些实例有包年包月定价
        - 记录价格查询成功和失败的实例
        """
        logger.info("\n" + "="*80)
        logger.info("测试2：GetSubscriptionPrice API - 代际支持情况")
        logger.info("="*80)
        
        results = {}
        
        for generation, instances in GENERATION_TEST_CASES.items():
            logger.info(f"\n{'─'*60}")
            logger.info(f"📊 测试代际: {generation}")
            logger.info(f"{'─'*60}")
            
            gen_results = []
            
            for instance_type, cpu, memory, desc in instances:
                logger.info(f"\n🔍 测试实例: {instance_type} ({desc}) - {cpu}C {memory}G")
                
                try:
                    price = pricing_service.get_official_price(
                        instance_type=instance_type,
                        region="cn-beijing",
                        period=1,
                        unit="Month"
                    )
                    
                    logger.info(f"✅ 价格查询成功: ¥{price:.2f} CNY/月")
                    gen_results.append({
                        "instance": instance_type,
                        "description": desc,
                        "success": True,
                        "price": price
                    })
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ 价格查询失败: {error_msg}")
                    gen_results.append({
                        "instance": instance_type,
                        "description": desc,
                        "success": False,
                        "error": error_msg
                    })
            
            results[generation] = gen_results
        
        # 汇总结果
        self._print_pricing_summary(results)
        
        # 验证：至少第6代和第7代应该有定价
        has_g6_pricing = any(
            r.get("success", False) 
            for r in results.get("第6代", [])
        )
        has_g7_pricing = any(
            r.get("success", False) 
            for r in results.get("第7代", [])
        )
        
        assert has_g6_pricing or has_g7_pricing, "第6代和第7代都没有定价数据"
    
    def _print_pricing_summary(self, results: Dict):
        """打印价格查询结果汇总"""
        logger.info("\n" + "="*80)
        logger.info("📊 GetSubscriptionPrice API 代际支持汇总")
        logger.info("="*80)
        
        for generation in sorted(results.keys(), key=lambda x: x, reverse=True):
            gen_results = results[generation]
            success_count = sum(1 for r in gen_results if r.get("success"))
            total_count = len(gen_results)
            
            logger.info(f"\n{generation}: {success_count}/{total_count} 成功")
            logger.info("─"*60)
            
            for result in gen_results:
                instance = result["instance"]
                desc = result["description"]
                
                if result.get("success"):
                    price = result.get("price", 0)
                    logger.info(f"  ✅ {instance:25s} {desc:20s} ¥{price:8.2f}/月")
                else:
                    error = result.get("error", "未知错误")
                    # 简化错误信息
                    if "PRICING_PLAN_RESULT_NOT_FOUND" in error:
                        error = "无定价方案"
                    elif "InvalidParameter" in error:
                        error = "参数无效"
                    logger.info(f"  ❌ {instance:25s} {desc:20s} {error}")


class TestRecommendAndPricingIntegration:
    """测试推荐和价格查询的集成兼容性"""
    
    def test_recommend_pricing_compatibility(self, sku_service, pricing_service):
        """
        测试：推荐的实例是否有对应的包年包月定价
        
        核心问题：
        - 推荐成功但价格查询失败的实例有哪些？
        - 哪些代际存在推荐成功但无定价的问题？
        """
        logger.info("\n" + "="*80)
        logger.info("测试3：推荐-价格查询兼容性测试")
        logger.info("="*80)
        
        # 测试配置
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
        
        compatibility_results = []
        
        for cpu, memory, desc in test_configs:
            logger.info(f"\n{'─'*60}")
            logger.info(f"📊 测试配置: {desc}")
            logger.info(f"{'─'*60}")
            
            for strategy, strategy_name in strategies:
                logger.info(f"\n🔍 策略: {strategy_name}")
                
                # Step 1: 推荐实例
                try:
                    recommended = sku_service.recommend_instance_type(
                        cpu_cores=cpu,
                        memory_gb=memory,
                        instance_charge_type="PrePaid",
                        priority_strategy=strategy
                    )
                    
                    if not recommended:
                        logger.warning(f"⚠️  推荐失败：未返回结果")
                        compatibility_results.append({
                            "config": desc,
                            "strategy": strategy_name,
                            "recommend_success": False,
                            "pricing_success": False,
                            "compatible": False,
                            "error": "推荐失败"
                        })
                        continue
                    
                    logger.info(f"✅ 推荐成功: {recommended}")
                    
                    # Step 2: 查询价格
                    try:
                        price = pricing_service.get_official_price(
                            instance_type=recommended,
                            region="cn-beijing",
                            period=1,
                            unit="Month"
                        )
                        
                        logger.info(f"✅ 价格查询成功: ¥{price:.2f} CNY/月")
                        logger.info(f"🎉 兼容性验证通过: {recommended} 可推荐且有定价")
                        
                        compatibility_results.append({
                            "config": desc,
                            "strategy": strategy_name,
                            "instance": recommended,
                            "recommend_success": True,
                            "pricing_success": True,
                            "compatible": True,
                            "price": price
                        })
                        
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(f"❌ 价格查询失败: {error_msg}")
                        logger.warning(f"⚠️  兼容性问题: {recommended} 可推荐但无定价")
                        
                        compatibility_results.append({
                            "config": desc,
                            "strategy": strategy_name,
                            "instance": recommended,
                            "recommend_success": True,
                            "pricing_success": False,
                            "compatible": False,
                            "error": error_msg
                        })
                    
                except Exception as e:
                    logger.error(f"❌ 推荐失败: {str(e)}")
                    compatibility_results.append({
                        "config": desc,
                        "strategy": strategy_name,
                        "recommend_success": False,
                        "pricing_success": False,
                        "compatible": False,
                        "error": str(e)
                    })
        
        # 汇总兼容性结果
        self._print_compatibility_summary(compatibility_results)
        
        # 验证：至少应该有一些配置是兼容的
        compatible_count = sum(1 for r in compatibility_results if r.get("compatible"))
        assert compatible_count > 0, "没有任何推荐实例有定价数据"
    
    def _print_compatibility_summary(self, results: List[Dict]):
        """打印兼容性测试汇总"""
        logger.info("\n" + "="*80)
        logger.info("📊 推荐-价格查询兼容性汇总")
        logger.info("="*80)
        
        # 统计
        total = len(results)
        compatible = sum(1 for r in results if r.get("compatible"))
        incompatible = sum(1 for r in results if r.get("recommend_success") and not r.get("pricing_success"))
        recommend_failed = sum(1 for r in results if not r.get("recommend_success"))
        
        logger.info(f"\n总测试数: {total}")
        logger.info(f"✅ 兼容（推荐成功 + 有定价）: {compatible} ({compatible/total*100:.1f}%)")
        logger.info(f"⚠️  不兼容（推荐成功 + 无定价）: {incompatible} ({incompatible/total*100:.1f}%)")
        logger.info(f"❌ 推荐失败: {recommend_failed} ({recommend_failed/total*100:.1f}%)")
        
        # 详细列表
        logger.info("\n" + "─"*60)
        logger.info("兼容的实例（推荐成功 + 有定价）:")
        logger.info("─"*60)
        for r in results:
            if r.get("compatible"):
                logger.info(
                    f"  {r['config']:10s} | {r['strategy']:15s} | "
                    f"{r['instance']:20s} | ¥{r.get('price', 0):.2f}/月"
                )
        
        logger.info("\n" + "─"*60)
        logger.info("不兼容的实例（推荐成功 + 无定价）:")
        logger.info("─"*60)
        for r in results:
            if r.get("recommend_success") and not r.get("pricing_success"):
                error = r.get("error", "")
                if "PRICING_PLAN_RESULT_NOT_FOUND" in error:
                    error = "无定价方案"
                logger.info(
                    f"  {r['config']:10s} | {r['strategy']:15s} | "
                    f"{r['instance']:20s} | {error}"
                )


def test_generate_markdown_report(sku_service, pricing_service):
    """
    生成Markdown格式的测试报告
    
    输出文件：tests/output/api_generation_support_report.md
    """
    # 确保输出目录存在
    output_dir = os.path.join(project_root, "tests", "output")
    os.makedirs(output_dir, exist_ok=True)
    
    report_path = os.path.join(output_dir, "api_generation_support_report.md")
    
    logger.info(f"\n生成测试报告: {report_path}")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 阿里云API代际支持测试报告\n\n")
        f.write(f"**测试日期**: 2025-12-03  \n")
        f.write(f"**测试区域**: cn-beijing (北京)  \n")
        f.write(f"**计费方式**: PrePaid (包年包月)  \n\n")
        
        f.write("---\n\n")
        f.write("## 测试目标\n\n")
        f.write("1. 验证 `DescribeRecommendInstanceType` API 支持推荐到哪个代际的实例\n")
        f.write("2. 验证 `GetSubscriptionPrice` API 支持查询哪些代际实例的包年包月定价\n")
        f.write("3. 测试推荐实例与价格查询的兼容性\n\n")
        
        f.write("---\n\n")
        f.write("## 测试结果\n\n")
        f.write("*详细测试日志请查看测试执行输出*\n\n")
        
        f.write("### 关键发现\n\n")
        f.write("根据测试结果，请在上述测试执行完成后手动填写以下内容：\n\n")
        f.write("1. **DescribeRecommendInstanceType API**:\n")
        f.write("   - [ ] 支持推荐第9代实例（g9i/c9i/r9i）\n")
        f.write("   - [ ] 支持推荐第8代实例（g8y/c8y/r8y）\n")
        f.write("   - [ ] 支持推荐第7代实例（g7/c7/r7）\n")
        f.write("   - [ ] 支持推荐第6代实例（g6/c6/r6）\n\n")
        
        f.write("2. **GetSubscriptionPrice API**:\n")
        f.write("   - [ ] 支持查询第9代实例价格\n")
        f.write("   - [ ] 支持查询第8代实例价格\n")
        f.write("   - [ ] 支持查询第7代实例价格\n")
        f.write("   - [ ] 支持查询第6代实例价格\n\n")
        
        f.write("3. **兼容性问题**:\n")
        f.write("   - [ ] 存在推荐成功但无定价的实例\n")
        f.write("   - [ ] 具体不兼容的代际：______\n\n")
        
        f.write("---\n\n")
        f.write("## 测试用例\n\n")
        
        for generation, instances in GENERATION_TEST_CASES.items():
            f.write(f"### {generation}\n\n")
            f.write("| 实例规格 | 说明 | CPU | 内存 |\n")
            f.write("|---------|------|-----|------|\n")
            for instance_type, cpu, memory, desc in instances:
                f.write(f"| {instance_type} | {desc} | {cpu}C | {memory}G |\n")
            f.write("\n")
    
    logger.info(f"✅ 报告已生成: {report_path}")
    

if __name__ == "__main__":
    # 运行测试并生成报告
    pytest.main([
        __file__,
        "-v",
        "-s",
        "--tb=short",
        f"--html={os.path.join(project_root, 'tests/output/api_generation_support_report.html')}",
        "--self-contained-html"
    ])
