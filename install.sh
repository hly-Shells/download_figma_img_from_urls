#!/bin/bash
# Figma 图片下载脚本 - 一键安装
# 使用 curl 下载脚本和依赖

set -e

REPO="https://raw.githubusercontent.com/hly-Shells/download_figma_img_from_urls/main"
INSTALL_DIR="${1:-.}"

echo "📦 Figma 图片下载工具 - 安装"
echo "   安装目录: $INSTALL_DIR"
echo ""

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo "📥 下载 download_figma_image.py ..."
curl -fsSL "$REPO/download_figma_image.py" -o download_figma_image.py

echo "📥 下载 requirements.txt ..."
curl -fsSL "$REPO/requirements.txt" -o requirements.txt

echo ""
echo "📦 安装 Python 依赖..."
if command -v pip3 &>/dev/null; then
    pip3 install -q -r requirements.txt
elif command -v pip &>/dev/null; then
    pip install -q -r requirements.txt
else
    python3 -m pip install -q -r requirements.txt
fi

echo ""
echo "✅ 安装完成！"
echo ""
echo "使用示例："
echo "  python3 download_figma_image.py --help"
echo "  python3 download_figma_image.py --url \"你的Figma链接\" --output output.png"
echo ""
