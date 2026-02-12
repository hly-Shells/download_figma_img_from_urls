#!/bin/bash
# 用本地项目文件更新已安装的 figmad

set -e

INSTALL_DIR="${1:-$HOME/.local/share/figmad}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📦 更新本地 figmad"
echo "   源目录: $SCRIPT_DIR"
echo "   目标目录: $INSTALL_DIR"
echo ""

if [[ ! -d "$INSTALL_DIR" ]]; then
    echo "⚠️  未找到安装目录，请先运行: ./install.sh"
    exit 1
fi

cp "$SCRIPT_DIR/download_figma_image.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/" 2>/dev/null || true

# 若存在 venv，更新依赖
if [[ -f "$INSTALL_DIR/venv/bin/pip" ]]; then
    echo "📦 更新 Python 依赖..."
    "$INSTALL_DIR/venv/bin/pip" install -q -r "$INSTALL_DIR/requirements.txt"
fi

echo ""
echo "✅ 更新完成！"
echo "   执行 figmad --help 试用"
echo ""
