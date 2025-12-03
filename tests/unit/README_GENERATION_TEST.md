# 阿里云API代际支持测试

## 📋 测试目标

本测试用于验证阿里云两个核心API对不同代际ECS实例的支持情况：

1. **DescribeRecommendInstanceType API** - 支持推荐到哪个代际的实例？
2. **GetSubscriptionPrice API** - 支持查询哪些代际实例的包年包月定价？

## 🔍 测试内容

### 测试1: 推荐API代际支持
- 测试配置: 4C16G、8C32G、16C64G
- 测试策略: NewProductFirst、InventoryFirst、PriceFirst
- 验证: API实际推荐的实例代际分布

### 测试2: 价格API代际支持
- 测试代际: 第5代 ~ 第9代
- 测试类型: 通用型(g系列)、计算型(c系列)、内存型(r系列)
- 验证: 哪些实例规格有包年包月定价

### 测试3: 推荐-价格兼容性
- 核心问题: 推荐成功的实例是否有定价？
- 验证: 哪些代际存在"推荐成功但无定价"的问题

## 🚀 快速开始

### 前置条件

1. **配置阿里云凭证**（必需）

在项目根目录的 `.env` 文件中配置：

```bash
ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret
```

2. **安装依赖**

```bash
pip install -r requirements.txt
pip install pytest pytest-html
```

### 运行测试

#### 方法1: 使用测试脚本（推荐）

```bash
./run_generation_support_test.sh
```

#### 方法2: 直接运行pytest

```bash
python -m pytest tests/unit/test_api_generation_support.py -v -s
```

#### 方法3: 运行单个测试

```bash
# 仅测试推荐API
python -m pytest tests/unit/test_api_generation_support.py::TestDescribeRecommendInstanceTypeSupport -v -s

# 仅测试价格API
python -m pytest tests/unit/test_api_generation_support.py::TestGetSubscriptionPriceSupport -v -s

# 仅测试兼容性
python -m pytest tests/unit/test_api_generation_support.py::TestRecommendAndPricingIntegration -v -s
```

## 📊 测试输出

### 输出文件

测试完成后会生成以下文件：

```
tests/output/
├── api_generation_support_test.log          # 完整测试日志
├── api_generation_support_report.md         # Markdown测试报告
└── api_generation_support_report.html       # HTML测试报告（如果安装了pytest-html）
```

### 查看报告

```bash
# 查看Markdown报告
cat tests/output/api_generation_support_report.md

# 在浏览器中查看HTML报告
open tests/output/api_generation_support_report.html  # macOS
```

### 控制台输出示例

```
================================================================================
测试1：DescribeRecommendInstanceType API - 代际支持情况
================================================================================

────────────────────────────────────────────────────────────────
📊 测试配置: 4C16G - 小规格
────────────────────────────────────────────────────────────────

🔍 策略: 新品优先 (NewProductFirst)
✅ 推荐成功: ecs.g9i.xlarge (第9代)

🔍 策略: 库存优先 (InventoryFirst)
✅ 推荐成功: ecs.g6.xlarge (第6代)

🔍 策略: 价格优先 (PriceFirst)
✅ 推荐成功: ecs.g6.xlarge (第6代)

================================================================================
📊 DescribeRecommendInstanceType API 代际支持汇总
================================================================================

配置: 4C16G - 小规格
  NewProductFirst      → ecs.g9i.xlarge        (第9代)
  InventoryFirst       → ecs.g6.xlarge         (第6代)
  PriceFirst           → ecs.g6.xlarge         (第6代)

代际推荐统计:
  第9代: 3 次
  第6代: 6 次
────────────────────────────────────────────────────────────────
```

## 📈 预期测试结果

根据 `TECHNICAL_ISSUES_ANALYSIS.md` 中的分析，预期结果如下：

### DescribeRecommendInstanceType API

| 推荐策略 | 主要推荐代际 | 说明 |
|---------|------------|------|
| NewProductFirst | 第9代（g9i/c9i） | ✅ 可推荐最新实例 |
| InventoryFirst | 第6代（g6/c6） | ✅ 可推荐库存充足实例 |
| PriceFirst | 第6代（g6/c6） | ✅ 可推荐价格低实例 |

**结论**: API支持推荐第5代~第9代所有实例

### GetSubscriptionPrice API

| 代际 | 预期结果 | 说明 |
|-----|---------|------|
| 第9代（g9i/c9i） | ❌ 无定价 | PRICING_PLAN_RESULT_NOT_FOUND |
| 第8代（g8y/c8y） | ❓ 待验证 | 可能有定价 |
| 第7代（g7/c7） | ✅ 有定价 | 成熟商用实例 |
| 第6代（g6/c6） | ✅ 有定价 | 成熟商用实例 |
| 第5代（g5/c5） | ❓ 待验证 | 可能已停售 |

