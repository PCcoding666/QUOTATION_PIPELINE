# -*- coding: utf-8 -*-
"""
Region schemas
"""
from pydantic import BaseModel
from typing import List


class RegionInfo(BaseModel):
    """区域信息"""
    id: str
    name: str


class RegionListResponse(BaseModel):
    """区域列表响应"""
    regions: List[RegionInfo]
