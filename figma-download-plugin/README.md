# UGC 图片导出下载 - Figma 插件

在 Figma 里选中图层后，设置倍率、格式与可选压缩，点击下载。**支持多选**，一次可导出多张；**面板不会自动关闭**，方便在浏览器弹出的「保存」里选好位置后再手动关掉。

## 最少操作：多张 3x + TinyPNG 一步到位

适合「从 Figma 下多张 3 倍图并直接用 TinyPNG 压缩」的场景，操作尽量少：

1. **一次性准备**  
   - 本机运行：`python3 scripts/figma_compress_server.py`（需 `TINYPNG_API_KEY`）。  
   - 插件里 **压缩服务 URL** 已预填为 `http://localhost:8765/compress`（默认值也写在同目录 `compress-service-url.txt`），无需手填，直接可用。

2. **日常使用**  
   - 在 Figma 里**多选**要导出的图层/帧。  
   - 倍率保持默认 **3x**，勾选 **「仅下载压缩图」**。  
   - 点 **「下载选中图层（多选即多张）」**。  

结果：每张图只下一个已压缩的 3x 文件（如 `节点ID@3x.png`），无原图、无 `_compress` 后缀，少点一次、少一堆原图文件。

## 面板说明

| 项 | 说明 |
|----|------|
| **倍率** | 1x / 2x / 3x / 4x（默认 3x） |
| **格式** | PNG 或 JPG |
| **压缩服务 URL** | 首次打开已预填 `http://localhost:8765/compress`（与同目录 `compress-service-url.txt` 一致）。可改端口后重填，会**记住**。需先在本机运行 `figma_compress_server.py`。 |
| **仅下载压缩图** | 勾选且已填压缩 URL 时，只下载 TinyPNG 压缩后的图，不下载原图；文件名仍为 `节点ID@倍数x.扩展名`。 |

下载触发后会提示「已触发下载，请在弹出的窗口中选择保存位置…」。若浏览器弹出保存/另存为窗口，请在弹框中选好目录再确定；用完后可手动关闭插件面板。

## 本地压缩服务（可选）

若希望「压缩服务 URL」生效，可在本机跑一个 HTTP 服务：接收 POST 的图片、返回压缩后的图片。

已提供脚本 **`scripts/figma_compress_server.py`**：

```bash
# 安装依赖
pip install flask requests

# 配置 TinyPNG Key（环境变量或项目根 .env 中的 TINYPNG_API_KEY）
export TINYPNG_API_KEY=你的key

# 启动（默认 http://127.0.0.1:8765/compress）
python3 scripts/figma_compress_server.py
```

插件内 **压缩服务 URL** 已默认预填为 `http://localhost:8765/compress`（默认值也保存在同目录 **`compress-service-url.txt`**，方便团队共享或脚本引用）。勾选 **「仅下载压缩图」** 时，每张只下一个已压缩的 3x 文件（文件名无 `_compress`）；不勾选则下原图 + `原名_compress.ext` 两份。

## 安装（开发模式）

1. 打开 Figma → **Resources** → **Plugins** → **Development** → **Import plugin from manifest…**
2. 选择本目录下的 **manifest.json**。
3. 运行 **Plugins** → **Development** → **UGC 图片导出下载**。

## 使用

1. 在画布中选中要导出的图层/帧（可多选）。
2. 打开插件，倍率默认 3x；压缩服务 URL 已预填，若要用 TinyPNG 可直接勾选 **仅下载压缩图**。
3. 点击 **「下载选中图层（多选即多张）」**。
4. 每张图按「节点ID@倍数x.格式」下载到浏览器默认下载目录；若勾选仅压缩且 URL 有效，则只下压缩后那一份。

若未选中任何节点就点下载，会提示「请先选中要导出的图层或帧」。

## 文件说明

```
figma-download-plugin/
├── manifest.json              # 插件入口、能力、networkAccess（localhost 压缩服务）
├── code.js                    # 主逻辑与内联 UI，内含默认压缩 URL
├── ui.html                    # 由 manifest 引用，实际使用 code.js 内联 HTML
├── compress-service-url.txt   # 默认压缩服务地址，与 code.js 内常量一致，便于查阅/脚本引用
└── README.md                  # 本说明
```

## 控制台里可忽略的提示

- `Unrecognized feature: 'local-network-access'`、`[Violation] … permissions policy`：来自 Figma 宿主，与插件逻辑无关，不影响导出与下载。
- 若想少看这些日志，可在控制台过滤掉包含 `Violation` 或 `permissions policy` 的条目。

## 故障排除

- **「请先选中要导出的图层或帧」**：先选中可导出的节点再点下载。
- **「xxx 不支持导出为图片」**：该节点类型不支持导出，可尝试成组/成帧后再导。
- **压缩失败（已下原图）**：检查压缩服务是否已启动、URL 是否正确、TINYPNG_API_KEY 是否有效（若用 `figma_compress_server.py`）。
