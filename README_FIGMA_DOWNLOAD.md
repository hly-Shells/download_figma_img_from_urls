# Figma 图片下载脚本说明

## ✅ 已完成的下载

背景图片已成功下载并优化：
- **文件**: `ugc_flutter/assets/images/account_login_background@3x.png`
- **大小**: 1.15 MB（已压缩，原始大小 1.32 MB）
- **压缩率**: 减少约 12.6%
- **分辨率**: @3x（高分辨率）
- **质量**: 高质量（无损压缩）

## 📥 如何下载返回按钮图片

### 方法 1: 使用脚本（推荐）

1. **在 Figma 中获取返回按钮的节点 ID**：
   - 打开 Figma 设计文件
   - 选择返回按钮元素
   - 在右侧面板查看节点 ID（格式如：`618:12345`）

2. **修改脚本**：
   ```python
   # 在 scripts/download_figma_login_images.py 中
   BACK_BUTTON_NODE_ID = "618:12345"  # 替换为实际的节点 ID
   ```

3. **运行脚本**：
   ```bash
   cd /Users/apple/workspace/github/ugc_box
   python3 scripts/download_figma_login_images.py
   ```

### 方法 2: 手动导出

1. 在 Figma 中选择返回按钮
2. 在右侧面板找到 "Export" 部分
3. 添加导出设置：PNG, 3x
4. 点击 "Export"
5. 将文件保存为：`ugc_flutter/assets/images/account_login_back_button.png`

## 🔄 重新下载背景图

如果需要重新下载背景图，直接运行：

```bash
cd /Users/apple/workspace/github/ugc_box
python3 scripts/download_figma_login_images.py
```

脚本会自动下载最新的背景图（@3x）。

## 📝 注意事项

- 脚本使用 Figma REST API，需要有效的 `FIGMA_ACCESS_TOKEN`
- Token 可以通过环境变量设置：`export FIGMA_ACCESS_TOKEN=your_token`
- 或者直接在脚本中修改 `FIGMA_ACCESS_TOKEN` 变量（不推荐，有安全风险）

## 🗜️ 图片压缩

脚本会自动对下载的图片进行优化压缩：
- **压缩方式**: PNG 优化（无损压缩）
- **压缩级别**: 6（平衡质量和大小）
- **预期效果**: 通常可以减少 10-20% 的文件大小，同时保持高质量
- **依赖**: 需要安装 Pillow 库（`pip3 install Pillow`）

如果 Pillow 未安装，脚本会跳过压缩，直接使用原始图片。

## 🎯 当前状态

- ✅ 背景图片已下载（@3x）
- ⏳ 返回按钮图片待下载（需要节点 ID）
