# -*- coding: utf-8 -*-
"""
文件处理工具
"""
import os
import uuid
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile
from typing import Tuple


# 临时文件目录
TEMP_UPLOAD_DIR = Path("temp_uploads")
OUTPUT_DIR = Path("output")

# 确保目录存在
TEMP_UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


async def save_upload_file(file: UploadFile) -> Tuple[str, Path]:
    """
    保存上传的文件
    
    Args:
        file: FastAPI上传文件对象
        
    Returns:
        Tuple[str, Path]: (任务ID, 文件路径)
    """
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{task_id}_{timestamp}_{file.filename}"
    file_path = TEMP_UPLOAD_DIR / filename
    
    # 保存文件
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    return task_id, file_path


def cleanup_temp_file(file_path: Path) -> None:
    """
    清理临时文件
    
    Args:
        file_path: 文件路径
    """
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception:
        pass


def get_output_path(task_id: str, original_filename: str) -> Path:
    """
    获取输出文件路径
    
    Args:
        task_id: 任务ID
        original_filename: 原始文件名
        
    Returns:
        Path: 输出文件路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(original_filename).stem
    output_filename = f"quotation_{stem}_{timestamp}.xlsx"
    return OUTPUT_DIR / output_filename


def validate_excel_file(filename: str) -> bool:
    """
    验证是否为Excel文件
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否为有效的Excel文件
    """
    allowed_extensions = {'.xlsx', '.xls'}
    return Path(filename).suffix.lower() in allowed_extensions
