# -*- coding: utf-8 -*-
import os
from alibabacloud_bssopenapi20171214.client import Client as BssClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_bssopenapi20171214 import models as bss_models
from alibabacloud_tea_util import models as util_models

# Hardcoded Internal Constants (Phase 5 Standardization)
PRODUCT_CODE = "ecs"
ORDER_TYPE = "NewOrder"
MODULE_CODE = "InstanceType"

class PricingService:
    def __init__(self, access_key_id: str, access_key_secret: str, region_id: str = "cn-beijing"):
        """
        Initializes the BSS Client.
        
        Phase 5: Default region changed to cn-beijing
        """
        config = open_api_models.Config(
            access_key_id=access_key_id.strip(),
            access_key_secret=access_key_secret.strip()
        )
        config.endpoint = 'business.aliyuncs.com'
        config.region_id = region_id
        self.client = BssClient(config)

    def get_official_price(self, instance_type: str, region: str = "cn-beijing", period: int = 1, unit: str = "Month") -> float:
        """
        Queries the official list price for an ECS instance using GetSubscriptionPrice.
        
        Phase 5 Updates:
        - Default region: cn-beijing (instead of requiring parameter)
        - Default unit: Month (instead of Year)
        - Simplified parameter order: instance_type first
        
        Args:
            instance_type: ECS实例规格 (e.g., "ecs.r6.4xlarge")
            region: 阿里云区域 (默认: "cn-beijing")
            period: 购买时长 (默认: 1个月)
            unit: 时间单位 ("Month" 或 "Year", 默认: "Month")
            
        Returns:
            float: 官方价格 (CNY)
        """

        # Construct the request using GetSubscriptionPrice
        # Phase 5: Use internal constants
        
        request = bss_models.GetSubscriptionPriceRequest(
            product_code=PRODUCT_CODE,           # "ecs"
            subscription_type="Subscription",     # 包年包月
            order_type=ORDER_TYPE,               # "NewOrder"
            service_period_quantity=period,
            service_period_unit=unit,            # "Month" (Phase 5 default)
            region=region,
            module_list=[
                bss_models.GetSubscriptionPriceRequestModuleList(
                    module_code=MODULE_CODE,     # "InstanceType"
                    config=f"InstanceType:{instance_type}"
                )
            ]
        )
        
        try:
            response = self.client.get_subscription_price(request)
            
            if response.body.code != 'Success':
                raise Exception(f"API Error: {response.body.message}")
                
            # Parse response to find OriginalPrice
            # The response structure: Body -> Data -> OriginalPrice
            if response.body.data and response.body.data.original_price:
                return float(response.body.data.original_price)
            else:
                raise Exception("Price data not found in response")
                
        except Exception as e:
            # Re-raise to be handled by main.py
            raise e
