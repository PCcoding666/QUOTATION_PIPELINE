# -*- coding: utf-8 -*-
"""
Data Ingestion Layer - The Abstraction for Multimodal Input
Designed for extensibility: Today Excel, Tomorrow Images, Voice, etc.
"""
from dataclasses import dataclass
from typing import Iterator, Literal, Any
from abc import ABC, abstractmethod
import pandas as pd
from pathlib import Path


@dataclass
class QuotationRequest:
    """
    统一的报价请求数据结构
    
    这个抽象层是关键：无论输入来自Excel、图片、语音，都转换为此标准格式
    这样下游处理逻辑（Parser、Matcher、Pricer）完全不需要知道数据来源
    """
    source_id: str  # 数据来源标识 (e.g., "Row 1", "Screenshot_001.png")
    content: Any  # 主要内容 (文本/图片路径/音频路径等)
    content_type: Literal["text", "image", "audio"]  # 内容类型
    context_notes: str = ""  # 补充备注信息
    
    def __str__(self) -> str:
        """便于调试的字符串表示"""
        content_preview = str(self.content)[:50] + "..." if len(str(self.content)) > 50 else str(self.content)
        return f"QuotationRequest(source={self.source_id}, type={self.content_type}, content={content_preview})"


class BaseDataLoader(ABC):
    """
    数据加载器抽象基类
    
    设计理念:
    - 定义统一的接口，让批处理器与具体数据格式解耦
    - 今天实现ExcelDataLoader，明天可以实现ImageDirLoader、VoiceTranscriptLoader
    - 批处理逻辑无需任何改动
    """
    
    @abstractmethod
    def load_data(self) -> Iterator[QuotationRequest]:
        """
        加载数据并转换为QuotationRequest流
        
        Yields:
            QuotationRequest: 标准化的报价请求对象
        """
        pass
    
    @abstractmethod
    def get_total_count(self) -> int:
        """
        获取总数据条数（用于进度显示）
        
        Returns:
            int: 数据总条数
        """
        pass


class ExcelDataLoader(BaseDataLoader):
    """
    Excel数据加载器 - BaseDataLoader的具体实现
    
    职责:
    - 读取Excel文件
    - 将每行数据转换为QuotationRequest对象
    - 处理列映射和数据清洗
    """
    
    def __init__(self, file_path: str, spec_column: str = "Specification", remarks_column: str = "Remarks"):
        """
        初始化Excel加载器
        
        Args:
            file_path: Excel文件路径
            spec_column: 规格说明列名
            remarks_column: 备注列名
        """
        self.file_path = Path(file_path)
        self.spec_column = spec_column
        self.remarks_column = remarks_column
        self._df = None
        
        # Validate file exists
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")
    
    def _load_dataframe(self) -> pd.DataFrame:
        """延迟加载DataFrame"""
        if self._df is None:
            try:
                self._df = pd.read_excel(self.file_path)
                
                # Validate required columns
                if self.spec_column not in self._df.columns:
                    raise ValueError(f"Column '{self.spec_column}' not found in Excel. Available: {list(self._df.columns)}")
                
                # Remarks column is optional
                if self.remarks_column not in self._df.columns:
                    print(f"⚠️  Warning: Column '{self.remarks_column}' not found. Using empty remarks.")
                    self._df[self.remarks_column] = ""
                
            except Exception as e:
                raise Exception(f"Failed to load Excel file: {e}")
        
        return self._df
    
    def load_data(self) -> Iterator[QuotationRequest]:
        """
        从Excel加载数据并转换为QuotationRequest流
        
        Yields:
            QuotationRequest: 每行数据对应一个请求对象
        """
        df = self._load_dataframe()
        
        for idx, row in df.iterrows():
            # Extract specification content
            spec_content = str(row[self.spec_column]).strip()
            
            # Skip empty rows
            if not spec_content or spec_content.lower() in ['nan', 'none', '']:
                continue
            
            # Extract remarks (optional)
            remarks = str(row.get(self.remarks_column, "")).strip()
            if remarks.lower() in ['nan', 'none']:
                remarks = ""
            
            # Construct QuotationRequest
            yield QuotationRequest(
                source_id=f"Row {idx + 2}",  # Excel row number (1-indexed + header)
                content=spec_content,
                content_type="text",
                context_notes=remarks
            )
    
    def get_total_count(self) -> int:
        """获取有效数据行数"""
        df = self._load_dataframe()
        # Count non-empty rows
        valid_rows = df[self.spec_column].notna() & (df[self.spec_column] != "")
        return valid_rows.sum()


# ============================================================================
# Future Extension Point: Image-based Input (Placeholder)
# ============================================================================

class ImageDirLoader(BaseDataLoader):
    """
    图片目录加载器 (未来扩展)
    
    设计思路:
    - 遍历指定目录下的所有图片文件
    - 将图片路径封装为QuotationRequest
    - content_type设为"image"
    - 下游Parser检测到image类型后，调用Vision Model进行OCR/理解
    """
    
    def __init__(self, dir_path: str, supported_formats: tuple = ('.png', '.jpg', '.jpeg')):
        """
        初始化图片目录加载器
        
        Args:
            dir_path: 图片目录路径
            supported_formats: 支持的图片格式
        """
        self.dir_path = Path(dir_path)
        self.supported_formats = supported_formats
        
        if not self.dir_path.exists() or not self.dir_path.is_dir():
            raise ValueError(f"Invalid directory path: {dir_path}")
    
    def load_data(self) -> Iterator[QuotationRequest]:
        """
        从图片目录加载数据
        
        Yields:
            QuotationRequest: 图片路径封装的请求对象
        """
        image_files = [
            f for f in self.dir_path.iterdir()
            if f.suffix.lower() in self.supported_formats
        ]
        
        for img_file in sorted(image_files):
            yield QuotationRequest(
                source_id=img_file.name,
                content=str(img_file.absolute()),  # Full path to image
                content_type="image",
                context_notes=""  # Could be extracted from filename or metadata
            )
    
    def get_total_count(self) -> int:
        """获取图片文件总数"""
        return len([
            f for f in self.dir_path.iterdir()
            if f.suffix.lower() in self.supported_formats
        ])
