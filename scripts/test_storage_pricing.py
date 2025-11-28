#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试包含存储的完整价格查询
场景: 16C 32G + 500G ESSD PL0云盘
期望: ecs.c9i.4xlarge + 500G存储 = ¥1757.29/月
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alibabacloud_bssopenapi20171214.client import Client as BssClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_bssopenapi20171214 import models as bss_models
from dotenv import load_dotenv

load_dotenv()

def test_storage_pricing():
    """测试包含存储的价格查询"""
    
    print("="*100)
    print("🧪 测试存储价格查询")
    print("="*100 + "\n")
    
    # 初始化BSS客户端
    access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    
    config = open_api_models.Config(
        access_key_id=access_key_id.strip(),
        access_key_secret=access_key_secret.strip()
    )
    config.endpoint = 'business.aliyuncs.com'
    config.region_id = 'cn-beijing'
    client = BssClient(config)
    
    # 测试场景
    instance_type = "ecs.c9i.4xlarge"  # 16C 32G
    storage_size = 500  # GB
    region = "cn-beijing"
    
    print(f"📋 测试场景:")
    print(f"   实例规格: {instance_type} (16C 32G)")
    print(f"   存储: {storage_size}G ESSD PL0云盘")
    print(f"   区域: {region}")
    print(f"   计费: 包年包月, 1个月")
    print(f"   期望价格: ¥1757.29/月\n")
    
    print("-"*100 + "\n")
    
    # 方案1: 只查询实例价格
    print("📊 方案1: 只查询实例价格 (当前实现)")
    print("-"*100)
    
    try:
        request = bss_models.GetSubscriptionPriceRequest(
            product_code="ecs",
            subscription_type="Subscription",
            order_type="NewOrder",
            service_period_quantity=1,
            service_period_unit="Month",
            region=region,
            module_list=[
                bss_models.GetSubscriptionPriceRequestModuleList(
                    module_code="InstanceType",
                    config=f"InstanceType:{instance_type}"
                )
            ]
        )
        
        response = client.get_subscription_price(request)
        
        if response.body.code == 'Success':
            price = float(response.body.data.original_price)
            print(f"✅ 实例价格: ¥{price:.2f}/月")
        else:
            print(f"❌ 查询失败: {response.body.message}")
    except Exception as e:
        print(f"❌ 异常: {str(e)}\n")
    
    print()
    
    # 方案2: 查询实例 + 系统盘
    print("📊 方案2: 查询实例 + 系统盘 (键值对格式)")
    print("-"*100)
    
    try:
        request = bss_models.GetSubscriptionPriceRequest(
            product_code="ecs",
            subscription_type="Subscription",
            order_type="NewOrder",
            service_period_quantity=1,
            service_period_unit="Month",
            region=region,
            module_list=[
                # 实例规格
                bss_models.GetSubscriptionPriceRequestModuleList(
                    module_code="InstanceType",
                    config=f"InstanceType:{instance_type}"
                ),
                # 系统盘 (键值对格式)
                bss_models.GetSubscriptionPriceRequestModuleList(
                    module_code="SystemDisk",
                    config=f"DiskCategory:cloud_essd,PerformanceLevel:PL0,Size:{storage_size}"
                )
            ]
        )
        
        response = client.get_subscription_price(request)
        
        if response.body.code == 'Success':
            price = float(response.body.data.original_price)
            print(f"✅ 实例+系统盘价格: ¥{price:.2f}/月")
            print(f"   期望价格: ¥1757.29/月")
            print(f"   差额: ¥{abs(price - 1757.29):.2f}")
            if abs(price - 1757.29) < 1:
                print(f"   ✅ 匹配成功!")
            else:
                print(f"   ⚠️ 存在差异")
        else:
            print(f"❌ 查询失败: {response.body.message}")
    except Exception as e:
        print(f"❌ 异常: {str(e)}\n")
    
    print()
    
    # 方案3: 查询实例 + 数据盘 (键值对格式)
    print("📊 方案3: 查询实例 + 数据盘 (键值对格式)")
    print("-"*100)
    
    try:
        request = bss_models.GetSubscriptionPriceRequest(
            product_code="ecs",
            subscription_type="Subscription",
            order_type="NewOrder",
            service_period_quantity=1,
            service_period_unit="Month",
            region=region,
            module_list=[
                # 实例规格
                bss_models.GetSubscriptionPriceRequestModuleList(
                    module_code="InstanceType",
                    config=f"InstanceType:{instance_type}"
                ),
                # 数据盘 (键值对格式)
                bss_models.GetSubscriptionPriceRequestModuleList(
                    module_code="DataDisk",
                    config=f"DiskCategory:cloud_essd,PerformanceLevel:PL0,Size:{storage_size}"
                )
            ]
        )
        
        response = client.get_subscription_price(request)
        
        if response.body.code == 'Success':
            price = float(response.body.data.original_price)
            print(f"✅ 实例+数据盘价格: ¥{price:.2f}/月")
            print(f"   期望价格: ¥1757.29/月")
            print(f"   差额: ¥{abs(price - 1757.29):.2f}")
            if abs(price - 1757.29) < 1:
                print(f"   ✅ 匹配成功!")
            else:
                print(f"   ⚠️ 存在差异")
        else:
            print(f"❌ 查询失败: {response.body.message}")
    except Exception as e:
        print(f"❌ 异常: {str(e)}\n")
    
    print()
    
    # 方案4: 尝试不同的云盘类型
    print("📊 方案4: 测试不同云盘类型格式")
    print("-"*100)
    
    disk_configs = [
        ("cloud_essd", "ESSD云盘"),
        ("cloud_efficiency", "高效云盘"),
        ("cloud_ssd", "SSD云盘"),
    ]
    
    for disk_type, desc in disk_configs:
        try:
            request = bss_models.GetSubscriptionPriceRequest(
                product_code="ecs",
                subscription_type="Subscription",
                order_type="NewOrder",
                service_period_quantity=1,
                service_period_unit="Month",
                region=region,
                module_list=[
                    bss_models.GetSubscriptionPriceRequestModuleList(
                        module_code="InstanceType",
                        config=f"InstanceType:{instance_type}"
                    ),
                    bss_models.GetSubscriptionPriceRequestModuleList(
                        module_code="DataDisk",
                        config=f"DataDisk:{disk_type}:{storage_size}"
                    )
                ]
            )
            
            response = client.get_subscription_price(request)
            
            if response.body.code == 'Success':
                price = float(response.body.data.original_price)
                print(f"   {desc} ({disk_type}): ¥{price:.2f}/月")
            else:
                print(f"   {desc}: 查询失败")
        except Exception as e:
            print(f"   {desc}: 异常 - {str(e)[:50]}")
    
    print("\n" + "="*100)
    print("📝 结论")
    print("="*100)
    print("""
需要确定:
1. 存储应该使用 SystemDisk 还是 DataDisk?
2. ESSD PL0 的正确配置格式是什么?
3. 可能的格式:
   - DataDisk:cloud_essd:PL0:{size}
   - DataDisk:cloud_essd:{size}
   - SystemDisk:cloud_essd:PL0:{size}
   
根据测试结果,我们将更新pricing_service.py以支持存储价格查询。
""")

if __name__ == "__main__":
    test_storage_pricing()
