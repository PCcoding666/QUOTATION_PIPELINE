#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM驱动的智能报价单解析 - 演示脚本

展示如何使用LLM驱动模式解析任意格式的Excel报价单
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from data_ingestion import LLMDrivenExcelLoader
from batch_processor import BatchQuotationProcessor
from pricing_service import PricingService
import os


def main():
    print("\n" + "="*80)
    print("🤖 LLM驱动的智能报价单解析系统")
    print("="*80)
    print("特点：")
    print("  ✅ 无需固定的表格格式")
    print("  ✅ 自动识别CPU、内存、存储等信息")
    print("  ✅ 适应各种不同的报价单结构")
    print("  ✅ 由Qwen-Plus大模型智能理解和提取数据")
    print("="*80 + "\n")
    
    # 示例文件
    example_file = "tests/data/xlsx/大马彩环境资源需求（3套环境） copy.xlsx"
    
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        excel_file = example_file
        print(f"📝 使用示例文件: {excel_file}")
        print("   (可以通过命令行参数指定其他Excel文件)\n")
    
    excel_path = Path(excel_file)
    
    if not excel_path.exists():
        print(f"❌ 文件不存在: {excel_file}")
        return
    
    try:
        # Step 1: 使用LLM驱动的加载器
        print("🔍 阶段1: LLM智能解析Excel表格")
        print("-" * 80)
        
        loader = LLMDrivenExcelLoader(file_path=str(excel_path))
        total_count = loader.get_total_count()
        
        print(f"✅ 成功识别 {total_count} 条资源配置\n")
        
        # Step 2: 批量处理
        print("💰 阶段2: 查询阿里云价格并生成报价")
        print("-" * 80)
        
        # 初始化价格服务
        pricing_service = PricingService(
            access_key_id=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
            access_key_secret=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
            region_id="cn-beijing"
        )
        
        # 批量处理
        processor = BatchQuotationProcessor(
            pricing_service=pricing_service,
            region="cn-beijing"
        )
        
        results = processor.process_batch(loader, verbose=False)
        
        # Step 3: 导出结果
        print("\n📊 阶段3: 导出报价结果")
        print("-" * 80)
        
        output_dir = Path("tests/output")
        output_dir.mkdir(exist_ok=True)
        
        from datetime import datetime
        output_filename = f"llm_parsed_{excel_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        output_path = output_dir / output_filename
        
        processor.export_to_excel(str(output_path))
        print(f"✅ 报价单已导出: {output_path}\n")
        
        # Step 4: 显示摘要
        print("="*80)
        print("📈 解析结果摘要")
        print("="*80)
        
        success_count = sum(1 for r in results if r['success'])
        failed_count = len(results) - success_count
        
        print(f"总计资源配置: {len(results)} 条")
        print(f"  ✅ 成功: {success_count} 条")
        print(f"  ❌ 失败: {failed_count} 条")
        
        if success_count > 0:
            total_cost = sum(r['price_cny_month'] for r in results if r['success'])
            print(f"\n💰 预估费用:")
            print(f"  月度成本: ¥{total_cost:,.2f} CNY/月")
            print(f"  年度成本: ¥{total_cost * 12:,.2f} CNY/年")
        
        print("\n" + "="*80)
        print("🎉 处理完成！")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