**核心问题**: 第9代实例可以推荐，但查不到包年包月价格

### 兼容性问题

| 配置 | NewProductFirst | InventoryFirst | PriceFirst |
|-----|----------------|----------------|------------|
| 4C16G | ❌ g9i有推荐无定价 | ✅ g6有推荐有定价 | ✅ g6有推荐有定价 |
| 8C32G | ❌ g9i有推荐无定价 | ✅ g6有推荐有定价 | ✅ g6有推荐有定价 |
| 16C64G | ❌ g9i有推荐无定价 | ✅ g6有推荐有定价 | ✅ g6有推荐有定价 |

**兼容率**: 约 66.7% (2/3策略兼容)

## 🎯 测试用例详情

测试覆盖的实例规格：

### 第9代实例
- `ecs.g9i.xlarge` - 第9代通用型（4C 16G）
- `ecs.c9i.2xlarge` - 第9代计算型（8C 16G）
- `ecs.r9i.xlarge` - 第9代内存型（4C 32G）
- `ecs.c9ae.2xlarge` - 第9代ARM计算型（8C 16G）

### 第8代实例
- `ecs.g8y.xlarge` - 第8代通用型（4C 16G）
- `ecs.c8y.2xlarge` - 第8代计算型（8C 16G）
- `ecs.r8y.xlarge` - 第8代内存型（4C 32G）
- `ecs.g8i.xlarge` - 第8代Intel通用型（4C 16G）

### 第7代实例
- `ecs.g7.xlarge` - 第7代通用型（4C 16G）
- `ecs.c7.2xlarge` - 第7代计算型（8C 16G）
- `ecs.r7.xlarge` - 第7代内存型（4C 32G）

### 第6代实例
- `ecs.g6.xlarge` - 第6代通用型（4C 16G）
- `ecs.c6.2xlarge` - 第6代计算型（8C 16G）
- `ecs.r6.xlarge` - 第6代内存型（4C 32G）

### 第5代实例
- `ecs.g5.xlarge` - 第5代通用型（4C 16G）
- `ecs.c5.2xlarge` - 第5代计算型（8C 16G）
- `ecs.r5.xlarge` - 第5代内存型（4C 32G）

## 🔧 故障排查

### 问题1: 凭证未配置

**错误信息**:
```
❌ 错误: 未配置阿里云凭证环境变量
```

**解决方法**:
在 `.env` 文件中配置阿里云凭证：
```bash
ALIBABA_CLOUD_ACCESS_KEY_ID=LTAI5t...
ALIBABA_CLOUD_ACCESS_KEY_SECRET=xxx...
```

### 问题2: pytest未安装

**错误信息**:
```
ModuleNotFoundError: No module named 'pytest'
```

**解决方法**:
```bash
pip install pytest pytest-html
```

### 问题3: 所有测试跳过

**错误信息**:
```
SKIPPED [1] tests/unit/test_api_generation_support.py:未配置阿里云凭证，跳过测试
```

**解决方法**:
检查 `.env` 文件是否正确配置，并确保环境变量已加载。

### 问题4: API调用失败

**可能原因**:
1. 网络问题 - 检查网络连接
2. 凭证权限不足 - 确保AccessKey有ECS和BSS权限
3. 区域不可用 - 某些实例规格在特定区域不可用

## 📚 相关文档

- [TECHNICAL_ISSUES_ANALYSIS.md](../../TECHNICAL_ISSUES_ANALYSIS.md) - 技术问题详细分析
- [DescribeRecommendInstanceType API文档](https://help.aliyun.com/zh/ecs/developer-reference/api-ecs-2014-05-26-describerecommendinstancetype)
- [GetSubscriptionPrice API文档](https://help.aliyun.com/zh/user-center/developer-reference/api-bssopenapi-2017-12-14-getsubscriptionprice)

## 💡 测试结果应用

基于测试结果，可以：

1. **优化推荐策略**
   - 避免使用推荐无定价实例的策略（如NewProductFirst）
   - 优先使用InventoryFirst或PriceFirst策略

2. **实现闭环验证**
   - 在推荐后立即验证价格
   - 价格查询失败时自动切换策略

3. **限制实例系列**
   - 仅推荐有定价的实例代际（第6代、第7代）
   - 避免推荐第9代等无定价实例

4. **更新文档**
   - 明确说明支持的代际范围
   - 警告可能的兼容性问题

---

**创建日期**: 2025-12-03  
**最后更新**: 2025-12-03  
**维护者**: AI助手
