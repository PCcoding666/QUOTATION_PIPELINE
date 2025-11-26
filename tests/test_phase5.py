# -*- coding: utf-8 -*-
"""
Phase 5 Test Script - Qwen-Max Integration Test
测试AI驱动的语义解析和按月定价功能
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from semantic_parser import parse_with_qwen
from pricing_service import PricingService
from sku_matcher import get_best_instance_sku

# Load environment variables
load_dotenv()

def test_ai_parsing():
    """测试Qwen-Max AI解析功能"""
    print("\n" + "="*100)
    print("🧪 Phase 5 Test 1: AI-Powered Semantic Parsing (Qwen-Max)")
    print("="*100 + "\n")
    
    test_cases = [
        "16C 64G | 数据库服务器",
        "8核 32G内存 | 算法计算节点",
        "32C 128G 500G存储 | Redis缓存集群",
    ]
    
    for idx, text in enumerate(test_cases, 1):
        print(f"\n[Test Case {idx}] Input: {text}")
        print("-" * 80)
        
        try:
            requirement = parse_with_qwen(text)
            print(f"✅ Parsed Result:")
            print(f"   - CPU: {requirement.cpu_cores} cores")
            print(f"   - Memory: {requirement.memory_gb} GB")
            print(f"   - Storage: {requirement.storage_gb} GB")
            print(f"   - Workload Type: {requirement.workload_type}")
            print(f"   - Environment: {requirement.environment}")
            
            # Test SKU matching
            sku = get_best_instance_sku(requirement)
            print(f"   - Matched SKU: {sku}")
            
        except Exception as e:
            print(f"❌ Error: {e}")


def test_monthly_pricing():
    """测试按月定价功能"""
    print("\n" + "="*100)
    print("🧪 Phase 5 Test 2: Monthly Pricing (cn-beijing region)")
    print("="*100 + "\n")
    
    # Initialize pricing service
    access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
    access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    
    if not access_key_id or not access_key_secret:
        print("⚠️  Skipping pricing test - Alibaba Cloud credentials not configured")
        return
    
    pricing_service = PricingService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id="cn-beijing"
    )
    
    test_instances = [
        "ecs.r6.2xlarge",  # Memory intensive
        "ecs.c6.2xlarge",  # Compute intensive
        "ecs.g6.2xlarge",  # General purpose
    ]
    
    for instance_type in test_instances:
        print(f"\n[Instance] {instance_type}")
        print("-" * 80)
        
        try:
            # Get monthly price
            monthly_price = pricing_service.get_official_price(
                instance_type=instance_type,
                region="cn-beijing",
                period=1,
                unit="Month"
            )
            
            # Get yearly price for comparison
            yearly_price = pricing_service.get_official_price(
                instance_type=instance_type,
                region="cn-beijing",
                period=1,
                unit="Year"
            )
            
            print(f"✅ Monthly Price:  ¥{monthly_price:,.2f} CNY/Month")
            print(f"✅ Yearly Price:   ¥{yearly_price:,.2f} CNY/Year")
            print(f"💡 Monthly*12:     ¥{monthly_price*12:,.2f} CNY/Year")
            
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """主测试函数"""
    print("\n" + "🚀" * 50)
    print("Phase 5 - The Brain Injection: Integration Test")
    print("🚀" * 50)
    
    # Test 1: AI Parsing
    test_ai_parsing()
    
    # Test 2: Monthly Pricing
    test_monthly_pricing()
    
    print("\n" + "="*100)
    print("✅ Phase 5 Test Complete!")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()
