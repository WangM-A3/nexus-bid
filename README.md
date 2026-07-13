# NEXUS · 招标文件合规检测工具

> 基于 AI 大模型 + 规则引擎的招标文件合规性自动检测系统

## 📋 项目简介

本工具响应国家发改委等8部门2026年2月印发的《关于加快招标投标领域人工智能推广应用的实施意见》（发改法规〔2026〕195号），针对其中"招标文件检测"重点场景，实现对招标文件的自动化合规审查。

### 检测维度

| 维度 | 说明 |
|------|------|
| 排斥限制竞争 | 地域歧视、规模歧视、品牌指定、过高业绩门槛、不合理资质要求等 |
| 违法违规条款 | 肢解项目规避招标、串通投标、违规分包、不合理收费等 |
| 错敏词检测 | 政治敏感词、错别字、不规范表述 |
| 评标办法合规性 | 价格分占比、主观分占比、评分标准合理性 |
| 其他风险 | 保证金比例超标、工期不合理、质保金过高、预付款过低、付款条件苛刻 |

### 检测流程

```
用户上传文件 → 文档解析(.docx/.pdf/.txt) → 规则引擎检测(正则+数值) → LLM深度分析(可选) → 合并去重 → 生成报告(JSON+PDF)
```

## 🛠️ 技术栈

| 组件 | 技术选型 |
|------|---------|
| 后端 | Python Flask |
| 前端 | 单页HTML + Bootstrap风格 + 深色主题 |
| 文档解析 | python-docx (.docx) / PyPDF2 (.pdf) / 内置 (.txt) |
| AI检测 | 硅基流动API (SiliconFlow) - Qwen/Qwen2.5-72B-Instruct |
| PDF报告 | ReportLab |
| 数据存储 | 内存（无需数据库） |

## 📦 项目结构

```
招标AI检测/
├── app.py              # Flask后端（路由+文档解析+规则检测+LLM调用+报告生成）
├── rules.py            # 规则引擎（排斥性条款关键词库+保证金/工期等数值检测规则）
├── templates/
│   └── index.html      # 前端页面（上传+结果展示+PDF下载）
├── requirements.txt    # Python依赖列表
├── deploy.sh           # 一键部署脚本
└── README.md           # 本文档
```

## 🚀 快速部署

### 方式一：一键部署脚本

```bash
chmod +x deploy.sh
./deploy.sh
```

脚本会自动完成：安装系统依赖 → 创建虚拟环境 → 安装Python依赖 → 配置环境变量 → 启动服务。

### 方式二：手动部署

#### 1. 系统依赖安装

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv fonts-wqy-zenhei

# CentOS/RHEL
sudo yum install -y python3 python3-pip
# 中文字体（用于PDF生成）
sudo yum install -y wqy-zenhei-fonts
```

#### 2. 创建虚拟环境并安装依赖

```bash
cd 招标AI检测
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. 配置环境变量

**必须配置**（否则仅规则引擎检测，无AI深度分析）：

```bash
export SILICONFLOW_API_KEY="你的硅基流动API Key"
```

获取API Key：
1. 访问 https://cloud.siliconflow.cn 注册账号
2. 新用户注册送 2000万 免费 Token
3. 在「API密钥」页面创建密钥，复制 `sk-` 开头的Key

可选配置：
```bash
export FLASK_ENV=production  # 生产模式
```

#### 4. 启动服务

```bash
python app.py
```

启动后访问 http://127.0.0.1:5000

#### 5. 后台运行（生产环境）

```bash
# 使用nohup
nohup python app.py > app.log 2>&1 &

# 或使用gunicorn（推荐）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🔌 API 接口说明

### 1. 前端页面
```
GET /
```
返回上传页面HTML。

### 2. 上传文件检测
```
POST /api/check
```
**请求**：`multipart/form-data`，字段 `file` 为上传的文件（.docx/.pdf/.txt）

**响应**：
```json
{
  "id": "abc123...",
  "filename": "招标文件.docx",
  "check_time": "2026-07-13 11:00:00",
  "summary": {"total": 8, "high": 2, "medium": 4, "low": 2},
  "items": [
    {
      "level": "高",
      "category": "排斥限制竞争",
      "description": "要求投标人为本地注册企业",
      "original_text": "投标人须为本地注册企业...",
      "legal_basis": "《招标投标法实施条例》第三十二条",
      "suggestion": "删除地域限制要求..."
    }
  ],
  "text_length": 15000,
  "llm_enabled": true
}
```

### 3. 获取报告（JSON / PDF）
```
GET /api/report/<report_id>          # 返回JSON
GET /api/report/<report_id>?format=pdf  # 下载PDF
```

### 4. 健康检查
```
GET /api/health
```
```json
{
  "status": "ok",
  "llm_enabled": true,
  "model": "Qwen/Qwen2.5-72B-Instruct"
}
```

## 🎨 前端特性

- **深色主题**：背景 `#0a0a1a`，主色 `#00ffff`（蓝绿色系），NEXUS品牌风格
- **拖拽上传**：支持点击选择和拖拽文件上传
- **实时反馈**：加载动画 + 阶段性提示文字
- **结构化展示**：检测结果按风险等级（高/中/低）排序，每条包含问题描述、原文引用、法规依据、修改建议
- **PDF下载**：一键下载格式化检测报告
- **响应式布局**：适配桌面和移动端

## 💰 成本说明

| 项目 | 费用 |
|------|------|
| 硅基流动API | 新用户免费2000万Token（Qwen2.5-72B-Instruct约¥0.004/千Token） |
| 服务器 | 任意可运行Python的Linux服务器 |
| 域名 | 可选，使用IP访问无需域名 |

每次检测大约消耗 2000-4000 Token，免费额度可支持约 5000-10000 次检测。

## ⚠️ 免责声明

本工具检测结果仅供参考，采用规则引擎与AI大语言模型相结合的方式进行分析，可能存在遗漏或误判。招标文件的最终合规性应以法律法规和行政监督部门的认定为准。建议在重要项目招标前，咨询专业法律顾问进行人工审查。

## 📄 许可证

MIT License
