# Streamlit前端使用指南

## 🚀 快速开始

### 本地运行

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**

确保 `.env` 文件包含以下配置：
```bash
ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret
DASHSCOPE_API_KEY=sk-your_dashscope_key
```

3. **启动应用**
```bash
# 方式1: 使用启动脚本（推荐）
./start_app.sh

# 方式2: 直接运行
streamlit run streamlit_app.py
```

4. **访问应用**

浏览器打开：http://localhost:8501

---

## 📋 功能说明

### 1. 地域选择
- 在左侧边栏选择目标阿里云区域
- 支持国内外15+个区域
- 选择后自动应用到所有服务组件

### 2. 文件上传
- **支持格式**：
  - Excel: `.xlsx`, `.xls`
  - 图片: `.png`, `.jpg`, `.jpeg`（开发中）
  
### 3. Excel处理
- 自动识别工作表
- 支持单表或全部工作表处理
- AI智能解析资源需求
- 实时显示处理进度

### 4. 结果导出
- 查看详细报价结果
- 下载Excel格式报价单
- 包含统计汇总信息

---

## 🌐 阿里云ECS部署

### 一键部署脚本

在阿里云ECS上（Ubuntu/Debian系统）：

```bash
# 1. 克隆代码
git clone https://github.com/PCcoding666/QUOTATION_PIPELINE.git
cd QUOTATION_PIPELINE

# 2. 运行部署脚本
sudo bash deploy/deploy.sh
```

部署脚本会自动完成：
- ✅ 安装系统依赖（Python3, Nginx等）
- ✅ 创建Python虚拟环境
- ✅ 安装项目依赖
- ✅ 配置Systemd服务
- ✅ 配置Nginx反向代理
- ✅ 启动应用服务

### 手动部署步骤

如果需要手动部署，请参考以下步骤：

#### 1. 安装系统依赖
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nginx git
```

#### 2. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件填写真实的API密钥
nano .env
```

#### 4. 配置Systemd服务
```bash
sudo cp deploy/quotation-app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable quotation-app.service
sudo systemctl start quotation-app.service
```

#### 5. 配置Nginx
```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/quotation-app
sudo ln -s /etc/nginx/sites-available/quotation-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. 开放防火墙端口
```bash
# 在阿里云ECS控制台的安全组规则中添加：
# - 入方向规则
# - 端口范围：80/80
# - 授权对象：0.0.0.0/0
```

---

## 🔧 运维管理

### 服务管理命令

```bash
# 查看服务状态
sudo systemctl status quotation-app.service

# 启动服务
sudo systemctl start quotation-app.service

# 停止服务
sudo systemctl stop quotation-app.service

# 重启服务
sudo systemctl restart quotation-app.service

# 查看日志
sudo journalctl -u quotation-app.service -f
```

### Nginx管理

```bash
# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx

# 查看错误日志
sudo tail -f /var/log/nginx/quotation-app-error.log
```

---

## 📊 系统架构

```
用户浏览器
    ↓
Nginx (80端口) - 反向代理
    ↓
Streamlit应用 (8501端口)
    ↓
┌─────────────┬─────────────┬─────────────┐
│ Pricing     │ SKU         │ Batch       │
│ Service     │ Service     │ Processor   │
└─────────────┴─────────────┴─────────────┘
         ↓
    阿里云API
```

---

## 🎨 界面特性

### 左侧边栏
- ⚙️ 系统配置
  - 地域选择
  - 高级选项
- 📊 系统信息
- ❓ 使用帮助

### 主界面
- 📁 文件上传区
- 📊 Excel处理选项
- 📈 实时进度显示
- 🎉 结果展示
- 💾 导出下载

---

## ⚠️ 注意事项

### 安全建议
1. 不要将 `.env` 文件提交到Git仓库
2. 定期更换API密钥
3. 配置HTTPS（生产环境必须）
4. 限制ECS安全组访问来源

### 性能优化
1. 使用Nginx缓存静态资源
2. 配置适当的超时时间
3. 监控服务器资源使用
4. 定期清理临时文件

### 故障排查
1. 检查 `.env` 文件配置
2. 查看服务日志：`journalctl -u quotation-app.service -f`
3. 检查Nginx日志：`/var/log/nginx/quotation-app-error.log`
4. 验证网络连接和防火墙规则

---

## 📞 技术支持

如有问题，请：
1. 查看日志文件
2. 检查GitHub Issues
3. 联系系统管理员

---

## 📝 更新日志

### v1.0.0 (2025-12-03)
- ✨ 初始版本发布
- 🎨 Streamlit界面实现
- 🌐 支持多区域选择
- 📁 Excel文件处理
- 🚀 一键部署脚本
