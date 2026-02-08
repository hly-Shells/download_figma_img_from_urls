#!/usr/bin/env python3
"""
Figma 空间/文件 图片批量下载
从 Figma 设计稿下载每页顶级 Frame/Component 图片，支持可配置倍率、无损压缩。
整合自 download_figma_img 项目。
"""

import argparse
import re
import sys
import time
from pathlib import Path

import requests

FIGMA_API_BASE = "https://api.figma.com/v1"
REQUEST_DELAY_SEC = 5
MAX_RETRIES = 3
RETRY_DELAY_SEC = 10


def parse_file_key(url_or_key: str) -> str | None:
    """从 Figma URL 或直接传入的 file_key 解析出 file_key。"""
    url_or_key = url_or_key.strip()
    if re.match(r"^[a-zA-Z0-9_-]+$", url_or_key):
        return url_or_key
    m = re.search(r"figma\.com/(?:design|file)/([a-zA-Z0-9_-]+)", url_or_key)
    if m:
        return m.group(1)
    return None


def sanitize_filename(name: str) -> str:
    """过滤非法文件名字符。"""
    return re.sub(r'[/\\:*?"<>|]', "_", name).strip() or "unnamed"


def collect_nodes_top_level(document: dict) -> list[dict]:
    """收集每页直接子节点中的 FRAME 和 COMPONENT。"""
    result = []
    for page in document.get("children", []):
        if page.get("type") != "CANVAS":
            continue
        page_name = sanitize_filename(page.get("name", "Page"))
        for child in page.get("children", []):
            if child.get("type") in ("FRAME", "COMPONENT"):
                result.append({
                    "id": child.get("id"),
                    "name": child.get("name", "unnamed"),
                    "page": page_name,
                    "path": sanitize_filename(child.get("name", "unnamed")),
                })
    return result


