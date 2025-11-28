#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API诊断脚本 - 测试阿里云ECS推荐API是否正常工作
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.sku_recommend_service import SKURecommendService
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def diagnose_api():
    """诊断API调用问题"""
    
    print("="*80)
    print("🔍 阿里云ECS API诊断工具")
    print("="*80 + "\n")
    
    # 检查环境变量
    access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    
    if not access_key_id or not access_key_secret:
        print("❌ 错误: 缺少阿里云API密钥")
        print("   请确保在.env文件中设置了以下环境变量:")
        print("   - ALIBABA_CLOUD_ACCESS_KEY_ID")
        print("   - ALIBABA_CLOUD_ACCESS_KEY_SECRET")
        return
    
    print(f"✅ AccessKey ID: {access_key_id[:8]}...{access_key_id[-4:]}")
    print(f"✅ AccessKey Secret: {'*' * 20}\n")
    
    # 初始化服务
    print("📡 初始化SKU推荐服务...")
    sku_service = SKURecommendService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id="cn-beijing"
    )
    print("✅ 服务初始化成功\n")
    
    # 测试用例
    test_cases = [
        {"cpu": 4, "memory": 8, "desc": "小型实例"},
        {"cpu": 8, "memory": 16, "desc": "中型实例"},
        {"cpu": 16, "memory": 32, "desc": "大型实例"},
    ]
    
    print("="*80)
    print("测试场景: 不限制实例系列(让API自动推荐)")
    print("="*80 + "\n")
    
    for idx, case in enumerate(test_cases, 1):
        cpu = case['cpu']
        memory = case['memory']
        desc = case['desc']
        
        print(f"[测试 {idx}/{len(test_cases)}] {desc}: {cpu}C {memory}G")
        print("-"*80)
        
        try:
            # 测试1: 价格优先策略
            print("  策略1: PriceFirst (价格优先)")
            instance_type = sku_service.recommend_instance_type(
                cpu_cores=cpu,
                memory_gb=memory,
                instance_charge_type="PrePaid",
                priority_strategy="PriceFirst"
            )
            
            if instance_type:
                print(f"    ✅ 推荐实例: {instance_type}")
            else:
                print(f"    ❌ API未返回推荐结果")
                print(f"    ℹ️  使用兜底规则...")
                fallback = sku_service._fallback_sku_mapping(cpu, memory)
                print(f"    ✅ 兜底实例: {fallback}")
            
            # 测试2: 库存优先策略
            print("\n  策略2: InventoryFirst (库存优先)")
            instance_type = sku_service.recommend_instance_type(
                cpu_cores=cpu,
                memory_gb=memory,
                instance_charge_type="PrePaid",
                priority_strategy="InventoryFirst"
            )
            
            if instance_type:
                print(f"    ✅ 推荐实例: {instance_type}")
            else:
                print(f"    ❌ API未返回推荐结果")
            
        except Exception as e:
            print(f"    ❌ 异常: {str(e)}")
        
        print("")
    
    print("="*80)
    print("🎯 诊断结论")
    print("="*80)
    print("""
如果所有测试都失败(返回API错误RecommendEmpty.InstanceTypeSoldOut)，可能的原因:

1. 区域库存问题:
   - cn-beijing区域可能某些规格库存不足
   - 建议: 尝试其他区域(如cn-hangzhou, cn-shanghai)

2. 账号权限问题:
   - 检查AccessKey是否有调用ECS API的权限
   - 建议: 在阿里云控制台检查RAM权限

3. API参数问题:
   - 计费方式PrePaid可能在某些场景下不可用
   - 建议: 尝试PostPaid(按量付费)

4. 阿里云限制:
   - 可能对新账号或欠费账号有限制
   - 建议: 检查账号状态

5. 实例规格下架:
   - 某些老规格可能已停售
   - 建议: 使用兜底规则(已实现)
""")
    
    print("💡 推荐操作:")
    print("   1. 如果API完全不可用，系统会自动使用兜底映射规则")
    print("   2. 兜底规则已更新为g9系列(第9代通用型)")
    print("   3. 可以考虑直接使用兜底规则跳过API调用\n")

if __name__ == "__main__":
    diagnose_api()
