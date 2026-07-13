#!/bin/bash
# ============================================================
# NEXUS · 招标文件合规检测工具 —— 一键部署脚本
# 用法: chmod +x deploy.sh && ./deploy.sh
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目根目录（脚本所在目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}  NEXUS · 招标文件合规检测工具 —— 一键部署${NC}"
echo -e "${CYAN}====================================================${NC}"
echo ""

# ============================================================
# Step 1: 检查Python环境
# ============================================================
echo -e "${YELLOW}[1/6] 检查Python环境...${NC}"

if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo -e "${RED}错误: 未找到Python，请先安装Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1)
echo -e "  Python版本: ${GREEN}${PYTHON_VERSION}${NC}"

# ============================================================
# Step 2: 安装系统依赖（中文字体）
# ============================================================
echo -e "${YELLOW}[2/6] 检查系统依赖...${NC}"

if command -v apt-get &>/dev/null; then
    if ! fc-list | grep -qi "wqy-zenhei\|noto.*cjk"; then
        echo "  安装中文字体（PDF报告需要）..."
        sudo apt-get update -qq && sudo apt-get install -y -qq fonts-wqy-zenhei 2>/dev/null || echo -e "  ${YELLOW}警告: 中文字体安装失败，PDF报告中文可能显示异常${NC}"
    else
        echo -e "  ${GREEN}中文字体已安装${NC}"
    fi
elif command -v yum &>/dev/null; then
    if ! fc-list | grep -qi "wqy-zenhei\|noto.*cjk"; then
        echo "  安装中文字体（PDF报告需要）..."
        sudo yum install -y -q wqy-zenhei-fonts 2>/dev/null || echo -e "  ${YELLOW}警告: 中文字体安装失败${NC}"
    else
        echo -e "  ${GREEN}中文字体已安装${NC}"
    fi
else
    echo -e "  ${YELLOW}警告: 无法自动安装中文字体，PDF报告中文可能显示异常${NC}"
fi

# ============================================================
# Step 3: 创建虚拟环境
# ============================================================
echo -e "${YELLOW}[3/6] 创建Python虚拟环境...${NC}"

if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    echo -e "  ${GREEN}虚拟环境创建成功${NC}"
else
    echo -e "  虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
source venv/bin/activate

# ============================================================
# Step 4: 安装Python依赖
# ============================================================
echo -e "${YELLOW}[4/6] 安装Python依赖...${NC}"

pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "  ${GREEN}依赖安装完成${NC}"

# ============================================================
# Step 5: 配置环境变量
# ============================================================
echo -e "${YELLOW}[5/6] 检查API Key配置...${NC}"

if [ -z "$SILICONFLOW_API_KEY" ]; then
    echo -e "  ${YELLOW}警告: 未设置 SILICONFLOW_API_KEY 环境变量${NC}"
    echo -e "  系统将以「仅规则引擎检测」模式运行（无AI深度分析）"
    echo ""
    echo -e "  如需启用AI深度分析，请执行以下步骤："
    echo -e "  1. 访问 ${CYAN}https://cloud.siliconflow.cn${NC} 注册账号（新用户送2000万免费Token）"
    echo -e "  2. 在「API密钥」页面创建密钥"
    echo -e "  3. 设置环境变量:"
    echo -e "     ${CYAN}export SILICONFLOW_API_KEY=\"sk-你的密钥\"${NC}"
    echo -e "  4. 重新运行本脚本"
    echo ""
    
    # 询问是否继续
    read -p "  是否继续以仅规则引擎模式启动？(y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}部署已取消${NC}"
        exit 0
    fi
else
    echo -e "  ${GREEN}SILICONFLOW_API_KEY 已配置${NC}"
fi

# ============================================================
# Step 6: 启动服务
# ============================================================
echo -e "${YELLOW}[6/6] 启动服务...${NC}"
echo ""

# 检查端口是否被占用
if command -v lsof &>/dev/null; then
    if lsof -i:5000 &>/dev/null; then
        echo -e "  ${YELLOW}端口5000已被占用，尝试终止旧进程...${NC}"
        kill $(lsof -t -i:5000) 2>/dev/null || true
        sleep 1
    fi
fi

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}  部署完成！服务正在启动...${NC}"
echo -e "${GREEN}====================================================${NC}"
echo ""
echo -e "  访问地址: ${CYAN}http://127.0.0.1:5000${NC}"
echo -e "  健康检查: ${CYAN}http://127.0.0.1:5000/api/health${NC}"
echo ""
echo -e "  按 ${YELLOW}Ctrl+C${NC} 停止服务"
echo ""

# 启动Flask
python app.py
