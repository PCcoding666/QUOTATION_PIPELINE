#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云ECS智能报价系统 - Streamlit前端界面
简洁设计：仅作为用户交互入口，所有业务逻辑由后端处理
"""
import streamlit as st
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import sys

# 添加项目路径到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.pricing_service import PricingService
from app.core.sku_recommend_service import SKURecommendService
from app.data.batch_processor import BatchQuotationProcessor
from app.data.data_ingestion import LLMDrivenExcelLoader

# 加载环境变量
load_dotenv()

# ============================================================================
# 页面配置
# ============================================================================
st.set_page_config(
    page_title="阿里云ECS智能报价系统",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# 简洁样式
# ============================================================================
st.markdown("""
<style>
    .stButton>button {
        background-color: #FF6A00;
        color: white;
    }
    .stButton>button:hover {
        background-color: #E65A00;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 辅助函数
# ============================================================================

@st.cache_data
def get_region_options():
    """获取阿里云区域选项"""
    return {
        "华北2（北京）": "cn-beijing",
        "华东2（上海）": "cn-shanghai",
        "华东1（杭州）": "cn-hangzhou",
        "华南1（深圳）": "cn-shenzhen",
        "华南2（广州）": "cn-guangzhou",
        "华北1（青岛）": "cn-qingdao",
        "华北3（张家口）": "cn-zhangjiakou",
        "西南1（成都）": "cn-chengdu",
        "香港": "cn-hongkong",
        "亚太东南1（新加坡）": "ap-southeast-1",
        "亚太东南5（雅加达）": "ap-southeast-5",
        "美国西部1（硅谷）": "us-west-1",
        "美国东部1（弗吉尼亚）": "us-east-1",
        "欧洲中部1（法兰克福）": "eu-central-1",
    }


def initialize_services(region_id: str):
    """
    初始化所有服务组件
    
    Args:
        region_id: 阿里云区域ID（如 cn-beijing）
        
    Returns:
        tuple: (pricing_service, sku_service, processor)
    """
    # 获取环境变量
    access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    dashscope_key = os.getenv('DASHSCOPE_API_KEY')
    
    if not access_key_id or not access_key_secret:
        st.error("❌ 缺少阿里云API密钥，请检查.env文件配置")
        st.stop()
    
    if not dashscope_key:
        st.warning("⚠️ 缺少DashScope API密钥，AI解析功能将不可用")
    
    # 初始化价格查询服务
    pricing_service = PricingService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id=region_id
    )
    
    # 初始化SKU推荐服务
    sku_service = SKURecommendService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id=region_id
    )
    
    # 初始化批量处理器
    processor = BatchQuotationProcessor(
        pricing_service=pricing_service,
        sku_recommend_service=sku_service,
        region=region_id
    )
    
    return pricing_service, sku_service, processor


def save_uploaded_file(uploaded_file):
    """保存上传文件到临时目录"""
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = temp_dir / f"{timestamp}_{uploaded_file.name}"
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path


# ============================================================================
# 侧边栏：配置
# ============================================================================
with st.sidebar:
    st.markdown("### ⚙️ 配置")
    
    # 地域选择
    region_options = get_region_options()
    selected_region = st.selectbox(
        "目标地域",
        options=list(region_options.keys()),
        index=0
    )
    
    region_id = region_options[selected_region]
    st.info(f"区域: **{region_id}**")
    
    st.markdown("---")
    st.caption("💡 计费模式: 包年包月")
    st.caption("🎯 推荐策略: NewProductFirst")

# ============================================================================
# 主界面
# ============================================================================

st.title("💰 阿里云ECS智能报价系统")
st.caption("上传Excel文件，自动生成报价单")

st.markdown("---")

# 文件上传
st.subheader("📁 上传Excel文件")

uploaded_file = st.file_uploader(
    "选择Excel文件",
    type=['xlsx', 'xls'],
    label_visibility="collapsed"
)

if uploaded_file:
    st.success(f"✅ 已选择: {uploaded_file.name}")
    
    # 开始处理按钮
    if st.button("🚀 开始生成报价", type="primary", use_container_width=True):
        start_processing = True
    else:
        start_processing = False
    
    # 处理逻辑
    if start_processing:
        with st.spinner("⚙️ 正在初始化服务..."):
            try:
                # 初始化服务
                pricing_service, sku_service, processor = initialize_services(region_id)
                st.success(f"✅ 服务初始化完成 (区域: {region_id})")
                
                # 保存文件
                file_path = save_uploaded_file(uploaded_file)
                st.info(f"📁 文件已保存: {file_path.name}")
                
                # 创建LLM加载器并调用后端处理
                st.info("🤖 使用AI智能解析 (LLMDrivenExcelLoader)")
                loader = LLMDrivenExcelLoader(str(file_path))
                
                # 调用后端的process_batch方法
                with st.spinner("📊 正在处理Excel文件..."):
                    results = processor.process_batch(loader, verbose=False)
                
                # 转换为DataFrame
                df_results = pd.DataFrame(results)
                
                # 统计信息
                success_count = df_results['success'].sum() if 'success' in df_results.columns else 0
                total_count = len(df_results)
                
                # 计算总价（仅统计成功的记录）
                successful_df = df_results[df_results['success'] == True]
                total_price = successful_df['price_cny_month'].sum() if not successful_df.empty else 0
                
                # 显示结果
                st.success("✅ 处理完成！")
                
                st.markdown("---")
                st.subheader("📊 处理结果")
                
                # 统计信息
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("总条数", total_count)
                with col2:
                    st.metric("成功", success_count)
                with col3:
                    st.metric("总价(月)", f"¥{total_price:,.2f}")
                
                # 显示详细结果表格
                st.dataframe(df_results, use_container_width=True, height=400)
                
                # 导出Excel
                st.markdown("---")
                output_dir = Path("tests/output")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"quotation_{Path(uploaded_file.name).stem}_{timestamp}.xlsx"
                output_path = output_dir / output_filename
                
                df_results.to_excel(output_path, index=False, engine='openpyxl')
                
                with open(output_path, "rb") as f:
                    excel_data = f.read()
                
                st.download_button(
                    label="📥 下载Excel报价单",
                    data=excel_data,
                    file_name=output_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # 清理临时文件
                try:
                    file_path.unlink()
                except:
                    pass
                
            except Exception as e:
                st.error(f"❌ 处理失败: {str(e)}")
                st.exception(e)

else:
    st.info("👆 请上传Excel文件开始处理")
