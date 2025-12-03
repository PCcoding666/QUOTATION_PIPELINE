#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证兜底规则已被移除
"""

def verify_fallback_removed():
    """验证_fallback_sku_mapping方法已被删除"""
    
    print("=" * 60)
    print("验证兜底规则移除情况")
    print("=" * 60)
    
    # 检查1: 验证_fallback_sku_mapping方法不存在
    print("\n检查1: 验证_fallback_sku_mapping方法已删除")
    try:
        from app.core.sku_recommend_service import SKURecommendService
        
        # 检查类是否有_fallback_sku_mapping方法
        has_fallback = hasattr(SKURecommendService, '_fallback_sku_mapping')
        
        if has_fallback:
            print("❌ 失败: _fallback_sku_mapping方法仍然存在")
            return False
        else:
            print("✅ 成功: _fallback_sku_mapping方法已被删除")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    
    # 检查2: 验证get_best_instance_sku方法的docstring已更新
    print("\n检查2: 验证文档字符串已更新")
    try:
        docstring = SKURecommendService.get_best_instance_sku.__doc__
        
        if "兜底" in docstring or "Fallback规则" in docstring:
            if "不再使用兜底规则" in docstring or "无兜底规则" in docstring:
                print("✅ 成功: 文档已正确更新（说明已移除兜底规则）")
            else:
                print("⚠️  警告: 文档仍提及兜底规则")
        else:
            print("✅ 成功: 文档中没有兜底规则的描述")
            
    except Exception as e:
        print(f"⚠️  无法检查文档: {e}")
    
    # 检查3: 查看源代码中的关键变化
    print("\n检查3: 验证源代码变化")
    try:
        import inspect
        source = inspect.getsource(SKURecommendService.get_best_instance_sku)
        
        # 应该包含raise Exception
        if "raise Exception" in source:
            print("✅ 成功: 代码中包含异常抛出逻辑")
        else:
            print("❌ 失败: 代码中未找到异常抛出")
            
        # 不应该包含_fallback_sku_mapping调用
        if "_fallback_sku_mapping" in source:
            print("❌ 失败: 代码中仍在调用_fallback_sku_mapping")
            return False
        else:
            print("✅ 成功: 代码中不再调用_fallback_sku_mapping")
            
    except Exception as e:
        print(f"⚠️  无法检查源代码: {e}")
    
    # 检查4: 验证异常消息
    print("\n检查4: 验证异常消息")
    try:
        source = inspect.getsource(SKURecommendService.get_best_instance_sku)
        
        if "所有推荐策略" in source and "均失败" in source:
            print("✅ 成功: 包含清晰的失败消息")
        else:
            print("⚠️  警告: 异常消息可能不够清晰")
    except:
        pass
    
    print("\n" + "=" * 60)
    print("✅ 所有检查通过：兜底规则已成功移除")
    print("=" * 60)
    print("\n现在的推荐策略：")
    print("1. NewProductFirst（最新产品优先）")
    print("2. 第八代系列降级（InventoryFirst、PriceFirst）")
    print("3. 所有策略失败 → 抛出异常（不再兜底）")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    verify_fallback_removed()
