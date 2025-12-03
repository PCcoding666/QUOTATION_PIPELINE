#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证Storage (GB)是否正确作为数据盘参数传入价格查询
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

# 读取之前的测试输出（修复前）
old_file = 'tests/output/output_00-YonBIP部署方案-v5-20251125_20251203_155537.xlsx'
df_old = pd.read_excel(old_file)

print("="*80)
print("修复前的测试数据分析")
print("="*80)
print(f"\n总记录数: {len(df_old)}")

# 统计不同Storage值的记录数
print("\nStorage (GB) 分布:")
storage_counts = df_old['Storage (GB)'].value_counts().sort_index()
for storage, count in storage_counts.items():
    print(f"  {storage:>6} GB: {count:>3} 条记录")

# 查看相同SKU但不同Storage的价格是否相同
print("\n检查: 相同SKU但不同Storage的价格是否相同?")
print("(如果相同,说明Storage未生效)")

# 找一个常见的SKU
print("\nSKU统计:")
sku_counts = df_old['Matched SKU'].value_counts().head(10)
for sku, count in sku_counts.items():
    print(f"  {sku}: {count} 条记录")

# 选择第一个出现多次的SKU进行分析
for common_sku in sku_counts.index:
    sku_data = df_old[df_old['Matched SKU'] == common_sku][['Storage (GB)', 'Price (CNY/Month)']].drop_duplicates().sort_values('Storage (GB)')
    if len(sku_data) > 1:
        break

print(f"\nSKU: {common_sku}")
print(sku_data.to_string(index=False))

if len(sku_data) > 1:
    unique_prices = sku_data['Price (CNY/Month)'].nunique()
    if unique_prices == 1:
        print("\n❌ 问题确认: 不同Storage值但价格相同 → Storage未生效!")
    else:
        print("\n✅ Storage值不同,价格也不同 → Storage已生效")
else:
    print("\n(该SKU只有一种Storage配置,无法对比)")

# 显示一些具体案例
print("\n具体案例:")
samples = df_old[df_old['Matched SKU'] == common_sku][
    ['Original Content', 'Storage (GB)', 'Matched SKU', 'Price (CNY/Month)']
].head(5)
print(samples.to_string(index=False))

print("\n" + "="*80)
print("验证结论:")
print("="*80)
print("根据上述分析,修复前的代码中:")
print("1. Excel中确实包含了多种Storage值 (100GB ~ 36900GB)")
print("2. 相同SKU在不同Storage下的价格需要观察是否相同")
print("3. 如果价格完全相同,说明Storage参数未被传递到价格查询API")
print("\n修复方案:")
print("已在 batch_processor.py 中添加:")
print("  data_disk_size = result.get('storage_gb', 100)")
print("  pricing_service.get_official_price(..., data_disk_size=data_disk_size)")
print("\n下次运行时,价格应该会根据Storage值变化!")
