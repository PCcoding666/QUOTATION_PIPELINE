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
from app.models import ResourceRequirement

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
        priority_strategy: str = "NewProductFirst",  # 推荐策略，支持多策略降级
        instance_type_families: Optional[list] = None  # 实例系列限制
    ) -> Optional[str]:
        """
        根据 CPU 和内存推荐实例规格
        
        Args:
            cpu_cores: CPU核心数
            memory_gb: 内存大小（GB）
            instance_charge_type: 计费方式 (PrePaid=包年包月, PostPaid=按量付费)
            zone_id: 可用区ID（可选）
            priority_strategy: 推荐策略
                - NewProductFirst: 新品优先 - 优先推荐最新发布的实例类型（g9i/u1/u2a等）
                - InventoryFirst: 库存优先 - 优先推荐库存充足的实例（推荐用于生产）
                - PriceFirst: 价格优先 - 优先推荐价格最便宜的实例
            instance_type_families: 实例系列限制（可选），如 ['ecs.g8y', 'ecs.c8y', 'ecs.r8y']
            
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
                scene='CREATE'
            )
            
            # 限制实例系列（优先第八代，避免推荐无价格的第九代）
            if instance_type_families:
                request.instance_type_family = instance_type_families
            
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
        根据资源需求获取最佳实例规格（两级推荐机制，无兜底规则）
        
        推荐策略：
        1. NewProductFirst（最新产品优先）- 不限制实例系列，让API返回最新可用产品
        2. 第八代系列（g8y/c8y/r8y）- 如果第一步失败，降级到第八代
        3. 所有策略失败 - 抛出异常，不再使用兜底规则
        
        Args:
            req: ResourceRequirement 标准化的资源需求对象
            
        Returns:
            str: 阿里云实例规格代码
            
        Raises:
            Exception: 当所有推荐策略都失败时抛出
        """
        logger.info(f"[STEP 2] 🎯 SKU推荐: {req.cpu_cores}C {req.memory_gb}G")
        
        # ========================================
        # 第一步：使用 NewProductFirst 策略（不限制实例系列）
        # ========================================
        logger.info(f"[STEP 2.1] 📦 尝试: NewProductFirst（最新产品优先）")
        
        recommended_sku = self.recommend_instance_type(
            cpu_cores=req.cpu_cores,
            memory_gb=req.memory_gb,
            instance_charge_type="PrePaid",
            priority_strategy="NewProductFirst",
            instance_type_families=None  # 不限制实例系列
        )
        
        if recommended_sku:
            logger.info(f"[STEP 2.1] ✅ NewProductFirst成功推荐: {recommended_sku}")
            return recommended_sku
        else:
            logger.warning(f"[STEP 2.1] ⚠️  NewProductFirst未返回结果")
        
        # ========================================
        # 第二步：降级到第八代系列
        # ========================================
        gen8_families = ["ecs.g8y", "ecs.c8y", "ecs.r8y"]
        strategies = [
            ("InventoryFirst", "库存优先"),
            ("PriceFirst", "价格优先")
        ]
        
        logger.info(f"[STEP 2.2] 📦 降级尝试: 第八代系列（g8y/c8y/r8y）")
        
        for strategy, strategy_name in strategies:
            sub_step = f"2.{strategies.index((strategy, strategy_name)) + 1}"
            logger.info(f"[STEP 2.{sub_step}] 🔄 第八代 - {strategy_name}")
            
            recommended_sku = self.recommend_instance_type(
                cpu_cores=req.cpu_cores,
                memory_gb=req.memory_gb,
                instance_charge_type="PrePaid",
                priority_strategy=strategy,
                instance_type_families=gen8_families
            )
            
            if recommended_sku:
                logger.info(f"[STEP 2.{sub_step}] ✅ 第八代成功推荐: {recommended_sku}")
                return recommended_sku
            else:
                logger.warning(f"[STEP 2.{sub_step}] ⚠️  未返回结果")
        
        # ========================================
        # 第三步：所有策略失败，抛出错误
        # ========================================
        logger.error(f"[STEP 2.3] ❌ 所有API策略均失败，无法推荐实例规格")
        raise Exception(
            f"无法为 {req.cpu_cores}C {req.memory_gb}G 推荐合适的实例规格。\n"
            f"所有推荐策略（NewProductFirst、第八代降级）均失败。\n"
            f"可能原因：\n"
            f"1. 该配置规格过大或过小，超出API推荐范围\n"
            f"2. 目标区域（{self.region_id}）该配置实例缺货\n"
            f"3. 网络连接问题或API调用失败"
        )
    


def get_instance_family_name(instance_type: str) -> str:
    """
    获取实例规格的友好名称
    
    Args:
        instance_type: 实例规格代码
        
    Returns:
        str: 友好的实例类型名称
    """
    # 完整的实例系列映射表
    family_map = {
        # 第九代实例
        "g9i": "通用型(第9代)",
        "c9i": "计算型(第9代)",
        "r9i": "内存型(第9代)",
        "c9a": "计算型(第9代AMD)",
        "g9a": "通用型(第9代AMD)",
        "r9a": "内存型(第9代AMD)",
        # 第八代实例
        "g8y": "通用型(第8代)",
        "c8y": "计算型(第8代)",
        "r8y": "内存型(第8代)",
        "g8i": "通用型(第8代)",
        "c8i": "计算型(第8代)",
        "r8i": "内存型(第8代)",
        "g8a": "通用型(第8代AMD)",
        "c8a": "计算型(第8代AMD)",
        "r8a": "内存型(第8代AMD)",
        # 第七代实例
        "g7": "通用型(第7代)",
        "c7": "计算型(第7代)",
        "r7": "内存型(第7代)",
        "g7a": "通用型(第7代AMD)",
        "c7a": "计算型(第7代AMD)",
        "r7a": "内存型(第7代AMD)",
        # 第六代实例
        "g6": "通用型(第6代)",
        "c6": "计算型(第6代)",
        "r6": "内存型(第6代)",
        # U系列（通用算力型）
        "u1": "U1",
        # 通用类型
        "g": "通用型",
        "c": "计算型",
        "r": "内存型",
    }
    
    # Extract family from instance type (e.g., "ecs.g9i.4xlarge" -> "g9i")
    try:
        parts = instance_type.split('.')
        if len(parts) >= 2:
            family_code = parts[1]  # 完整的实例系列代码
            
            # 先尝试完整匹配
            if family_code in family_map:
                return family_map[family_code]
            
            # 尝试匹配前3个字符（如 g9i, c8y）
            if len(family_code) >= 3 and family_code[:3] in family_map:
                return family_map[family_code[:3]]
            
            # 尝试匹配前2个字符（如 g7, c6）
            if len(family_code) >= 2 and family_code[:2] in family_map:
                return family_map[family_code[:2]]
            
            # 尝试匹配第一个字符（如 g, c, r）
            if family_code[0] in family_map:
                return family_map[family_code[0]]
            
            return family_code.upper()
        return "通用型"
    except:
        return "通用型"
