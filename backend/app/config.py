# -*- coding: utf-8 -*-
"""
配置管理模块
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # API配置
    app_name: str = "阿里云ECS智能报价系统"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # 阿里云配置
    alibaba_cloud_access_key_id: str
    alibaba_cloud_access_key_secret: str
    
    # DashScope配置
    dashscope_api_key: str
    
    # 默认区域
    default_region: str = "cn-beijing"
    
    # 文件上传配置
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    
    # CORS配置
    cors_origins: list = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
