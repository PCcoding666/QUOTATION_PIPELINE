# -*- coding: utf-8 -*-
"""
单元测试：验证 DescribePrice API 对不同代际实例的支持情况

测试目标：
验证 DescribePrice API 是否支持所有代际实例的价格查询，包括最新的第9代

API文档：https://help.aliyun.com/zh/ecs/developer-reference/api-ecs-2014-05-26-describeprice

测试方法：
- 测试第5代到第9代的典型实例规格
- 测试通用型(g系列)、计算型(c系列)、内存型(r系列)
- 对比 GetSubscriptionPrice 和 DescribePrice 的支持范围

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

from alibabacloud_ecs20140526 import models as ecs_models
from alibabacloud_ecs20140526.client import Client as EcsClient
from alibabacloud_tea_openapi import models as open_api_models

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


@pytest.fixture(scope="module")
def ecs_client():
    """初始化 ECS 客户端"""
    access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
    access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    
    if not access_key_id or not access_key_secret:
        pytest.skip("未配置阿里云凭证，跳过测试")
    
    config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id="cn-beijing",
        endpoint="ecs.cn-beijing.aliyuncs.com"
    )
    
    return EcsClient(config)


class TestDescribePriceAPI:
    """测试 DescribePrice API 对不同代际实例的支持"""
    
    def test_describe_price_by_generation(self, ecs_client):
        """
        测试：DescribePrice API 对不同代际实例的价格查询支持
        
        测试目标：
        1. 验证是否支持第7/8/9代实例的价格查询
        2. 对比 GetSubscriptionPrice API 的支持范围
        3. 确定是否可以作为 GetSubscriptionPrice 的替代方案
        """
        logger.info("\n" + "="*80)
        logger.info("测试：DescribePrice API - 代际支持情况")
        logger.info("="*80)
        
        results = {}
        
        for generation, instances in GENERATION_TEST_CASES.items():
            logger.info(f"\n{'─'*60}")
            logger.info(f"📊 测试代际: {generation}")
            logger.info(f"{'─'*60}")
            
            generation_results = []
            
            for instance_type, cpu, memory, desc in instances:
                logger.info(f"\n🔍 测试实例: {instance_type} ({desc})")
                logger.info(f"   配置: {cpu}C {memory}G")
                
                try:
                    # 调用 DescribePrice API
                    price = self._query_price_via_describe_price(
                        ecs_client, 
                        instance_type, 
                        "cn-beijing"
                    )
                    
                    logger.info(f"✅ 价格查询成功")
                    logger.info(f"   包年包月价格: ¥{price:.2f} CNY/月")
                    
                    generation_results.append({
                        "instance_type": instance_type,
                        "description": desc,
                        "success": True,
                        "price": price,
                        "error": None
                    })
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ 价格查询失败: {error_msg}")
                    
                    generation_results.append({
                        "instance_type": instance_type,
                        "description": desc,
                        "success": False,
                        "price": None,
                        "error": error_msg
                    })
            
            results[generation] = generation_results
        
        # 打印汇总报告
        self._print_summary(results)
        
        # 保存详细报告
        self._save_report(results)
        
        # 验证至少有一些实例能查询到价格
        total_success = sum(
            sum(1 for r in gen_results if r["success"])
            for gen_results in results.values()
        )
        
        assert total_success > 0, "所有实例的价格查询都失败了"
        
        logger.info(f"\n✅ 测试完成，成功查询价格的实例数: {total_success}")
    
    def _query_price_via_describe_price(
        self, 
        client: EcsClient, 
        instance_type: str, 
        region: str
    ) -> float:
        """
        使用 DescribePrice API 查询实例价格
        
        参数：
            client: ECS客户端
            instance_type: 实例规格，如 "ecs.g9i.xlarge"
            region: 区域ID，如 "cn-beijing"
        
        返回：
            float: 包年包月月价格（CNY）
        """
        # 根据实例代际选择合适的系统盘类型
        system_disk_category = self._get_system_disk_category(instance_type)
        
        # 创建系统盘配置
        system_disk = ecs_models.DescribePriceRequestSystemDisk(
            category=system_disk_category,
            size=40  # 默认40GB
        )
        
        # 创建数据盘配置（可选）
        data_disks = [
            ecs_models.DescribePriceRequestDataDisk(
                category=system_disk_category,
                size=100  # 默认100GB数据盘
            )
        ]
        
        request = ecs_models.DescribePriceRequest(
            region_id=region,
            resource_type="instance",
            instance_type=instance_type,
            price_unit="Month",
            period=1,
            # 包年包月相关参数
            instance_network_type="vpc",
            io_optimized="optimized",
            # 系统盘配置（必需）
            system_disk=system_disk,
            # 数据盘配置（可选）
            data_disk=data_disks
        )
        
        response = client.describe_price(request)
        
        # 提取价格信息
        if response.body.price_info and response.body.price_info.price:
            original_price = float(response.body.price_info.price.original_price)
            return original_price
        else:
            raise Exception("API返回成功但没有价格数据")
    
    def _get_system_disk_category(self, instance_type: str) -> str:
        """
        根据实例类型返回推荐的系统盘类型
        
        不同代际的实例支持不同的云盘类型：
        - 第7代及以上：推荐使用 cloud_essd (ESSD云盘)
        - 第6代：cloud_efficiency 或 cloud_ssd
        - 第5代：cloud_efficiency 或 cloud_ssd
        """
        # 提取代际信息
        if '.g9' in instance_type or '.c9' in instance_type or '.r9' in instance_type:
            # 第9代实例，使用ESSD云盘
            return 'cloud_essd'
        elif '.g8' in instance_type or '.c8' in instance_type or '.r8' in instance_type:
            # 第8代实例，使用ESSD云盘
            return 'cloud_essd'
        elif '.g7' in instance_type or '.c7' in instance_type or '.r7' in instance_type:
            # 第7代实例，使用ESSD云盘
            return 'cloud_essd'
        elif '.g6' in instance_type or '.c6' in instance_type or '.r6' in instance_type:
            # 第6代实例，使用高效云盘或SSD云盘
            return 'cloud_efficiency'
        else:
            # 第5代及其他，使用高效云盘
            return 'cloud_efficiency'
    
    def _print_summary(self, results: Dict):
        """打印测试结果汇总"""
        logger.info("\n" + "="*80)
        logger.info("测试结果汇总")
        logger.info("="*80)
        
        for generation, gen_results in results.items():
            total = len(gen_results)
            success = sum(1 for r in gen_results if r["success"])
            fail = total - success
            success_rate = (success / total * 100) if total > 0 else 0
            
            status = "✅ 完全支持" if success == total else \
                     "⚠️ 部分支持" if success > 0 else \
                     "❌ 不支持"
            
            logger.info(f"\n{generation}: {status}")
            logger.info(f"  测试实例数: {total}")
            logger.info(f"  成功查询: {success}")
            logger.info(f"  查询失败: {fail}")
            logger.info(f"  成功率: {success_rate:.1f}%")
            
            # 列出成功的实例
            if success > 0:
                logger.info(f"  成功实例:")
                for r in gen_results:
                    if r["success"]:
                        logger.info(f"    ✅ {r['instance_type']}: ¥{r['price']:.2f}/月")
            
            # 列出失败的实例
            if fail > 0:
                logger.info(f"  失败实例:")
                for r in gen_results:
                    if not r["success"]:
                        logger.info(f"    ❌ {r['instance_type']}: {r['error']}")
    
    def _save_report(self, results: Dict):
        """保存详细测试报告到文件"""
        output_dir = os.path.join(project_root, "tests", "output")
        os.makedirs(output_dir, exist_ok=True)
        
        report_path = os.path.join(output_dir, "DESCRIBE_PRICE_API_TEST_REPORT.md")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# DescribePrice API 代际支持测试报告\n\n")
            f.write("**测试日期**: 2025-12-03\n")
            f.write("**测试区域**: cn-beijing\n")
            f.write("**API**: DescribePrice (ECS)\n\n")
            f.write("---\n\n")
            
            f.write("## 测试目标\n\n")
            f.write("验证 DescribePrice API 是否支持所有代际实例的价格查询，包括:\n")
            f.write("- 第9代实例 (g9i/c9i/r9i)\n")
            f.write("- 第8代实例 (g8y/c8y/r8y)\n")
            f.write("- 第7代实例 (g7/c7/r7)\n")
            f.write("- 第6代实例 (g6/c6/r6)\n")
            f.write("- 第5代实例 (g5/c5/r5)\n\n")
            
            f.write("## 测试结果汇总\n\n")
            f.write("| 代际 | 测试实例数 | 成功查询 | 查询失败 | 支持状态 |\n")
            f.write("|------|-----------|---------|---------|----------|\n")
            
            for generation, gen_results in results.items():
                total = len(gen_results)
                success = sum(1 for r in gen_results if r["success"])
                fail = total - success
                
                status = "✅ 完全支持" if success == total else \
                         "⚠️ 部分支持" if success > 0 else \
                         "❌ 不支持"
                
                f.write(f"| {generation} | {total}个 | {success}个 | {fail}个 | {status} |\n")
            
            f.write("\n## 详细测试结果\n\n")
            
            for generation, gen_results in results.items():
                f.write(f"### {generation}\n\n")
                f.write("| 实例规格 | 状态 | 价格/月 | 错误信息 |\n")
                f.write("|---------|------|--------|----------|\n")
                
                for r in gen_results:
                    status = "✅ 成功" if r["success"] else "❌ 失败"
                    price = f"¥{r['price']:.2f}" if r["success"] else "-"
                    error = r["error"] if r["error"] else "-"
                    
                    f.write(f"| {r['instance_type']} | {status} | {price} | {error} |\n")
                
                f.write("\n")
            
            f.write("## 结论\n\n")
            
            total_all = sum(len(gen_results) for gen_results in results.values())
            success_all = sum(
                sum(1 for r in gen_results if r["success"])
                for gen_results in results.values()
            )
            success_rate_all = (success_all / total_all * 100) if total_all > 0 else 0
            
            f.write(f"- **总测试实例数**: {total_all}\n")
            f.write(f"- **成功查询数**: {success_all}\n")
            f.write(f"- **总体成功率**: {success_rate_all:.1f}%\n\n")
            
            if success_rate_all >= 80:
                f.write("✅ **DescribePrice API 支持大部分代际实例的价格查询**\n\n")
                f.write("推荐使用 DescribePrice API 替代 GetSubscriptionPrice API。\n")
            elif success_rate_all >= 50:
                f.write("⚠️ **DescribePrice API 部分支持不同代际实例**\n\n")
                f.write("需要结合其他API使用，或仅查询支持的代际。\n")
            else:
                f.write("❌ **DescribePrice API 支持度较低**\n\n")
                f.write("不建议作为主要价格查询方案。\n")
            
            f.write("\n## 对比 GetSubscriptionPrice API\n\n")
            f.write("GetSubscriptionPrice API 测试结果（来自之前的测试）:\n")
            f.write("- ✅ 第5代: 100% 支持\n")
            f.write("- ✅ 第6代: 100% 支持\n")
            f.write("- ❌ 第7代: 0% 支持\n")
            f.write("- ❌ 第8代: 0% 支持\n")
            f.write("- ❌ 第9代: 0% 支持\n\n")
            
            # 比较两个API
            for generation in ["第9代", "第8代", "第7代"]:
                if generation in results:
                    gen_results = results[generation]
                    success = sum(1 for r in gen_results if r["success"])
                    total = len(gen_results)
                    
                    if success == total:
                        f.write(f"✅ **{generation}**: DescribePrice 完全支持，GetSubscriptionPrice 不支持\n")
                        f.write(f"   → DescribePrice 是更好的选择\n\n")
        
        logger.info(f"\n📄 详细报告已保存: {report_path}")


class TestDescribePriceVsGetSubscriptionPrice:
    """对比测试：DescribePrice vs GetSubscriptionPrice"""
    
    def test_compare_apis(self, ecs_client):
        """
        对比测试两个API对第7代实例的支持情况
        
        预期结果：
        - GetSubscriptionPrice: 不支持第7代
        - DescribePrice: 支持第7代
        """
        logger.info("\n" + "="*80)
        logger.info("对比测试: DescribePrice vs GetSubscriptionPrice")
        logger.info("="*80)
        
        test_instance = "ecs.g7.xlarge"
        region = "cn-beijing"
        
        logger.info(f"\n测试实例: {test_instance}")
        logger.info(f"测试区域: {region}")
        
        # 测试 DescribePrice
        logger.info(f"\n{'─'*60}")
        logger.info("API 1: DescribePrice")
        logger.info(f"{'─'*60}")
        
        describe_price_success = False
        describe_price_value = None
        
        try:
            # 创建系统盘配置（第7代需要ESSD云盘）
            system_disk = ecs_models.DescribePriceRequestSystemDisk(
                category='cloud_essd',  # 第7代使用ESSD云盘
                size=40
            )
            
            # 创建数据盘配置
            data_disks = [
                ecs_models.DescribePriceRequestDataDisk(
                    category='cloud_essd',
                    size=100
                )
            ]
            
            request = ecs_models.DescribePriceRequest(
                region_id=region,
                resource_type="instance",
                instance_type=test_instance,
                price_unit="Month",
                period=1,
                instance_network_type="vpc",
                io_optimized="optimized",
                system_disk=system_disk,
                data_disk=data_disks
            )
            
            response = ecs_client.describe_price(request)
            
            if response.body.price_info and response.body.price_info.price:
                describe_price_value = float(response.body.price_info.price.original_price)
                describe_price_success = True
                logger.info(f"✅ DescribePrice 查询成功")
                logger.info(f"   价格: ¥{describe_price_value:.2f}/月")
            else:
                logger.error(f"❌ DescribePrice 返回成功但无价格数据")
                
        except Exception as e:
            logger.error(f"❌ DescribePrice 查询失败: {str(e)}")
        
        # 测试 GetSubscriptionPrice
        logger.info(f"\n{'─'*60}")
        logger.info("API 2: GetSubscriptionPrice")
        logger.info(f"{'─'*60}")
        
        from app.core.pricing_service import PricingService
        
        access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
        access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
        
        pricing_service = PricingService(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            region_id=region
        )
        
        subscription_price_success = False
        subscription_price_value = None
        
        try:
            subscription_price_value = pricing_service.get_official_price(
                instance_type=test_instance,
                region=region,
                period=1,
                unit="Month"
            )
            subscription_price_success = True
            logger.info(f"✅ GetSubscriptionPrice 查询成功")
            logger.info(f"   价格: ¥{subscription_price_value:.2f}/月")
            
        except Exception as e:
            logger.error(f"❌ GetSubscriptionPrice 查询失败: {str(e)}")
        
        # 结论
        logger.info(f"\n{'='*60}")
        logger.info("对比结论")
        logger.info(f"{'='*60}")
        
        if describe_price_success and not subscription_price_success:
            logger.info(f"✅ DescribePrice 支持第7代实例")
            logger.info(f"❌ GetSubscriptionPrice 不支持第7代实例")
            logger.info(f"\n💡 推荐: 使用 DescribePrice API 替代 GetSubscriptionPrice")
        elif describe_price_success and subscription_price_success:
            logger.info(f"✅ 两个API都支持第7代实例")
            logger.info(f"   DescribePrice: ¥{describe_price_value:.2f}/月")
            logger.info(f"   GetSubscriptionPrice: ¥{subscription_price_value:.2f}/月")
        elif not describe_price_success and subscription_price_success:
            logger.info(f"❌ DescribePrice 不支持第7代实例")
            logger.info(f"✅ GetSubscriptionPrice 支持第7代实例")
        else:
            logger.info(f"❌ 两个API都不支持第7代实例")
        
        # 验证至少有一个API支持
        assert describe_price_success or subscription_price_success, \
            "两个API都无法查询第7代实例价格"


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v", "-s"])
