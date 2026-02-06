# download_figma_img_from_urls

从 Figma 下载图片并支持 TinyPNG 压缩。支持 `--url` 单张、`--urls` 多张、`--urls-file` 从文件读取。

## 安装

### 方式一：curl 一键安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/hly-Shells/download_figma_img_from_urls/main/install.sh | bash

# 或指定安装目录
curl -fsSL https://raw.githubusercontent.com/hly-Shells/download_figma_img_from_urls/main/install.sh | bash -s /path/to/install
```

### 方式二：curl 手动下载

```bash
curl -fsSL https://raw.githubusercontent.com/hly-Shells/download_figma_img_from_urls/main/download_figma_image.py -o download_figma_image.py
curl -fsSL https://raw.githubusercontent.com/hly-Shells/download_figma_img_from_urls/main/requirements.txt -o requirements.txt
pip install -r requirements.txt
```

### 方式三：Git 克隆

```bash
git clone https://github.com/hly-Shells/download_figma_img_from_urls.git
cd download_figma_img_from_urls
pip install -r requirements.txt
```

## 快速使用

```bash
# 单张图片
python3 download_figma_image.py --url "你的Figma链接" --output output.png

# 批量下载（命令行传入多个 URL）
python3 download_figma_image.py --urls "url1" "url2" --output-dir ./images

# 批量下载（从文件读取）
python3 download_figma_image.py --urls-file urls.txt --output-dir ./images
```

---

## Figma 插件（在 Figma 内直接下载）

若已在 Figma 中打开设计稿，可用**插件**在界面里一键导出选中图层，无需 URL、无需 Token：

- **位置**：`figma-download-plugin/`
- **安装**：Figma → Resources → Plugins → Development → **Import plugin from manifest**，选择 `figma-download-plugin/manifest.json`
- **使用**：选中图层 → 打开插件「UGC 图片导出下载」→ 选择倍率(1x/2x/3x)、格式(PNG/JPG) → 点击「下载选中图层」

### 插件最少操作：多张 3x + TinyPNG 一步到位

1. **一次性准备**：本机运行 `python3 figma_compress_server.py`（需 `TINYPNG_API_KEY`）
2. **日常使用**：在 Figma 里多选要导出的图层 → 倍率保持 3x，勾选「仅下载压缩图」→ 点击「下载选中图层（多选即多张）」  
   结果：每张图只下一个已压缩的 3x 文件，无原图。

### 插件面板说明

| 项 | 说明 |
|----|------|
| **倍率** | 1x / 2x / 3x / 4x（默认 3x） |
| **格式** | PNG 或 JPG |
| **压缩服务 URL** | 默认 `http://localhost:8765/compress`，需先运行 `figma_compress_server.py` |
| **仅下载压缩图** | 勾选时只下载 TinyPNG 压缩后的图 |

### 本地压缩服务（插件用）

```bash
pip install flask requests
export TINYPNG_API_KEY=你的key
python3 figma_compress_server.py
```

---

## 配置环境变量

脚本支持多种方式配置，按优先级从高到低：

1. 命令行参数 `--figma-token`、`--tinypng-key`
2. 指定的环境变量文件 `--env-file`
3. 当前目录下的 `.env` 文件（自动查找）
4. 终端环境变量

### 使用 .env 文件（推荐）

在项目根目录创建 `.env`：

```bash
FIGMA_ACCESS_TOKEN=YOUR_FIGMA_ACCESS_TOKEN
TINYPNG_API_KEY=YOUR_TINYPNG_API_KEY
```

`.env` 支持：`KEY=value`、`KEY="value"`、`#` 注释、空行。

> ⚠️ 将 `.env` 加入 `.gitignore`，不要提交到 Git。

### 获取 API Keys

- **Figma Token**：https://www.figma.com/ → Settings → Personal access tokens
- **TinyPNG Key**：https://tinypng.com/developers（免费每月 500 次）

---

## 命令行使用详解

### 输入方式（三选一）

| 参数 | 说明 | 示例 |
|------|------|------|
| `--url` | 单个 Figma URL | `--url "https://www.figma.com/design/xxx?node-id=618-21942"` |
| `--urls` | 多个 Figma URL（命令行传入） | `--urls "url1" "url2"` |
| `--urls-file` | 包含多个 URL 的文件（每行一个，支持 # 注释） | `--urls-file urls.txt` |
| `--file-key` + `--node-id` | 单独指定 file-key 和 node-id | `--file-key xxx --node-id 618:21942` |

> `--url`、`--urls`、`--urls-file` 与 `--file-key/--node-id` 互斥。

### 输出参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--output` | 输出文件路径 | 自动生成（基于 node-id） |
| `--output-dir` | 批量下载时的输出目录 | 当前目录 |

自动生成文件名：`{node_id}@{scale}x.{format}`，如 `618_21942@3x.png`。

### 可选参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--env-file` | 环境变量文件路径 | 无 |
| `--figma-token` | Figma Access Token | 按优先级读取 |
| `--tinypng-key` | TinyPNG API Key | 按优先级读取 |
| `--scale` | 分辨率倍数 1x/2x/3x | `3` |
| `--format` | 格式 png/jpg/svg/pdf | `png` |
| `--no-compress` | 跳过 TinyPNG 压缩 | `False` |

---

## 使用示例

### 单张图片

```bash
# 使用 URL，指定输出
python3 download_figma_image.py --url "https://www.figma.com/design/xxx?node-id=618-21942" --output output.png

# 使用 URL，自动生成文件名
python3 download_figma_image.py --url "https://www.figma.com/design/xxx?node-id=618-21942"

# 使用 file-key + node-id
python3 download_figma_image.py --file-key mVCcQJPK1pHXRauJULaQiC --node-id 618:21942 --output output.png
```

### 批量下载

```bash
# 从文件读取
python3 download_figma_image.py --urls-file urls.txt --output-dir assets/images

# 命令行传入多个 URL
python3 download_figma_image.py --urls "url1" "url2" "url3" --output-dir assets/images
```

### 其他示例

```bash
# @2x 不压缩
python3 download_figma_image.py --url "..." --output out@2x.png --scale 2 --no-compress

# SVG 格式
python3 download_figma_image.py --url "..." --output icon.svg --format svg --no-compress

# 指定环境变量文件
python3 download_figma_image.py --url "..." --output out.png --env-file /path/to/.env
```

---

## URL 格式说明

支持的 Figma URL 格式：

- `https://www.figma.com/design/{file_key}/文件名?node-id={node_id}`
- `https://figma.com/design/{file_key}/文件名?node-id={node_id}`
- 可包含其他查询参数（如 `&m=dev`）

在 Figma 中：选中元素 → 右键「Copy link」或从浏览器地址栏复制。

---

## TinyPNG 压缩

- 通常可减少 50–80% 文件大小，视觉几乎无差异
- 免费 API 每月 500 次
- 未配置 TinyPNG 时可用 `--no-compress` 跳过压缩

---

## 常见问题

**提示「需要提供 Figma Access Token」**  
通过 `--figma-token` 或环境变量 `FIGMA_ACCESS_TOKEN` 提供。

**TinyPNG 压缩失败**  
检查 API key、是否超限、网络；或使用 `--no-compress` 跳过。

**无法获取节点信息**  
检查 File Key、Node ID、Token 是否有效，是否有文件访问权限。

**图片下载失败**  
检查网络、输出目录是否存在。

---

## 相关链接

- [Figma API](https://www.figma.com/developers/api)
- [TinyPNG API](https://tinypng.com/developers)
