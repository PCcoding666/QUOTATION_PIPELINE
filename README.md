# Quotation Pipeline - 智能云服务器报价系统

> 基于AI的阿里云ECS智能报价自动化系统，支持Excel批量处理和多工作表解析

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 目录

- [系统概述](#系统概述)
- [系统架构](#系统架构)
- [核心功能](#核心功能)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [API文档](#api文档)

## 🎯 系统概述

Quotation Pipeline 是一个智能化的云服务器报价系统，通过集成阿里云API和AI技术，实现从Excel表格到精准报价的全自动化流程。

**核心特性：**
- 🤖 **AI驱动解析** - 使用Qwen-Plus智能解析Excel表格数据
- 🔄 **动态SKU推荐** - 调用阿里云API实时推荐最优实例规格
- 💰 **实时询价** - 基于阿里云BSS OpenAPI获取官方价格
- 📊 **批量处理** - 支持多工作表Excel文件批量解析
- 🎯 **智能过滤** - 仅处理ECS产品，其他产品自动跳过
- 📈 **包年包月计费** - 统一使用Subscription计费模式

## 🏗️ 系统架构

### 整体架构图

```mermaid
graph TB
    subgraph "输入层"
        A[Excel文件<br/>多工作表支持] --> B[LLMDrivenExcelLoader<br/>Qwen-Plus驱动]
    end
    
    subgraph "AI解析层"
        B --> C[半结构化数据提取]
        C --> D[AI语义解析<br/>Qwen-Plus]
        D --> E{产品类型识别}
        E -->|ECS| F[QuotationRequest]
        E -->|非ECS| G[标记跳过]
    end
    
    subgraph "SKU推荐层"
        F --> H[SKURecommendService]
        H --> I{DescribeRecommendInstanceType<br/>API调用}
        I -->|成功| J[实例规格推荐<br/>g9i/u1/u2系列]
        I -->|失败| K[兜底映射规则<br/>g6/c6/r6系列]
        J --> L[最优实例SKU]
        K --> L
    end
    
    subgraph "定价查询层"
        L --> M[PricingService]
        M --> N[DescribePrice API<br/>包年包月PrePaid]
        N --> O[实例价格+存储价格]
        O --> P[月度总价]
    end
    
    subgraph "输出层"
        P --> Q[BatchQuotationProcessor]
        G --> Q
        Q --> R[Excel报价表<br/>按工作表输出]
        Q --> S[统计汇总<br/>成本+资源]
    end

### 核心组件架构

```mermaid
graph TB
    subgraph "数据摄入层"
        A[LLMDrivenExcelLoader] --> B[DashScope API<br/>Qwen-Plus]
        A --> C[OpenPyXL<br/>Excel读取]
    end
    
    subgraph "核心服务层"
        D[SKURecommendService] --> E[ECS API Client<br/>实例推荐]
        F[PricingService] --> G[ECS API Client<br/>价格查询]
    end
    
    subgraph "业务处理层"
        H[BatchQuotationProcessor]
        H --> D
        H --> F
        H --> I[产品过滤器<br/>仅处理ECS]
    end
    
    subgraph "数据模型层"
        J[QuotationRequest] --> H
        A --> J
        H --> K[处理结果<br/>Result Dict]
    end
    
    subgraph "输出层"
        K --> L[Pandas DataFrame]
        L --> M[Excel Writer<br/>多工作表输出]
    end

## 📈 业务流程时序图

### 完整处理流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Pipeline as run_pipeline.py
    participant Excel as Excel文件
    participant Loader as LLMDrivenExcelLoader
    participant Qwen as Qwen-Plus AI
    participant Processor as BatchQuotationProcessor
    participant SKU as SKURecommendService
    participant ECS as ECS API
    participant Price as PricingService
    participant Output as Excel输出

    User->>Pipeline: 执行报价流程
    Pipeline->>Excel: 读取工作表列表
    Excel-->>Pipeline: 返回所有工作表名称
    
    loop 每个工作表
        Pipeline->>Loader: load_data(sheet_name)
        Loader->>Excel: 读取工作表数据
        Excel-->>Loader: 返回原始表格数据
        Loader->>Loader: 提取半结构化数据<br/>(行号+内容+上下文)
        Loader->>Qwen: AI解析请求<br/>(CPU/内存/产品/主机数/存储)
        Qwen-->>Loader: 返回结构化数据
        Loader-->>Pipeline: QuotationRequest列表
        
        Pipeline->>Processor: process_batch(requests)
        
        loop 每个请求
            Processor->>Processor: 检查产品类型
            alt 非ECS产品
                Processor->>Processor: 标记"跳过非-ECS产品"
            else ECS产品
                Processor->>SKU: recommend_instance_type<br/>(CPU核心+内存GB)
                SKU->>ECS: DescribeRecommendInstanceType<br/>InventoryFirst策略
                alt API成功
                    ECS-->>SKU: 返回推荐实例<br/>(g9i/u1/u2系列)
                else API失败
                    SKU->>SKU: 兜底映射规则<br/>(g6/c6/r6系列)
                end
                SKU-->>Processor: 实例SKU
                
                Processor->>Price: get_instance_price<br/>(实例类型+区域+存储)
                Price->>ECS: DescribePrice<br/>PrePaid包年包月
                ECS-->>Price: 实例价格+存储价格
                Price-->>Processor: 月度总价(CNY)
                
                Processor->>Processor: 记录完整报价结果
            end
        end
        
        Processor-->>Pipeline: 返回处理结果列表
        Pipeline->>Output: export_to_excel<br/>(output_{sheet_name}.xlsx)
        Output-->>Pipeline: 保存成功
        
        Pipeline->>Pipeline: 统计汇总<br/>(成功率/主机数/成本)
    end
    
    Pipeline->>Pipeline: 生成全局汇总
    Pipeline-->>User: 显示统计报告<br/>(月度/年度成本)

### SKU推荐详细流程

```mermaid
sequenceDiagram
    participant Processor as BatchProcessor
    participant SKU as SKURecommendService
    participant API as ECS API
    participant Fallback as 兜底规则
    
    Processor->>SKU: recommend_instance_type<br/>(cpu_cores=16, memory_gb=64)
    
    SKU->>SKU: 构建API请求参数<br/>instance_charge_type=PrePaid<br/>priority_strategy=InventoryFirst
    
    SKU->>API: DescribeRecommendInstanceType<br/>Cores=16<br/>Memory=65536MB<br/>NetworkType=vpc<br/>IoOptimized=optimized
    
    alt API调用成功
        API-->>SKU: 返回推荐列表<br/>Zone A: ecs.g9i.4xlarge<br/>Zone B: ecs.u1-c1m4.4xlarge
        SKU->>SKU: 选择第一个推荐<br/>(库存优先)
        SKU-->>Processor: ecs.g9i.4xlarge
    else API失败或无库存
        API-->>SKU: Error或空列表
        SKU->>SKU: 触发兜底机制
        SKU->>Fallback: _fallback_sku_mapping<br/>(16, 64)
        Fallback->>Fallback: 精确匹配规则<br/>(16C, 64G) → ecs.g6.4xlarge
        Fallback-->>SKU: ecs.g6.4xlarge
        SKU-->>Processor: ecs.g6.4xlarge
    end
    
    Note over Processor,Fallback: 推荐策略: 优先最新代际(g9i)→高性价比(u1/u2)→兜底(g6)

### 多工作表处理流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Pipeline as run_pipeline.py
    participant Excel as Excel文件
    participant Loader as LLMDrivenExcelLoader
    participant Processor as BatchProcessor
    participant Output as 输出目录

    User->>Pipeline: python run_pipeline.py
    Pipeline->>Pipeline: 加载环境变量<br/>(API Keys)
    Pipeline->>Excel: openpyxl.load_workbook()
    Excel-->>Pipeline: 返回工作簿对象
    Pipeline->>Excel: 获取工作表列表
    Excel-->>Pipeline: sheet_names列表
    
    Pipeline->>Pipeline: 创建服务实例<br/>(SKUService+PricingService)
    
    loop 每个工作表
        Pipeline->>Loader: load_data(sheet_name)
        Loader->>Excel: 读取工作表数据
        Loader->>Loader: AI解析<br/>(Qwen-Plus)
        Loader-->>Pipeline: QuotationRequest列表
        
        Pipeline->>Processor: process_batch(loader)
        
        loop 每个配置项
            Processor->>Processor: 产品过滤
            alt ECS产品
                Processor->>Processor: SKU推荐+价格查询
            else 非ECS
                Processor->>Processor: 标记跳过
            end
        end
        
        Processor-->>Pipeline: results列表
        
        Pipeline->>Output: export_to_excel<br/>(output_{sheet}_{timestamp}.xlsx)
        Output-->>Pipeline: 文件已保存
        
        Pipeline->>Pipeline: 累计统计数据<br/>(主机/CPU/内存/成本)
    end
    
    Pipeline->>Pipeline: 生成全局汇总报告<br/>(成功率+总成本)
    Pipeline->>User: 显示完整统计<br/>(月度¥XXX/年度¥XXX)
    Pipeline-->>User: 处理完成<br/>(N个输出文件)

## 🔧 核心功能

### 1. LLM驱动的数据解析

使用Qwen-Plus智能识别Excel表格中的资源配置信息：

```python
from app.data.data_ingestion import LLMDrivenExcelLoader

loader = LLMDrivenExcelLoader(
    file_path="quotation.xlsx",
    api_key=os.getenv("DASHSCOPE_API_KEY")
)

# 自动解析多个工作表
for request in loader.load_data(sheet_name="标准-生产"):
    print(f"{request.product_name}: {request.cpu_cores}C {request.memory_gb}G")
```

**智能识别能力：**
- 自动提取CPU核心数、内存大小、存储容量
- 智能识别产品类型（ECS、PolarDB、WAF等）
- 处理跨工作表Excel公式引用
- 支持非标准格式的表格

### 2. 动态SKU推荐

基于阿里云API实时推荐最优实例规格：

```python
from app.core.sku_recommend_service import SKURecommendService

sku_service = SKURecommendService(
    access_key_id=access_key_id,
    access_key_secret=access_key_secret,
    region_id="cn-beijing"
)

# 推荐实例
instance_type = sku_service.recommend_instance_type(
    cpu_cores=16,
    memory_gb=64,
    instance_charge_type="PrePaid",  # 包年包月
    priority_strategy="PriceFirst"   # 价格优先
)
# 返回: ecs.g6.4xlarge
```

**推荐策略：**
- 价格优先（PriceFirst）
- 库存优先（InventoryFirst）
- 最新产品优先（NewProductFirst）

**兜底机制：**
当API调用失败时，自动使用内置映射规则：

| CPU核心 | 内存(GB) | SKU规格 |
|---------|---------|---------|
| 4 | 16 | ecs.g6.xlarge |
| 8 | 32 | ecs.g6.2xlarge |
| 16 | 64 | ecs.g6.4xlarge |
| 32 | 128 | ecs.g6.8xlarge |

### 3. 实时价格查询

调用阿里云BSS OpenAPI获取官方价格：

```python
from app.core.pricing_service import PricingService

pricing_service = PricingService(
    access_key_id=access_key_id,
    access_key_secret=access_key_secret,
    region_id="cn-beijing"
)

price = pricing_service.get_official_price(
    instance_type="ecs.g6.4xlarge",
    region="cn-beijing",
    period=1,
    unit="Month"  # 包年包月
)
# 返回: 1920.0 (CNY/月)
```

### 4. 批量处理和多工作表支持

```python
from app.data.batch_processor import BatchQuotationProcessor

processor = BatchQuotationProcessor(
    pricing_service=pricing_service,
    sku_recommend_service=sku_service,
    region="cn-beijing"
)

# 处理多个工作表
for sheet_name in ["标准-开发", "标准-测试", "标准-生产"]:
    results = processor.process_batch(
        data_loader=loader,
        verbose=True
    )
    processor.export_to_excel(f"output_{sheet_name}.xlsx")
```

## 🛠️ 技术栈

### 后端框架
- **Python 3.8+** - 核心开发语言
- **Pandas** - 数据处理和Excel操作
- **OpenPyXL** - Excel文件读写

### AI服务
- **DashScope** - 阿里云灵积平台
- **Qwen-Plus** - 通义千问大模型（数据解析）

### 阿里云SDK
- **alibabacloud_ecs20140526** - ECS实例推荐API
- **alibabacloud_bssopenapi20171214** - BSS计费查询API
- **alibabacloud_tea_openapi** - OpenAPI通用库

### 数据模型
- **Pydantic** - 数据验证和模型定义
- **Dataclasses** - 轻量级数据结构

## 🚀 快速开始

### 项目结构

```
Quotation_Pipeline/
├── app/                          # 核心业务代码包
│   ├── __init__.py
│   ├── models.py                # 数据模型定义
│   ├── core/                    # 核心服务层
│   │   ├── __init__.py
│   │   ├── pricing_service.py  # 价格查询服务
│   │   ├── sku_recommend_service.py  # SKU推荐服务
│   │   └── semantic_parser.py  # 语义解析服务
│   ├── data/                    # 数据处理层
│   │   ├── __init__.py
│   │   ├── data_ingestion.py   # 数据摄入
│   │   └── batch_processor.py  # 批处理器
│   └── matchers/                # 匹配器模块
│       ├── __init__.py
│       └── sku_matcher.py      # SKU匹配器
│
├── tests/                       # 测试目录
│   ├── __init__.py
│   ├── data/                    # 测试数据
│   │   └── xlsx/
│   ├── output/                  # 测试输出
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   │   ├── test_single_row.py
│   │   ├── test_new_system.py
│   │   └── test_multi_sheet.py
│   └── e2e/                     # 端到端测试
│       ├── test_e2e_real_world.py
│       └── create_sample_test_data.py
│
├── scripts/                     # 工具脚本
│   └── demo_llm_parser.py      # 演示脚本
│
├── docs/                        # 文档目录
│   ├── CHANGELOG.md
│   ├── TESTING_GUIDE.md
│   └── PHASE6_COMPLETION_SUMMARY.md
│
├── main.py                      # 主入口文件
├── requirements.txt             # 依赖管理
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git忽略规则
└── README.md                    # 项目说明
```

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd Quotation_Pipeline

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# 阿里云API密钥
ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret

# 阿里云灵积平台密钥
DASHSCOPE_API_KEY=your_dashscope_api_key
```

### 3. 运行测试

```bash
# 测试单行数据处理
python3 tests/integration/test_single_row.py

# 测试新系统（SKU推荐+价格查询）
python3 tests/integration/test_new_system.py

# 测试多工作表处理
python3 tests/integration/test_multi_sheet.py

# 运行端到端测试
python3 tests/e2e/test_e2e_real_world.py
```

### 4. 处理实际数据

```python
from app.data.data_ingestion import LLMDrivenExcelLoader
from app.data.batch_processor import BatchQuotationProcessor
from app.core.pricing_service import PricingService
from app.core.sku_recommend_service import SKURecommendService
import os

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

# 加载数据
loader = LLMDrivenExcelLoader(
    file_path="your_quotation.xlsx",
    api_key=os.getenv("DASHSCOPE_API_KEY")
)

# 批处理
processor = BatchQuotationProcessor(
    pricing_service=pricing_service,
    sku_recommend_service=sku_service,
    region="cn-beijing"
)

results = processor.process_batch(loader, verbose=True)
processor.export_to_excel("output_quotation.xlsx")
```

## 📖 使用指南

### Excel文件格式要求

系统支持灵活的Excel格式，AI会自动识别以下信息：

```
推荐格式（但不限于此）：

| 服务器类别 | 安装内容 | 主机数 | CPU(核数) | 内存(G) | 数据盘(G) |
|-----------|---------|-------|-----------|---------|-----------|
| 中间件    | Nginx   | 1     | 16        | 64      | 1000      |
| 数据库    | MySQL   | 2     | 32        | 128     | 2000      |
```

**AI可识别的关键信息：**
- CPU核心数（支持：8C、8核、8 cores等多种表达）
- 内存大小（支持：64G、64GB、64 GiB等）
- 存储容量
- 主机数量
- 产品类型（ECS、PolarDB、WAF等）

### 产品过滤规则

系统当前**仅处理ECS产品**，其他产品自动跳过：

```
✅ ECS         → 正常处理，生成报价
⏭️  PolarDB    → 跳过，标记"跳过非-ECS产品"
⏭️  WAF        → 跳过
⏭️  云安全中心 → 跳过
```

### 输出文件格式

生成的Excel报价表包含以下列：

| 列名 | 说明 |
|------|------|
| Source ID | 数据来源标识（工作表+行号） |
| Product Name | 产品名称（ECS/PolarDB/WAF等） |
| Original Content | 原始内容 |
| Context Notes | 上下文备注 |
| Host Count | 主机数量 |
| CPU Cores | CPU核心数 |
| Memory (GB) | 内存大小 |
| Storage (GB) | 存储容量 |
| Workload Type | 工作负载类型 |
| Matched SKU | 匹配的实例规格 |
| Instance Family | 实例系列 |
| Price (CNY/Month) | 月度价格 |
| Status | 处理状态 |
| Error | 错误信息 |

## 🔌 API文档

### SKURecommendService

#### `recommend_instance_type()`

推荐实例规格。

**参数：**
- `cpu_cores: int` - CPU核心数
- `memory_gb: float` - 内存大小(GB)
- `instance_charge_type: str` - 计费方式（默认："PrePaid"）
- `zone_id: Optional[str]` - 可用区ID（可选）
- `priority_strategy: str` - 推荐策略（默认："PriceFirst"）

**返回：**
- `Optional[str]` - 推荐的实例规格，如 "ecs.g6.4xlarge"

**示例：**
```python
sku = sku_service.recommend_instance_type(
    cpu_cores=16,
    memory_gb=64,
    instance_charge_type="PrePaid",
    priority_strategy="PriceFirst"
)
```

### PricingService

#### `get_official_price()`

查询实例官方价格。

**参数：**
- `instance_type: str` - 实例规格
- `region: str` - 地域（默认："cn-beijing"）
- `period: int` - 购买时长（默认：1）
- `unit: str` - 时间单位（默认："Month"）

**返回：**
- `float` - 官方价格(CNY)

**示例：**
```python
price = pricing_service.get_official_price(
    instance_type="ecs.g6.4xlarge",
    region="cn-beijing",
    period=1,
    unit="Month"
)
```

### LLMDrivenExcelLoader

#### `load_data()`

加载并解析Excel数据。

**参数：**
- `sheet_name: Optional[str]` - 工作表名称（可选）

**返回：**
- `Iterator[QuotationRequest]` - 报价请求迭代器

**示例：**
```python
for request in loader.load_data(sheet_name="标准-生产"):
    print(f"{request.cpu_cores}C {request.memory_gb}G")
```

## 📝 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)

### 最新变更 (2025-11-27)

- ✨ 新增基于API的动态SKU推荐机制
- 🔄 统一使用包年包月计费模式
- 🎯 实现ECS产品过滤，其他产品自动跳过
- 🛡️ 添加API失败兜底规则
- 📊 支持多工作表独立处理

## ⚠️ 注意事项

1. **API调用费用** - 系统会产生实际的API调用费用
2. **网络要求** - 需要稳定的网络连接访问阿里云服务
3. **API配额** - 确保账户有足够的API调用配额
4. **数据隐私** - Excel数据会发送到云端AI，请勿使用敏感信息

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📧 联系方式

如有问题或建议，请通过Issue联系。
