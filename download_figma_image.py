#!/usr/bin/env python3
"""
通用的 Figma 图片下载和压缩脚本
支持从 Figma 下载图片并使用 TinyPNG 进行压缩
"""

import os
import sys
import argparse
import time
import requests
import json
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Figma API 请求重试配置
FIGMA_API_RETRIES = 4
FIGMA_API_TIMEOUT = 90
FIGMA_API_RETRY_DELAY = 2

# TinyPNG API 配置
TINYPNG_API_URL = "https://api.tinify.com/shrink"


def load_env_file(file_path):
    """
    从 .env 文件中加载环境变量
    
    支持格式：
    - KEY=value
    - KEY="value"
    - KEY='value'
    - # 注释行
    - 空行
    
    返回: dict 包含加载的环境变量
    """
    env_vars = {}
    if not file_path or not file_path.exists():
        return env_vars
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                
                # 解析 KEY=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 移除引号
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    env_vars[key] = value
    except Exception as e:
        print(f"⚠️  读取环境变量文件失败 {file_path}: {e}")
    
    return env_vars


def get_config_value(key, env_file=None, default=None):
    """
    按优先级获取配置值：
    1. 指定的环境变量文件
    2. 当前目录下的 .env 文件
    3. 终端环境变量
    
    返回: 配置值或 None
    """
    # 优先级 1: 指定的环境变量文件
    if env_file:
        env_vars = load_env_file(Path(env_file))
        if key in env_vars:
            return env_vars[key]
    
    # 优先级 2: 当前目录下的 .env 文件
    current_dir = Path.cwd()
    env_path = current_dir / '.env'
    if env_path.exists():
        env_vars = load_env_file(env_path)
        if key in env_vars:
            return env_vars[key]
    
    # 优先级 3: 终端环境变量
    return os.getenv(key, default)


def parse_figma_url(url):
    """
    从 Figma URL 中解析出 file-key 和 node-id
    
    支持的 URL 格式：
    - https://www.figma.com/design/{file_key}/文件名?node-id={node_id}
    - https://www.figma.com/file/{file_key}/文件名?node-id={node_id}
    - https://figma.com/design/{file_key}/文件名?node-id={node_id}
    
    返回: (file_key, node_id) 或 (None, None)，无 node-id 时返回 (file_key, None)
    """
    try:
        # 解析 URL
        parsed = urlparse(url)
        
        # 提取 file-key（从路径中）
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[0] in ['design', 'file']:
            file_key = path_parts[1]
        else:
            return None, None
        
        # 提取 node-id（从查询参数中）
        query_params = parse_qs(parsed.query)
        node_id_param = query_params.get('node-id', [None])[0]
        
        if not node_id_param:
            return file_key, None
        
        # 将 node-id 中的 - 替换为 :（Figma URL 使用 -，API 使用 :）
        node_id = node_id_param.replace('-', ':')
        
        return file_key, node_id
    except Exception as e:
        print(f"⚠️  URL 解析失败: {e}")
        return None, None


