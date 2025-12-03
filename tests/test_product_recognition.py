#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产品识别逻辑测试 - 验证 ECS vs PolarDB 识别的准确性

测试目标：
1. 验证必须同时满足两个条件才识别为 PolarDB：
   a) 提到 PolarDB 产品名称
   b) 提到 PolarDB 的准确规格型号（如 polar.mysql.x4.large）
2. 验证只提到 PolarDB 但没有准确规格的场景正确识别为 ECS
3. 确保前后两层识别逻辑一致
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.semantic_parser import _is_polardb_request


def test_product_recognition():
    """测试产品识别逻辑"""
    
    print("="*80)
    print("🧪 产品识别逻辑测试")
    print("="*80 + "\n")
    
    # 测试用例：应该被识别为 ECS 的场景
    ecs_scenarios = [
        "16C 64G | 多维数据库",
        "32C 128G | 数据库服务器",
        "8C 32G | Redis数据库",
        "16C 64G | MySQL应用服务器",
        "4C 16G | 数据库中间件",
        "8C 32G | 缓存数据库",
        "16C 64G | Web服务器",
        "32C 128G | 应用服务器",
        "8C 16G | 中间件",
        "4C 8G | Nginx网关",
        # 新增：这些也应该被识别为 ECS
        "8C 32G | 云数据库服务",
        "16C 64G | 数据库服务 RDS",
        "4C 16G | MySQL实例",
        "8C 32G | PostgreSQL实例",
        "16C 64G | 数据库实例",
        # 核心：只提到 PolarDB 但没有准确规格，应该识别为 ECS
        "16C 64G | PolarDB数据库",
        "32C 128G | polardb实例",
        "8C 32G | PolarDB 集群",
        "16C 64G | 使用PolarDB",
        "4C 16G | Polar DB服务",
    ]
    
    # 测试用例：应该被识别为 PolarDB 的场景
    # 必须同时包含 PolarDB 关键词 + 准确规格型号
    polardb_scenarios = [
        "polar.mysql.x4.large",
        "polar.pg.x8.medium",
        "PolarDB polar.mysql.x4.large",
        "polardb实例 polar.mysql.x2.large",
        "polar.o.x4.xlarge | PolarDB集群",
    ]
    
    print("📊 测试场景 1: 应该识别为 ECS 的场景")
    print("-"*80)
    ecs_pass = 0
    ecs_fail = 0
    
    for scenario in ecs_scenarios:
        is_polardb = _is_polardb_request(scenario)
        is_ecs = not is_polardb
        
        status = "✅" if is_ecs else "❌"
        result = "ECS" if is_ecs else "PolarDB"
        
        print(f"{status} {scenario:<50} → {result}")
        
        if is_ecs:
            ecs_pass += 1
        else:
            ecs_fail += 1
    
    print(f"\n结果: {ecs_pass}/{len(ecs_scenarios)} 通过, {ecs_fail}/{len(ecs_scenarios)} 失败")
    
    print("\n" + "="*80)
    print("📊 测试场景 2: 应该识别为 PolarDB 的场景")
    print("-"*80)
    polardb_pass = 0
    polardb_fail = 0
    
    for scenario in polardb_scenarios:
        is_polardb = _is_polardb_request(scenario)
        
        status = "✅" if is_polardb else "❌"
        result = "PolarDB" if is_polardb else "ECS"
        
        print(f"{status} {scenario:<50} → {result}")
        
        if is_polardb:
            polardb_pass += 1
        else:
            polardb_fail += 1
    
    print(f"\n结果: {polardb_pass}/{len(polardb_scenarios)} 通过, {polardb_fail}/{len(polardb_scenarios)} 失败")
    
    # 总结
    print("\n" + "="*80)
    print("📈 测试总结")
    print("="*80)
    total_pass = ecs_pass + polardb_pass
    total_tests = len(ecs_scenarios) + len(polardb_scenarios)
    accuracy = (total_pass / total_tests) * 100
    
    print(f"总测试用例: {total_tests}")
    print(f"✅ 通过: {total_pass}")
    print(f"❌ 失败: {ecs_fail + polardb_fail}")
    print(f"准确率: {accuracy:.1f}%")
    
    if accuracy == 100:
        print("\n🎉 所有测试通过！产品识别逻辑正确！")
        return True
    else:
        print(f"\n⚠️  有 {ecs_fail + polardb_fail} 个测试失败，需要进一步调整识别规则")
        return False


if __name__ == "__main__":
    success = test_product_recognition()
    sys.exit(0 if success else 1)
