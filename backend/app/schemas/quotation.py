# -*- coding: utf-8 -*-
"""
Pydantic schemas for API request and response models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any


class BatchQuotationRequest(BaseModel):
    """批量报价请求"""
    region_id: str = Field(..., description="阿里云区域ID", example="cn-beijing")


class QuotationItemResponse(BaseModel):
    """单条报价记录响应"""
    source_id: str
    product_name: str
    cpu_cores: Optional[int]
    memory_gb: Optional[int]
    storage_gb: Optional[int]
    matched_sku: Optional[str]
    instance_family: Optional[str]
    price_cny_month: Optional[float]
    success: bool
    error: Optional[str]


class BatchQuotationResponse(BaseModel):
    """批量报价响应"""
    task_id: str
    total_count: int
    success_count: int
    results: List[QuotationItemResponse]
    download_url: str
