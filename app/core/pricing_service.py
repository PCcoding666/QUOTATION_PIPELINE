# -*- coding: utf-8 -*-
import os
from alibabacloud_ecs20140526.client import Client as EcsClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ecs20140526 import models as ecs_models

class PricingService:
    def __init__(self, access_key_id: str, access_key_secret: str, region_id: str = "cn-beijing"):
        """
        初始化ECS客户端 (使用DescribePrice API)
        
        改进:
        - 从BSS OpenAPI切换到ECS DescribePrice API
        - 支持最新实例规格(g9i/c9i等)
        - 支持查询存储价格
        """
        config = open_api_models.Config(
            access_key_id=access_key_id.strip(),
            access_key_secret=access_key_secret.strip()
        )
        config.endpoint = f'ecs.{region_id}.aliyuncs.com'
        config.region_id = region_id
        self.client = EcsClient(config)
        self.region_id = region_id

    def get_official_price(
        self, 
        instance_type: str, 
        region: str = None,
        period: int = 1, 
        unit: str = "Month",
        storage_gb: int = 0,
        storage_category: str = "cloud_essd",
        storage_performance_level: str = "PL0"
    ) -> float:
        """
        使用ECS DescribePrice API查询实例价格(包含存储)
        
        改进:
        - 支持最新实例规格(g9i/c9i/u2a等)
        - 支持查询数据盘价格
        - 返回实例+存储的完整价格
        
        Args:
            instance_type: ECS实例规格 (e.g., "ecs.g9i.4xlarge")
            region: 阿里云区域 (默认使用初始化时的region)
            period: 购买时长 (默认: 1)
            unit: 时间单位 ("Month" 或 "Year", 默认: "Month")
            storage_gb: 数据盘大小(GB), 0表示不添加数据盘
            storage_category: 数据盘类型 (默认: "cloud_essd")
            storage_performance_level: 性能等级 (默认: "PL0")
            
        Returns:
            float: 官方价格 (CNY/月 或 CNY/年)
        """
        if region is None:
            region = self.region_id
        
        # 构建请求
        request_params = {
            'region_id': region,
            'resource_type': 'instance',
            'instance_type': instance_type,
            'price_unit': unit,
            'period': period,
            # 系统盘(必需)
            'system_disk': ecs_models.DescribePriceRequestSystemDisk(
                category='cloud_essd',
                size=80,
                performance_level='PL0'
            )
        }
        
        # 如果指定了数据盘大小,添加数据盘配置
        if storage_gb > 0:
            request_params['data_disk'] = [
                ecs_models.DescribePriceRequestDataDisk(
                    category=storage_category,
                    size=storage_gb,
                    performance_level=storage_performance_level
                )
            ]
        
        request = ecs_models.DescribePriceRequest(**request_params)
        
        try:
            response = self.client.describe_price(request)
            
            if response.body.price_info and response.body.price_info.price:
                return float(response.body.price_info.price.original_price)
            else:
                raise Exception("Price data not found in response")
                
        except Exception as e:
            # Re-raise to be handled by caller
            raise e