def get_file(token: str, file_key: str) -> dict:
    """获取 Figma 文件结构。"""
    url = f"{FIGMA_API_BASE}/files/{file_key}"
    resp = requests.get(url, headers={"X-Figma-Token": token}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _request_with_retry(method: str, url: str, retry_on: tuple = (), **kwargs) -> requests.Response:
    """带重试的 HTTP 请求，处理 SSL/连接错误及 500/429。"""
    retry_exceptions = (requests.exceptions.SSLError, requests.exceptions.ConnectionError, OSError)
    resp = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.request(method, url, timeout=120, **kwargs)
            if resp.ok:
                return resp
            if resp.status_code not in retry_on:
                return resp
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY_SEC * (attempt + 1)
                print(f"  [重试] {resp.status_code}，{wait} 秒后重试 ({attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait)
        except retry_exceptions as e:
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY_SEC * (attempt + 1)
                print(f"  [重试] 连接/SSL 错误，{wait} 秒后重试 ({attempt + 1}/{MAX_RETRIES}): {e!r}")
                time.sleep(wait)
            else:
                raise
    return resp


def get_image_urls(token: str, file_key: str, node_ids: list[str], scale: float, fmt: str = "png") -> dict:
    """批量获取图片导出 URL，500/429/SSL/连接错误时自动重试。"""
    ids_param = ",".join(node_ids)
    url = f"{FIGMA_API_BASE}/images/{file_key}"
    params = {"ids": ids_param, "scale": scale, "format": fmt}
    resp = _request_with_retry(
        "GET", url,
        retry_on=(500, 429),
        headers={"X-Figma-Token": token},
        params=params,
    )
    if resp.ok:
        return resp.json().get("images", {})
    err_msg = resp.text
    try:
        err_body = resp.json()
        err_msg = err_body.get("message", err_msg) or err_body.get("err", str(err_body))
    except Exception:
        pass
    raise requests.HTTPError(f"{resp.status_code} {resp.reason}: {err_msg}", response=resp)


def download_image_bytes(url: str) -> bytes:
    """下载图片二进制内容，SSL/连接错误时自动重试。"""
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()
            return resp.content
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError, OSError) as e:
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY_SEC * (attempt + 1)
                print(f"    [重试] 下载连接错误，{wait} 秒后重试: {e!r}")
                time.sleep(wait)
            else:
                raise


def compress_png_oxipng(filepath: Path, level: int = 4) -> None:
    """使用 pyoxipng 无损压缩 PNG。"""
    try:
        import oxipng
        oxipng.optimize(str(filepath), str(filepath), level=level)
    except ImportError:
        pass  # pyoxipng 未安装则跳过
    except Exception as e:
        print(f"  [警告] 压缩失败 {filepath}: {e}")


def run_export(
    token: str,
    file_key: str,
    nodes: list[dict],
    output_dir: Path,
    scale: float,
    compress: bool,
    batch_size: int = 5,
    fmt: str = "png",
) -> int:
    """导出一批节点到指定目录。"""
    if not nodes:
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    used_paths: dict[str, int] = {}

    def unique_path(node: dict) -> Path:
        page, base_path, nid = node["page"], node["path"], node["id"]
        base_flat = base_path.replace("/", "_")
        key = f"{page}/{base_flat}"
        idx = used_paths.get(key, 0)
        used_paths[key] = idx + 1
        safe_id = nid.replace(":", "_")
        ext = f".{fmt}"
        if idx == 0:
            name = f"{base_flat}_{safe_id}{ext}"
        else:
            name = f"{base_flat}_{safe_id}_{idx}{ext}"
        return output_dir / sanitize_filename(page) / sanitize_filename(name)

    count = 0
    i = 0
    while i < len(nodes):
        batch = nodes[i : i + batch_size]
        ids = [n["id"] for n in batch]
        print(f"  请求 {len(ids)} 个节点...")
        try:
            urls = get_image_urls(token, file_key, ids, scale, fmt)
            time.sleep(REQUEST_DELAY_SEC)

            for node in batch:
                nid = node["id"]
                url = urls.get(nid)
                if not url:
                    print(f"  [跳过] {node['name']} ({nid}) - 无法渲染")
                    continue
                out_path = unique_path(node)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    data = download_image_bytes(url)
                    out_path.write_bytes(data)
                    if compress and fmt == "png" and data[:8] == b"\x89PNG\r\n\x1a\n":
                        compress_png_oxipng(out_path)
                    count += 1
                    print(f"  [OK] {out_path.relative_to(output_dir)}")
                except Exception as e:
                    print(f"  [失败] {node['name']}: {e}")
            i += len(batch)
        except requests.HTTPError as e:
            if batch_size > 1 and e.response is not None and e.response.status_code in (400, 500):
                print(f"  [拆分] 批次失败，改为逐节点请求...")
                batch_size = 1
                continue
            if batch_size == 1:
                print(f"  [跳过] 节点渲染失败，跳过本批: {e}")
                i += 1
                continue
            raise

    return count


def load_env_file(file_path: Path) -> dict:
    """从 .env 文件中加载环境变量"""
    env_vars = {}
    if not file_path or not file_path.exists():
        return env_vars
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key, value = key.strip(), value.strip()
                    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    env_vars[key] = value
    except Exception:
        pass
    return env_vars


def get_config_value(key: str, env_file: Path | None = None, default: str | None = None) -> str | None:
    """按优先级获取配置值"""
    if env_file:
        env_vars = load_env_file(env_file)
        if key in env_vars:
            return env_vars[key]
    env_path = Path.cwd() / '.env'
    if env_path.exists():
        env_vars = load_env_file(env_path)
        if key in env_vars:
            return env_vars[key]
    import os
    return os.getenv(key, default)


def main() -> bool:
    parser = argparse.ArgumentParser(
        description="从 Figma 设计稿批量下载每页顶级 Frame/Component 图片（空间/文件模式），支持可配置倍率、无损压缩。"
    )
    parser.add_argument(
        "url_or_key",
        nargs="?",
        help="Figma 文件 URL 或 file_key",
    )
    parser.add_argument("--file-key", "-k", help="Figma 文件 key（可与 URL 二选一）")
    parser.add_argument("--scale", "-s", type=float, default=3, help="导出倍率，默认 3")
    parser.add_argument("--output-dir", "-o", default="./output", help="输出根目录，默认 ./output")
    parser.add_argument("--batch-size", "-b", type=int, default=5, help="每批请求节点数，400/500 时可减小，默认 5")
    parser.add_argument("--no-compress", action="store_true", help="跳过 oxipng 无损压缩")
    parser.add_argument("--format", "-f", default="png", choices=["png", "jpg"], help="导出格式，默认 png")
    parser.add_argument("--env-file", help="环境变量文件路径")
    parser.add_argument("--figma-token", "-t", help="Figma API Token（或 FIGMA_ACCESS_TOKEN / FIGMA_TOKEN）")

    args = parser.parse_args()

    env_file = Path(args.env_file) if args.env_file else None
    token = (
        args.figma_token
        or get_config_value("FIGMA_ACCESS_TOKEN", env_file)
        or get_config_value("FIGMA_TOKEN", env_file)
    )

    file_key = args.file_key or (args.url_or_key and parse_file_key(args.url_or_key))
    if not file_key:
        print("❌ 错误: 请提供 Figma URL 或 --file-key", file=sys.stderr)
        parser.print_help()
        return False

    if not token:
        print("❌ 错误: 请设置 FIGMA_ACCESS_TOKEN 或 FIGMA_TOKEN 环境变量，或使用 --figma-token", file=sys.stderr)
        return False

    output_root = Path(args.output_dir)
    compress = not args.no_compress

    print(f"📂 正在获取文件结构: {file_key}")
    file_data = get_file(token, file_key)
    document = file_data.get("document", {})

    nodes = collect_nodes_top_level(document)
    if not nodes:
        print("⚠️  未找到可导出的顶级 Frame/Component")
        return True

    print(f"\n📥 导出 {len(nodes)} 个顶级画板 -> {output_root}（每批 {args.batch_size} 个节点）")
    total = run_export(
        token, file_key, nodes, output_root,
        args.scale, compress, args.batch_size, args.format
    )

    print(f"\n✅ 完成，共下载 {total} 张图片。")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
