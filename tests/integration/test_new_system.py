#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的SKU推荐服务和包年包月计费模式
"""
import os
from dotenv import load_dotenv
from sku_recommend_service import SKURecommendService
from pricing_service import PricingService

# 加载环境变量
load_dotenv()

def test_sku_recommend_and_pricing():
    """测试SKU推荐和价格查询"""
    
    # 获取密钥
    access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    
    if not access_key_id or not access_key_secret:
        print("❌ 缺少阿里云API密钥")
        return
    
    print("\n" + "="*80)
    print("🧪 测试新系统：SKU推荐 + 包年包月计费")
    print("="*80 + "\n")
    
    # 初始化服务
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
    
    # 测试场景
    test_cases = [
        {"cpu": 4, "memory": 16, "desc": "小型应用"},
        {"cpu": 8, "memory": 32, "desc": "中型应用"},
        {"cpu": 16, "memory": 64, "desc": "大型应用"},
    ]
    
    for idx, test_case in enumerate(test_cases, 1):
        cpu = test_case["cpu"]
        memory = test_case["memory"]
        desc = test_case["desc"]
        
        print(f"\n{'─'*80}")
        print(f"测试用例 {idx}: {desc} ({cpu}C {memory}G)")
        print(f"{'─'*80}")
        
        # Step 1: SKU推荐
        print(f"[STEP 1] 🔍 调用 DescribeRecommendInstanceType API...")
        instance_type = sku_service.recommend_instance_type(
            cpu_cores=cpu,
            memory_gb=memory,
            instance_charge_type="PrePaid",  # 包年包月
            priority_strategy="PriceFirst"   # 价格优先
        )
        
        if instance_type:
            print(f"[STEP 1] ✅ 推荐实例: {instance_type}")
            
            # Step 2: 价格查询
            print(f"[STEP 2] 💰 查询包年包月价格...")
            try:
                price = pricing_service.get_official_price(
                    instance_type=instance_type,
                    region="cn-beijing",
                    period=1,
                    unit="Month"
                )
                print(f"[STEP 2] ✅ 价格: ¥{price:,.2f} / 月")
                print(f"         年度成本: ¥{price * 12:,.2f} / 年")
            except Exception as e:
                print(f"[STEP 2] ❌ 价格查询失败: {e}")
        else:
            print(f"[STEP 1] ❌ SKU推荐失败")
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_sku_recommend_and_pricing()
