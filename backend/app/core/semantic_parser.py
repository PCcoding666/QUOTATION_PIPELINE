# -*- coding: utf-8 -*-
"""
Semantic Parser - AI-Powered Text Understanding Module
Phase 5 Enhancement: Real AI Integration with Qwen-Max
- Upgraded from regex rules to Alibaba Cloud DashScope (qwen-max)
- Direct HTTP API calls (no SDK dependency)
- Intelligent workload classification via LLM reasoning
- Token-efficient caching system
"""
import os
import json
import re
import requests
from typing import Dict, Any, Literal
from app.models.domain import ResourceRequirement

# DashScope API Configuration
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
# Note: API Key is loaded dynamically in parse_with_qwen() to ensure .env is loaded first

# In-Memory Cache for LLM Results (Token Optimization)
_llm_cache: Dict[str, Dict[str, Any]] = {}

# PolarDB相关关键词列表（用于检测非 ECS 场景）
# 策略：极其严格，必须同时满足两个条件才识别为 PolarDB：
#   1. 提到 PolarDB 产品名称
#   2. 提到 PolarDB 的准确规格型号（如 polar.mysql.x4.large）
# 否则，即使提到 PolarDB，也视为在 ECS 上部署 PolarDB 应用，识别为 ECS
POLARDB_KEYWORDS = [
    "polardb", "polar db", "polar-db", "PolarDB", "POLARDB",
]


def _is_polardb_request(text: str) -> bool:
    """
    检测输入文本是否为 PolarDB 产品规格请求
    
    策略：极其严格，必须同时满足两个条件：
    1. 提到 "PolarDB" 产品名称
    2. 提到 PolarDB 的准确规格型号（如 polar.mysql.x4.large、polar.pg.x8.medium）
    
    否则，即使提到 PolarDB，也视为在 ECS 上部署 PolarDB 应用，识别为 ECS
    
    示例：
    - "16C 64G | PolarDB数据库" → ECS（只是描述，没有准确规格）
    - "polar.mysql.x4.large" → PolarDB（有准确规格）
    - "PolarDB polar.mysql.x4.large" → PolarDB（同时满足两个条件）
    
    Args:
        text: 输入文本
        
    Returns:
        bool: 如果是 PolarDB 规格请求返回 True，否则返回 False
    """
    text_lower = text.lower()
    
    # 条件1：检查是否提到 PolarDB 产品名称
    has_polardb_keyword = False
    polardb_keywords = ["polardb", "polar db", "polar-db"]
    
    for keyword in polardb_keywords:
        if keyword in text_lower:
            has_polardb_keyword = True
            break
    
    # 条件2：检查是否包含 PolarDB 的准确规格型号
    # PolarDB 规格格式：polar.{mysql|pg|o}.{x数字}.{规格}
    # 例如：polar.mysql.x4.large, polar.pg.x8.medium, polar.o.x4.xlarge
    import re
    polardb_spec_pattern = r'polar\.(mysql|pg|o)\.x\d+\.(small|medium|large|xlarge|2xlarge|4xlarge|8xlarge|12xlarge|16xlarge)'
    has_polardb_spec = bool(re.search(polardb_spec_pattern, text_lower))
    
    # 必须同时满足两个条件
    # 或者单独出现规格型号（规格本身就包含 polar 前缀）
    return (has_polardb_keyword and has_polardb_spec) or has_polardb_spec


def _get_ecs_enhanced_system_prompt(is_ecs_scenario: bool) -> str:
    """
    根据场景类型生成增强的系统提示词
    
    Args:
        is_ecs_scenario: 是否为 ECS 实例部署场景
        
    Returns:
        str: 系统提示词
    """
    base_prompt = """You are an Alibaba Cloud Architect. Analyze the server requirement string.

**Extraction Rules:**
1. Extract CPU (int) and Memory (int).
2. Infer the **Workload Type** based on keywords:
   - "Database", "Redis", "Cache", "Large Memory" -> "memory_intensive"
   - "Algorithm", "Training", "Encoding", "High Freq" -> "compute_intensive"
   - "Web", "App", "Gateway", "General", or Unspecified -> "general_purpose"
3. Ignore environment stages (Dev/Test/Prod).

**Output Format:**
Return strictly valid JSON:
{
  "cpu": 16,
  "memory": 64,
  "workload_type": "memory_intensive" | "compute_intensive" | "general_purpose",
  "reasoning": "Brief reason for classification"
}"""
    
    if is_ecs_scenario:
        # ECS 场景增强提示
        ecs_enhancement = """

**IMPORTANT - ECS Instance Scenario:**
This request is for an **ECS (Elastic Compute Service) instance deployment**.
- The output should be interpreted as ECS virtual machine specifications.
- Focus on CPU cores, memory size, and workload characteristics for ECS SKU matching.
- Do NOT interpret this as a managed database service (like PolarDB, RDS, etc.).
- The recommended SKU will be used for ECS instance type selection (e.g., ecs.g9i.xlarge)."""
        return base_prompt + ecs_enhancement
    
    return base_prompt


