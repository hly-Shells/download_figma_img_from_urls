#!/bin/bash
# Figma 图片下载工具 - 一键安装
# 安装后可直接使用 figmad 命令

set -e

REPO="https://raw.githubusercontent.com/hly-Shells/download_figma_img_from_urls/main"
INSTALL_DIR="${1:-$HOME/.local/share/figmad}"
BIN_DIR="${HOME}/.local/bin"

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
echo "📦 创建虚拟环境并安装依赖..."
INSTALL_DIR_ABS="$(cd "$INSTALL_DIR" && pwd)"
PYTHON_BIN=""

if python3 -m venv "$INSTALL_DIR/venv" 2>/dev/null; then
    "$INSTALL_DIR/venv/bin/pip" install -q -r requirements.txt
    PYTHON_BIN="$INSTALL_DIR_ABS/venv/bin/python"
else
    echo "   虚拟环境创建失败，尝试 pip --user 安装..."
    if python3 -m pip install --user -q -r requirements.txt 2>/dev/null; then
        PYTHON_BIN="python3"
    else
        echo "❌ 安装失败。请确保已安装 Python 3 和 pip，或尝试："
        echo "   python3 -m ensurepip --user"
        echo "   python3 -m pip install --user -r requirements.txt"
        exit 1
    fi
fi

# 创建 figmad 命令到 ~/.local/bin，确保全局可用
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/figmad" << EOF
#!/bin/bash
exec "$PYTHON_BIN" "$INSTALL_DIR_ABS/download_figma_image.py" "\$@"
EOF
chmod +x "$BIN_DIR/figmad"

# 确保 ~/.local/bin 在 PATH 中
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "📌 将 $BIN_DIR 加入 PATH..."
    for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
        if [[ -f "$rc" ]]; then
            if ! grep -q '\.local/bin' "$rc" 2>/dev/null; then
                echo "" >> "$rc"
                echo '# figmad' >> "$rc"
                echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$rc"
                echo "   已添加到 $rc"
                break
            fi
        fi
    done
    echo ""
    echo "⚠️  请执行以下命令使 PATH 生效，或重新打开终端："
    echo "   source ~/.bashrc   # 或 source ~/.zshrc"
    echo ""
fi

echo ""
echo "✅ 安装完成！"
echo ""
echo "使用示例："
echo "  figmad --help"
echo "  figmad --url \"你的Figma链接\" --output output.png"
echo "  figmad --urls \"url1\" \"url2\" --output-dir ./images"
echo "  figmad --space \"Figma文件URL\" --output-dir ./exports"
echo ""
