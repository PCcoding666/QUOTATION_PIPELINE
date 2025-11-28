# Phase 6 - End-to-End Integration Testing Suite

## 概述

这是一个全面的端到端集成测试套件，用于验证整个报价管道的实际运行情况。

**关键特性:**
- ✅ **真实API调用** - 不使用Mock，直接连接生产API
- ✅ **双输出日志** - 控制台(INFO) + 文件(DEBUG)
- ✅ **完整的Pipeline验证** - 从数据加载到价格查询
- ✅ **健壮的错误处理** - 友好的错误提示和日志

## 测试覆盖

### Test Case 1: Environment Health Check (环境健康检查)
- ✅ 验证 `.env` 文件存在
- ✅ 验证 `ALIBABA_CLOUD_ACCESS_KEY_ID` 已配置
- ✅ 验证 `ALIBABA_CLOUD_ACCESS_KEY_SECRET` 已配置
- ✅ 验证 `DASHSCOPE_API_KEY` 已配置

### Test Case 2: Component Connectivity (组件连接性测试)
- ✅ **AI Parser** - 发送测试文本到Qwen-Max并验证响应
- ✅ **Pricing Service** - 查询固定SKU价格并验证结果

### Test Case 3: Real Data Batch Processing (真实数据批处理)
- ✅ 扫描测试数据目录
- ✅ 加载所有Excel文件
- ✅ 运行完整的Pipeline (Parse → Match → Price)
- ✅ 验证输出文件生成
- ✅ 验证输出包含价格列
- ✅ 验证处理结果

## 目录结构

```
tests/
├── test_e2e_real_world.py          # 主测试套件
├── create_sample_test_data.py      # 测试数据生成脚本
├── data/
│   └── xlsx/                       # Excel测试数据存放目录
│       └── sample_test.xlsx        # 示例测试数据
└── output/                         # 测试输出目录
    └── output_*.xlsx               # 处理后的结果文件

logs/
└── e2e_test_run_*.log              # 详细的测试日志
```

## 使用方法

### 1. 准备环境

确保已安装所有依赖:

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件:

```bash
ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret
DASHSCOPE_API_KEY=your_dashscope_api_key
```

### 3. 准备测试数据

**选项A: 使用示例数据**

运行辅助脚本创建示例测试数据:

```bash
python3 tests/create_sample_test_data.py
```

**选项B: 使用自定义数据**

将您的Excel文件放入 `tests/data/xlsx/` 目录。

Excel文件要求:
- 必须包含规格列（列名包含"Spec"、"规格"或"配置"）
- 可选包含备注列（列名包含"Remark"、"备注"或"Note"）

示例格式:

| Specification | Remarks |
|---------------|---------|
| 16C 64G | 测试环境 |
| 8C 32G 数据库 | 生产环境 |

### 4. 运行测试

```bash
python3 tests/test_e2e_real_world.py
```

## 日志系统

测试套件使用双输出日志系统:

### 控制台输出 (INFO级别)
显示测试进度和关键信息:
```
[2024-11-26 10:30:00] [INFO] - >>> [TEST CASE 1] Environment Health Check
[2024-11-26 10:30:01] [INFO] - ✅ .env file exists
[2024-11-26 10:30:02] [INFO] - ✅ ALIBABA_CLOUD_ACCESS_KEY_ID loaded
```

### 文件日志 (DEBUG级别)
保存在 `logs/e2e_test_run_YYYYMMDD_HHMMSS.log`:
```
[2024-11-26 10:30:00] [DEBUG] [test_e2e_real_world:89] - Checking .env file at: /path/to/.env
[2024-11-26 10:30:01] [DEBUG] [test_e2e_real_world:105] - Key preview: LTAI****...ab12
```

## 输出验证

测试套件会自动验证以下内容:

1. **输出文件生成** - 确保每个输入文件都有对应的输出
2. **价格列存在** - 验证 `Price (CNY/Month)` 列存在
3. **处理状态** - 统计成功和失败的行数
4. **错误日志** - 记录所有失败项的详细错误信息

## 输出示例

测试成功时的输出:

