# -*- coding: utf-8 -*-
import os
import logging
from alibabacloud_ecs20140526.client import Client as EcsClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ecs20140526 import models as ecs_models

logger = logging.getLogger(__name__)

# Hardcoded Internal Constants (Phase 6 - DescribePrice API)
DEFAULT_SYSTEM_DISK_SIZE = 40  # GB
DEFAULT_DATA_DISK_SIZE = 100   # GB
DEFAULT_IO_OPTIMIZED = "optimized"
DEFAULT_NETWORK_TYPE = "vpc"

class PricingService:
    def __init__(self, access_key_id: str, access_key_secret: str, region_id: str = "cn-beijing"):
        """
        Initializes the ECS Client.
        
        Phase 6: Switched to DescribePrice API (ECS native API)
        - Supports all instance generations (5th-9th)
        - More accurate pricing with disk configurations
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
        system_disk_size: int = DEFAULT_SYSTEM_DISK_SIZE,
        data_disk_size: int = DEFAULT_DATA_DISK_SIZE
    ) -> float:
        """
        Queries the official list price for an ECS instance using DescribePrice API.
        
        Phase 6 Updates:
        - Switched to DescribePrice API (supports all generations: 5th-9th)
        - Added system disk and data disk configurations
        - Automatic disk type selection based on instance generation
        
        Args:
            instance_type: ECS实例规格 (e.g., "ecs.g7.xlarge")
            region: 阿里云区域 (默认使用初始化时的region_id)
            period: 购买时长 (默认: 1个月)
            unit: 时间单位 ("Month" 或 "Year", 默认: "Month")
            system_disk_size: 系统盘大小 (GB, 默认: 40GB)
            data_disk_size: 数据盘大小 (GB, 默认: 100GB)
            
        Returns:
            float: 官方价格 (CNY), 包含实例+系统盘+数据盘总价
        """
        # 使用初始化时的region或传入的region
        region = region or self.region_id
        
        # 根据实例代际选择合适的磁盘类型
        disk_category = self._get_system_disk_category(instance_type)
        
        # 创建系统盘配置
        system_disk = ecs_models.DescribePriceRequestSystemDisk(
            category=disk_category,
            size=system_disk_size
        )
        
        # 创建数据盘配置
        data_disks = [
            ecs_models.DescribePriceRequestDataDisk(
                category=disk_category,
                size=data_disk_size
            )
        ]
        
        # 构建DescribePrice请求
        request = ecs_models.DescribePriceRequest(
            region_id=region,
            resource_type="instance",
            instance_type=instance_type,
            price_unit=unit,
            period=period,
            instance_network_type=DEFAULT_NETWORK_TYPE,
            io_optimized=DEFAULT_IO_OPTIMIZED,
            system_disk=system_disk,
            data_disk=data_disks
        )
        
        # 日志：打印请求参数
        logger.info(f"价格查询参数:")
        logger.info(f"  实例规格: {instance_type}")
        logger.info(f"  区域: {region}")
        logger.info(f"  计费周期: {period} {unit}")
        logger.info(f"  系统盘: {disk_category} {system_disk_size}GB")
        logger.info(f"  数据盘: {disk_category} {data_disk_size}GB")
        
        try:
            response = self.client.describe_price(request)
            
            # 提取价格信息
            if response.body.price_info and response.body.price_info.price:
                original_price = float(response.body.price_info.price.original_price)
                logger.info(f"  ✅ 价格查询成功: ¥{original_price:.2f}/{unit}")
                return original_price
            else:
                raise Exception("API返回成功但没有价格数据")
                
        except Exception as e:
            logger.error(f"  ❌ 价格查询失败: {str(e)}")
            raise e
    
    def _get_system_disk_category(self, instance_type: str) -> str:
        """
        根据实例类型返回推荐的系统盘类型
        
        不同代际的实例支持不同的云盘类型：
        - 第7代及以上：推荐使用 cloud_essd (ESSD云盘)
        - 第6代及以下：使用 cloud_efficiency (高效云盘)
        
        Args:
            instance_type: 实例规格，如 "ecs.g7.xlarge"
            
        Returns:
            str: 云盘类型 (cloud_essd 或 cloud_efficiency)
        """
        # 第9代实例
        if '.g9' in instance_type or '.c9' in instance_type or '.r9' in instance_type:
            return 'cloud_essd'
        # 第8代实例
        elif '.g8' in instance_type or '.c8' in instance_type or '.r8' in instance_type:
            return 'cloud_essd'
        # 第7代实例
        elif '.g7' in instance_type or '.c7' in instance_type or '.r7' in instance_type:
            return 'cloud_essd'
        # 第6代及以下
        else:
            return 'cloud_efficiency'
