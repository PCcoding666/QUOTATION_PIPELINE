# Phase 6 - End-to-End Integration Testing Guide

## 🎯 测试目标

验证整个报价管道在真实环境中的完整功能：
- ✅ 环境配置完整性
- ✅ AI解析服务连接性 (DashScope Qwen-Max)
- ✅ 价格查询服务连接性 (Alibaba Cloud BSS)
- ✅ 批量处理数据完整性
- ✅ 输出结果准确性

## 🚀 快速开始

### 方式1: 使用Shell脚本 (推荐)

```bash
# 在项目根目录执行
./run_e2e_tests.sh
```

脚本会自动:
1. 检查Python环境
2. 验证.env配置
3. 创建必要的目录
4. 生成示例测试数据(如果不存在)
5. 运行测试套件
6. 显示日志文件位置

### 方式2: 直接运行Python脚本

```bash
# 在项目根目录执行
python3 tests/test_e2e_real_world.py
```

## 📋 测试前准备清单

### 1. 环境配置

确保 `.env` 文件存在并包含以下变量:

```bash
# 阿里云API密钥 (用于BSS价格查询)
ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret

# DashScope API密钥 (用于Qwen-Max AI解析)
DASHSCOPE_API_KEY=your_dashscope_api_key
```

### 2. 依赖安装

```bash
pip3 install -r requirements.txt
```

必需的依赖包:
- `alibabacloud_bssopenapi20171214` - BSS OpenAPI SDK
- `python-dotenv` - 环境变量管理
- `pandas` - 数据处理
- `openpyxl` - Excel读写
- `requests` - HTTP客户端

### 3. 测试数据准备

**选项A: 自动生成示例数据**

```bash
python3 tests/create_sample_test_data.py
```

**选项B: 使用自定义数据**

将Excel文件放入 `tests/data/xlsx/` 目录:

```
tests/
└── data/
    └── xlsx/
        ├── your_test_file1.xlsx
        └── your_test_file2.xlsx
```

Excel格式要求:
- **必须列**: 包含"Spec"、"规格"或"配置"的列
- **可选列**: 包含"Remark"、"备注"或"Note"的列

示例:

| Specification | Remarks |
|---------------|---------|
| 16C 64G | 生产环境 |
| 8C 32G 数据库 | MySQL主库 |
| 32C 128G 计算密集型 | AI训练服务器 |

## 🧪 测试用例详解

### Test Case 1: Environment Health Check

**目的**: 验证运行环境配置

**验证项**:
- [x] `.env` 文件存在
- [x] `ALIBABA_CLOUD_ACCESS_KEY_ID` 已配置且非空
- [x] `ALIBABA_CLOUD_ACCESS_KEY_SECRET` 已配置且非空
- [x] `DASHSCOPE_API_KEY` 已配置且非空

**预期输出**:
```
>>> [TEST CASE 1] Environment Health Check
✅ .env file exists
✅ ALIBABA_CLOUD_ACCESS_KEY_ID loaded (length: 24)
✅ DASHSCOPE_API_KEY loaded (length: 48)
🎉 Environment variables loaded successfully
```

### Test Case 2: Component Connectivity

**目的**: 验证核心组件的网络连接性

**Part 1: AI Parser (Qwen-Max)**
- 发送测试文本: `"Test 16C 64G"`
- 验证AI返回有效JSON
- 断言: `cpu=16`

**Part 2: Pricing Service (BSS OpenAPI)**
- 查询固定SKU: `ecs.g6.large`
- 区域: `cn-beijing`
- 断言: `price > 0`

**预期输出**:
```
>>> [TEST CASE 2] Component Connectivity (Smoke Test)
>>> [STEP 1] Testing AI Parser (DashScope Qwen-Max)...
🤖 AI analyzing intent via Qwen-Max...
✅ AI Result: 16C 64G -> general (General purpose configuration)
✅ AI Parser OK - Parsed as: 16C 64G

>>> [STEP 2] Testing Pricing Service (BSS OpenAPI)...
✅ Pricing Service OK - Price: ¥342.00 CNY/Month
🎉 Smoke tests for AI and BSS passed
```

### Test Case 3: Real Data Batch Processing

**目的**: 验证端到端批量处理能力

**处理流程**:
```
1. 扫描 tests/data/xlsx/ 目录
2. 加载所有 .xlsx / .xls 文件
3. 对每个文件:
   a. 数据加载 (ExcelDataLoader)
   b. AI解析 (SemanticParser + Qwen-Max)
   c. SKU匹配 (SkuMatcher)
   d. 价格查询 (PricingService + BSS)
   e. 结果导出 (Excel)
4. 验证输出文件
```

