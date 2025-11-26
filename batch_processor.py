# -*- coding: utf-8 -*-
"""
Batch Processor - Format-Agnostic Pipeline Runner
Designed to work with ANY data source via the BaseDataLoader abstraction
"""
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import asdict

from data_ingestion import BaseDataLoader, QuotationRequest
from semantic_parser import parse_requirement
from sku_matcher import get_best_instance_sku, get_instance_family_name
from pricing_service import PricingService
from Tea.exceptions import TeaException


class BatchQuotationProcessor:
    """
    批量报价处理器
    
    核心设计理念：
    - 完全不关心数据来源格式（Excel/Image/Audio等）
    - 只依赖BaseDataLoader抽象接口
    - 这样当需要支持新格式时，只需实现新的Loader，本类无需修改
    """
    
    def __init__(self, pricing_service: PricingService, region: str = "cn-beijing"):
        """
        初始化批处理器
        
        Phase 5: Default region changed to cn-beijing
        
        Args:
            pricing_service: 价格查询服务实例
            region: 阿里云区域 (默认: cn-beijing)
        """
        self.pricing_service = pricing_service
        self.region = region
        self.results: List[Dict[str, Any]] = []
    
    def process_batch(self, data_loader: BaseDataLoader, verbose: bool = True) -> List[Dict[str, Any]]:
        """
        批量处理报价请求
        
        Pipeline流程 (与Phase 3一致，但数据源解耦):
        1. Parse: QuotationRequest -> ResourceRequirement
        2. Match: ResourceRequirement -> Instance SKU
        3. Quote: Instance SKU -> Official Price
        
        Args:
            data_loader: 数据加载器 (Excel/Image/任何实现了BaseDataLoader的类)
            verbose: 是否显示详细进度
            
        Returns:
            List[Dict]: 处理结果列表
        """
        self.results = []
        total_count = data_loader.get_total_count()
        
        if verbose:
            print(f"\n{'='*100}")
            print(f"📦 Batch Processing Started: {total_count} requests")
            print(f"{'='*100}\n")
        
        for idx, request in enumerate(data_loader.load_data(), 1):
            if verbose:
                print(f"\n{'─'*100}")
                print(f"🔄 Processing [{idx}/{total_count}]: {request.source_id}")
                print(f"{'─'*100}")
            
            result = self._process_single_request(request, verbose=verbose)
            self.results.append(result)
        
        if verbose:
            self._print_summary()
        
        return self.results
    
    def _process_single_request(self, request: QuotationRequest, verbose: bool = True) -> Dict[str, Any]:
        """
        处理单个报价请求
        
        Args:
            request: 报价请求对象
            verbose: 是否显示详细信息
            
        Returns:
            Dict: 处理结果
        """
        result = {
            'source_id': request.source_id,
            'content': request.content,
            'content_type': request.content_type,
            'context_notes': request.context_notes,
            'success': False,
            'error': None
        }
        
        try:
            # Step 1: Semantic Parsing
            if verbose:
                print(f"  [1/3] 🤖 Semantic Parsing...")
            
            requirement = parse_requirement(request)
            result['cpu_cores'] = requirement.cpu_cores
            result['memory_gb'] = requirement.memory_gb
            result['storage_gb'] = requirement.storage_gb
            result['environment'] = requirement.environment
            result['workload_type'] = requirement.workload_type
            
            if verbose:
                print(f"        ✅ {requirement.cpu_cores}C | {requirement.memory_gb}G | {requirement.storage_gb}G存储")
                print(f"        ✅ Environment: {requirement.environment} | Workload: {requirement.workload_type}")
            
            # Step 2: SKU Matching
            if verbose:
                print(f"  [2/3] 🎯 SKU Grounding...")
            
            instance_sku = get_best_instance_sku(requirement)
            instance_family = get_instance_family_name(instance_sku)
            result['matched_sku'] = instance_sku
            result['instance_family'] = instance_family
            
            if verbose:
                print(f"        ✅ {instance_sku} ({instance_family})")
            
            # Step 3: Price Query (Phase 5: Monthly pricing)
            if verbose:
                print(f"  [3/3] 💰 Fetching Price...")
            
            price = self.pricing_service.get_official_price(
                instance_type=instance_sku,
                region=self.region,
                period=1,      # 1 Month (Phase 5 default)
                unit="Month"   # Phase 5: Monthly pricing
            )
            result['price_cny_month'] = price
            result['success'] = True
            
            if verbose:
                print(f"        ✅ ¥{price:,.2f} CNY / Month\n")
        
        except NotImplementedError as e:
            # Multimodal features not yet implemented
            result['error'] = str(e)
            if verbose:
                print(f"  ⚠️  {e}\n")
        
        except TeaException as e:
            # API error
            result['error'] = f"API Error: {e.message}"
            if verbose:
                print(f"  ❌ API Error: {e.message}")
                if e.data:
                    print(f"     RequestId: {e.data.get('RequestId', 'N/A')}\n")
        
        except Exception as e:
            # Other errors
            result['error'] = str(e)
            if verbose:
                print(f"  ❌ Error: {e}\n")
        
        return result
    
    def _print_summary(self):
        """打印批处理汇总"""
        print(f"\n{'='*100}")
        print("📊 BATCH QUOTATION SUMMARY")
        print(f"{'='*100}")
        
        # Header
        print(f"{'No.':<6} {'Source ID':<20} {'Spec':<30} {'SKU':<20} {'Price (CNY/M)':>15}")
        print('─'*100)
        
        # Results
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        for idx, result in enumerate(self.results, 1):
            if result['success']:
                spec_summary = f"{result['cpu_cores']}C {result['memory_gb']}G | {result['workload_type'][:8]}"
                sku_display = f"{result['matched_sku']}"
                price_display = f"¥{result['price_cny_month']:,.2f}"
                
                print(f"{idx:<6} {result['source_id']:<20} {spec_summary:<30} {sku_display:<20} {price_display:>15}")
            else:
                error_msg = result['error'][:40] if result['error'] else "Unknown Error"
                print(f"{idx:<6} {result['source_id']:<20} {'FAILED':<30} {'-':<20} {'N/A':>15}")
                print(f"       Error: {error_msg}")
        
        print('='*100)
        
        # Statistics
        print(f"\n📈 Statistics:")
        print(f"   Total Requests:  {len(self.results)}")
        print(f"   ✅ Successful:   {len(successful)}")
        print(f"   ❌ Failed:       {len(failed)}")
        
        if successful:
            total_cost = sum(r['price_cny_month'] for r in successful)
            print(f"\n💰 Cost Summary:")
            print(f"   Total Cost:      ¥{total_cost:,.2f} CNY / Month")
            print(f"   Annual Estimate: ¥{total_cost * 12:,.2f} CNY / Year")
            print(f"   Average Cost:    ¥{total_cost/len(successful):,.2f} CNY / Month")
        
        print()
    
    def export_to_excel(self, output_path: str):
        """
        将结果导出到Excel
        
        Args:
            output_path: 输出文件路径
        """
        if not self.results:
            raise ValueError("No results to export. Run process_batch() first.")
        
        # Prepare data for DataFrame
        export_data = []
        for result in self.results:
            row = {
                'Source ID': result['source_id'],
                'Original Content': result['content'],
                'Context Notes': result.get('context_notes', ''),
                'CPU Cores': result.get('cpu_cores', 'N/A'),
                'Memory (GB)': result.get('memory_gb', 'N/A'),
                'Storage (GB)': result.get('storage_gb', 'N/A'),
                'Environment': result.get('environment', 'N/A'),
                'Workload Type': result.get('workload_type', 'N/A'),
                'Matched SKU': result.get('matched_sku', 'N/A'),
                'Instance Family': result.get('instance_family', 'N/A'),
                'Price (CNY/Month)': result.get('price_cny_month', 'N/A'),
                'Status': 'Success' if result['success'] else 'Failed',
                'Error': result.get('error', '')
            }
            export_data.append(row)
        
        # Create DataFrame and export
        df = pd.DataFrame(export_data)
        df.to_excel(output_path, index=False, engine='openpyxl')
        
        print(f"✅ Results exported to: {output_path}\n")
