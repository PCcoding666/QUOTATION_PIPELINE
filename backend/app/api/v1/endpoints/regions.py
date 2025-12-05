# -*- coding: utf-8 -*-
"""
区域相关API端点
"""
from fastapi import APIRouter
from app.schemas.region import RegionListResponse, RegionInfo
from app.utils.response import success_response

router = APIRouter()


@router.get("/")
async def get_regions():
    """
    获取阿里云区域列表
    
    Returns:
        区域列表
    """
    regions = [
        {"id": "cn-beijing", "name": "华北2（北京）"},
        {"id": "cn-shanghai", "name": "华东2（上海）"},
        {"id": "cn-hangzhou", "name": "华东1（杭州）"},
        {"id": "cn-shenzhen", "name": "华南1（深圳）"},
        {"id": "cn-guangzhou", "name": "华南2（广州）"},
        {"id": "cn-qingdao", "name": "华北1（青岛）"},
        {"id": "cn-zhangjiakou", "name": "华北3（张家口）"},
        {"id": "cn-chengdu", "name": "西南1（成都）"},
        {"id": "cn-hongkong", "name": "香港"},
        {"id": "ap-southeast-1", "name": "亚太东南1（新加坡）"},
        {"id": "ap-southeast-5", "name": "亚太东南5（雅加达）"},
        {"id": "us-west-1", "name": "美国西部1（硅谷）"},
        {"id": "us-east-1", "name": "美国东部1（弗吉尼亚）"},
        {"id": "eu-central-1", "name": "欧洲中部1（法兰克福）"},
    ]
    
    return success_response(data={"regions": regions})
