#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行Pipeline处理大马彩环境资源需求文件
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

from app.data.data_ingestion import LLMDrivenExcelLoader
from app.data.batch_processor import BatchQuotationProcessor
from app.core.pricing_service import PricingService
from app.core.sku_recommend_service import SKURecommendService
import openpyxl


def main():
    """运行完整的报价Pipeline"""
    
    print("\n" + "="*100)
    print("🚀 Quotation Pipeline - 大马彩环境资源需求处理")
    print("="*100 + "\n")
    
    # 文件路径 - 可通过命令行参数指定
    import sys
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "tests/data/xlsx/大马彩环境资源需求（3套环境）.xlsx"
    
    if not os.path.exists(input_file):
        print(f"❌ 文件不存在: {input_file}")
        return
    
    print(f"📂 输入文件: {input_file}")
    
    # 检查环境变量
    access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    dashscope_key = os.getenv('DASHSCOPE_API_KEY')
    
    if not access_key_id or not access_key_secret:
        print("❌ 缺少阿里云API密钥，请设置环境变量:")
        print("   ALIBABA_CLOUD_ACCESS_KEY_ID")
        print("   ALIBABA_CLOUD_ACCESS_KEY_SECRET")
        return
    
    if not dashscope_key:
        print("❌ 缺少DashScope API密钥，请设置环境变量:")
        print("   DASHSCOPE_API_KEY")
        return
    
    print("✅ 环境变量检查通过\n")
    
    # 读取工作表列表
    wb = openpyxl.load_workbook(input_file, data_only=True)
    all_sheets = wb.sheetnames
    
    print(f"📑 工作表列表: {all_sheets}")
    print(f"📋 共 {len(all_sheets)} 个工作表\n")
    
    # 初始化服务
    print("🔧 初始化服务...")
    
    pricing_service = PricingService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id="cn-beijing"
    )
    print("   ✅ 价格查询服务")
    
    sku_service = SKURecommendService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id="cn-beijing"
    )
    print("   ✅ SKU推荐服务\n")
    
    # 为每个工作表处理
    output_dir = Path("tests/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_results = {}
    
    for idx, sheet_name in enumerate(all_sheets, 1):
        print(f"\n{'#'*100}")
        print(f"🔄 处理工作表 [{idx}/{len(all_sheets)}]: {sheet_name}")
        print(f"{'#'*100}\n")
        
        try:
            # 创建数据加载器
            loader = LLMDrivenExcelLoader(file_path=input_file)
            
            # 创建批处理器
            processor = BatchQuotationProcessor(
                pricing_service=pricing_service,
                sku_recommend_service=sku_service,
                region="cn-beijing"
            )
            
            # 修改load_data以支持指定工作表
            original_load_data = loader.load_data
            original_get_total_count = loader.get_total_count
            
            def load_data_with_sheet():
                return original_load_data(sheet_name=sheet_name)
            
            def get_total_count_with_sheet():
                semi_structured_data = loader._extract_semi_structured_data(sheet_name)
                parsed_data = loader._parse_with_llm(semi_structured_data)
                return len(parsed_data)
            
            loader.load_data = load_data_with_sheet
            loader.get_total_count = get_total_count_with_sheet
            
            # 执行处理
            results = processor.process_batch(loader, verbose=True)
            all_results[sheet_name] = results
            
            # 生成输出文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"output_{sheet_name}_{timestamp}.xlsx"
            
            processor.export_to_excel(str(output_file))
            print(f"\n✅ 工作表 [{sheet_name}] 处理完成")
            print(f"📄 输出文件: {output_file}")
            
        except Exception as e:
            print(f"\n❌ 工作表 [{sheet_name}] 处理失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
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
        success_results = [r for r in results if r.get('success', False)]
        
        sheet_hosts = sum(r.get('host_count', 1) for r in success_results)
        sheet_cpus = sum(r.get('cpu_cores', 0) * r.get('host_count', 1) for r in success_results)
        sheet_memory = sum(r.get('memory_gb', 0) * r.get('host_count', 1) for r in success_results)
        sheet_storage = sum(r.get('storage_gb', 0) * r.get('host_count', 1) for r in success_results)
        sheet_cost = sum(r.get('price_cny_month', 0) * r.get('host_count', 1) for r in success_results)
        
        print(f"📑 {sheet_name}:")
        print(f"   - 成功处理: {len(success_results)}/{len(results)} 条")
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
    
    print("🎉 Pipeline处理完成！")
    print(f"📁 输出文件保存在: {output_dir}/\n")


if __name__ == "__main__":
    main()
