#!/usr/bin/env python3
"""
从 Figma 下载账号登录页面的图片资源
直接使用 Figma REST API 下载背景图和返回按钮图片（@3x）
"""

import os
import sys
import requests
import json
import base64
from pathlib import Path

# TinyPNG API 配置
# 优先使用环境变量，如果没有则使用默认 key
TINYPNG_API_KEY = os.getenv("TINYPNG_API_KEY", "")
TINYPNG_API_URL = "https://api.tinify.com/shrink"

# Figma 配置
FIGMA_FILE_KEY = "mVCcQJPK1pHXRauJULaQiC"
FIGMA_NODE_ID = "618:21942"  # 背景图片的节点 ID（从 Figma URL 获取）
# 返回按钮节点 ID（如果知道的话，可以在这里添加）
BACK_BUTTON_NODE_ID = None  # 例如: "618:12345"
FIGMA_ACCESS_TOKEN = os.getenv("FIGMA_ACCESS_TOKEN", "")

# 输出目录
OUTPUT_DIR = Path(__file__).parent.parent / "ugc_flutter" / "assets" / "images"

# Figma API 基础 URL
FIGMA_API_BASE = "https://api.figma.com/v1"


def get_file_node_info(file_key, node_id):
    """获取 Figma 文件的节点详细信息"""
    url = f"{FIGMA_API_BASE}/files/{file_key}/nodes"
    params = {
        "ids": node_id
    }
    headers = {
        "X-Figma-Token": FIGMA_ACCESS_TOKEN
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


def get_image_export_url(file_key, node_ids, scale=3, format="png"):
    """获取图片导出 URL"""
    url = f"{FIGMA_API_BASE}/images/{file_key}"
    params = {
        "ids": ",".join(node_ids),
        "format": format,
        "scale": scale
    }
    headers = {
        "X-Figma-Token": FIGMA_ACCESS_TOKEN
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取图片导出 URL 失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应状态码: {e.response.status_code}")
            print(f"响应内容: {e.response.text}")
        return None


def optimize_image_with_tinypng(input_path, output_path):
    """使用 TinyPNG API 优化图片，压缩文件大小但保持高质量"""
    if not TINYPNG_API_KEY:
        print("   ⚠️  TINYPNG_API_KEY 未设置，跳过 TinyPNG 压缩")
        print("   💡 提示: 设置环境变量 TINYPNG_API_KEY 或修改脚本中的 API key")
        print("   📝 获取 API key: https://tinypng.com/developers")
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
            auth=('api', TINYPNG_API_KEY),
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


def download_image(url, output_path, optimize=True):
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
        if optimize:
            print("🔧 正在使用 TinyPNG 优化图片...")
            optimize_image_with_tinypng(temp_path, output_path)
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


def find_child_nodes(node_data, target_names=None):
    """递归查找子节点"""
    found_nodes = []
    
    if not node_data or 'document' not in node_data:
        return found_nodes
    
    def traverse(node, parent_name=""):
        node_name = node.get('name', '').lower()
        node_id = node.get('id', '')
        node_type = node.get('type', '')
        
        # 检查是否是目标节点
        if target_names:
            for target in target_names:
                if target.lower() in node_name:
                    found_nodes.append({
                        'id': node_id,
                        'name': node.get('name', ''),
                        'type': node_type
                    })
        
        # 递归查找子节点
        if 'children' in node:
            for child in node['children']:
                traverse(child, node_name)
    
    # 从根节点开始遍历
    if 'nodes' in node_data and FIGMA_NODE_ID in node_data['nodes']:
        root_node = node_data['nodes'][FIGMA_NODE_ID].get('document', {})
        traverse(root_node)
    
    return found_nodes


def main():
    print("🚀 开始从 Figma 下载账号登录页面图片资源...")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print(f"🔑 文件 Key: {FIGMA_FILE_KEY}")
    print(f"📍 节点 ID: {FIGMA_NODE_ID}")
    if TINYPNG_API_KEY:
        print(f"🗜️  TinyPNG API: 已配置")
    else:
        print(f"⚠️  TinyPNG API: 未配置（将跳过压缩）")
        print(f"   💡 设置环境变量: export TINYPNG_API_KEY=your_api_key")
        print(f"   📝 获取 API key: https://tinypng.com/developers")
    print()
    
    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 获取节点信息
    print("📥 获取 Figma 节点信息...")
    node_info = get_file_node_info(FIGMA_FILE_KEY, FIGMA_NODE_ID)
    
    if not node_info:
        print("❌ 无法获取节点信息")
        print("\n💡 请检查：")
        print("   1. FIGMA_ACCESS_TOKEN 是否正确（在环境变量中设置）")
        print("   2. 文件权限是否足够")
        print("   3. 网络连接是否正常")
        print("   4. 节点 ID 是否正确")
        return False
    
    print("✅ 节点信息获取成功")
    print(f"📄 节点数据预览: {json.dumps(node_info, indent=2, ensure_ascii=False)[:500]}...")
    print()
    
    # 尝试查找背景和返回按钮节点
    print("🔍 查找背景和返回按钮节点...")
    target_nodes = find_child_nodes(node_info, ['background', 'back', 'button', '返回'])
    
    if target_nodes:
        print(f"✅ 找到 {len(target_nodes)} 个可能的节点:")
        for node in target_nodes:
            print(f"   - {node['name']} ({node['type']}): {node['id']}")
    else:
        print("⚠️  未找到目标节点，将使用整个页面节点导出")
        target_nodes = [{'id': FIGMA_NODE_ID, 'name': 'full_page', 'type': 'FRAME'}]
    
    print()
    
    # 获取图片导出 URL（@3x）
    print("📸 获取图片导出 URL (@3x)...")
    node_ids = [node['id'] for node in target_nodes]
    image_urls = get_image_export_url(FIGMA_FILE_KEY, node_ids, scale=3)
    
    if not image_urls or 'images' not in image_urls:
        print("❌ 无法获取图片导出 URL")
        return False
    
    print("✅ 图片导出 URL 获取成功")
    print()
    
    # 下载图片
    success_count = 0
    
    # 下载背景图（使用第一个节点或整个页面）
    if node_ids[0] in image_urls['images']:
        bg_url = image_urls['images'][node_ids[0]]
        if bg_url:
            output_path = OUTPUT_DIR / "account_login_background@3x.png"
            print(f"📥 下载背景图 (@3x)...")
            if download_image(bg_url, output_path):
                success_count += 1
            print()
    
    # 如果有多个节点，尝试下载返回按钮
    if len(node_ids) > 1 and node_ids[1] in image_urls['images']:
        btn_url = image_urls['images'][node_ids[1]]
        if btn_url:
            output_path = OUTPUT_DIR / "account_login_back_button.png"
            print(f"📥 下载返回按钮...")
            if download_image(btn_url, output_path):
                success_count += 1
            print()
    elif BACK_BUTTON_NODE_ID:
        # 如果指定了返回按钮节点 ID，单独下载
        print(f"📥 下载返回按钮（节点 ID: {BACK_BUTTON_NODE_ID}）...")
        btn_urls = get_image_export_url(FIGMA_FILE_KEY, [BACK_BUTTON_NODE_ID], scale=3)
        if btn_urls and 'images' in btn_urls and BACK_BUTTON_NODE_ID in btn_urls['images']:
            btn_url = btn_urls['images'][BACK_BUTTON_NODE_ID]
            if btn_url:
                output_path = OUTPUT_DIR / "account_login_back_button.png"
                if download_image(btn_url, output_path):
                    success_count += 1
                print()
    elif len(node_ids) == 1:
        # 如果只有一个节点，也尝试下载作为背景
        print("💡 提示: 只找到一个节点，已下载为背景图")
        print("   如果需要返回按钮图片：")
        print("   1. 在 Figma 中选择返回按钮节点")
        print("   2. 在右侧面板查看节点 ID（格式如：618:12345）")
        print("   3. 修改脚本中的 BACK_BUTTON_NODE_ID 变量")
        print("   4. 重新运行脚本")
    
    print()
    if success_count > 0:
        print(f"✅ 成功下载 {success_count} 个图片文件")
        print(f"📁 文件位置: {OUTPUT_DIR}")
    else:
        print("❌ 未能下载任何图片")
        print("\n💡 建议：")
        print("   1. 在 Figma 中打开设计文件")
        print("   2. 选择背景图层，查看节点 ID（在右侧面板）")
        print("   3. 选择返回按钮，查看节点 ID")
        print("   4. 修改脚本中的节点 ID，然后重新运行")
    
    return success_count > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