**验证项**:
- [x] 输出文件已生成
- [x] 输出包含 `Price (CNY/Month)` 列
- [x] 统计成功/失败行数
- [x] 记录所有错误详情

**预期输出**:
```
>>> [TEST CASE 3] Real Data Batch Processing
>>> [STEP 1] Scanning test data directory...
📁 Found 1 Excel file(s) to process

>>> [FILE 1/1] Processing: sample_test.xlsx
>>> [STEP 3.1] Loading data from Excel...
✅ Using columns - Spec: 'Specification', Remarks: 'Remarks'
✅ Loaded 4 valid row(s)

>>> [STEP 3.2] Running batch quotation pipeline...
─── Processing Row 1/4 ───
✅ [1] 16C 64G -> ecs.g7.4xlarge -> ¥1,234.56

>>> [STEP 3.3] Exporting results to Excel...
✅ Output saved to: tests/output/output_sample_test_20241126_103000.xlsx

>>> [STEP 3.4] Validating output file...
✅ Output file exists
✅ 'Price (CNY/Month)' column exists
📊 Results: 4 success, 0 failed
✅ Processed file [sample_test.xlsx]: 4 successes, 0 failures
🎉 All batch processing tests passed
```

## 📊 日志系统

### 双输出架构

**控制台 (INFO级别)**:
- 用户友好的进度信息
- 关键步骤的成功/失败状态
- 测试汇总结果

**日志文件 (DEBUG级别)**:
- 完整的调试信息
- API调用详情
- 异常堆栈跟踪

### 日志文件位置

```
logs/
└── e2e_test_run_YYYYMMDD_HHMMSS.log
```

### 日志格式

**控制台**:
```
[2024-11-26 10:30:00] [INFO] - ✅ Environment variables loaded successfully
```

**文件**:
```
[2024-11-26 10:30:00] [DEBUG] [test_e2e_real_world:89] - Checking .env file at: /path/to/.env
```

### 日志级别说明

| 级别 | 用途 | 输出位置 |
|------|------|----------|
| DEBUG | 详细调试信息 | 仅文件 |
| INFO | 关键步骤信息 | 控制台 + 文件 |
| WARNING | 警告信息 | 控制台 + 文件 |
| ERROR | 错误信息 | 控制台 + 文件 |

## 📈 输出结果

### 测试汇总

```
====================================================================================================
📊 TEST EXECUTION SUMMARY
====================================================================================================
✅ PASSED    | Environment Health Check
✅ PASSED    | Component Connectivity
✅ PASSED    | Real Data Batch Processing
====================================================================================================
Total: 3 | Passed: 3 | Failed: 0
====================================================================================================

🎉 ALL TESTS PASSED - Pipeline is production-ready!
```

### 退出代码

| 代码 | 含义 |
|------|------|
| 0 | 所有测试通过 |
| 1 | 至少一个测试失败 |
| 130 | 用户中断 (Ctrl+C) |

### 输出文件

处理后的Excel文件保存在:

```
tests/output/
└── output_<原文件名>_<时间戳>.xlsx
```

输出文件包含以下列:
- `Source ID` - 数据来源标识
- `Original Content` - 原始规格文本
- `Context Notes` - 备注信息
- `CPU Cores` - 解析的CPU核心数
- `Memory (GB)` - 解析的内存大小
- `Storage (GB)` - 解析的存储大小
- `Environment` - 环境类型
- `Workload Type` - 工作负载类型
- `Matched SKU` - 匹配的实例SKU
- `Instance Family` - 实例族名称
- `Price (CNY/Month)` - 月度价格 ⭐
- `Status` - 处理状态 (Success/Failed)
- `Error` - 错误信息 (如果失败)

## 🔍 故障排查

### 常见问题

#### 问题1: 环境变量未加载

**症状**:
```
❌ DASHSCOPE_API_KEY is empty or not set
```

**解决方案**:
1. 确认 `.env` 文件在项目根目录
2. 检查文件格式:
   ```bash
   # 正确格式
   DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxx
   
   # 错误格式 (不要使用引号)
   DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxx"
   ```
3. 确保没有多余空格

#### 问题2: API调用失败

**症状**:
```
❌ API Error: InvalidAccessKeyId
```

**解决方案**:
1. 验证AccessKey是否正确
2. 检查网络连接
3. 确认账户状态正常
4. 验证API权限是否充足

#### 问题3: 无测试数据

**症状**:
```
⚠️  No Excel files found in: tests/data/xlsx
```

**解决方案**:
```bash
# 生成示例数据
python3 tests/create_sample_test_data.py
```

#### 问题4: 价格查询失败

**症状**:
```
❌ API Error: Forbidden.RAM
```

**解决方案**:
1. 确认RAM角色有BSS OpenAPI权限
2. 在阿里云控制台授予权限:
   - `AliyunBSSReadOnlyAccess` (只读权限)
   - `AliyunBSSFullAccess` (完全权限)

