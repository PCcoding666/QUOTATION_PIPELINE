#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比API推荐与手动选择的差异分析
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.sku_recommend_service import SKURecommendService
from app.core.pricing_service import PricingService
from dotenv import load_dotenv

load_dotenv()

def analyze_recommendation_difference():
    """分析API推荐与手动选择的差异"""
    
    print("="*100)
    print("🔍 API推荐 vs 手动选择 - 差异分析")
    print("="*100 + "\n")
    
    # 初始化服务
    access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    
    sku_service = SKURecommendService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id="cn-beijing"
    )
    
    pricing_service = PricingService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id="cn-beijing"
    )
    
    # 测试场景: 16C 64G (与手动流程一致)
    cpu = 16
    memory = 64
    
    print(f"📋 测试场景: {cpu}C {memory}G, 区域=cn-beijing, 计费方式=包年包月")
    print("="*100 + "\n")
    
    # 手动选择的预期结果
    manual_expected = "ecs.g9i.4xlarge"
    manual_price = 1908.82
    
    print("🎯 手动流程预期结果:")
    print(f"   实例规格: {manual_expected}")
    print(f"   月度价格: ¥{manual_price}/月")
    print(f"   特点: 通用型 g9i (第9代Intel), 最新代际, 46个可用区\n")
    
    print("-"*100 + "\n")
    
    # 当前API推荐结果
    print("🤖 当前API推荐结果:")
    
    # 测试不同策略
    strategies = [
        ("PriceFirst", "价格优先"),
        ("InventoryFirst", "库存优先"),
    ]
    
    for strategy, desc in strategies:
        print(f"\n📊 策略: {strategy} ({desc})")
        print("-"*100)
        
        instance_type = sku_service.recommend_instance_type(
            cpu_cores=cpu,
            memory_gb=memory,
            instance_charge_type="PrePaid",
            priority_strategy=strategy
        )
        
        if instance_type:
            print(f"   推荐实例: {instance_type}")
            
            # 尝试查询价格
            try:
                price = pricing_service.get_official_price(
                    instance_type=instance_type,
                    region="cn-beijing",
                    period=1,
                    unit="Month"
                )
                print(f"   月度价格: ¥{price}/月")
            except Exception as e:
                print(f"   月度价格: 查询失败 - {str(e)[:50]}...")
            
            # 对比分析
            if instance_type == manual_expected:
                print(f"   ✅ 匹配: 与手动选择一致")
            else:
                print(f"   ❌ 不匹配: 期望 {manual_expected}, 实际 {instance_type}")
        else:
            print(f"   ❌ API推荐失败")
    
    print("\n" + "="*100)
    print("📝 差异分析报告")
    print("="*100 + "\n")
    
    print("""
🔍 关键差异点:

1. **API选择逻辑差异**
   手动流程:
   - 筛选条件: 16C 64G, 包年包月, 北京区域
   - 代际: 不限制(留空)
   - 排序: 默认排序 (通常按推荐度/新旧/可用区数量)
   - 选择: **直接取第一个推荐结果**
   
   当前API (DescribeRecommendInstanceType):
   - priority_strategy="PriceFirst" → 优先考虑价格
   - priority_strategy="InventoryFirst" → 优先考虑库存
   - 可能不会优先推荐最新代际
   - 可能推荐特殊系列(g6r, e-, u2a等)

2. **手动流程推荐的实例特点**
   ecs.g9i.4xlarge:
   - 第9代Intel通用型 (最新代际)
   - 46个可用区 (可用性最高)
   - 价格: ¥1908.82/月 (不是最便宜,但综合最优)
   - 排在推荐列表第1位

3. **当前API推荐的问题**
   可能推荐:
   - ecs.g6r.4xlarge (第6代, 老规格, 不支持包年包月价格查询)
   - ecs.c7a.4xlarge (计算优化型, 非通用型)
   - ecs.e-c1m4.2xlarge (经济型, 不支持包年包月)
   - ecs.u2a-c1m2.4xlarge (通用算力型, 非主流系列)

4. **根本原因**
   ❌ DescribeRecommendInstanceType API 可能:
      - 推荐策略与控制台不同
      - 不优先考虑代际新旧
      - 不考虑包年包月兼容性
      - 返回结果与控制台UI排序逻辑不一致

5. **解决方案建议**
   ✅ 方案1: 使用 DescribeInstanceTypes API
      - 主动查询所有匹配16C64G的实例
      - 手动按代际/系列/可用区数排序
      - 选择第一个结果
      - 模拟控制台推荐逻辑
   
   ✅ 方案2: 硬编码优先级规则
      - 优先选择 g9i > g9a > g9ae > g8i > g8a ...
      - 按照控制台推荐顺序预定义规则
      - API失败时使用此规则
   
   ✅ 方案3: 直接使用兜底映射(最简单)
      - 16C 64G → ecs.g9i.4xlarge
      - 预定义最优SKU映射表
      - 跳过API调用
""")
    
    print("\n💡 推荐操作:")
    print("   1. 使用DescribeInstanceTypes API查询所有16C64G实例")
    print("   2. 按代际(g9>g8>g7)、子系列(i>a>ae)排序")
    print("   3. 过滤掉不支持包年包月的系列(e-/u1/u2/g6r等)")
    print("   4. 选择第一个结果")
    print("   5. 验证价格可查询性\n")

if __name__ == "__main__":
    analyze_recommendation_difference()
