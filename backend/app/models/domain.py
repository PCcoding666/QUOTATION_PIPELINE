# -*- coding: utf-8 -*-
"""
The Golden Schema - Standardized Metadata for AI-Native Quotation System
This schema ensures consistency across all input sources (Excel, Image, Voice, etc.)
"""
from pydantic import BaseModel, Field
from typing import Literal


class ResourceRequirement(BaseModel):
    """
    Standardized Resource Requirement Schema
    Captures the *intent* of the user, not just raw numbers
    """
    raw_input: str = Field(..., description="原始输入文本，用于日志记录和追溯")
    cpu_cores: int = Field(..., description="CPU核心数", gt=0)
    memory_gb: int = Field(..., description="内存容量(GB)", gt=0)
    storage_gb: int = Field(default=0, description="存储容量(GB)", ge=0)
    environment: Literal["dev", "prod", "test"] = Field(
        ..., 
        description="环境类型: dev(开发), prod(生产), test(测试)"
    )
    workload_type: Literal["general", "compute", "memory_intensive"] = Field(
        ...,
        description="工作负载类型: general(通用), compute(计算密集), memory_intensive(内存密集)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "raw_input": "16C 64G 1000G存储 | 备注: 生产环境-多维数据库",
                "cpu_cores": 16,
                "memory_gb": 64,
                "storage_gb": 1000,
                "environment": "prod",
                "workload_type": "memory_intensive"
            }
        }

    def __str__(self) -> str:
        """格式化输出，便于调试"""
        return (
            f"\n{'='*60}\n"
            f"资源需求解析结果\n"
            f"{'='*60}\n"
            f"原始输入:     {self.raw_input}\n"
            f"CPU核心数:    {self.cpu_cores}C\n"
            f"内存:         {self.memory_gb}GB\n"
            f"存储:         {self.storage_gb}GB\n"
            f"环境类型:     {self.environment}\n"
            f"工作负载类型: {self.workload_type}\n"
            f"{'='*60}\n"
        )
