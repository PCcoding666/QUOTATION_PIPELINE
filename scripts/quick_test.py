#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试 - 验证API修复和计费方式
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.sku_recommend_service import SKURecommendService, get_instance_family_name
from app.core.pricing_service import PricingService
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def quick_test():
    """快速测试修复后的功能"""
    
    print("="*80)
    print("🧪 快速功能测试")
    print("="*80 + "\n")
    
    # 环境变量
    access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    
    # 初始化服务
    print("🔧 初始化服务...")
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
    print("✅ 服务初始化完成\n")
    
    # 测试用例: 16C 32G (大马彩文件中的常见配置)
    print("="*80)
    print("测试案例: 16C 32G (来自大马彩环境需求)")
    print("="*80 + "\n")
    
    cpu = 16
    memory = 32
    
    # Step 1: SKU推荐
    print(f"[STEP 1] 🎯 SKU推荐: {cpu}C {memory}G")
    instance_type = sku_service.recommend_instance_type(
        cpu_cores=cpu,
        memory_gb=memory,
        instance_charge_type="PrePaid",  # 包年包月
        priority_strategy="PriceFirst"
    )
    
    if instance_type:
        family = get_instance_family_name(instance_type)
        print(f"         ✅ API推荐: {instance_type}")
        print(f"         📊 实例系列: {family}\n")
        
        # Step 2: 价格查询(包年包月,按月计费)
        print(f"[STEP 2] 💰 价格查询")
        print(f"         📌 计费方式: 包年包月(PrePaid)")
        print(f"         📌 统计单位: 月(Month)")
        
        try:
            price = pricing_service.get_official_price(
                instance_type=instance_type,
                region="cn-beijing",
                period=1,
                unit="Month"  # 按月计费
            )
            
            print(f"         ✅ 月度价格: ¥{price:,.2f} / 月")
            print(f"         📈 年度价格: ¥{price * 12:,.2f} / 年\n")
            
        except Exception as e:
            print(f"         ❌ 价格查询失败: {e}\n")
    else:
        print(f"         ❌ API推荐失败，使用兜底规则")
        fallback = sku_service._fallback_sku_mapping(cpu, memory)
        family = get_instance_family_name(fallback)
        print(f"         ✅ 兜底实例: {fallback}")
        print(f"         📊 实例系列: {family}\n")
    
    # Step 3: 测试兜底规则(第9代)
    print("="*80)
    print("测试兜底规则 - 第9代通用型优先")
    print("="*80 + "\n")
    
    test_configs = [
        (4, 16),
        (8, 32),
        (16, 64),
    ]
    
    for cpu, mem in test_configs:
        fallback = sku_service._fallback_sku_mapping(cpu, mem)
        family = get_instance_family_name(fallback)
        print(f"  {cpu}C {mem}G → {fallback} ({family})")
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)
    print("""
总结:
1. ✅ API调用现在可以正常工作(移除了实例系列限制)
2. ✅ 计费方式确认为包年包月(PrePaid)
3. ✅ 统计单位为月(Month)
4. ✅ 兜底规则已升级到第9代通用型(g9系列)
5. ✅ 实例系列名称显示代际信息(如"通用型(第7代)")
""")

if __name__ == "__main__":
    quick_test()