def parse_requirement(request: 'QuotationRequest') -> ResourceRequirement:
    """
    解析报价请求为资源需求 (多模态入口)
    
    Phase 5: 使用Qwen-Max进行智能解析
    - 当前支持: text (Qwen-Max AI理解)
    - 未来支持: image (Qwen-VL多模态)
    - 未来支持: audio (语音转文本 + 解析)
    
    Args:
        request: QuotationRequest对象 (来自任何数据源)
        
    Returns:
        ResourceRequirement: 标准化的资源需求对象
        
    Raises:
        NotImplementedError: 当content_type不支持时
    """
    
    # Forward Compatibility Check: Vision Model Integration Point
    if request.content_type == "image":
        raise NotImplementedError(
            "🔮 Qwen-VL integration pending. "
            "Future: Use Qwen-VL to extract specs from screenshots."
        )
    
    # Future Extension Point: Audio/Voice Input
    if request.content_type == "audio":
        raise NotImplementedError(
            "🎤 Audio transcription + parsing pending. "
            "Future: ASR + Qwen-Max parsing."
        )
    
    # Current Implementation: Text-based AI parsing
    if request.content_type == "text":
        # Combine main content with context notes for richer understanding
        full_text = request.content
        if request.context_notes:
            full_text = f"{full_text} | {request.context_notes}"
        
        return parse_with_qwen(full_text)
    
    # Unsupported content type
    raise ValueError(f"Unsupported content_type: {request.content_type}")


def parse_with_qwen(text: str) -> ResourceRequirement:
    """
    使用阿里云DashScope (qwen-max) 进行智能解析
    
    Phase 5核心升级：从规则引擎到真正的AI理解
    - 使用HTTP API直接调用qwen-max模型
    - 智能推理工作负载类型
    - 缓存机制优化token消耗
    
    增强功能：
    - 若输入文本中未明确提及 PolarDB 等关键词，默认为 ECS 实例部署场景
    - 对 ECS 场景增强提示，确保语义解析为 ECS 实例需求
    
    Args:
        text: 原始非结构化文本输入
        
    Returns:
        ResourceRequirement: 标准化的资源需求对象
        
    Example:
        >>> parse_with_qwen("16C 64G 1000G存储 | 备注: 生产环境-多维数据库")
    """
    
    # Step 1: Check cache first (Token optimization)
    if text in _llm_cache:
        print("💾 Cache hit - reusing previous AI analysis")
        cached_result = _llm_cache[text]
        return ResourceRequirement(
            raw_input=text,
            cpu_cores=cached_result["cpu"],
            memory_gb=cached_result["memory"],
            storage_gb=cached_result.get("storage", 0),
            environment="prod",  # Phase 5: No longer classify environment
            workload_type=cached_result["workload_type"]
        )
    
    # Step 2: 检测是否为 ECS 场景（默认为 ECS，除非明确提及 PolarDB 等关键词）
    is_ecs_scenario = not _is_polardb_request(text)
    
    if is_ecs_scenario:
        print("💻 ECS Instance Scenario detected - applying ECS-specific parsing")
    else:
        print("🗄️  PolarDB/RDS Scenario detected - using standard parsing")
    
    # Step 3: Call Qwen-Max for AI analysis with enhanced prompt
    print("🤖 AI analyzing intent via Qwen-Max...")
    
    # 使用增强的系统提示词
    system_prompt = _get_ecs_enhanced_system_prompt(is_ecs_scenario)
    
    user_prompt = f"Analyze this requirement: {text}"
    
    try:
        # Load API Key dynamically (to ensure .env is loaded)
        api_key = os.getenv("DASHSCOPE_API_KEY")
        
        if not api_key:
            raise Exception("DASHSCOPE_API_KEY not configured in environment")
        
        # Prepare HTTP request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen-max",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,  # Low temperature for consistent extraction
        }
        
        # Call DashScope API
        response = requests.post(
            DASHSCOPE_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"DashScope API Error: {response.status_code} - {response.text}")
        
        # Parse AI response
        response_data = response.json()
        ai_response = response_data["choices"][0]["message"]["content"]
        
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r'{.*}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError(f"Failed to extract JSON from AI response: {ai_response}")
        
        parsed_result = json.loads(json_str)
        
        # Validate required fields
        cpu = int(parsed_result["cpu"])
        memory = int(parsed_result["memory"])
        workload_type = parsed_result["workload_type"]
        
        # Normalize workload_type to match our schema
        workload_map = {
            "memory_intensive": "memory_intensive",
            "compute_intensive": "compute",
            "general_purpose": "general"
        }
        normalized_workload = workload_map.get(workload_type, "general")
        
        # Extract storage using regex fallback (AI may not always provide)
        storage = _extract_storage_gb(text)
        
        # Cache the result
        _llm_cache[text] = {
            "cpu": cpu,
            "memory": memory,
            "storage": storage,
            "workload_type": normalized_workload,
            "reasoning": parsed_result.get("reasoning", "")
        }
        
        print(f"✅ AI Result: {cpu}C {memory}G -> {normalized_workload} ({parsed_result.get('reasoning', 'N/A')})")
        
        return ResourceRequirement(
            raw_input=text,
            cpu_cores=cpu,
            memory_gb=memory,
            storage_gb=storage,
            environment="prod",  # Phase 5: Simplified - no environment classification
            workload_type=normalized_workload
        )
        
    except Exception as e:
        print(f"⚠️ AI parsing failed: {e}. Falling back to regex rules.")
        # Fallback to regex-based parsing
        return _fallback_parse(text)


