# 变更日志

## 2025-11-27 - 系统升级：SKU推荐API + 包年包月计费

### 主要变更

#### 1. SKU推荐机制升级
- **新增**: `sku_recommend_service.py` - 使用阿里云 `DescribeRecommendInstanceType` API 动态推荐实例规格
- **替代**: 旧的硬编码 SKU 匹配逻辑（`sku_matcher.py`）
- **特性**:
  - 基于 CPU 和内存自动推荐最优实例规格
  - 支持价格优先策略（`PriceFirst`）
  - API失败时自动降级到简单映射规则（兜底机制）
  - 限制推荐范围到常见实例系列（g6, c6, r6）

#### 2. 统一包年包月计费模式
- **修改**: 所有价格查询统一使用包年包月（`Subscription`/`PrePaid`）计费模式
- **参数**: `instance_charge_type="PrePaid"`
- **单位**: 按月计费（`unit="Month"`, `period=1`）

#### 3. 产品过滤机制
- **新增**: 只处理 ECS 产品，其他产品（PolarDB、WAF、云安全中心等）自动跳过
- **行为**: 非ECS产品在结果中标记为 "跳过非-ECS产品: {产品名}"
- **输出**: SKU、Instance Family、Price 字段显示为 'N/A'

### 技术实现

#### 新增文件
1. `sku_recommend_service.py` - SKU推荐服务
   - `SKURecommendService` 类
   - `recommend_instance_type()` - 调用阿里云API
   - `_fallback_sku_mapping()` - 兜底映射规则
   - `get_instance_family_name()` - 获取实例系列友好名称

#### 修改文件
1. `batch_processor.py`
   - 构造函数新增 `sku_recommend_service` 参数
   - 添加产品过滤逻辑（只处理ECS）
   - 更新日志输出（STEP标记）

2. `test_multi_sheet.py`
   - 初始化 `SKURecommendService`
   - 传递给 `BatchQuotationProcessor`

3. `requirements.txt`
   - 新增依赖：`alibabacloud_ecs20140526`

### API参数

#### DescribeRecommendInstanceType API
```python
request = DescribeRecommendInstanceTypeRequest(
    region_id="cn-beijing",
    network_type='vpc',
    cores=cpu_cores,
    memory=float(memory_gb),
    instance_charge_type="PrePaid",  # 包年包月
    io_optimized='optimized',
    priority_strategy="PriceFirst",  # 价格优先
    scene='CREATE',
    instance_type_family=['ecs.g6', 'ecs.c6', 'ecs.r6']
)
```

### 兜底规则映射表

| CPU核心数 | 内存(GB) | SKU规格 |
|----------|---------|---------|
| 2 | 8 | ecs.g6.large |
| 4 | 16 | ecs.g6.xlarge |
| 8 | 32 | ecs.g6.2xlarge |
| 16 | 64 | ecs.g6.4xlarge |
| 32 | 128 | ecs.g6.8xlarge |
| 64 | 256 | ecs.g6.16xlarge |

*不在表中的配置会自动匹配最接近的规格*

### 测试结果

#### 功能测试
- ✅ SKU推荐API调用成功
- ✅ API失败时兜底规则生效
- ✅ 包年包月价格查询成功
- ✅ 非ECS产品正确跳过
- ✅ 多工作表处理正常

#### 示例输出
```
[STEP 1] 📊 数据提取...
        ✅ 16C | 64G | 100G存储
[STEP 2] 🎯 SKU推荐: 16C 64G
[STEP 2.1] 🔍 调用 DescribeRecommendInstanceType API...
[STEP 2.2] ⚠️  API推荐失败，使用简单映射规则
[STEP 2.3] ✅ 兜底规则匹配: ecs.g6.4xlarge
        ✅ ecs.g6.4xlarge (通用型)
[STEP 3] 💰 查询价格 (包年包月)...
        ✅ ¥1,920.00 CNY / 月
```

### 向后兼容性

- ⚠️ **不兼容**: 需要同时初始化 `PricingService` 和 `SKURecommendService`
- ⚠️ **不兼容**: `BatchQuotationProcessor` 构造函数签名变更

### 迁移指南

#### 旧代码
```python
processor = BatchQuotationProcessor(
    pricing_service=pricing_service,
    region="cn-beijing"
)
```

#### 新代码
```python
# 1. 初始化SKU推荐服务
sku_recommend_service = SKURecommendService(
    access_key_id=access_key_id,
    access_key_secret=access_key_secret,
    region_id="cn-beijing"
)

# 2. 传递给批处理器
processor = BatchQuotationProcessor(
    pricing_service=pricing_service,
    sku_recommend_service=sku_recommend_service,
    region="cn-beijing"
)
```

### 已知问题

1. **实例库存不足**: 当指定实例系列库存不足时，API返回 `RecommendEmpty.InstanceTypeSoldOut`，系统会自动降级到兜底规则
2. **定价计划缺失**: 部分推荐的实例类型可能在包年包月定价系统中不可用，返回 `PRICE.PRICING_PLAN_RESULT_NOT_FOUND`

### 未来改进

1. 支持更多产品类型的询价（PolarDB、WAF、云安全中心）
2. 动态调整实例系列过滤器
3. 缓存API推荐结果减少调用次数
4. 支持多地域实例推荐
