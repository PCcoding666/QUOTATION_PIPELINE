#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试第八代实例价格查询"""

import os
import logging
from dotenv import load_dotenv
from app.core.pricing_service import PricingService

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')

# 加载环境变量
load_dotenv()

# 初始化服务
pricing_service = PricingService(
    access_key_id=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
    access_key_secret=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
    region_id="cn-beijing"
)

print("\n" + "="*60)
print("测试第八代实例价格查询")
print("="*60)

# 测试第八代实例
test_instances = [
    ("ecs.g8y.4xlarge", "通用型第八代"),
    ("ecs.c8y.4xlarge", "计算优化型第八代"),
    ("ecs.r8y.4xlarge", "内存优化型第八代"),
]

for instance_type, instance_name in test_instances:
    print(f"\n=== 测试: {instance_type} ({instance_name}) ===")
    try:
        price = pricing_service.get_official_price(
            instance_type=instance_type,
            region="cn-beijing",
            period=1,
            unit="Month"
        )
        print(f"✅ 价格查询成功: ¥{price} CNY/月")
    except Exception as e:
        print(f"❌ 价格查询失败: {e}")

print("\n" + "="*60)
print("测试完成")
print("="*60)