def get_file_structure(file_key, access_token):
    """获取 Figma 文件的完整结构（带重试，应对 Response ended prematurely 等网络问题）"""
    url = f"https://api.figma.com/v1/files/{file_key}"
    headers = {
        "X-Figma-Token": access_token,
        "User-Agent": "figmad/1.0",
    }
    last_error = None
    for attempt in range(1, FIGMA_API_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, timeout=FIGMA_API_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt < FIGMA_API_RETRIES:
                delay = FIGMA_API_RETRY_DELAY * attempt
                print(f"   ⚠️  第 {attempt} 次尝试失败: {e}")
                print(f"   🔄 {delay} 秒后重试 ({attempt + 1}/{FIGMA_API_RETRIES})...")
                time.sleep(delay)
            else:
                break
    print(f"❌ 获取文件结构失败（已重试 {FIGMA_API_RETRIES} 次）: {last_error}")
    if hasattr(last_error, 'response') and last_error.response is not None:
        print(f"   响应状态码: {last_error.response.status_code}")
        if last_error.response.text:
            print(f"   响应内容: {last_error.response.text[:500]}")
    return None


def collect_frame_nodes(node, page_name="", nodes_list=None):
    """
    递归遍历节点树，收集可导出的 Frame 节点（每页的直接子节点）
    返回: [(node_id, node_name, page_name), ...]
    """
    if nodes_list is None:
        nodes_list = []
    
    if not node or 'id' not in node:
        return nodes_list
    
    node_type = node.get('type', '')
    
    # DOCUMENT 是根节点，遍历其子节点（CANVAS 页面）
    if node_type == 'DOCUMENT':
        children = node.get('children', [])
        for child in children:
            page_name = child.get('name', 'Page') if child.get('name') else 'Page'
            collect_frame_nodes(child, page_name, nodes_list)
        return nodes_list
    
    # CANVAS 是页面，遍历其直接子节点（通常是 Frame/画板）
    if node_type == 'CANVAS':
        children = node.get('children', [])
        for child in children:
            if child.get('id'):
                child_name = child.get('name', 'unnamed')
                nodes_list.append((child['id'], child_name, page_name))
        return nodes_list
    
    return nodes_list


def optimize_image_with_tinypng(input_path, output_path, api_key):
    """使用 TinyPNG API 优化图片，压缩文件大小但保持高质量"""
    if not api_key:
        print("   ⚠️  TinyPNG API key 未提供，跳过压缩")
        # 如果 API key 不可用，直接复制文件
        import shutil
        shutil.copy2(input_path, output_path)
        return False
    
    try:
        # 获取原始文件大小
        original_size = os.path.getsize(input_path)
        
        # 读取图片文件
        with open(input_path, 'rb') as f:
            image_data = f.read()
        
        # 调用 TinyPNG API
        print("   🔄 正在使用 TinyPNG API 压缩...")
        response = requests.post(
            TINYPNG_API_URL,
            auth=('api', api_key),
            data=image_data,
            timeout=30
        )
        
        if response.status_code == 201:
            # 获取压缩后的图片 URL
            compressed_url = response.json()['output']['url']
            
            # 下载压缩后的图片
            compressed_response = requests.get(compressed_url, timeout=30)
            compressed_response.raise_for_status()
            
            # 保存压缩后的图片
            with open(output_path, 'wb') as f:
                f.write(compressed_response.content)
            
            # 获取压缩后文件大小
            compressed_size = os.path.getsize(output_path)
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            # 显示压缩信息
            if compressed_size < original_size:
                print(f"   ✨ TinyPNG 压缩: {original_size / 1024:.1f} KB → {compressed_size / 1024:.1f} KB (减少 {compression_ratio:.1f}%)")
            else:
                print(f"   ℹ️  大小: {compressed_size / 1024:.1f} KB (已优化)")
            
            # 显示 API 使用情况
            if 'compression-count' in response.headers:
                remaining = response.headers.get('compression-count', 'N/A')
                print(f"   📊 API 剩余次数: {remaining}")
            
            return True
        else:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('error', response.text)
            print(f"   ❌ TinyPNG API 错误: {error_msg}")
            # 如果 API 调用失败，使用原始文件
            import shutil
            shutil.copy2(input_path, output_path)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  TinyPNG API 请求失败: {e}")
        # 如果请求失败，使用原始文件
        import shutil
        shutil.copy2(input_path, output_path)
        return False
    except Exception as e:
        print(f"   ⚠️  压缩失败: {e}，使用原始文件")
        # 如果压缩失败，使用原始文件
        import shutil
        shutil.copy2(input_path, output_path)
        return False


def download_image(url, output_path, optimize=True, api_key=None):
    """下载图片到指定路径，并可选地进行优化压缩"""
    try:
        print(f"📥 正在下载: {url}")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 临时文件路径
        temp_path = output_path.with_suffix('.tmp')
        
        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))
        
        # 下载图片到临时文件
        downloaded = 0
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   进度: {percent:.1f}%", end='', flush=True)
        
        print(f"\n✅ 下载完成: {downloaded / 1024:.1f} KB")
        
        # 优化图片（使用 TinyPNG API）
        if optimize and api_key:
            print("🔧 正在使用 TinyPNG 优化图片...")
            optimize_image_with_tinypng(temp_path, output_path, api_key)
            # 删除临时文件
            if temp_path.exists():
                temp_path.unlink()
        else:
            # 直接移动文件
            import shutil
            shutil.move(temp_path, output_path)
        
        final_size = os.path.getsize(output_path)
        print(f"✅ 最终文件: {output_path.name} ({final_size / 1024:.1f} KB)")
        return True
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 下载失败 {output_path}: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 处理失败 {output_path}: {e}")
        return False


