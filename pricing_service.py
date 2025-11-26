# -*- coding: utf-8 -*-
import os
from alibabacloud_bssopenapi20171214.client import Client as BssClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_bssopenapi20171214 import models as bss_models
from alibabacloud_tea_util import models as util_models

class PricingService:
    def __init__(self, access_key_id: str, access_key_secret: str, region_id: str = "cn-hangzhou"):
        """
        Initializes the BSS Client.
        """
        config = open_api_models.Config(
            access_key_id=access_key_id.strip(),
            access_key_secret=access_key_secret.strip()
        )
        config.endpoint = 'business.aliyuncs.com'
        config.region_id = region_id
        self.client = BssClient(config)

    def get_official_price(self, region: str, instance_type: str, period: int = 1) -> float:
        """
        Queries the official list price for an ECS instance using GetSubscriptionPrice.
        """
        
        # DEBUG: DescribePricingModule to find correct codes
        try:
            print("Debug: Querying Pricing Modules for ECS...")
            module_req = bss_models.DescribePricingModuleRequest(
                product_code="ecs",
                subscription_type="Subscription",
                product_type=""  # Try empty string first
            )
            module_resp = self.client.describe_pricing_module(module_req)
            print(f"Debug: DescribePricingModule Response Code: {module_resp.body.code}")
            print(f"Debug: DescribePricingModule Response Message: {module_resp.body.message}")
            
            if module_resp.body.data and module_resp.body.data.module_list:
                module_list = module_resp.body.data.module_list.module_list if hasattr(module_resp.body.data.module_list, 'module_list') else []
                print(f"Debug: Module List Length: {len(module_list)}")
                print("\nDebug: Available Modules:")
                for idx, m in enumerate(module_list[:10]):  # Show first 10 modules
                    print(f"\n Module {idx+1}: Code={m.module_code}, Name={m.module_name}")
                    if hasattr(m, 'config_list') and m.config_list:
                        configs = m.config_list.config if hasattr(m.config_list, 'config') else []
                        print(f"   Available configs ({len(configs)} total):")
                        for c in configs[:5]:  # Show first 5 configs
                            print(f"     - {c.value if hasattr(c, 'value') else c}")
                        if len(configs) > 5:
                            print(f"     ... and {len(configs) - 5} more")
        except Exception as e:
            print(f"Debug: Failed to describe modules: {e}")
            import traceback
            traceback.print_exc()

        # Construct the request using GetSubscriptionPrice
        # This API is more standard for subscription pricing.
        
        request = bss_models.GetSubscriptionPriceRequest(
            product_code="ecs",
            subscription_type="Subscription",
            order_type="NewOrder",
            service_period_quantity=period,
            service_period_unit="Year",
            region=region,  # Add region parameter at request level
            module_list=[
                bss_models.GetSubscriptionPriceRequestModuleList(
                    module_code="InstanceType",
                    config=f"InstanceType:{instance_type}"  # Correct format: moduleCode:value
                )
            ]
        )
        
        try:
            response = self.client.get_subscription_price(request)
            
            # Debug: Print full response
            print(f"\nDebug: API Response Code: {response.body.code}")
            print(f"Debug: API Response Message: {response.body.message}")
            if response.body.data:
                print(f"Debug: Response Data: {response.body.data}")
            
            if response.body.code != 'Success':
                raise Exception(f"API Error: {response.body.message}")
                
            # Parse response to find OriginalAmount
            # The response structure: Body -> Data -> OriginalPrice
            if response.body.data and response.body.data.original_price:
                return float(response.body.data.original_price)
            else:
                raise Exception("Price data not found in response")
                
        except Exception as e:
            # Re-raise to be handled by main.py
            raise e
