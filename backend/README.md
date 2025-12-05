# FastAPI Backend - 阿里云ECS智能报价系统

## 项目结构

```
backend/
├── app/                          # 应用主目录
│   ├── api/                      # API路由层
│   │   └── v1/                   # API v1版本
│   │       ├── endpoints/        # 端点定义
│   │       │   ├── quotations.py # 报价相关接口
│   │       │   └── regions.py    # 区域相关接口
│   │       └── router.py         # 路由聚合
│   ├── core/                     # 核心业务层
│   │   ├── pricing_service.py
│   │   ├── semantic_parser.py
│   │   └── sku_recommend_service.py
│   ├── data/                     # 数据处理层
│   │   ├── batch_processor.py
│   │   └── data_ingestion.py
│   ├── matchers/                 # 匹配逻辑
│   │   └── sku_matcher.py
│   ├── models/                   # 数据模型
│   │   └── domain.py             # 业务模型
│   ├── schemas/                  # Pydantic模式定义
│   │   ├── quotation.py
│   │   └── region.py
│   ├── services/                 # 服务层
│   │   └── quotation_service.py  # 报价业务编排
│   ├── utils/                    # 工具类
│   │   ├── file_handler.py       # 文件处理
│   │   └── response.py           # 响应封装
│   └── config.py                 # 配置管理
├── main.py                       # FastAPI应用入口
├── requirements.txt              # 后端依赖
└── .env                          # 环境变量
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
# 编辑 .env 文件，填写阿里云和DashScope API密钥
```

### 3. 启动开发服务器

```bash
# 方式1：直接运行（单进程）
python main.py

# 方式2：使用uvicorn（推荐用于开发）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 方式3：使用gunicorn（推荐用于生产，3 workers）
gunicorn main:app -w 3 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 4. 访问API文档

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- 健康检查: http://localhost:8000/health

## API端点

### 报价相关

#### POST /api/v1/quotations/batch
批量报价处理

**请求参数（multipart/form-data）：**
- `file`: Excel文件
- `region_id`: 阿里云区域ID（如cn-beijing）

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "task_id": "uuid",
    "total_count": 10,
    "success_count": 8,
    "results": [...],
    "download_url": "/api/v1/quotations/download/{task_id}"
  }
}
```

#### GET /api/v1/quotations/download/{task_id}
下载报价结果文件

**响应：** Excel文件流

### 区域相关

#### GET /api/v1/regions/
获取阿里云区域列表

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "regions": [
      {"id": "cn-beijing", "name": "华北2（北京）"},
      ...
    ]
  }
}
```

## 生产部署

### 使用Gunicorn + Uvicorn Workers

推荐配置（2核2G服务器）：

```bash
gunicorn main:app \
  -w 3 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/quotation-api-access.log \
  --error-logfile /var/log/quotation-api-error.log
```

### Worker数量建议

| 配置 | Worker数量 | 内存估算 | 说明 |
|------|-----------|----------|------|
| 保守方案 | 2 workers | 1GB | 稳定优先 |
| 平衡方案 | 3 workers | 1.2GB | 推荐配置 |
| 激进方案 | 4 workers | 1.2GB | 性能优先 |

## 测试

```bash
# 测试健康检查
curl http://localhost:8000/health

# 测试获取区域列表
curl http://localhost:8000/api/v1/regions/

# 测试批量报价（需要准备Excel文件）
curl -X POST http://localhost:8000/api/v1/quotations/batch \
  -F "file=@test.xlsx" \
  -F "region_id=cn-beijing"
```

## 技术栈

- **FastAPI**: 现代化高性能Web框架
- **Uvicorn**: ASGI服务器
- **Gunicorn**: 进程管理器
- **Pydantic**: 数据验证
- **Pandas**: 数据处理
- **阿里云SDK**: BSS OpenAPI, ECS API
- **DashScope**: AI语义解析

## 注意事项

1. **环境变量**: 确保 `.env` 文件配置正确
2. **内存管理**: 2G内存下建议使用2-3个worker
3. **文件清理**: 系统会自动清理临时文件
4. **日志管理**: 生产环境建议配置日志轮转
