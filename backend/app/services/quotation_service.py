# -*- coding: utf-8 -*-
"""
报价业务编排层
封装BatchQuotationProcessor，提供API友好的接口
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from app.core.pricing_service import PricingService
from app.core.sku_recommend_service import SKURecommendService
from app.data.batch_processor import BatchQuotationProcessor
from app.data.data_ingestion import LLMDrivenExcelLoader
from app.utils.file_handler import get_output_path, cleanup_temp_file


class QuotationService:
    """
    报价服务编排层
    
    职责：
    - 文件接收和验证
    - 调用BatchQuotationProcessor处理业务逻辑
    - 结果文件生成和管理
    - 任务状态跟踪（可选）
    """
    
    def __init__(
        self, 
        access_key_id: str, 
        access_key_secret: str,
        region_id: str = "cn-beijing"
    ):
        """
        初始化报价服务
        
        Args:
            access_key_id: 阿里云AccessKey ID
            access_key_secret: 阿里云AccessKey Secret
            region_id: 阿里云区域ID
        """
        # 初始化核心服务
        self.pricing_service = PricingService(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            region_id=region_id
        )
        
        self.sku_service = SKURecommendService(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            region_id=region_id
        )
        
        self.region_id = region_id
    
    def process_quotation(
        self, 
        file_path: Path, 
        task_id: str,
        original_filename: str
    ) -> Dict[str, Any]:
        """
        处理报价请求
        
        Args:
            file_path: 上传文件路径
            task_id: 任务ID
            original_filename: 原始文件名
            
        Returns:
            Dict: 处理结果
                - task_id: 任务ID
                - total_count: 总记录数
                - success_count: 成功数量
                - results: 结果列表
                - download_url: 下载链接
        """
        try:
            # 创建数据加载器
            loader = LLMDrivenExcelLoader(str(file_path))
            
            # 创建批处理器
            processor = BatchQuotationProcessor(
                pricing_service=self.pricing_service,
                sku_recommend_service=self.sku_service,
                region=self.region_id
            )
            
            # 执行批量处理（关闭verbose，在API中不需要打印日志）
            results = processor.process_batch(loader, verbose=False)
            
            # 统计信息
            total_count = len(results)
            success_count = sum(1 for r in results if r.get('success', False))
            
            # 生成输出文件
            output_path = get_output_path(task_id, original_filename)
            df_results = pd.DataFrame(results)
            df_results.to_excel(output_path, index=False, engine='openpyxl')
            
            # 清理临时文件
            cleanup_temp_file(file_path)
            
            # 返回结果
            return {
                "task_id": task_id,
                "total_count": total_count,
                "success_count": success_count,
                "results": results,
                "download_url": f"/api/v1/quotations/download/{task_id}"
            }
            
        except Exception as e:
            # 清理临时文件
            cleanup_temp_file(file_path)
            raise e
