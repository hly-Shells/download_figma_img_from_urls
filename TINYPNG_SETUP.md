# TinyPNG API 配置说明

## 为什么使用 TinyPNG？

TinyPNG 使用智能压缩算法，可以：
- **减少文件大小高达 80%**，同时保持高质量
- 使用**智能有损压缩**技术，视觉上几乎无差异
- 支持 PNG、JPEG、WebP、AVIF 格式
- 提供免费的 API 服务（每月 500 次压缩）

参考：[TinyPNG 官网](https://tinypng.com/)

## 如何获取 API Key

1. **访问 TinyPNG 开发者页面**
   - 打开 https://tinypng.com/developers
   - 输入你的邮箱地址
   - 点击 "Get API key"

2. **验证邮箱**
   - 检查你的邮箱，点击验证链接
   - 你会收到 API key（格式类似：`abc123def456ghi789`）

3. **配置 API Key**

   **方法 1: 环境变量（推荐）**
   ```bash
   export TINYPNG_API_KEY=your_api_key_here
   ```

   **方法 2: 修改脚本**
   ```python
   # 在 scripts/download_figma_login_images.py 中
   TINYPNG_API_KEY = "your_api_key_here"
   ```

## API 限制

- **免费版**: 每月 500 次压缩
- **付费版**: 根据订阅计划有不同的限制
- 每次压缩会显示剩余次数

## 使用效果

使用 TinyPNG API 压缩通常可以：
- 减少 50-80% 的文件大小
- 保持高质量的视觉效果
- 比本地压缩（Pillow）效果更好

## 故障排除

### API Key 未设置
如果看到 "TINYPNG_API_KEY 未设置" 的提示：
1. 检查环境变量是否正确设置
2. 或者直接在脚本中设置 API key

### API 调用失败
如果 API 调用失败：
- 检查网络连接
- 验证 API key 是否正确
- 检查是否超过每月限制
- 脚本会自动使用原始文件作为备用方案

## 测试 API Key

运行脚本时，如果 API key 配置正确，你会看到：
```
🗜️  TinyPNG API: 已配置
🔧 正在使用 TinyPNG 优化图片...
   🔄 正在使用 TinyPNG API 压缩...
   ✨ TinyPNG 压缩: 1322.5 KB → 450.3 KB (减少 66.0%)
   📊 API 剩余次数: 499
```

如果未配置，会看到：
```
⚠️  TinyPNG API: 未配置（将跳过压缩）
```