def get_file_node_info(file_key, node_id, access_token):
    """获取 Figma 文件的节点详细信息"""
    url = f"https://api.figma.com/v1/files/{file_key}/nodes"
    params = {
        "ids": node_id
    }
    headers = {
        "X-Figma-Token": access_token
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取节点信息失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应状态码: {e.response.status_code}")
            print(f"响应内容: {e.response.text}")
        return None


def get_image_export_url(file_key, node_ids, scale=3, format="png", access_token=None):
    """获取图片导出 URL（带重试）"""
    url = f"https://api.figma.com/v1/images/{file_key}"
    params = {
        "ids": ",".join(node_ids),
        "format": format,
        "scale": scale
    }
    headers = {"User-Agent": "figmad/1.0"}
    if access_token:
        headers["X-Figma-Token"] = access_token
    last_error = None
    for attempt in range(1, FIGMA_API_RETRIES + 1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=FIGMA_API_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt < FIGMA_API_RETRIES:
                time.sleep(FIGMA_API_RETRY_DELAY * attempt)
            else:
                break
    print(f"❌ 获取图片导出 URL 失败（已重试 {FIGMA_API_RETRIES} 次）: {last_error}")
    if hasattr(last_error, 'response') and last_error.response is not None:
        print(f"   响应状态码: {last_error.response.status_code}")
        if last_error.response.text:
            print(f"   响应内容: {last_error.response.text[:300]}")
    return None


def download_single_image(url, output_path, figma_token, tinypng_key, scale=3, format='png', no_compress=False, file_key=None, node_id=None):
    """下载单张图片的辅助函数"""
    # 如果提供了 file_key 和 node_id，直接使用；否则从 URL 解析
    if not file_key or not node_id:
        if url:
            file_key, node_id = parse_figma_url(url)
            if not file_key or not node_id:
                print(f"❌ 无法解析 URL: {url}")
                return False
        else:
            print("❌ 错误: 需要提供 URL 或 file_key 和 node_id")
            return False
    
    # 获取节点信息
    node_info = get_file_node_info(file_key, node_id, figma_token)
    if not node_info:
        print(f"❌ 无法获取节点信息: {node_id}")
        return False
    
    # 获取图片导出 URL
    image_urls = get_image_export_url(
        file_key,
        [node_id],
        scale=scale,
        format=format,
        access_token=figma_token
    )
    
    if not image_urls or 'images' not in image_urls or node_id not in image_urls['images']:
        print(f"❌ 无法获取图片导出 URL: {node_id}")
        return False
    
    image_url = image_urls['images'][node_id]
    if not image_url:
        print(f"❌ 图片导出 URL 为空: {node_id}")
        return False
    
    # 下载并压缩图片
    output_path_obj = Path(output_path)
    return download_image(
        image_url,
        output_path_obj,
        optimize=not no_compress,
        api_key=tinypng_key if not no_compress else None
    )


def load_urls_from_file(file_path):
    """从文件中读取 URL 列表"""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                # 检查是否是 URL
                if line.startswith('http'):
                    urls.append(line)
                else:
                    print(f"⚠️  第 {line_num} 行不是有效的 URL，已跳过: {line}")
    except Exception as e:
        print(f"❌ 读取文件失败 {file_path}: {e}")
        return None
    
    return urls


def generate_output_filename(node_id, scale=3, format='png', output_dir=None):
    """根据 node-id 生成输出文件名"""
    # 将 node_id 中的 : 替换为 _，作为文件名
    safe_node_id = node_id.replace(':', '_')
    filename = f"{safe_node_id}@{scale}x.{format}"
    
    if output_dir:
        return Path(output_dir) / filename
    else:
        return Path(filename)


def sanitize_filename(name):
    """将节点名称转为安全的文件名"""
    if not name:
        return "unnamed"
    # 移除或替换不安全字符
    safe = re.sub(r'[<>:"/\\|?*]', '_', name)
    safe = re.sub(r'\s+', '_', safe).strip('._')
    return safe[:100] if safe else "unnamed"


def generate_space_output_filename(page_name, frame_name, node_id, scale=3, format='png', output_dir=None):
    """为空间模式生成输出文件名：页面名/画板名@倍数.格式"""
    safe_page = sanitize_filename(page_name)
    safe_frame = sanitize_filename(frame_name)
    safe_node_id = node_id.replace(':', '_')
    filename = f"{safe_frame}@{scale}x.{format}"
    
    if output_dir:
        return Path(output_dir) / safe_page / filename
    else:
        return Path(safe_page) / filename


def main():
    parser = argparse.ArgumentParser(
        description='从 Figma 下载图片并使用 TinyPNG 压缩',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单张图片：使用 Figma URL（推荐，最简单）
  %(prog)s --url "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942" --output output.png

  # 单张图片：自动生成文件名（基于 node-id）
  %(prog)s --url "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942"

  # 批量下载：从文件读取 URL 列表
  %(prog)s --urls-file urls.txt --output-dir assets/images

  # 批量下载：命令行直接传入多个 URL
  %(prog)s --urls "https://www.figma.com/design/...?node-id=618-1" "https://www.figma.com/design/...?node-id=618-2" --output-dir assets/images

  # 批量下载：自动生成文件名（基于 node-id）
  %(prog)s --urls-file urls.txt

  # 使用 .env 文件（自动查找当前目录下的 .env）
  %(prog)s --url "https://www.figma.com/design/..." --output output.png

  # 指定分辨率
  %(prog)s --url "https://www.figma.com/design/..." --output output@2x.png --scale 2

  # 不使用压缩
  %(prog)s --url "https://www.figma.com/design/..." --output output.png --no-compress

  # 下载整个空间（文件内所有页面的顶级画板）
  %(prog)s --space "https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc" --output-dir ./exports
        """
    )
    
    # URL、批量文件、整个空间或单独参数（四选一）
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--url',
        help='Figma 设计 URL（例如：https://www.figma.com/design/mVCcQJPK1pHXRauJULaQiC/ugc?node-id=618-21942）'
    )
    input_group.add_argument(
        '--urls',
        nargs='+',
        metavar='URL',
        help='多个 Figma URL（直接在命令行传入）'
    )
    input_group.add_argument(
        '--urls-file',
        help='包含多个 Figma URL 的文件路径（每行一个 URL，支持 # 注释）'
    )
    input_group.add_argument(
        '--space',
        metavar='URL',
        help='Figma 空间/文件 URL（下载整个文件内所有页面的顶级画板）'
    )
    
    # 单独参数（与 --url、--urls、--urls-file 互斥）
    file_key_group = parser.add_argument_group('单独参数（与 --url 和 --urls-file 互斥）')
    file_key_group.add_argument(
        '--file-key',
        help='Figma 文件 Key（从 Figma URL 中获取，例如：mVCcQJPK1pHXRauJULaQiC）'
    )
    file_key_group.add_argument(
        '--node-id',
        help='Figma 节点 ID（从 Figma URL 中获取，例如：618:21942）'
    )
    
    parser.add_argument(
        '--output',
        help='输出文件路径（单张图片时必需，批量下载时可选。如果未指定，使用当前目录和 node-id 作为文件名）'
    )
    parser.add_argument(
        '--output-dir',
        default='.',
        help='批量下载时的输出目录（默认：当前目录）'
    )
    
    # 可选参数
    parser.add_argument(
        '--env-file',
        help='环境变量文件路径（.env 格式）。如果不指定，会自动查找当前目录下的 .env 文件'
    )
    parser.add_argument(
        '--figma-token',
        default=None,
        help='Figma Access Token（优先级：命令行参数 > 环境变量文件 > .env 文件 > 终端环境变量）'
    )
    parser.add_argument(
        '--tinypng-key',
        default=None,
        help='TinyPNG API Key（优先级：命令行参数 > 环境变量文件 > .env 文件 > 终端环境变量）'
    )
    parser.add_argument(
        '--scale',
        type=int,
        default=3,
        choices=[1, 2, 3, 4],
        help='图片分辨率倍数（1x, 2x, 3x, 4x），默认 3'
    )
    parser.add_argument(
        '--format',
        default='png',
        choices=['png', 'jpg', 'svg', 'pdf'],
        help='图片格式，默认 png'
    )
    parser.add_argument(
        '--no-compress',
        action='store_true',
        help='跳过 TinyPNG 压缩'
    )
    
    args = parser.parse_args()
    
    # 加载环境变量（按优先级）
    env_file_path = Path(args.env_file) if args.env_file else None
    
    # 获取配置值（按优先级：命令行参数 > 环境变量文件 > .env 文件 > 终端环境变量）
    figma_token = args.figma_token or get_config_value('FIGMA_ACCESS_TOKEN', env_file_path)
    tinypng_key = args.tinypng_key or get_config_value('TINYPNG_API_KEY', env_file_path)
    
    # 验证必需参数
    if not figma_token:
        print("❌ 错误: 需要提供 Figma Access Token")
        print("   可以通过以下方式设置：")
        print("   1. --figma-token 参数")
        print("   2. --env-file 指定的环境变量文件")
        print("   3. 当前目录下的 .env 文件")
        print("   4. 终端环境变量 FIGMA_ACCESS_TOKEN")
        return False
    
    # 显示环境变量来源
    if env_file_path:
        print(f"📄 环境变量文件: {env_file_path}")
    elif (Path.cwd() / '.env').exists():
        print(f"📄 环境变量文件: {Path.cwd() / '.env'}")
    
    if tinypng_key and not args.no_compress:
        print(f"🗜️  TinyPNG API: 已配置")
    elif args.no_compress:
        print(f"🗜️  TinyPNG 压缩: 已禁用")
    else:
        print(f"⚠️  TinyPNG API: 未配置（将跳过压缩）")
        print(f"   💡 可以通过以下方式设置：")
        print(f"      - --tinypng-key 参数")
        print(f"      - --env-file 指定的环境变量文件")
        print(f"      - 当前目录下的 .env 文件")
        print(f"      - 终端环境变量 TINYPNG_API_KEY")
        print(f"   📝 获取 API key: https://tinypng.com/developers")
    print()
    
    # 处理整个空间下载（--space）
    if args.space:
        print(f"📂 空间模式：下载整个 Figma 文件")
        print(f"🔗 URL: {args.space}")
        file_key, _ = parse_figma_url(args.space)
        if not file_key:
            print("❌ 错误: 无法从 URL 中解析 file-key")
            return False
        
        print(f"🔑 文件 Key: {file_key}")
        print(f"📁 输出目录: {args.output_dir}")
        print(f"📐 分辨率: {args.scale}x")
        print(f"📄 格式: {args.format}")
        print()
        
        # 获取文件结构
        print("🔄 正在获取文件结构...")
        file_data = get_file_structure(file_key, figma_token)
        if not file_data:
            return False
        
        document = file_data.get('document')
        if not document:
            print("❌ 错误: 文件结构中没有 document 节点")
            return False
        
        # 收集所有可导出的 Frame 节点
        nodes_list = collect_frame_nodes(document)
        if not nodes_list:
            print("⚠️  未找到可导出的画板（每页的顶级 Frame）")
            print("   提示: 确保 Figma 文件中每页有至少一个画板/Frame")
            return False
        
        print(f"✅ 找到 {len(nodes_list)} 个画板")
        print()
        
        # 批量获取图片导出 URL（Figma API 单次最多 50 个节点）
        BATCH_SIZE = 50
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        for i in range(0, len(nodes_list), BATCH_SIZE):
            batch = nodes_list[i:i + BATCH_SIZE]
            node_ids = [n[0] for n in batch]
            
            image_urls = get_image_export_url(
                file_key,
                node_ids,
                scale=args.scale,
                format=args.format,
                access_token=figma_token
            )
            
            if not image_urls or 'images' not in image_urls:
                print(f"❌ 获取导出 URL 失败")
                continue
            
            for node_id, node_name, page_name in batch:
                image_url = image_urls['images'].get(node_id)
                if not image_url:
                    print(f"   ⚠️  跳过 {page_name}/{node_name}: 无导出 URL")
                    continue
                
                output_path = generate_space_output_filename(
                    page_name, node_name, node_id,
                    args.scale, args.format, args.output_dir
                )
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                print(f"📥 [{success_count + 1}/{len(nodes_list)}] {page_name} / {node_name}")
                if download_image(
                    image_url,
                    output_path,
                    optimize=not args.no_compress,
                    api_key=tinypng_key if not args.no_compress else None
                ):
                    success_count += 1
                    print(f"   ✅ 完成")
                else:
                    print(f"   ❌ 失败")
                print()
        
        print(f"✅ 空间下载完成：成功 {success_count}/{len(nodes_list)}")
        return success_count > 0
    
    # 处理批量下载（--urls 或 --urls-file）
    urls = None
    if args.urls_file:
        urls = load_urls_from_file(Path(args.urls_file))
        if urls is None:
            return False
    elif args.urls:
        urls = [u.strip() for u in args.urls if u and u.strip()]

    if urls is not None:
        if args.urls_file:
            print(f"📋 批量下载模式：从文件读取 URL 列表")
            print(f"📄 URL 文件: {args.urls_file}")
        else:
            print(f"📋 批量下载模式：命令行传入 {len(urls)} 个 URL")
        print(f"📁 输出目录: {args.output_dir}")
        print(f"📐 分辨率: {args.scale}x")
        print(f"📄 格式: {args.format}")
        print()

        if not urls:
            print("❌ URL 列表为空或没有有效的 URL")
            return False

        print(f"✅ 找到 {len(urls)} 个 URL")
        print()
        
        # 批量下载
        success_count = 0
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for idx, url in enumerate(urls, 1):
            print(f"[{idx}/{len(urls)}] 处理 URL: {url}")
            
            # 解析 URL 获取 node_id
            file_key, node_id = parse_figma_url(url)
            if not file_key or not node_id:
                print(f"   ❌ 跳过：无法解析 URL")
                continue
            
            # 生成输出文件名
            if args.output and idx == 1:
                # 如果指定了输出，只对第一张图片使用
                output_path = Path(args.output)
            else:
                # 自动生成文件名（基于 node-id）
                output_path = generate_output_filename(node_id, args.scale, args.format, args.output_dir)
            
            print(f"   📁 输出: {output_path}")
            
            # 下载图片
            if download_single_image(url, output_path, figma_token, tinypng_key, args.scale, args.format, args.no_compress):
                success_count += 1
                print(f"   ✅ 完成")
            else:
                print(f"   ❌ 失败")
            print()
        
        print(f"✅ 批量下载完成：成功 {success_count}/{len(urls)}")
        return success_count > 0
    
    # 处理单张图片下载
    file_key = None
    node_id = None
    
    if args.url:
        # 从 URL 中解析
        print(f"🔗 解析 Figma URL: {args.url}")
        file_key, node_id = parse_figma_url(args.url)
        if not file_key:
            print("❌ 错误: 无法从 URL 中解析 file-key")
            return False
        if not node_id:
            print("⚠️  警告: URL 中没有 node-id，请确保 URL 包含 node-id 参数")
    else:
        # 使用单独参数
        file_key = args.file_key
        node_id = args.node_id
        if not file_key or not node_id:
            print("❌ 错误: 需要提供 --url、--urls、--urls-file、--space 或同时提供 --file-key 和 --node-id")
            return False
    
    # 确定输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        # 自动生成文件名（基于 node-id）
        if not node_id:
            print("❌ 错误: 未指定输出路径且无法从 URL 中获取 node-id")
            return False
        output_path = generate_output_filename(node_id, args.scale, args.format)
        print(f"💡 未指定输出路径，自动生成: {output_path}")
    
    # 输出配置信息
    print("🚀 开始从 Figma 下载图片...")
    print(f"📁 输出文件: {output_path}")
    print(f"🔑 文件 Key: {file_key}")
    print(f"📍 节点 ID: {node_id}")
    print(f"📐 分辨率: {args.scale}x")
    print(f"📄 格式: {args.format}")
    print()
    
    # 下载单张图片
    success = download_single_image(
        args.url if args.url else None,
        output_path,
        figma_token,
        tinypng_key,
        args.scale,
        args.format,
        args.no_compress,
        file_key,
        node_id
    )
    
    if success:
        print()
        print("✅ 图片下载和优化完成！")
        print(f"📁 文件位置: {output_path.absolute()}")
    else:
        print()
        print("❌ 图片下载失败")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