```
🚀 QUOTATION PIPELINE - END-TO-END INTEGRATION TEST SUITE
====================================================================================================
Phase 6: Real-world validation with actual API connectivity
NO MOCKING - All network calls are REAL
====================================================================================================

[2024-11-26 10:30:00] [INFO] - 📝 Logging initialized - File: logs/e2e_test_run_20241126_103000.log

====================================================================================================
>>> [TEST CASE 1] Environment Health Check
====================================================================================================
[2024-11-26 10:30:01] [INFO] - ✅ .env file exists
[2024-11-26 10:30:01] [INFO] - ✅ ALIBABA_CLOUD_ACCESS_KEY_ID loaded (length: 24)
[2024-11-26 10:30:01] [INFO] - ✅ DASHSCOPE_API_KEY loaded (length: 48)
[2024-11-26 10:30:01] [INFO] - 🎉 Environment variables loaded successfully

====================================================================================================
>>> [TEST CASE 2] Component Connectivity (Smoke Test)
====================================================================================================
[2024-11-26 10:30:02] [INFO] - >>> [STEP 1] Testing AI Parser (DashScope Qwen-Max)...
🤖 AI analyzing intent via Qwen-Max...
✅ AI Result: 16C 64G -> general (General purpose configuration)
[2024-11-26 10:30:05] [INFO] - ✅ AI Parser OK - Parsed as: 16C 64G
[2024-11-26 10:30:05] [INFO] - >>> [STEP 2] Testing Pricing Service (BSS OpenAPI)...
[2024-11-26 10:30:06] [INFO] - ✅ Pricing Service OK - Price: ¥342.00 CNY/Month
[2024-11-26 10:30:06] [INFO] - 🎉 Smoke tests for AI and BSS passed

====================================================================================================
>>> [TEST CASE 3] Real Data Batch Processing
====================================================================================================
[2024-11-26 10:30:07] [INFO] - >>> [STEP 1] Scanning test data directory...
[2024-11-26 10:30:07] [INFO] - 📁 Found 1 Excel file(s) to process
[2024-11-26 10:30:07] [INFO] - ✅ Processed file [sample_test.xlsx]: 4 successes, 0 failures
[2024-11-26 10:30:10] [INFO] - 🎉 All batch processing tests passed

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

## 错误处理

测试套件会友好地处理以下错误:

- ❌ **FileNotFoundError** - 测试数据文件不存在
- ❌ **PermissionError** - 文件访问权限问题
- ❌ **API错误** - Alibaba Cloud或DashScope API调用失败
- ❌ **环境变量缺失** - 必需的API密钥未配置

所有错误都会记录到日志文件中，便于调试。

## 注意事项

⚠️ **重要提示:**

1. **真实API调用** - 本测试套件不使用Mock，会产生实际的API调用费用
2. **网络连接** - 需要稳定的网络连接访问Alibaba Cloud和DashScope服务
3. **API配额** - 请确保您的账户有足够的API调用配额
4. **数据隐私** - 测试数据会发送到云端API，请勿使用敏感信息

## 故障排除

### 问题1: 环境变量未加载
**症状:** 提示 `DASHSCOPE_API_KEY is empty or not set`

**解决方案:**
1. 确认 `.env` 文件在项目根目录
2. 检查 `.env` 文件格式是否正确
3. 确保没有多余的空格或引号

### 问题2: API调用失败
**症状:** `API Error: ...`

**解决方案:**
1. 检查网络连接
2. 验证API密钥是否有效
3. 确认账户是否有足够的配额

### 问题3: 测试数据未找到
**症状:** `No Excel files found in: ...`

**解决方案:**
1. 运行 `python3 tests/create_sample_test_data.py` 创建示例数据
2. 或手动将Excel文件放入 `tests/data/xlsx/` 目录

## 扩展测试

您可以轻松添加更多测试数据:

1. 在 `tests/data/xlsx/` 中添加新的Excel文件
2. 测试套件会自动检测并处理所有 `.xlsx` 和 `.xls` 文件
3. 每个文件的处理结果会独立验证和报告

## 退出代码

- `0` - 所有测试通过
- `1` - 至少一个测试失败
- `130` - 用户中断 (Ctrl+C)

## 技术细节

### Pipeline验证流程

```
Excel文件
  ↓
[Data Ingestion] - ExcelDataLoader
  ↓
[Semantic Parsing] - Qwen-Max AI
  ↓
[SKU Matching] - Rule-based Matcher
  ↓
[Pricing Query] - Alibaba BSS API
  ↓
Excel输出 + 日志
```

### 关键验证点

每个步骤都有详细的日志记录:
- 📥 **数据加载** - 验证文件格式和列名
- 🤖 **AI解析** - 记录AI推理过程和结果
- 🎯 **SKU匹配** - 显示匹配的实例类型
- 💰 **价格查询** - 显示官方价格

## 相关文件

- `batch_processor.py` - 批处理核心逻辑
- `semantic_parser.py` - AI解析引擎
- `pricing_service.py` - 价格查询服务
- `data_ingestion.py` - 数据加载抽象层

## 支持

如有问题,请查看日志文件 `logs/e2e_test_run_*.log` 获取详细信息。
