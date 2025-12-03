#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试第八代优先推荐策略"""

import os
import logging
from dotenv import load_dotenv
from app.core.sku_recommend_service import SKURecommendService
from app.models import ResourceRequirement

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')

# 加载环境变量
load_dotenv()

# 初始化服务
sku_service = SKURecommendService(
    access_key_id=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
    access_key_secret=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
    region_id="cn-beijing"
)

# 测试案例：16C64G配置
print("\n" + "="*60)
print("测试第八代优先推荐策略 - 16C64G配置")
print("="*60)

req = ResourceRequirement(
    raw_input="测试第八代推荐策略 - 16C64G",
    cpu_cores=16,
    memory_gb=64,
    storage_gb=100,
    environment="prod",
    workload_type="general"
)

recommended_sku = sku_service.get_best_instance_sku(req)

print("\n" + "="*60)
print(f"最终推荐结果: {recommended_sku}")
print("="*60)

# 检查是否为第八代实例
if recommended_sku:
    if "g8" in recommended_sku or "c8" in recommended_sku or "r8" in recommended_sku:
        print("✅ 成功推荐第八代实例")
    elif "g7" in recommended_sku or "c7" in recommended_sku or "r7" in recommended_sku:
        print("⚠️  降级到第七代实例")
    elif "g6" in recommended_sku or "c6" in recommended_sku or "r6" in recommended_sku:
        print("⚠️  降级到第六代实例")
    else:
        print("⚠️  未知实例类型")
