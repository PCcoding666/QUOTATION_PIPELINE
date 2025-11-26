# -*- coding: utf-8 -*-
"""
Phase 4: Multimodal-Ready Batch Processing
Architecture: Data Source Agnostic via Abstraction Layer
"""
import os
import sys
from dotenv import load_dotenv

from pricing_service import PricingService
from data_ingestion import ExcelDataLoader
from batch_processor import BatchQuotationProcessor


def run_batch_processing():
    """
    Phase 4: 批量处理 - 多模态就绪架构
    
    核心设计:
    - 数据源抽象层: BaseDataLoader
    - 当前实现: ExcelDataLoader
    - 未来扩展: ImageDirLoader, AudioTranscriptLoader, etc.
    - 处理逻辑完全与数据格式无关
    """
    
    # Load credentials
    load_dotenv()
    access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    
    if not access_key_id or not access_key_secret:
        print("❌ Error: Please set ALIBABA_CLOUD_ACCESS_KEY_ID and ALIBABA_CLOUD_ACCESS_KEY_SECRET in .env file.")
        sys.exit(1)
    
    # Configuration (Phase 5: Updated paths)
    REGION = "cn-beijing"
    INPUT_FILE = "tests/data/xlsx/input_sample.xlsx"  # Sample input file
    OUTPUT_FILE = "tests/output/output_quoted.xlsx"
    
    print("\n" + "="*100)
    print("Phase 4: Multimodal-Ready Batch Processing System")
    print("="*100)
    print(f"\n📂 Input Source:  {INPUT_FILE}")
    print(f"💾 Output Target: {OUTPUT_FILE}")
    print(f"🌏 Region:        {REGION}")
    print(f"\n🔑 Architecture Highlight:")
    print(f"   - Today:  ExcelDataLoader -> BatchProcessor -> Excel Output")
    print(f"   - Future: ImageDirLoader -> Same BatchProcessor -> Excel Output")
    print(f"   - Zero code changes needed in BatchProcessor!\n")
    
    try:
        # Initialize components
        print("🔧 Initializing components...")
        
        # 1. Data Ingestion Layer (Abstraction Point)
        loader = ExcelDataLoader(INPUT_FILE)
        print(f"   ✅ Data Loader: ExcelDataLoader (found {loader.get_total_count()} records)")
        
        # 2. Pricing Service
        pricing_service = PricingService(access_key_id, access_key_secret, REGION)
        print(f"   ✅ Pricing Service: Connected to Alibaba Cloud BSS API")
        
        # 3. Batch Processor (Format-Agnostic)
        processor = BatchQuotationProcessor(pricing_service, region=REGION)
        print(f"   ✅ Batch Processor: Ready (multimodal-capable)\n")
        
        # Execute batch processing
        results = processor.process_batch(loader, verbose=True)
        
        # Export results
        print(f"📊 Exporting results to Excel...")
        processor.export_to_excel(OUTPUT_FILE)
        
        print("🎉 Batch processing completed successfully!")
        print(f"\n📄 Next Steps:")
        print(f"   1. Open {OUTPUT_FILE} to review quotations")
        print(f"   2. To process images: Implement ImageDirLoader (same pipeline works!)")
        print(f"   3. To add new instance types: Update sku_matcher.INSTANCE_CATALOG\n")
        
    except FileNotFoundError as e:
        print(f"\n❌ File Error: {e}")
        print(f"   Please ensure {INPUT_FILE} exists in the current directory.\n")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """
    Main entry point - Phase 4: Batch Processing with Multimodal-Ready Architecture
    """
    run_batch_processing()

if __name__ == "__main__":
    main()
