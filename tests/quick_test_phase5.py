# -*- coding: utf-8 -*-
"""
快速测试Phase 5功能 - 处理大马彩文件（前3条记录）
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

load_dotenv()

# 简单测试数据
test_requests = [
    QuotationRequest(
        source_id="Test_1_中间件",
        content="16C 64G 1000G存储",
        content_type="text",
        context_notes="中间件服务器 | Nginx Redis Kafka"
    ),
    QuotationRequest(
        source_id="Test_2_数据库",
        content="8C 64G 1000G存储",
        content_type="text",
        context_notes="数据库服务器 | MySQL PostgreSQL"
    ),
    QuotationRequest(
        source_id="Test_3_计算节点",
        content="16C 32G 500G存储",
        content_type="text",
        context_notes="算法计算 | 高性能计算"
    ),
]

access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')

if not access_key_id or not access_key_secret:
    print("❌ Missing credentials")
    sys.exit(1)

print("\n" + "="*100)
print("🧪 Phase 5 Quick Test - 3 Sample Requests")
print("="*100)
print(f"📍 Region: cn-beijing")
print(f"💰 Pricing: Monthly (Phase 5)\n")

# Initialize services
pricing_service = PricingService(
    access_key_id=access_key_id,
    access_key_secret=access_key_secret,
    region_id="cn-beijing"
)

processor = BatchQuotationProcessor(
    pricing_service=pricing_service,
    region="cn-beijing"
)

# Process requests
results = []
for idx, request in enumerate(test_requests, 1):
    print(f"\n{'─'*100}")
    print(f"🔄 Processing [{idx}/3]: {request.source_id}")
    print(f"{'─'*100}")
    
    result = processor._process_single_request(request, verbose=True)
    results.append(result)

processor.results = results
processor._print_summary()

# Export
output_file = "output/quick_test_result.xlsx"
processor.export_to_excel(output_file)
print(f"\n✅ Results exported to: {output_file}\n")
