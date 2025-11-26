# -*- coding: utf-8 -*-
"""
专门处理大马彩环境资源需求Excel的脚本
处理复杂的多Sheet、多列格式
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import pandas as pd

from pricing_service import PricingService
from batch_processor import BatchQuotationProcessor
from data_ingestion import QuotationRequest

def main():
    # Load credentials
    load_dotenv()
    access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    
    if not access_key_id or not access_key_secret:
        print("❌ Error: Please set credentials in .env file.")
        sys.exit(1)
    
    # Configuration (Phase 5: Updated to cn-beijing and monthly pricing)
    REGION = "cn-beijing"
    INPUT_FILE = "data/xlsx/大马彩环境资源需求（3套环境）.xlsx"
    OUTPUT_FILE = "output/output_大马彩_quoted_phase5.xlsx"
    
    print("\n" + "="*100)
    print("🚀 处理大马彩环境资源需求文件")
    print("="*100)
    print(f"\n📂 输入文件: {INPUT_FILE}")
    print(f"💾 输出文件: {OUTPUT_FILE}\n")
    
    # Read all sheets
    xl_file = pd.ExcelFile(INPUT_FILE)
    print(f"📋 发现 {len(xl_file.sheet_names)} 个Sheet: {xl_file.sheet_names}\n")
    
    # Initialize Pricing Service
    pricing_service = PricingService(access_key_id, access_key_secret, REGION)
    processor = BatchQuotationProcessor(pricing_service, region=REGION)
    
    all_requests = []
    
    # Process each sheet
    for sheet_name in xl_file.sheet_names:
        print(f"\n{'='*80}")
        print(f"📄 处理Sheet: {sheet_name}")
        print('='*80)
        
        df = pd.read_excel(INPUT_FILE, sheet_name=sheet_name)
        df = df.dropna(how='all', axis=0)
        df = df.dropna(how='all', axis=1)
        
        if len(df) == 0:
            print("⚠️  无有效数据，跳过")
            continue
        
        # 分析列结构，尝试找到CPU、内存、存储等列
        cpu_col_idx = None
        mem_col_idx = None
        storage_col_idx = None
        
        # 查找表头行（包含"CPU"、"内存"等关键词）
        for idx, row in df.iterrows():
            row_str = ' '.join([str(v) for v in row.values if pd.notna(v)])
            if 'CPU' in row_str and '内存' in row_str:
                # 找到列索引
                for col_idx, val in enumerate(row.values):
                    if pd.notna(val):
                        if 'CPU' in str(val):
                            cpu_col_idx = col_idx
                        elif '内存' in str(val):
                            mem_col_idx = col_idx
                        elif '数据盘' in str(val) or '存储' in str(val):
                            storage_col_idx = col_idx
                
                # 设置这一行为新表头
                df.columns = df.iloc[idx]
                df = df.iloc[idx+1:].reset_index(drop=True)
                break
        
        if cpu_col_idx is None:
            print("⚠️  无法识别数据列，跳过此Sheet")
            continue
        
        print(f"✅ 识别到数据列: CPU列={cpu_col_idx}, 内存列={mem_col_idx}, 存储列={storage_col_idx}")
        print(f"📊 有效数据行数: {len(df)}\n")
        
        # 遍历数据行
        for idx, row in df.iterrows():
            try:
                # 使用位置索引而不是列名（因为有NaN列名）
                row_values = row.values
                
                # 提取服务器类别和安装内容作为备注（前5列的非空值）
                desc_parts = []
                for i in range(min(5, len(row_values))):
                    val = row_values[i]
                    if pd.notna(val):
                        val_str = str(val).strip()
                        if val_str and val_str not in ['nan', 'NaN', '总计']:
                            desc_parts.append(val_str)
                
                description = ' - '.join(desc_parts) if desc_parts else f"{sheet_name} Row {idx+2}"
                
                # 跳过总计行和空行
                if '总计' in str(description) or len(desc_parts) == 0:
                    continue
                
                # 提取数值（使用列索引）
                cpu_val = row_values[cpu_col_idx] if cpu_col_idx < len(row_values) else 0
                mem_val = row_values[mem_col_idx] if mem_col_idx < len(row_values) else 0
                storage_val = row_values[storage_col_idx] if storage_col_idx < len(row_values) else 0
                
                # 转换为数字（处理特殊格式如"500*2"）
                try:
                    cpu = int(float(cpu_val)) if pd.notna(cpu_val) and cpu_val != 0 else 0
                    memory = int(float(mem_val)) if pd.notna(mem_val) and mem_val != 0 else 0
                    
                    # 处理存储列（可能是"500*2"这样的格式）
                    if pd.notna(storage_val) and storage_val != 0:
                        storage_str = str(storage_val)
                        if '*' in storage_str:
                            # 解析"500*2"格式
                            parts = storage_str.split('*')
                            storage = int(float(parts[0].strip())) * int(float(parts[1].strip()))
                        else:
                            storage = int(float(storage_val))
                    else:
                        storage = 0
                except Exception as conv_err:
                    print(f"  ⚠️  数据转换失败 行{idx}: {conv_err}")
                    continue
                
                # 跳过无效配置
                if cpu == 0 or memory == 0:
                    continue
                
                # 构建请求文本
                spec_text = f"{cpu}C {memory}G {storage}G存储"
                
                # 创建QuotationRequest
                request = QuotationRequest(
                    source_id=f"{sheet_name} - {description}",
                    content=spec_text,
                    content_type="text",
                    context_notes=f"{sheet_name} | {description}"
                )
                
                all_requests.append(request)
                print(f"  ✓ {request.source_id}: {spec_text}")
                
            except Exception as e:
                print(f"  ⚠️  跳过行{idx}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    print(f"\n{'='*100}")
    print(f"📦 总计提取 {len(all_requests)} 条有效请求")
    print(f"{'='*100}\n")
    
    if len(all_requests) == 0:
        print("❌ 没有有效数据可处理")
        sys.exit(1)
    
    # 手动批处理（因为我们没有使用标准的DataLoader）
    results = []
    for idx, request in enumerate(all_requests, 1):
        print(f"\n{'─'*100}")
        print(f"🔄 Processing [{idx}/{len(all_requests)}]: {request.source_id}")
        print(f"{'─'*100}")
        
        result = processor._process_single_request(request, verbose=True)
        results.append(result)
    
    processor.results = results
    processor._print_summary()
    
    # 导出结果
    print(f"\n📊 导出结果到 {OUTPUT_FILE}...")
    processor.export_to_excel(OUTPUT_FILE)
    
    print("\n🎉 处理完成！\n")

if __name__ == "__main__":
    main()
