# Figma 图片下载工具 - 快速开始

## 一分钟快速开始

### 方法 1: 单张图片 - 使用 .env 文件（推荐）⭐

1. **创建 .env 文件**（在项目根目录）

```bash
# .env 文件内容
FIGMA_ACCESS_TOKEN=your_figma_token
TINYPNG_API_KEY=your_tinypng_key
```

2. **运行脚本**

```bash
# 指定输出路径
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942" \
  --output assets/images/background@3x.png

# 或自动生成文件名（基于 node-id）
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942"
```

就这么简单！脚本会自动从 URL 中提取参数，从 .env 文件读取配置。

### 方法 2: 批量下载 - 从文件读取 URL ⭐

1. **创建 URL 文件**（例如 `urls.txt`）：

```text
https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942
https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-12345
```

2. **批量下载**：

```bash
python3 scripts/download_figma_image.py \
  --urls-file urls.txt \
  --output-dir assets/images
```

脚本会自动为每张图片生成文件名（基于 `node-id`）。

### 方法 2b: 批量下载 - 命令行直接传入多个 URL

```bash
python3 scripts/download_figma_image.py \
  --urls "https://www.figma.com/design/...?node-id=618-21942" \
         "https://www.figma.com/design/...?node-id=618-12345" \
  --output-dir assets/images
```

### 方法 3: 使用终端环境变量

```bash
# 设置环境变量
export FIGMA_ACCESS_TOKEN=your_figma_token
export TINYPNG_API_KEY=your_tinypng_key

# 运行脚本
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942" \
  --output assets/images/background@3x.png
```

## 使用 Figma URL（推荐方式）

直接复制 Figma 设计链接，无需手动提取参数：

```bash
# 从 Figma 复制链接，直接使用
python3 scripts/download_figma_image.py \
  --url "你的 Figma URL" \
  --output 输出文件路径
```

支持的 URL 格式：
- `https://www.figma.com/design/{file_key}/文件名?node-id={node_id}`
- `https://figma.com/design/{file_key}/文件名?node-id={node_id}`
- 包含其他查询参数也可以（如 `&m=dev`）

## 使用单独参数（备选方式）

如果需要手动指定参数：

```bash
python3 scripts/download_figma_image.py \
  --file-key mVCcQJPK1pHXRauJULaQiC \
  --node-id 618:21942 \
  --output assets/images/background@3x.png
```

## 常用命令

### 下载 @3x 图片并压缩
```bash
python3 scripts/download_figma_image.py \
  --file-key FILE_KEY \
  --node-id NODE_ID \
  --output output@3x.png \
  --scale 3
```

### 下载 @2x 图片（不压缩）
```bash
python3 scripts/download_figma_image.py \
  --file-key FILE_KEY \
  --node-id NODE_ID \
  --output output@2x.png \
  --scale 2 \
  --no-compress
```

### 下载 SVG 格式
```bash
python3 scripts/download_figma_image.py \
  --file-key FILE_KEY \
  --node-id NODE_ID \
  --output icon.svg \
  --format svg \
  --no-compress
```

## 获取 API Keys

- **Figma Token**: https://www.figma.com/ → Settings → Personal access tokens
- **TinyPNG Key**: https://tinypng.com/developers

## 详细文档

查看完整使用说明：[DOWNLOAD_FIGMA_IMAGE_USAGE.md](./DOWNLOAD_FIGMA_IMAGE_USAGE.md)
