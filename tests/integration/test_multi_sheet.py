#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多工作表Excel解析测试脚本
"""
import os
from pathlib import Path
from app.data.data_ingestion import LLMDrivenExcelLoader
from app.data.batch_processor import BatchQuotationProcessor
from app.core.pricing_service import PricingService
from app.core.sku_recommend_service import SKURecommendService
import openpyxl
from datetime import datetime


def test_multi_sheet_processing(file_path: str, output_dir: str = "tests/output"):
    """
    测试多工作表处理
    
    Args:
        file_path: Excel文件路径
        output_dir: 输出目录
    """
    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 读取工作表列表
    wb = openpyxl.load_workbook(file_path, data_only=True)
    all_sheets = wb.sheetnames
    
    print(f"\n{'='*100}")
    print(f"📄 Excel文件: {file_path}")
    print(f"📑 工作表列表: {all_sheets}")
    print(f"{'='*100}\n")
    
    # 根据用户需求，跳过第1张汇总表，处理第2、3、4张工作表
    # 索引：0=资源总量(跳过), 1=标准-开发, 2=标准-测试, 3=标准-生产
    sheets_to_process = all_sheets[1:4]  # 取索引1,2,3
    
    print(f"📋 将处理以下工作表: {sheets_to_process}")
    print(f"⏭️  跳过汇总表: {all_sheets[0]}\n")
    
    # 初始化价格服务（从环境变量读取密钥）
    access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    
    if not access_key_id or not access_key_secret:
        print("⚠️  警告: 未设置阿里云API密钥，将跳过价格查询步骤")
        print("   请设置环境变量: ALIBABA_CLOUD_ACCESS_KEY_ID 和 ALIBABA_CLOUD_ACCESS_KEY_SECRET")
        return
    
    pricing_service = PricingService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id="cn-beijing"
    )
    
    # 初始化SKU推荐服务
    sku_recommend_service = SKURecommendService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id="cn-beijing"
    )
    
    # 为每个工作表单独处理
    all_results = {}
    
    for sheet_name in sheets_to_process:
        print(f"\n{'#'*100}")
        print(f"🔄 处理工作表: {sheet_name}")
        print(f"{'#'*100}\n")
        
        # 为每个工作表创建独立的数据加载器
        data_loader = LLMDrivenExcelLoader(file_path=file_path)
        
        # 创建批处理器
        processor = BatchQuotationProcessor(
            pricing_service=pricing_service,
            sku_recommend_service=sku_recommend_service,
            region="cn-beijing"
        )
        
        # 修改load_data以支持指定工作表
        # 手动注入sheet_name到load_data方法
        original_load_data = data_loader.load_data
        
        def load_data_with_sheet():
            return original_load_data(sheet_name=sheet_name)
        
        # 也需要修改get_total_count
        original_get_total_count = data_loader.get_total_count
        
        def get_total_count_with_sheet():
            # 临时解析一次来获取数量
            semi_structured_data = data_loader._extract_semi_structured_data(sheet_name)
            parsed_data = data_loader._parse_with_llm(semi_structured_data)
            return len(parsed_data)
        
        data_loader.load_data = load_data_with_sheet
        data_loader.get_total_count = get_total_count_with_sheet
        
        # 执行处理
        results = processor.process_batch(data_loader, verbose=True)
        all_results[sheet_name] = results
        
        # 为每个工作表生成独立的输出文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_stem = Path(file_path).stem
        output_file = f"{output_dir}/output_{file_stem}_{sheet_name}_{timestamp}.xlsx"
        
        processor.export_to_excel(output_file)
        print(f"\n✅ 工作表 [{sheet_name}] 处理完成，输出文件: {output_file}")
    
    # 汇总统计
    print(f"\n\n{'='*100}")
    print("📊 全局汇总统计")
    print(f"{'='*100}\n")
    
    total_hosts = 0
    total_cpus = 0
    total_memory = 0
    total_storage = 0
    total_monthly_cost = 0
    
    for sheet_name, results in all_results.items():
        sheet_hosts = sum(r.get('host_count', 1) for r in results if r['success'])
        sheet_cpus = sum(r.get('cpu_cores', 0) * r.get('host_count', 1) for r in results if r['success'])
        sheet_memory = sum(r.get('memory_gb', 0) * r.get('host_count', 1) for r in results if r['success'])
        sheet_storage = sum(r.get('storage_gb', 0) * r.get('host_count', 1) for r in results if r['success'])
        sheet_cost = sum(r.get('price_cny_month', 0) * r.get('host_count', 1) for r in results if r['success'])
        
        print(f"📑 {sheet_name}:")
        print(f"   - 主机数: {sheet_hosts} 台")
        print(f"   - CPU核心: {sheet_cpus} 核")
        print(f"   - 内存: {sheet_memory} GB")
        print(f"   - 存储: {sheet_storage} GB")
        print(f"   - 月度成本: ¥{sheet_cost:,.2f}")
        print()
        
        total_hosts += sheet_hosts
        total_cpus += sheet_cpus
        total_memory += sheet_memory
        total_storage += sheet_storage
        total_monthly_cost += sheet_cost
    
    print(f"{'─'*100}")
    print(f"📊 总计:")
    print(f"   - 总主机数: {total_hosts} 台")
    print(f"   - 总CPU核心: {total_cpus} 核")
    print(f"   - 总内存: {total_memory} GB")
    print(f"   - 总存储: {total_storage} GB")
    print(f"   - 月度总成本: ¥{total_monthly_cost:,.2f}")
    print(f"   - 年度总成本: ¥{total_monthly_cost * 12:,.2f}")
    print(f"{'='*100}\n")


if __name__ == "__main__":
    # 测试文件路径
    test_file = "tests/data/xlsx/00-YonBIP部署方案-v5-20251125.xlsx"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        exit(1)
    
    test_multi_sheet_processing(test_file)