def _fallback_parse(text: str) -> ResourceRequirement:
    """
    Fallback parsing using regex rules when AI fails
    """
    cpu_cores = _extract_cpu_cores(text)
    memory_gb = _extract_memory_gb(text)
    storage_gb = _extract_storage_gb(text)
    workload_type = _identify_workload_type(text)
    
    return ResourceRequirement(
        raw_input=text,
        cpu_cores=cpu_cores,
        memory_gb=memory_gb,
        storage_gb=storage_gb,
        environment="prod",
        workload_type=workload_type
    )


def _extract_cpu_cores(text: str) -> int:
    """提取CPU核心数 (例如: 16C, 32核)"""
    # Match patterns like "16C", "32核", "8 cores"
    patterns = [
        r'(\d+)\s*[Cc](?:\s|$|[^\w])',  # 16C
        r'(\d+)\s*核',                   # 32核
        r'(\d+)\s*cores?',               # 8 cores
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    
    # Default fallback
    return 2


def _extract_memory_gb(text: str) -> int:
    """提取内存容量 (例如: 64G, 128GB)"""
    # Match patterns like "64G", "128GB", "32 GB"
    patterns = [
        r'(\d+)\s*[Gg][Bb]?(?:\s|$|[^\w])',  # 64G or 64GB
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    
    # Default fallback
    return 4


def _extract_storage_gb(text: str) -> int:
    """提取存储容量 (例如: 1000G存储, 500GB磁盘)"""
    # Match patterns like "1000G存储", "500GB"
    patterns = [
        r'(\d+)\s*[Gg][Bb]?\s*存储',     # 1000G存储
        r'存储\s*[:\:：]?\s*(\d+)\s*[Gg]', # 存储: 500G
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    
    # Default fallback
    return 0


def _identify_environment(text: str) -> Literal["dev", "prod", "test"]:
    """
    识别环境类型
    关键词映射:
    - 生产/production/prod -> prod
    - 开发/development/dev -> dev
    - 测试/test/staging -> test
    """
    text_lower = text.lower()
    
    # Production environment keywords
    if any(keyword in text for keyword in ["生产", "正式"]):
        return "prod"
    if any(keyword in text_lower for keyword in ["production", "prod"]):
        return "prod"
    
    # Development environment keywords
    if any(keyword in text for keyword in ["开发", "研发"]):
        return "dev"
    if any(keyword in text_lower for keyword in ["development", "dev"]):
        return "dev"
    
    # Test environment keywords
    if any(keyword in text for keyword in ["测试", "预发", "灰度"]):
        return "test"
    if any(keyword in text_lower for keyword in ["test", "staging", "uat"]):
        return "test"
    
    # Default to dev
    return "dev"


def _identify_workload_type(text: str) -> Literal["general", "compute", "memory_intensive"]:
    """
    识别工作负载类型 (AI核心逻辑)
    关键词映射:
    - 数据库/缓存/Redis -> memory_intensive (内存密集型)
    - 算法/AI/训练/计算 -> compute (计算密集型)
    - 中间件/Web/API -> general (通用型)
    """
    text_lower = text.lower()
    
    # Memory-intensive workload keywords
    memory_keywords = ["数据库", "缓存", "redis", "memcache", "mysql", "oracle", "postgresql", "mongo"]
    if any(keyword in text_lower for keyword in memory_keywords):
        return "memory_intensive"
    
    # Compute-intensive workload keywords
    compute_keywords = ["算法", "ai", "训练", "计算", "深度学习", "machine learning", "gpu", "科学计算"]
    if any(keyword in text_lower for keyword in compute_keywords):
        return "compute"
    
    # General workload keywords
    general_keywords = ["中间件", "web", "api", "网关", "nginx", "tomcat", "应用服务"]
    if any(keyword in text_lower for keyword in general_keywords):
        return "general"
    
    # Default to general
    return "general"
