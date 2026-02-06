#!/bin/bash
# 从 Figma 下载账号登录页面的图片资源

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 开始从 Figma 下载图片资源...${NC}"

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 未安装，请先安装 Python 3${NC}"
    exit 1
fi

# 检查 requests 库
if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  requests 库未安装，正在安装...${NC}"
    pip3 install requests
fi

# 运行 Python 脚本
python3 "$(dirname "$0")/download_figma_images.py"
