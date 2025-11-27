# -*- coding: utf-8 -*-
"""
SKU Recommend Service - 使用阿里云API推荐实例规格
替代硬编码的SKU匹配逻辑，使用 DescribeRecommendInstanceType API
"""
from typing import Optional
import logging
from alibabacloud_ecs20140526.client import Client as EcsClient
from alibabacloud_ecs20140526 import models as ecs_models
from alibabacloud_tea_openapi import models as open_api_models
from models import ResourceRequirement

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SKURecommendService:
    """
    使用阿里云 DescribeRecommendInstanceType API 推荐实例规格
    """
    
    def __init__(self, access_key_id: str, access_key_secret: str, region_id: str = "cn-beijing"):
        """
        初始化 ECS 客户端
        
        Args:
            access_key_id: 阿里云 AccessKey ID
            access_key_secret: 阿里云 AccessKey Secret
            region_id: 地域 ID (默认: cn-beijing)
        """
        config = open_api_models.Config(
            access_key_id=access_key_id.strip(),
            access_key_secret=access_key_secret.strip()
        )
        # ECS endpoint
        config.endpoint = f'ecs.{region_id}.aliyuncs.com'
        config.region_id = region_id
        self.client = EcsClient(config)
        self.region_id = region_id
    
    def recommend_instance_type(
        self, 
        cpu_cores: int, 
        memory_gb: float,
        instance_charge_type: str = "PrePaid",  # 包年包月
        zone_id: Optional[str] = None,
        priority_strategy: str = "PriceFirst"
    ) -> Optional[str]:
        """
        根据 CPU 和内存推荐实例规格
        
        Args:
            cpu_cores: CPU核心数
            memory_gb: 内存大小（GB）
            instance_charge_type: 计费方式 (PrePaid=包年包月, PostPaid=按量付费)
            zone_id: 可用区ID（可选）
            priority_strategy: 推荐策略 (PriceFirst=价格优先, InventoryFirst=库存优先)
            
        Returns:
            str: 推荐的实例规格，如 "ecs.g6.4xlarge"，失败返回None
        """
        try:
            request = ecs_models.DescribeRecommendInstanceTypeRequest(
                region_id=self.region_id,
                network_type='vpc',
                cores=cpu_cores,
                memory=float(memory_gb),
                instance_charge_type=instance_charge_type,
                io_optimized='optimized',
                priority_strategy=priority_strategy,
                scene='CREATE',
                instance_type_family=['ecs.g6', 'ecs.c6', 'ecs.r6']  # 限制在常见的实例系列
            )
            
            # 如果指定了可用区
            if zone_id:
                request.zone_id = zone_id
                request.zone_match_mode = 'Include'
            
            logger.info(
                f"[STEP 2.1] 🔍 调用 DescribeRecommendInstanceType API: "
                f"{cpu_cores}C {memory_gb}G, 计费方式={instance_charge_type}, 区域={self.region_id}"
            )
            
            response = self.client.describe_recommend_instance_type(request)
            
            # 解析推荐结果
            if (response.body and 
                response.body.data and 
                response.body.data.recommend_instance_type and
                len(response.body.data.recommend_instance_type) > 0):
                
                # 获取第一个推荐的实例规格（已按优先级排序）
                recommended = response.body.data.recommend_instance_type[0]
                instance_type_info = recommended.instance_type
                instance_type = instance_type_info.instance_type
                
                logger.info(
                    f"[STEP 2.2] ✅ API推荐实例规格: {instance_type} "
                    f"({instance_type_info.cores}C {instance_type_info.memory}M) "
                    f"优先级={recommended.priority}"
                )
                
                return instance_type
            else:
                logger.warning(f"[STEP 2.2] ⚠️  API未返回推荐实例规格")
                return None
                
        except Exception as e:
            logger.error(f"[STEP 2.2] ❌ API调用失败: {str(e)}")
            return None
    
    def get_best_instance_sku(self, req: ResourceRequirement) -> str:
        """
        根据资源需求获取最佳实例规格（兼容旧接口）
        
        Args:
            req: ResourceRequirement 标准化的资源需求对象
            
        Returns:
            str: 阿里云实例规格代码
        """
        logger.info(f"[STEP 2] 🎯 SKU推荐: {req.cpu_cores}C {req.memory_gb}G")
        
        # 使用API推荐
        recommended_sku = self.recommend_instance_type(
            cpu_cores=req.cpu_cores,
            memory_gb=req.memory_gb,
            instance_charge_type="PrePaid"  # 包年包月
        )
        
        # 如果API推荐失败，使用简单映射规则作为兜底
        if not recommended_sku:
            logger.warning(f"[STEP 2.2] ⚠️  API推荐失败，使用简单映射规则")
            recommended_sku = self._fallback_sku_mapping(req.cpu_cores, req.memory_gb)
            logger.info(f"[STEP 2.3] ✅ 兜底规则匹配: {recommended_sku}")
        
        return recommended_sku
    
    def _fallback_sku_mapping(self, cpu_cores: int, memory_gb: float) -> str:
        """
        简单的SKU映射规则（当API调用失败时使用）
        
        Args:
            cpu_cores: CPU核心数
            memory_gb: 内存大小（GB）
            
        Returns:
            str: 实例规格
        """
        # 简单的通用型映射表 (g6系列 - 通用型)
        sku_map = {
            (2, 8): "ecs.g6.large",
            (4, 16): "ecs.g6.xlarge",
            (8, 32): "ecs.g6.2xlarge",
            (16, 64): "ecs.g6.4xlarge",
            (32, 128): "ecs.g6.8xlarge",
            (64, 256): "ecs.g6.16xlarge",
        }
        
        # 精确匹配
        key = (cpu_cores, int(memory_gb))
        if key in sku_map:
            return sku_map[key]
        
        # 模糊匹配 - 找最接近的配置
        min_distance = float('inf')
        best_match = "ecs.g6.large"
        
        for (cpu, mem), sku in sku_map.items():
            distance = abs(cpu - cpu_cores) + abs(mem - memory_gb)
            if distance < min_distance:
                min_distance = distance
                best_match = sku
        
        return best_match


def get_instance_family_name(instance_type: str) -> str:
    """
    获取实例规格的友好名称
    
    Args:
        instance_type: 实例规格代码
        
    Returns:
        str: 友好的实例类型名称
    """
    family_map = {
        "r7": "内存优化型",
        "r6": "内存优化型",
        "c7": "计算优化型",
        "c6": "计算优化型",
        "g7": "通用型",
        "g6": "通用型",
        "r": "内存优化型",
        "c": "计算优化型",
        "g": "通用型",
    }
    
    # Extract family from instance type (e.g., "ecs.r7.4xlarge" -> "r7")
    try:
        parts = instance_type.split('.')
        if len(parts) >= 2:
            family_code = parts[1][:2]  # 取前两位，如 "g6", "r7"
            return family_map.get(family_code, family_code.upper())
        return "通用型"
    except:
        return "通用型"
