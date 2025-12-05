# -*- coding: utf-8 -*-
"""
统一响应封装工具
"""
from typing import Any, Optional
from pydantic import BaseModel


class APIResponse(BaseModel):
    """统一API响应格式"""
    code: int
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None


def success_response(data: Any = None, message: str = "success") -> dict:
    """
    成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        
    Returns:
        dict: 标准响应格式
    """
    return {
        "code": 200,
        "message": message,
        "data": data
    }


def error_response(code: int = 500, message: str = "Internal Server Error", error: str = None) -> dict:
    """
    错误响应
    
    Args:
        code: 错误码
        message: 错误消息
        error: 详细错误信息
        
    Returns:
        dict: 标准错误响应格式
    """
    return {
        "code": code,
        "message": message,
        "error": error
    }
