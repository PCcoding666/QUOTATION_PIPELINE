# -*- coding: utf-8 -*-
"""
Batch Processor - Format-Agnostic Pipeline Runner
Designed to work with ANY data source via the BaseDataLoader abstraction
"""
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import asdict

from app.data.data_ingestion import BaseDataLoader, QuotationRequest
from app.core.semantic_parser import parse_requirement
from app.core.pricing_service import PricingService
from Tea.exceptions import TeaException
from app.core.sku_recommend_service import SKURecommendService, get_instance_family_name


class BatchQuotationProcessor:
    """
    批量报价处理器
    
    核心设计理念：
    - 完全不关心数据来源格式（Excel/Image/Audio等）
    - 只依赖BaseDataLoader抽象接口
    - 这样当需要支持新格式时，只需实现新的Loader，本类无需修改
    """
    
    def __init__(
        self, 
        pricing_service: PricingService, 
        sku_recommend_service: SKURecommendService,
        region: str = "cn-beijing"
    ):
        """
        初始化批处理器
        
        Args:
            pricing_service: 价格查询服务实例
            sku_recommend_service: SKU推荐服务实例
            region: 阿里云区域 (默认: cn-beijing)
        """
        self.pricing_service = pricing_service
        self.sku_recommend_service = sku_recommend_service
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
            'product_name': request.product_name,
            'host_count': request.host_count,
            'success': False,
            'error': None
        }
        
        # 产品过滤：只处理 ECS 产品
        if request.product_name.upper() != "ECS":
            result['error'] = f"跳过非-ECS产品: {request.product_name}"
            result['matched_sku'] = 'N/A'
            result['instance_family'] = 'N/A'
            result['price_cny_month'] = 'N/A'
            if verbose:
                print(f"  ⏭️  跳过非-ECS产品: {request.product_name}\n")
            return result
        
        try:
            # Step 1: 数据提取
            if verbose:
                print(f"  [STEP 1] 📊 数据提取...")
            
            if request.cpu_cores is not None and request.memory_gb is not None:
                # 直接使用结构化数据
                result['cpu_cores'] = request.cpu_cores
                result['memory_gb'] = request.memory_gb
                result['storage_gb'] = request.storage_gb
                result['workload_type'] = 'general'
                
                if verbose:
                    print(f"        ✅ {result['cpu_cores']}C | {result['memory_gb']}G | {result['storage_gb']}G存储")
                
                # 创建 requirement 对象
                from app.models.domain import ResourceRequirement
                requirement = ResourceRequirement(
                    raw_input=request.content,
                    cpu_cores=request.cpu_cores,
                    memory_gb=request.memory_gb,
                    storage_gb=request.storage_gb,
                    environment='prod',
                    workload_type='general'
                )
            else:
                # 需要AI解析
                if verbose:
                    print(f"  [STEP 1] 🤖 AI语义解析...")
                
                requirement = parse_requirement(request)
                result['cpu_cores'] = requirement.cpu_cores
                result['memory_gb'] = requirement.memory_gb
                result['storage_gb'] = requirement.storage_gb
                result['workload_type'] = requirement.workload_type
                
                if verbose:
                    print(f"        ✅ {requirement.cpu_cores}C | {requirement.memory_gb}G | {requirement.storage_gb}G存储")
                    print(f"        ✅ Workload: {requirement.workload_type}")
            
            # Step 2: SKU推荐 (使用 DescribeRecommendInstanceType API)
            instance_sku = self.sku_recommend_service.get_best_instance_sku(requirement)
            instance_family = get_instance_family_name(instance_sku)
            result['matched_sku'] = instance_sku
            result['instance_family'] = instance_family
            
            if verbose:
                print(f"        ✅ {instance_sku} ({instance_family})")
            
            # Step 3: Price Query (Phase 5: Monthly pricing)
            if verbose:
                print(f"  [STEP 3] 💰 查询价格 (包年包月)...")
            
            # 使用Excel中的Storage值作为数据盘大小，系统盘默认40GB
            data_disk_size = result.get('storage_gb', 100)  # 默认100GB
            
            price = self.pricing_service.get_official_price(
                instance_type=instance_sku,
                region=self.region,
                period=1,
                unit="Month",
                system_disk_size=40,  # 系统盘固定40GB
                data_disk_size=data_disk_size  # 使用Excel中的Storage值
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
        
        仅输出以下10列（严格顺序）：
        1. 服务器类别 <- context_notes
        2. 产品名称 <- product_name
        3. 服务数量 <- host_count
        4. CPU(core) <- cpu_cores
        5. 内存(G) <- memory_gb
        6. 存储(G) <- storage_gb
        7. 产品规格 <- matched_sku
        8. 列表单价 <- price_cny_month
        9. 折扣 <- 空白
        10. 折后总价 <- 空白
        
        Args:
            output_path: 输出文件路径
        """
        if not self.results:
            raise ValueError("No results to export. Run process_batch() first.")
        
        # Prepare data for DataFrame - 仅包含用户指定的10列
        export_data = []
        for result in self.results:
            row = {
                '服务器类别': result.get('context_notes', ''),
                '产品名称': result.get('product_name', 'ECS'),
                '服务数量': result.get('host_count', 1),
                'CPU(core)': result.get('cpu_cores', 'N/A'),
                '内存(G)': result.get('memory_gb', 'N/A'),
                '存储(G)': result.get('storage_gb', 'N/A'),
                '产品规格': result.get('matched_sku', 'N/A'),
                '列表单价': result.get('price_cny_month', 'N/A'),
                '折扣': None,  # 保持空白
                '折后总价': None  # 保持空白
            }
            export_data.append(row)
        
        # Create DataFrame and export
        df = pd.DataFrame(export_data)
        df.to_excel(output_path, index=False, engine='openpyxl')
        
        print(f"✅ Results exported to: {output_path}\n")
