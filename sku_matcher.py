# -*- coding: utf-8 -*-
"""
SKU Matcher - The Grounding Layer
Translates Abstract Intent into Concrete Alibaba Cloud Product SKUs
"""
from models import ResourceRequirement
from typing import Dict, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Instance Catalog - Business Logic Mapping
# Key: (workload_type, cpu_cores, memory_gb)
# Value: Alibaba Cloud Instance Type ID
INSTANCE_CATALOG: Dict[Tuple[str, int, int], str] = {
    # Memory Intensive Workloads (数据库场景)
    # r6 系列 - 内存优化型 (更稳定，广泛支持)
    ("memory_intensive", 16, 64): "ecs.r6.4xlarge",
    ("memory_intensive", 8, 64): "ecs.r6.2xlarge",
    ("memory_intensive", 32, 128): "ecs.r6.8xlarge",
    ("memory_intensive", 4, 32): "ecs.r6.xlarge",
    
    # Compute Intensive Workloads (算法/AI场景)
    # c6 系列 - 计算优化型
    ("compute", 16, 32): "ecs.c6.4xlarge",
    ("compute", 8, 16): "ecs.c6.2xlarge",
    ("compute", 32, 64): "ecs.c6.8xlarge",
    ("compute", 4, 8): "ecs.c6.xlarge",
    
    # General Purpose Workloads (通用场景)
    # g6 系列 - 通用型
    ("general", 16, 64): "ecs.g6.4xlarge",
    ("general", 8, 32): "ecs.g6.2xlarge",
    ("general", 32, 128): "ecs.g6.8xlarge",
    ("general", 4, 16): "ecs.g6.xlarge",
}

# Default fallback instance
DEFAULT_INSTANCE = "ecs.g6.large"


def get_best_instance_sku(req: ResourceRequirement) -> str:
    """
    根据资源需求匹配最佳的阿里云实例规格
    
    Grounding Logic:
    1. 精确匹配: 根据 (workload_type, cpu_cores, memory_gb) 查找
    2. 降级匹配: 如果没有精确匹配，尝试找最接近的配置
    3. 兜底策略: 如果仍无匹配，返回默认通用型实例
    
    Args:
        req: ResourceRequirement 标准化的资源需求对象
        
    Returns:
        str: 阿里云实例规格代码 (e.g., "ecs.r7.4xlarge")
    """
    
    # Step 1: Exact match lookup
    lookup_key = (req.workload_type, req.cpu_cores, req.memory_gb)
    
    if lookup_key in INSTANCE_CATALOG:
        matched_sku = INSTANCE_CATALOG[lookup_key]
        logger.info(
            f"✅ Exact match found: {req.workload_type} | "
            f"{req.cpu_cores}C {req.memory_gb}G -> {matched_sku}"
        )
        return matched_sku
    
    # Step 2: Fuzzy match - Find closest configuration with same workload type
    logger.warning(
        f"⚠️  No exact match for: {req.workload_type} | "
        f"{req.cpu_cores}C {req.memory_gb}G"
    )
    
    # Try to find instances with same workload type
    candidates = [
        (key, sku) for key, sku in INSTANCE_CATALOG.items()
        if key[0] == req.workload_type
    ]
    
    if candidates:
        # Find the closest match by CPU cores
        closest = min(
            candidates,
            key=lambda x: abs(x[0][1] - req.cpu_cores) + abs(x[0][2] - req.memory_gb)
        )
        matched_sku = closest[1]
        logger.info(
            f"🔍 Fuzzy match found: {req.workload_type} | "
            f"{req.cpu_cores}C {req.memory_gb}G -> {matched_sku} "
            f"(closest to {closest[0][1]}C {closest[0][2]}G)"
        )
        return matched_sku
    
    # Step 3: Fallback to default
    logger.warning(
        f"⚠️  No suitable match found. Falling back to default: {DEFAULT_INSTANCE}"
    )
    return DEFAULT_INSTANCE


def get_instance_family_name(instance_type: str) -> str:
    """
    获取实例规格的友好名称
    
    Args:
        instance_type: 实例规格代码
        
    Returns:
        str: 友好的实例类型名称
    """
    family_map = {
        "r7": "内存优化型 r7",
        "c7": "计算优化型 c7",
        "g7": "通用型 g7",
        "g6": "通用型 g6",
        "r": "内存优化型",
        "c": "计算优化型",
        "g": "通用型",
    }
    
    # Extract family from instance type (e.g., "ecs.r7.4xlarge" -> "r7")
    try:
        parts = instance_type.split('.')
        if len(parts) >= 2:
            family = parts[1].rstrip('0123456789')
            return family_map.get(family, family.upper())
        return "未知类型"
    except:
        return "未知类型"
