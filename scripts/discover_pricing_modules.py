#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询DescribePricingModule API以发现正确的配置格式
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alibabacloud_bssopenapi20171214.client import Client as BssClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_bssopenapi20171214 import models as bss_models
from dotenv import load_dotenv

load_dotenv()

def discover_modules():
    """查询支持的模块配置"""
    
    print("="*100)
    print("🔍 查询ECS产品的定价模块配置")
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
    
    # 查询ECS产品的定价模块
    try:
        request = bss_models.DescribePricingModuleRequest(
            product_code="ecs",
            subscription_type="Subscription"  # 包年包月
        )
        
        response = client.describe_pricing_module(request)
        
        if response.body.code == 'Success':
            print("✅ 查询成功\n")
            print("="*100)
            print("📋 可用的定价模块:")
            print("="*100 + "\n")
            
            modules = response.body.data.module_list.module
            
            for idx, module in enumerate(modules, 1):
                print(f"{idx}. Module Code: {module.module_code}")
                print(f"   Module Name: {module.module_name}")
                
                if hasattr(module, 'config_list') and module.config_list:
                    print(f"   支持的配置:")
                    if hasattr(module.config_list, 'config'):
                        configs = module.config_list.config
                        for config in configs[:5]:  # 只显示前5个
                            print(f"      - {config}")
                
                if hasattr(module, 'values') and module.values:
                    print(f"   可选值:")
                    if hasattr(module.values, 'value'):
                        values = module.values.value
                        for value in values[:5]:  # 只显示前5个
                            print(f"      - {value}")
                
                print()
        else:
            print(f"❌ 查询失败: {response.body.message}")
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")

if __name__ == "__main__":
    discover_modules()
