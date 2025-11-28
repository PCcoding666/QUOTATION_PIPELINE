#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试单行数据处理
"""
import os
from dotenv import load_dotenv
from app.data.data_ingestion import QuotationRequest
from app.data.batch_processor import BatchQuotationProcessor
from app.core.pricing_service import PricingService
from app.core.sku_recommend_service import SKURecommendService

load_dotenv()

def test_single_request():
    """测试单行数据处理"""
    
    # 获取密钥
    access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    
    if not access_key_id or not access_key_secret:
        print("❌ 缺少阿里云API密钥")
        return
    
    print("\n" + "="*80)
    print("🧪 测试单行数据处理（ECS产品 + 包年包月计费）")
    print("="*80 + "\n")
    
    # 初始化服务
    pricing_service = PricingService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id="cn-beijing"
    )
    
    sku_recommend_service = SKURecommendService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id="cn-beijing"
    )
    
    processor = BatchQuotationProcessor(
        pricing_service=pricing_service,
        sku_recommend_service=sku_recommend_service,
        region="cn-beijing"
    )
    
    # 测试数据 - ECS产品
    test_requests = [
        QuotationRequest(
            source_id="Test-ECS-1",
            content="16C 64G",
            content_type="text",
            context_notes="测试ECS",
            product_name="ECS",  # ECS产品
            host_count=1,
            cpu_cores=16,
            memory_gb=64,
            storage_gb=100
        ),
        QuotationRequest(
            source_id="Test-PolarDB-1",
            content="16C 64G",
            content_type="text",
            context_notes="测试PolarDB",
            product_name="PolarDB",  # 非ECS产品，应该被跳过
            host_count=1,
            cpu_cores=16,
            memory_gb=64,
            storage_gb=100
        )
    ]
    
    # 处理请求
    for request in test_requests:
        print(f"\n{'─'*80}")
        print(f"🔄 测试: {request.source_id} (产品: {request.product_name})")
        print(f"{'─'*80}")
        
        result = processor._process_single_request(request, verbose=True)
        
        if result['success']:
            print(f"\n✅ 成功:")
            print(f"   - SKU: {result['matched_sku']}")
            print(f"   - 价格: ¥{result['price_cny_month']:,.2f} / 月")
        else:
            print(f"\n⚠️  跳过/失败:")
            print(f"   - 原因: {result['error']}")
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_single_request()
