#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper script to create sample test data for E2E testing
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

# Sample test data
test_data = {
    'Specification': [
        '16C 64G',
        '8C 32G 数据库',
        '32C 128G 计算密集型',
        '4C 16G Web服务器'
    ],
    'Remarks': [
        '测试环境',
        '生产环境 - MySQL',
        'AI训练 - TensorFlow',
        '应用服务器'
    ]
}

# Create DataFrame
df = pd.DataFrame(test_data)

# Output path
output_path = Path(__file__).parent / 'data' / 'xlsx' / 'sample_test.xlsx'
output_path.parent.mkdir(parents=True, exist_ok=True)

# Save to Excel
df.to_excel(output_path, index=False, engine='openpyxl')

print(f"✅ Sample test data created: {output_path}")
print(f"   Total rows: {len(df)}")
