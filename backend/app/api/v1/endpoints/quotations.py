# -*- coding: utf-8 -*-
"""
报价相关API端点
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from app.services.quotation_service import QuotationService
from app.utils.response import success_response, error_response
from app.utils.file_handler import save_upload_file, validate_excel_file
from app.config import Settings, get_settings

router = APIRouter()


def get_quotation_service(
    region_id: str,
    settings: Settings = Depends(get_settings)
) -> QuotationService:
    """
    获取QuotationService实例（依赖注入）
    
    Args:
        region_id: 区域ID
        settings: 配置对象
        
    Returns:
        QuotationService: 报价服务实例
    """
    return QuotationService(
        access_key_id=settings.alibaba_cloud_access_key_id,
        access_key_secret=settings.alibaba_cloud_access_key_secret,
        region_id=region_id
    )


@router.post("/batch")
async def create_batch_quotation(
    file: UploadFile = File(..., description="Excel文件"),
    region_id: str = Form(..., description="阿里云区域ID"),
    settings: Settings = Depends(get_settings)
):
    """
    批量报价处理API
    
    Args:
        file: 上传的Excel文件
        region_id: 阿里云区域ID（如cn-beijing）
        
    Returns:
        批量报价结果
    """
    try:
        # 验证文件类型
        if not validate_excel_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail="文件格式错误，仅支持.xlsx和.xls格式"
            )
        
        # 保存上传文件
        task_id, file_path = await save_upload_file(file)
        
        # 创建报价服务
        quotation_service = get_quotation_service(region_id, settings)
        
        # 处理报价
        result = quotation_service.process_quotation(
            file_path=file_path,
            task_id=task_id,
            original_filename=file.filename
        )
        
        return success_response(data=result)
        
    except Exception as e:
        return error_response(
            code=500,
            message="处理失败",
            error=str(e)
        )


@router.get("/download/{task_id}")
async def download_quotation_result(task_id: str):
    """
    下载报价结果文件
    
    Args:
        task_id: 任务ID
        
    Returns:
        Excel文件流
    """
    try:
        # 查找输出文件
        output_dir = Path("output")
        matching_files = list(output_dir.glob(f"quotation_*{task_id.split('_')[0]}*.xlsx"))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        file_path = matching_files[0]
        
        return FileResponse(
            path=file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=file_path.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")
