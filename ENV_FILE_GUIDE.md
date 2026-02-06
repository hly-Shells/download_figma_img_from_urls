# 环境变量文件配置指南

## .env 文件格式

脚本支持标准的 `.env` 文件格式，支持以下特性：

- `KEY=value` 格式
- 支持引号：`KEY="value"` 或 `KEY='value'`
- 支持注释：以 `#` 开头的行
- 忽略空行

### 示例 .env 文件

```bash
# Figma API 配置
FIGMA_ACCESS_TOKEN=YOUR_FIGMA_ACCESS_TOKEN

# TinyPNG API 配置
TINYPNG_API_KEY=YOUR_TINYPNG_API_KEY

# 注释行会被忽略
# 空行也会被忽略
```

## 环境变量读取优先级

脚本按以下优先级读取环境变量（从高到低）：

1. **命令行参数** (`--figma-token`, `--tinypng-key`)
2. **指定的环境变量文件** (`--env-file /path/to/.env`)
3. **当前目录下的 .env 文件**（自动查找）
4. **终端环境变量** (`export FIGMA_ACCESS_TOKEN=...`)

## 使用方式

### 方式 1: 自动查找 .env 文件（推荐）⭐

在项目根目录创建 `.env` 文件：

```bash
# 创建 .env 文件
cat > .env << 'EOF'
FIGMA_ACCESS_TOKEN=your_figma_token
TINYPNG_API_KEY=your_tinypng_key
EOF

# 运行脚本（自动查找 .env）
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/..." \
  --output output.png
```

### 方式 2: 指定环境变量文件

```bash
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/..." \
  --output output.png \
  --env-file /path/to/custom.env
```

### 方式 3: 使用终端环境变量

```bash
export FIGMA_ACCESS_TOKEN=your_token
export TINYPNG_API_KEY=your_key
python3 scripts/download_figma_image.py \
  --url "https://www.figma.com/design/..." \
  --output output.png
```

## 安全建议

⚠️ **重要**：`.env` 文件包含敏感信息，请确保：

1. **添加到 .gitignore**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **创建 .env.example 模板**
   ```bash
   # .env.example（提交到 Git）
   FIGMA_ACCESS_TOKEN=your_figma_token_here
   TINYPNG_API_KEY=your_tinypng_key_here
   ```

3. **不要提交 .env 文件到 Git 仓库**

## 验证配置

运行脚本时，如果成功读取 .env 文件，会显示：

```
📄 环境变量文件: /path/to/.env
🗜️  TinyPNG API: 已配置
```

如果没有找到 .env 文件，会显示：

```
⚠️  TinyPNG API: 未配置（将跳过压缩）
```

## 故障排除

### 问题 1: 脚本无法读取 .env 文件

**检查**：
- 确认 `.env` 文件在项目根目录（运行脚本的目录）
- 确认文件格式正确（`KEY=value`）
- 确认没有语法错误

### 问题 2: 环境变量未生效

**检查优先级**：
- 如果使用了 `--figma-token` 参数，会覆盖 .env 文件中的值
- 确认 .env 文件中的 key 名称正确（`FIGMA_ACCESS_TOKEN` 和 `TINYPNG_API_KEY`）

### 问题 3: 引号问题

**解决方案**：
- 支持带引号的值：`KEY="value"` 或 `KEY='value'`
- 也支持不带引号：`KEY=value`
- 脚本会自动处理引号
