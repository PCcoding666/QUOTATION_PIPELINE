#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试价格查询API - 调试版本"""

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

# 测试查询第9代实例价格
print("\n=== 测试1：查询 ecs.g9i.4xlarge 价格 ===")
try:
    price = pricing_service.get_official_price(
        instance_type="ecs.g9i.4xlarge",
        region="cn-beijing",
        period=1,
        unit="Month"
    )
    print(f"✅ 价格查询成功: ¥{price} CNY/月")
except Exception as e:
    print(f"❌ 价格查询失败: {e}")

# 测试查询第6代实例价格（对照组）
print("\n=== 测试2：查询 ecs.g6.4xlarge 价格 ===")
try:
    price = pricing_service.get_official_price(
        instance_type="ecs.g6.4xlarge",
        region="cn-beijing",
        period=1,
        unit="Month"
    )
    print(f"✅ 价格查询成功: ¥{price} CNY/月")
except Exception as e:
    print(f"❌ 价格查询失败: {e}")
