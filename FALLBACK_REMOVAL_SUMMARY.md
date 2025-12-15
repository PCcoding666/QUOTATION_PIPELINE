# 兜底规则移除总结

## 背景

用户发现配置 `256C 1024G 6000GB` 被推荐为 `ecs.g6.16xlarge (第6代)`，这是因为触发了兜底规则。

### 问题原因分析

1. **NewProductFirst 策略失败**：该超大配置在目标区域可能缺货或不支持
2. **第八代系列降级失败**：InventoryFirst 和 PriceFirst 策略也无法推荐
3. **触发兜底规则**：`_fallback_sku_mapping()` 方法使用硬编码映射表
   - 映射表最大只到 `64C 256G → ecs.g6.16xlarge`
   - 通过模糊匹配，将 `256C 1024G` 匹配到了最接近的 `ecs.g6.16xlarge`

### 用户要求

> "如果是触发了兜底，那么现在请你把所有的兜底规则删除，如果错误了，直接报错"

## 修改内容

### 1. 删除兜底方法

**文件**: `app/core/sku_recommend_service.py`

**删除的方法**: `_fallback_sku_mapping(cpu_cores, memory_gb)`（第196-232行，共37行）

```python
# 已删除的代码
def _fallback_sku_mapping(self, cpu_cores: int, memory_gb: float) -> str:
    """简单的SKU映射规则（当API调用失败时使用）"""
    sku_map = {
        (2, 8): "ecs.g6.large",
        (4, 16): "ecs.g6.xlarge",
        (8, 32): "ecs.g6.2xlarge",
        (16, 64): "ecs.g6.4xlarge",
        (32, 128): "ecs.g6.8xlarge",
        (64, 256): "ecs.g6.16xlarge",
    }
    # 精确匹配 + 模糊匹配逻辑
    ...
```

### 2. 修改推荐逻辑

**修改前**（第187-194行）：
```python
# 第三步：本地映射规则兜底
logger.warning(f"[STEP 2.3] ⚠️  所有API策略均失败，使用本地映射规则兜底")
recommended_sku = self._fallback_sku_mapping(req.cpu_cores, req.memory_gb)
logger.info(f"[STEP 2.3] ✅ 兜底规则匹配: {recommended_sku}")
return recommended_sku
```

**修改后**（第187-201行）：
```python
# 第三步：所有策略失败，抛出错误
logger.error(f"[STEP 2.3] ❌ 所有API策略均失败，无法推荐实例规格")
raise Exception(
    f"无法为 {req.cpu_cores}C {req.memory_gb}G 推荐合适的实例规格。\n"
    f"所有推荐策略（NewProductFirst、第八代降级）均失败。\n"
    f"可能原因：\n"
    f"1. 该配置规格过大或过小，超出API推荐范围\n"
    f"2. 目标区域（{self.region_id}）该配置实例缺货\n"
    f"3. 网络连接问题或API调用失败"
)
```

### 3. 更新文档字符串

**修改前**：
```python
"""
根据资源需求获取最佳实例规格（支持两级推荐机制）

推荐策略：
1. NewProductFirst（最新产品优先）
2. 第八代系列（g8y/c8y/r8y）
3. Fallback规则 - 本地映射表兜底
```

**修改后**：
```python
"""
根据资源需求获取最佳实例规格（两级推荐机制，无兜底规则）

推荐策略：
1. NewProductFirst（最新产品优先）
2. 第八代系列（g8y/c8y/r8y）
3. 所有策略失败 - 抛出异常，不再使用兜底规则

Raises:
    Exception: 当所有推荐策略都失败时抛出
```

## 现在的推荐流程

```
┌─────────────────────────────────────────┐
│  STEP 2.1: NewProductFirst              │
│  （最新产品优先，不限制实例系列）       │
└──────────────┬──────────────────────────┘
               │
               ├── 成功 → 返回推荐的SKU
               │
               └── 失败 ↓
                         
┌─────────────────────────────────────────┐
│  STEP 2.2: 第八代系列降级               │
│  限制: ecs.g8y, ecs.c8y, ecs.r8y        │
│  策略1: InventoryFirst (库存优先)       │
│  策略2: PriceFirst (价格优先)           │
└──────────────┬──────────────────────────┘
               │
               ├── 成功 → 返回推荐的SKU
               │
               └── 失败 ↓
                         
┌─────────────────────────────────────────┐
│  STEP 2.3: 抛出异常                     │
│  ❌ 所有推荐策略均失败                  │
│  🚫 不再使用兜底规则                    │
└─────────────────────────────────────────┘
```

## 验证结果

运行验证脚本 `tests/verify_no_fallback.py`：

```
✅ 检查1: _fallback_sku_mapping方法已被删除
✅ 检查2: 文档已正确更新（说明已移除兜底规则）
✅ 检查3: 代码中包含异常抛出逻辑，不再调用_fallback_sku_mapping
✅ 检查4: 包含清晰的失败消息

✅ 所有检查通过：兜底规则已成功移除
```

## 影响范围

### 正常配置（16C 64G 等常见规格）
- ✅ **无影响**：NewProductFirst 或第八代降级可以正常推荐
- 预期推荐：`ecs.g9i.4xlarge` 或 `ecs.g8y.4xlarge`

### 超大/特殊配置（256C 1024G 等）
- ❌ **会抛出异常**：所有API策略失败后不再兜底
- 异常消息清晰说明失败原因和可能的解决方向
- 用户需要：
  1. 检查该配置是否在目标区域可用
  2. 联系阿里云确认实例规格支持情况
  3. 考虑调整配置需求

## 代码变更统计

- **删除行数**: 44行
- **修改行数**: 16行
- **文件数**: 1个 (`app/core/sku_recommend_service.py`)

## 后续建议

1. **监控异常率**：观察实际使用中有多少配置会触发异常
2. **优化API策略**：如果异常率高，考虑添加更多降级策略
3. **增强错误处理**：在批处理层面捕获异常，跳过失败的配置并记录
4. **区域切换支持**：允许用户尝试其他区域的实例推荐

## 相关文件

- 核心修改：`app/core/sku_recommend_service.py`
- 验证脚本：`tests/verify_no_fallback.py`
- 本文档：`FALLBACK_REMOVAL_SUMMARY.md`
