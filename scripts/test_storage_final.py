#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试: 基于阿里云文档的正确格式测试存储价格
参考: https://help.aliyun.com/document_detail/98971.html
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alibabacloud_bssopenapi20171214.client import Client as BssClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_bssopenapi20171214 import models as bss_models
from dotenv import load_dotenv

load_dotenv()

def test_correct_format():
    """使用正确的格式测试"""
    
    print("="*100)
    print("🧪 测试存储价格 - 正确格式")
    print("="*100 + "\n")
    
    # 初始化
    access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    
    config = open_api_models.Config(
        access_key_id=access_key_id.strip(),
        access_key_secret=access_key_secret.strip()
    )
    config.endpoint = 'business.aliyuncs.com'
    client = BssClient(config)
    
    instance_type = "ecs.c9i.4xlarge"
    storage_size = 500
    region = "cn-beijing"
    
    print(f"📋 场景: {instance_type} + {storage_size}G ESSD PL0")
    print(f"   期望价格: ¥1757.29/月\n")
    
    # 根据文档,SystemDisk的config格式可能是 key:value 或者只有value
    test_cases = [
        {
            "name": "方案1: 系统盘 (category:size格式)",
            "modules": [
                {"code": "InstanceType", "config": f"InstanceType:{instance_type}"},
                {"code": "SystemDisk", "config": f"cloud_essd:{storage_size}"}
            ]
        },
        {
            "name": "方案2: 数据盘 (category:size格式)",
            "modules": [
                {"code": "InstanceType", "config": f"InstanceType:{instance_type}"},
                {"code": "DataDisk", "config": f"cloud_essd:{storage_size}"}
            ]
        },
        {
            "name": "方案3: 系统盘 (只有category)",
            "modules": [
                {"code": "InstanceType", "config": f"InstanceType:{instance_type}"},
                {"code": "SystemDisk", "config": "cloud_essd"}
            ]
        },
        {
            "name": "方案4: 系统盘 + 性能等级",
            "modules": [
                {"code": "InstanceType", "config": f"InstanceType:{instance_type}"},
                {"code": "SystemDisk", "config": "cloud_essd"},
                {"code": "PerformanceLevel", "config": "PL0"},
                {"code": "Size", "config": str(storage_size)}
            ]
        },
    ]
    
    for test in test_cases:
        print(f"📊 {test['name']}")
        print("-"*100)
        
        try:
            module_list = []
            for m in test['modules']:
                module_list.append(
                    bss_models.GetSubscriptionPriceRequestModuleList(
                        module_code=m['code'],
                        config=m['config']
                    )
                )
            
            request = bss_models.GetSubscriptionPriceRequest(
                product_code="ecs",
                subscription_type="Subscription",
                order_type="NewOrder",
                service_period_quantity=1,
                service_period_unit="Month",
                region=region,
                module_list=module_list
            )
            
            response = client.get_subscription_price(request)
            
            if response.body.code == 'Success':
                price = float(response.body.data.original_price)
                print(f"   ✅ 价格: ¥{price:.2f}/月")
                print(f"   期望: ¥1757.29/月")
                diff = abs(price - 1757.29)
                print(f"   差额: ¥{diff:.2f}")
                if diff < 1:
                    print(f"   🎉 完美匹配!")
            else:
                print(f"   ❌ 失败: {response.body.message[:80]}")
        except Exception as e:
            error_msg = str(e)
            if "PRICING_PLAN_RESULT_NOT_FOUND" in error_msg:
                print(f"   ❌ 该实例规格不支持包年包月价格查询")
            else:
                print(f"   ❌ 异常: {error_msg[:80]}")
        
        print()
    
    print("="*100)
    print("💡 如果所有方案都失败,可能原因:")
    print("   1. ecs.c9i.4xlarge 不支持 GetSubscriptionPrice API")
    print("   2. 需要使用更老的实例规格进行测试")
    print("   3. 建议尝试 ecs.c7.4xlarge 或 ecs.g7.4xlarge")
    print("="*100)

if __name__ == "__main__":
    test_correct_format()
