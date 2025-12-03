#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试ESSD PL0性能等级配置"""

import os
import logging
from dotenv import load_dotenv
from app.core.pricing_service import PricingService

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 初始化服务
pricing_service = PricingService(
    access_key_id=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
    access_key_secret=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
    region_id="cn-beijing"
)

print("\n" + "="*80)
print("测试ESSD云盘性能等级配置")
print("="*80)

# 测试场景1：默认使用PL0
print("\n【场景1】默认配置 - 应该使用ESSD PL0")
print("-"*80)
try:
    price_pl0 = pricing_service.get_official_price(
        instance_type="ecs.g7.xlarge",
        region="cn-beijing",
        period=1,
        unit="Month",
        system_disk_size=40,
        data_disk_size=100
        # performance_level默认为"PL0"
    )
    print(f"✅ PL0价格: ¥{price_pl0:.2f} CNY/月")
except Exception as e:
    print(f"❌ 查询失败: {e}")

# 测试场景2：显式指定PL1（对比）
print("\n【场景2】显式指定ESSD PL1（对比组）")
print("-"*80)
try:
    price_pl1 = pricing_service.get_official_price(
        instance_type="ecs.g7.xlarge",
        region="cn-beijing",
        period=1,
        unit="Month",
        system_disk_size=40,
        data_disk_size=100,
        performance_level="PL1"  # 显式指定PL1
    )
    print(f"✅ PL1价格: ¥{price_pl1:.2f} CNY/月")
    
    # 价格对比
    print(f"\n💰 价格对比:")
    print(f"   PL0: ¥{price_pl0:.2f}")
    print(f"   PL1: ¥{price_pl1:.2f}")
    print(f"   差价: ¥{price_pl1 - price_pl0:.2f} (PL1比PL0贵 {((price_pl1 - price_pl0) / price_pl0 * 100):.1f}%)")
    
except Exception as e:
    print(f"❌ 查询失败: {e}")

# 测试场景3：不同代际实例
print("\n【场景3】测试不同代际实例的PL0配置")
print("-"*80)

test_instances = [
    ("ecs.g9i.xlarge", "第9代通用型"),
    ("ecs.g8y.xlarge", "第8代通用型"),
    ("ecs.g7.xlarge", "第7代通用型"),
    ("ecs.g6.xlarge", "第6代通用型（高效云盘）"),
]

for instance_type, desc in test_instances:
    print(f"\n测试 {instance_type} ({desc})")
    try:
        price = pricing_service.get_official_price(
            instance_type=instance_type,
            region="cn-beijing",
            period=1,
            unit="Month"
        )
        print(f"✅ 价格: ¥{price:.2f} CNY/月")
    except Exception as e:
        print(f"❌ 查询失败: {str(e)[:100]}")

print("\n" + "="*80)
print("测试完成")
print("="*80)
