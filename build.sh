#!/bin/bash
# AI Agent 快速打包脚本
# 适用于 Linux/macOS 系统

set -e

echo "======================================"
echo "🚀 AI Agent 打包工具"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在项目根目录
if [ ! -f "main.py" ]; then
    echo -e "${RED}错误：请在项目根目录执行此脚本${NC}"
    exit 1
fi

# 检查 flet 是否安装
if ! command -v flet &> /dev/null; then
    echo -e "${RED}错误：未找到 flet 命令，请先安装：pip install flet${NC}"
    exit 1
fi

# 显示版本信息
echo -e "${YELLOW}Flet 版本:${NC}"
flet --version
echo ""

# 清理旧的构建文件
echo -e "${YELLOW}清理旧的构建文件...${NC}"
rm -rf dist/ build/ __pycache__/ .pytest_cache/
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.pyc" -exec rm -rf {} + 2>/dev/null || true
echo -e "${GREEN}✓ 清理完成${NC}"
echo ""

# 开始打包
echo -e "${YELLOW}开始打包...${NC}"
echo "这可能需要 5-10 分钟，请耐心等待..."
echo ""

# 检测操作系统
OS="$(uname -s)"

case "$OS" in
    Linux*)
        DATA_SEPARATOR=":"
        ICON_FILE="assets/icon.png"
        OUTPUT_NAME="AI-Agent-Linux"
        ;;
    Darwin*)
        DATA_SEPARATOR=":"
        ICON_FILE="assets/icon.icns"
        OUTPUT_NAME="AI-Agent-macOS"
        ;;
    *)
        echo -e "${RED}不支持的操作系统：$OS${NC}"
        exit 1
        ;;
esac

# 执行打包命令
echo -e "${YELLOW}执行打包命令...${NC}"
flet pack main.py \
  --name "AI Agent" \
  --file-version "1.0.0" \
  --product-version "1.0.0" \
  --icon "$ICON_FILE" \
  --add-data "theme${DATA_SEPARATOR}theme" \
  --add-data "components${DATA_SEPARATOR}components" \
  --add-data "views${DATA_SEPARATOR}views" \
  --add-data "core${DATA_SEPARATOR}core" \
  --add-data "tools${DATA_SEPARATOR}tools" \
  --add-data "controllers${DATA_SEPARATOR}controllers" \
  --add-data "services${DATA_SEPARATOR}services" \
  --add-data "utils${DATA_SEPARATOR}utils" \
  --hidden-import langchain \
  --hidden-import langchain_openai \
  --hidden-import langchain_deepseek \
  --hidden-import yaml \
  --hidden-import aiohttp \
  --hidden-import dotenv \
  --hidden-import tree_sitter \
  --hidden-import tree_sitter_python

# 检查打包结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}======================================"
    echo "✅ 打包成功！"
    echo -e "${GREEN}======================================${NC}"
    echo ""
    
    # 显示生成的文件
    if [ -d "dist/AI Agent" ]; then
        echo -e "${YELLOW}生成的文件:${NC}"
        ls -lh "dist/AI Agent/"
        echo ""
        
        # 计算文件大小
        SIZE=$(du -sh "dist/AI Agent" | cut -f1)
        echo -e "${YELLOW}总大小：${NC}$SIZE"
        echo ""
        
        echo -e "${GREEN}运行方式:${NC}"
        echo "cd 'dist/AI Agent'"
        echo "./AI\ Agent"
        echo ""
    fi
    
    echo -e "${YELLOW}提示:${NC}"
    echo "- 可执行文件位于：dist/AI Agent/"
    echo "- 如需分发，请将整个目录打包"
    echo "- 首次启动可能需要几秒钟加载"
    echo ""
    
else
    echo ""
    echo -e "${RED}======================================"
    echo "❌ 打包失败！"
    echo -e "${RED}======================================${NC}"
    echo ""
    echo "请检查以下常见问题："
    echo "1. 确保所有依赖已安装：pip install -r requirements.txt"
    echo "2. 检查图标文件是否存在：$ICON_FILE"
    echo "3. 查看上方错误信息"
    echo ""
    exit 1
fi
