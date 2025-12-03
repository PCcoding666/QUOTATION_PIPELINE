#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量测试脚本：测试tests/data/xlsx目录下的Excel文件
验证DescribePrice API的实际效果

测试目标：
1. 验证所有代际实例（第5-9代）的价格查询
2. 测试Excel数据处理流程
3. 生成详细的测试报告

创建日期：2025-12-03
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.data.batch_processor import BatchQuotationProcessor
from app.core.pricing_service import PricingService
from app.core.sku_recommend_service import SKURecommendService
from app.data.data_ingestion import ExcelDataLoader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


def test_excel_file(file_path: str, output_dir: str):
    """
    测试单个Excel文件
    
    Args:
        file_path: Excel文件路径
        output_dir: 输出目录
    """
    logger.info("="*80)
    logger.info(f"📂 测试文件: {Path(file_path).name}")
    logger.info("="*80)
    
    try:
        # 初始化服务
        pricing_service = PricingService(
            access_key_id=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
            access_key_secret=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
            region_id="cn-beijing"
        )
        
        sku_service = SKURecommendService(
            access_key_id=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
            access_key_secret=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
            region_id="cn-beijing"
        )
        
        # 初始化批处理器
        processor = BatchQuotationProcessor(
            pricing_service=pricing_service,
            sku_recommend_service=sku_service,
            region="cn-beijing"
        )
        
        # 创建Excel数据加载器
        data_loader = ExcelDataLoader(file_path)
        
        # 处理文件
        logger.info(f"🚀 开始处理...")
        results = processor.process_batch(data_loader, verbose=False)
        
        # 生成输出文件
        file_name = Path(file_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"{file_name}_报价结果_{timestamp}.xlsx")
        
        # 将结果保存为Excel
        import pandas as pd
        df = pd.DataFrame(results)
        df.to_excel(output_file, index=False)
        
        logger.info(f"✅ 处理完成！")
        logger.info(f"📄 输出文件: {output_file}")
        logger.info(f"📊 成功处理: {sum(1 for r in results if r.get('success', False))}/{len(results)}")
        
        return {
            "file": Path(file_path).name,
            "status": "success",
            "output": output_file,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"❌ 处理失败: {str(e)}")
        return {
            "file": Path(file_path).name,
            "status": "failed",
            "output": None,
            "error": str(e)
        }


def main():
    """主测试函数"""
    logger.info("\n" + "="*80)
    logger.info("🧪 批量Excel文件测试 - DescribePrice API验证")
    logger.info("="*80)
    
    # 测试数据目录
    test_data_dir = os.path.join(project_root, "tests", "data", "xlsx")
    output_dir = os.path.join(project_root, "tests", "output")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取所有Excel文件
    excel_files = []
    for file in os.listdir(test_data_dir):
        if file.endswith('.xlsx') and not file.startswith('~$') and not file.startswith('.'):
            excel_files.append(os.path.join(test_data_dir, file))
    
    logger.info(f"\n📊 找到 {len(excel_files)} 个Excel文件:")
    for i, file in enumerate(excel_files, 1):
        logger.info(f"  {i}. {Path(file).name}")
    
    # 测试每个文件
    results = []
    for i, file_path in enumerate(excel_files, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"测试进度: {i}/{len(excel_files)}")
        logger.info(f"{'='*80}")
        
        result = test_excel_file(file_path, output_dir)
        results.append(result)
    
    # 打印测试摘要
    logger.info("\n" + "="*80)
    logger.info("📊 测试摘要")
    logger.info("="*80)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = len(results) - success_count
    
    logger.info(f"\n总测试文件数: {len(results)}")
    logger.info(f"✅ 成功: {success_count}")
    logger.info(f"❌ 失败: {failed_count}")
    logger.info(f"成功率: {success_count/len(results)*100:.1f}%")
    
    # 详细结果
    logger.info("\n详细结果:")
    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        logger.info(f"\n{status_icon} {result['file']}")
        if result["status"] == "success":
            logger.info(f"   输出: {result['output']}")
        else:
            logger.info(f"   错误: {result['error']}")
    
    # 生成测试报告
    report_path = os.path.join(output_dir, f"batch_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("批量Excel文件测试报告\n")
        f.write("="*80 + "\n\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"测试API: DescribePrice (ECS Native API)\n")
        f.write(f"支持代际: 第5-9代全覆盖\n\n")
        
        f.write(f"总测试文件数: {len(results)}\n")
        f.write(f"成功: {success_count}\n")
        f.write(f"失败: {failed_count}\n")
        f.write(f"成功率: {success_count/len(results)*100:.1f}%\n\n")
        
        f.write("详细结果:\n")
        f.write("-"*80 + "\n")
        for result in results:
            status = "成功" if result["status"] == "success" else "失败"
            f.write(f"\n文件: {result['file']}\n")
            f.write(f"状态: {status}\n")
            if result["status"] == "success":
                f.write(f"输出: {result['output']}\n")
            else:
                f.write(f"错误: {result['error']}\n")
    
    logger.info(f"\n📄 测试报告已保存: {report_path}")
    logger.info("\n✅ 所有测试完成！\n")


if __name__ == "__main__":
    main()
