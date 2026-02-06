# Figma 图片下载脚本使用说明

## 在 Figma 里直接下载（插件方式）

若你已在 Figma 中打开设计稿，可用**插件**在界面里一键导出选中图层，无需 URL、无需 Token：

- 位置：**scripts/figma-download-plugin/**  
- 安装：Figma → Resources → Plugins → Development → **Import plugin from manifest**，选择该目录下的 `manifest.json`  
- 使用：选中图层 → 打开插件「UGC 图片导出下载」→ 选择倍率(1x/2x/3x)、格式(PNG/JPG) → 点击「下载选中图层」

详细说明见 [figma-download-plugin/README.md](figma-download-plugin/README.md)。

---

## 简介

`download_figma_image.py` 是一个通用的 Figma 图片下载和压缩工具，支持：
- 从 Figma 下载图片（支持 1x、2x、3x 分辨率）
- 使用 TinyPNG API 自动压缩图片
- 支持多种图片格式（PNG、JPG、SVG、PDF）

## 安装依赖

```bash
pip3 install requests
```

## 配置环境变量

脚本支持多种方式配置环境变量，按优先级从高到低：

1. **命令行参数** (`--figma-token`, `--tinypng-key`)
2. **指定的环境变量文件** (`--env-file`)
3. **当前目录下的 .env 文件**（自动查找）
4. **终端环境变量**

### 方法 1: 使用 .env 文件（推荐）⭐

在项目根目录创建 `.env` 文件：

```bash
# .env 文件内容
FIGMA_ACCESS_TOKEN=YOUR_FIGMA_ACCESS_TOKEN
TINYPNG_API_KEY=YOUR_TINYPNG_API_KEY
```

脚本会自动查找当前目录下的 `.env` 文件。

> **当前配置的 API Keys**：
> - **Figma Access Token**: `YOUR_FIGMA_ACCESS_TOKEN`
> - **TinyPNG API Key**: `YOUR_TINYPNG_API_KEY`

### 方法 2: 使用指定的环境变量文件

```bash
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/..." \
  --output output.png \
  --env-file /path/to/.env
```

### 方法 3: 使用终端环境变量

```bash
export FIGMA_ACCESS_TOKEN=YOUR_FIGMA_ACCESS_TOKEN
export TINYPNG_API_KEY=YOUR_TINYPNG_API_KEY
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/..." \
  --output output.png
```

### 方法 4: 使用命令行参数

```bash
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/..." \
  --output output.png \
  --figma-token YOUR_FIGMA_ACCESS_TOKEN \
  --tinypng-key YOUR_TINYPNG_API_KEY
```

## 获取 API Keys

### 1. Figma Access Token

1. 访问 https://www.figma.com/
2. 登录账号
3. 进入 Settings → Account → Personal access tokens
4. 创建新的 token
5. 复制 token

### 2. TinyPNG API Key（可选，用于压缩）

1. 访问 https://tinypng.com/developers
2. 输入邮箱地址
3. 点击 "Get API key"
4. 验证邮箱并获取 API key

## 基本使用

### 方法 1: 单张图片 - 使用 Figma URL（推荐，最简单）⭐

直接使用 Figma 设计链接，脚本会自动解析参数：

```bash
# 设置环境变量（或使用 .env 文件）
export FIGMA_ACCESS_TOKEN=YOUR_FIGMA_ACCESS_TOKEN
export TINYPNG_API_KEY=YOUR_TINYPNG_API_KEY

# 使用 URL，指定输出路径
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942&m=dev" \
  --output assets/images/background@3x.png

# 使用 URL，自动生成文件名（基于 node-id）
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942"
```

输出：`618_21942@3x.png`（在当前目录）

### 方法 2: 批量下载 - 从文件读取 URL 列表 ⭐

支持从文本文件中读取多个 Figma URL，批量下载图片：

**步骤 1**：创建 URL 文件（例如 `urls.txt`）：

```text
# Figma URL 列表
# 每行一个 URL，支持 # 注释
# 空行会被忽略

# 背景图片
https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942

# 返回按钮
https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-12345
```

**步骤 2**：批量下载：

```bash
# 指定输出目录，自动生成文件名（基于 node-id）
python3 scripts/download_figma_image.py \
  --urls-file urls.txt \
  --output-dir assets/images
```

输出文件：
- `assets/images/618_21942@3x.png`
- `assets/images/618_12345@3x.png`

**自动生成文件名规则**：
- 文件名格式：`{node_id}@{scale}x.{format}`
- `node-id` 中的 `:` 会被替换为 `_`（例如：`618:21942` → `618_21942`）
- 如果不指定 `--output-dir`，默认使用当前目录

### 方法 2b: 批量下载 - 命令行直接传入多个 URL

支持在命令行中直接传入多个 Figma URL：

```bash
python3 scripts/download_figma_image.py \
  --urls "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942" \
         "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-12345" \
  --output-dir assets/images
```

### 方法 3: 单张图片 - 使用单独参数

```bash
python3 scripts/download_figma_image.py \
  --file-key mVCcQJPK1pHXRauJULaQiC \
  --node-id 618:21942 \
  --output assets/images/background@3x.png \
  --figma-token YOUR_FIGMA_ACCESS_TOKEN \
  --tinypng-key YOUR_TINYPNG_API_KEY
```

### 方法 4: 使用环境变量（推荐）

```bash
# 设置环境变量
export FIGMA_ACCESS_TOKEN=YOUR_FIGMA_ACCESS_TOKEN
export TINYPNG_API_KEY=YOUR_TINYPNG_API_KEY

# 运行脚本（使用 URL 或单独参数）
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/..." \
  --output assets/images/background@3x.png
```

## 参数说明

### 输入方式（三选一）

**方式 1: 使用 URL（推荐）**

| 参数 | 说明 | 示例 |
|------|------|------|
| `--url` | Figma 设计 URL（自动解析 file-key 和 node-id） | `https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942` |

**方式 2a: 批量下载 - 从文件读取 URL**

| 参数 | 说明 | 示例 |
|------|------|------|
| `--urls-file` | 包含多个 Figma URL 的文件路径（每行一个 URL，支持 # 注释） | `urls.txt` |

**方式 2b: 批量下载 - 命令行传入多个 URL**

| 参数 | 说明 | 示例 |
|------|------|------|
| `--urls` | 多个 Figma URL（直接在命令行传入） | `"url1" "url2" "url3"` |

**方式 3: 使用单独参数**

| 参数 | 说明 | 示例 |
|------|------|------|
| `--file-key` | Figma 文件 Key（从 URL 中获取） | `mVCcQJPK1pHXRauJULaQiC` |
| `--node-id` | Figma 节点 ID（从 URL 中获取） | `618:21942` |

> **注意**: `--url`、`--urls`、`--urls-file` 和 `--file-key/--node-id` 是互斥的，只能使用其中一种方式。

### 输出参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--output` | 输出文件路径（单张图片时可选，批量下载时可选） | 自动生成 | `assets/images/background@3x.png` |
| `--output-dir` | 批量下载时的输出目录 | 当前目录 | `assets/images` |

**自动生成文件名规则**：
- 如果不指定 `--output`，脚本会根据 `node-id` 自动生成文件名
- 文件名格式：`{node_id}@{scale}x.{format}`（例如：`618_21942@3x.png`）
- `node-id` 中的 `:` 会被替换为 `_`，以确保文件名合法

### 可选参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--env-file` | 环境变量文件路径 | 无 | `/path/to/.env` |
| `--figma-token` | Figma Access Token | 按优先级读取 | `figd_xxx...` |
| `--tinypng-key` | TinyPNG API Key | 按优先级读取 | `kLCTYhpdt...` |
| `--scale` | 图片分辨率倍数 | `3` | `1`, `2`, `3` |
| `--format` | 图片格式 | `png` | `png`, `jpg`, `svg`, `pdf` |
| `--no-compress` | 跳过 TinyPNG 压缩 | `False` | - |

## 使用示例

### 示例 1: 使用 URL 和 .env 文件（推荐）⭐

```bash
# 确保项目根目录有 .env 文件
# .env 内容：
#   FIGMA_ACCESS_TOKEN=YOUR_FIGMA_ACCESS_TOKEN
#   TINYPNG_API_KEY=YOUR_TINYPNG_API_KEY

python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942" \
  --output assets/images/background@3x.png \
  --scale 3
```

### 示例 1.1: 使用指定的环境变量文件

```bash
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942" \
  --output assets/images/background@3x.png \
  --env-file /path/to/custom.env
```

### 示例 2: 使用 URL 下载 @2x 图片（不使用压缩）

```bash
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942" \
  --output assets/images/background@2x.png \
  --scale 2 \
  --no-compress
```

### 示例 3: 批量下载 - 从文件读取 URL

**步骤 1**：创建 URL 文件 `urls.txt`：

```text
# 背景图片
https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942

# 返回按钮
https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-12345
```

**步骤 2**：批量下载：

```bash
python3 scripts/download_figma_image.py \
  --urls-file urls.txt \
  --output-dir assets/images
```

输出：
- `assets/images/618_21942@3x.png`
- `assets/images/618_12345@3x.png`

### 示例 4: 使用单独参数下载 JPG 格式

```bash
python3 scripts/download_figma_image.py \
  --file-key mVCcQJPK1pHXRauJULaQiC \
  --node-id 618:21942 \
  --output assets/images/background.jpg \
  --format jpg
```

### 示例 5: 使用 URL 下载 SVG 格式

```bash
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-12345" \
  --output assets/images/icon.svg \
  --format svg \
  --no-compress
```

## 如何从 Figma URL 获取参数

### 方法 1: 直接使用 URL（推荐）⭐

最简单的方式是直接使用完整的 Figma URL，脚本会自动解析：

```bash
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942&m=dev" \
  --output output.png
```

脚本会自动：
- 从 URL 中提取 File Key: `mVCcQJPK1pHXRauJULaQiC`
- 从 URL 中提取 Node ID: `618:21942`（自动将 `-` 转换为 `:`）

### 方法 2: 手动提取参数

如果需要使用单独参数，可以从 Figma URL 中提取：

Figma URL 格式：
```
https://www.figma.com/design/{FILE_KEY}/文件名?node-id={NODE_ID}
```

例如：
```
https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942
```

- **File Key**: `mVCcQJPK1pHXRauJULaQiC`（URL 中 `/design/` 后面的部分）
- **Node ID**: `618:21942`（注意：URL 中是 `618-21942`，需要转换为 `618:21942`）

### 在 Figma 中获取 URL

1. 在 Figma 中选择元素
2. 右键点击元素 → "Copy link"
3. 或者从浏览器地址栏复制完整 URL

## 压缩效果

使用 TinyPNG API 压缩通常可以：
- **减少 50-80%** 的文件大小
- 保持高质量的视觉效果
- 智能有损压缩，视觉上几乎无差异

### 压缩示例

```
原始大小: 1322.5 KB
压缩后: 366.9 KB
减少: 72.3%
```

## 环境变量配置优先级

脚本按以下优先级读取环境变量（从高到低）：

1. **命令行参数** (`--figma-token`, `--tinypng-key`)
2. **指定的环境变量文件** (`--env-file`)
3. **当前目录下的 .env 文件**（自动查找）
4. **终端环境变量**

### 推荐方式：使用 .env 文件

在项目根目录创建 `.env` 文件：

```bash
# .env 文件内容
FIGMA_ACCESS_TOKEN=YOUR_FIGMA_ACCESS_TOKEN
TINYPNG_API_KEY=YOUR_TINYPNG_API_KEY
```

**优点**：
- 不需要每次设置环境变量
- 可以添加到 `.gitignore` 中，避免泄露密钥
- 团队可以共享 `.env.example` 模板

**注意**：确保将 `.env` 添加到 `.gitignore` 中，不要提交到 Git 仓库。

### 备选方式：终端环境变量

#### 临时设置（当前终端会话）

```bash
export FIGMA_ACCESS_TOKEN=YOUR_FIGMA_ACCESS_TOKEN
export TINYPNG_API_KEY=YOUR_TINYPNG_API_KEY
```

#### 永久设置（添加到 ~/.zshrc 或 ~/.bashrc）

```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
export FIGMA_ACCESS_TOKEN=YOUR_FIGMA_ACCESS_TOKEN
export TINYPNG_API_KEY=YOUR_TINYPNG_API_KEY
```

然后重新加载配置：
```bash
source ~/.zshrc  # 或 source ~/.bashrc
```

## 常见问题

### 1. 提示 "需要提供 Figma Access Token"

**解决方案**：
- 通过 `--figma-token` 参数提供
- 或设置环境变量 `FIGMA_ACCESS_TOKEN`

### 2. TinyPNG API 压缩失败

**可能原因**：
- API key 无效
- 超过每月限制（免费版 500 次）
- 网络问题

**解决方案**：
- 检查 API key 是否正确
- 使用 `--no-compress` 跳过压缩
- 检查网络连接

### 3. 无法获取节点信息

**可能原因**：
- File Key 或 Node ID 错误
- Access Token 无效
- 没有文件访问权限

**解决方案**：
- 检查 File Key 和 Node ID 是否正确
- 确认 Access Token 有效
- 确认有文件访问权限

### 4. 图片下载失败

**可能原因**：
- 网络连接问题
- 图片 URL 过期
- 文件路径不存在

**解决方案**：
- 检查网络连接
- 重新运行脚本获取新的 URL
- 确保输出目录存在或可创建

## 输出示例

成功运行时的输出：

```
🚀 开始从 Figma 下载图片...
📁 输出文件: assets/images/background@3x.png
🔑 文件 Key: mVCcQJPK1pHXRauJULaQiC
📍 节点 ID: 618:21942
📐 分辨率: 3x
📄 格式: png
🗜️  TinyPNG API: 已配置

📥 获取 Figma 节点信息...
✅ 节点信息获取成功

📸 获取图片导出 URL (3x)...
✅ 图片导出 URL 获取成功

📥 下载背景图 (@3x)...
📥 正在下载: https://figma-alpha-api.s3.us-west-2.amazonaws.com/...
   进度: 100.0%
✅ 下载完成: 1322.5 KB
🔧 正在使用 TinyPNG 优化图片...
   🔄 正在使用 TinyPNG API 压缩...
   ✨ TinyPNG 压缩: 1322.5 KB → 366.9 KB (减少 72.3%)
   📊 API 剩余次数: 499
✅ 最终文件: background@3x.png (366.9 KB)

✅ 图片下载和优化完成！
📁 文件位置: /path/to/assets/images/background@3x.png
```

## 批量下载（已内置支持）⭐

脚本已内置批量下载功能，使用 `--urls-file` 参数即可：

**创建 URL 文件**（例如 `urls.txt`）：

```text
# 每行一个 URL，支持 # 注释
# 空行会被忽略

https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942
https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-12345
```

**批量下载**：

```bash
python3 scripts/download_figma_image.py \
  --urls-file urls.txt \
  --output-dir assets/images
```

**自动生成文件名**：
- 批量下载时，如果不指定 `--output`，每张图片都会根据其 `node-id` 自动生成文件名
- 文件名格式：`{node_id}@{scale}x.{format}`（例如：`618_21942@3x.png`）
- `node-id` 中的 `:` 会被替换为 `_`，以确保文件名合法

**使用示例文件**：

项目已包含示例文件 `scripts/urls_example.txt`：

```bash
python3 scripts/download_figma_image.py \
  --urls-file scripts/urls_example.txt \
  --output-dir assets/images
```

**旧方式（不推荐）**：如果需要手动循环下载：

## 相关文档

- [Figma API 文档](https://www.figma.com/developers/api)
- [TinyPNG API 文档](https://tinypng.com/developers)
- [TinyPNG 设置说明](./TINYPNG_SETUP.md)
- [环境变量文件配置指南](./ENV_FILE_GUIDE.md)

## 许可证

本脚本为项目内部工具，遵循项目许可证。