#### 问题5: AI解析失败

**症状**:
```
⚠️ AI parsing failed: ... Falling back to regex rules.
```

**解决方案**:
1. 检查DashScope API Key是否有效
2. 确认qwen-max模型可用
3. 检查网络连接
4. 回退规则引擎会自动启用，不影响功能

### 调试步骤

1. **查看详细日志**:
   ```bash
   cat logs/e2e_test_run_*.log
   ```

2. **逐个测试用例运行**:
   编辑 `test_e2e_real_world.py`，注释掉不需要的测试

3. **手动验证API连接**:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   
   # 测试Qwen-Max
   from semantic_parser import parse_with_qwen
   result = parse_with_qwen("16C 64G")
   print(result)
   
   # 测试BSS
   from pricing_service import PricingService
   import os
   pricing = PricingService(
       os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
       os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
   )
   price = pricing.get_official_price("ecs.g6.large")
   print(price)
   ```

## 📖 详细步骤日志示例

测试过程中，每个主要步骤都会生成详细日志:

```
>>> [STEP 1] Loading Data from tests/data/xlsx/sample_test.xlsx
[DEBUG] File path: /Users/.../sample_test.xlsx
[DEBUG] Available columns: ['Specification', 'Remarks']
[INFO] ✅ Using columns - Spec: 'Specification', Remarks: 'Remarks'
[INFO] ✅ Loaded 4 valid row(s)

>>> [STEP 2] AI Parsing Row 1...
[DEBUG] Source: Row 2
[DEBUG] Content: 16C 64G
[INFO] 🤖 AI analyzing intent via Qwen-Max...
[DEBUG] Sending test input: '16C 64G'
[DEBUG] AI Response: CPU=16, Memory=64, Workload=general
[INFO] ✅ Intent Detected: General Purpose

>>> [STEP 3] SKU Matching...
[DEBUG] Requirement: 16C, 64G, general
[INFO] ✅ Mapped to ecs.g7.4xlarge

>>> [STEP 4] Fetching Price...
[DEBUG] Querying price for: ecs.g7.4xlarge in cn-beijing
[DEBUG] Price received: ¥1234.56
[INFO] ✅ ¥1,234.56 CNY / Month
```

## 🎯 性能基准

**预期执行时间** (取决于网络和数据量):

| 测试用例 | 耗时 |
|---------|------|
| Environment Health Check | <1s |
| Component Connectivity | 3-5s |
| Batch Processing (4行) | 10-15s |
| Batch Processing (100行) | 3-5分钟 |

**API调用次数** (对于4行测试数据):
- DashScope API: 4次 (每行1次AI解析)
- BSS API: 4次 (每行1次价格查询)

## ⚠️ 注意事项

### API成本

- **真实API调用**: 本测试会产生实际的API调用费用
- **建议**: 在小数据集上测试，验证通过后再处理大批量数据

### 网络要求

- 需要稳定的互联网连接
- 能够访问:
  - `dashscope.aliyuncs.com`
  - `business.aliyuncs.com`

### 数据隐私

- 测试数据会发送到阿里云API
- 请勿使用敏感或机密信息

### 并发限制

- DashScope有QPS限制
- BSS OpenAPI有请求频率限制
- 建议控制批处理数据量

## 🚀 扩展测试

### 添加自定义测试数据

1. 准备Excel文件:
   ```
   tests/data/xlsx/
   ├── scenario_1_web_servers.xlsx
   ├── scenario_2_databases.xlsx
   └── scenario_3_ai_workloads.xlsx
   ```

2. 运行测试:
   ```bash
   ./run_e2e_tests.sh
   ```
   
   测试套件会自动处理所有文件

### 添加自定义验证逻辑

编辑 `tests/test_e2e_real_world.py`:

```python
# 在 test_real_data_batch_processing() 中添加自定义断言
def test_real_data_batch_processing() -> bool:
    
    # 自定义验证: 确保价格在合理范围内
    for result in results:
        if result['success']:
            price = result['price_cny_month']
            assert 0 < price < 100000, f"Price out of range: {price}"
    
    return True
```

## 📚 相关文档

- [tests/README.md](tests/README.md) - 测试目录说明
- [batch_processor.py](batch_processor.py) - 批处理逻辑
- [semantic_parser.py](semantic_parser.py) - AI解析引擎
- [pricing_service.py](pricing_service.py) - 价格查询服务

## 🆘 获取帮助

如遇到问题:

1. 查看日志文件: `logs/e2e_test_run_*.log`
2. 参考故障排查章节
3. 检查环境配置和网络连接
4. 验证API密钥和权限

---

**祝测试顺利! 🎉**
