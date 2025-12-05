# -*- coding: utf-8 -*-
"""
API v1 路由聚合
"""
from fastapi import APIRouter
from app.api.v1.endpoints import quotations, regions

router = APIRouter()

# 包含各个端点路由
router.include_router(quotations.router, prefix="/quotations", tags=["quotations"])
router.include_router(regions.router, prefix="/regions", tags=["regions"])
