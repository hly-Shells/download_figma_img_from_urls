#!/usr/bin/env python3
"""
从 Figma 下载账号登录页面的图片资源
使用 Figma REST API 下载背景图和返回按钮图片
"""

import os
import sys
import requests
import json
from pathlib import Path

# Figma 配置
FIGMA_FILE_KEY = "mVCcQJPK1pHXRauJULaQiC"
FIGMA_NODE_ID = "618:21941"
FIGMA_ACCESS_TOKEN = os.getenv("FIGMA_ACCESS_TOKEN", "")

# 输出目录
OUTPUT_DIR = Path(__file__).parent.parent / "ugc_flutter" / "assets" / "images"

# Figma API 基础 URL
FIGMA_API_BASE = "https://api.figma.com/v1"


def get_file_nodes(file_key, node_id=None):
    """获取 Figma 文件的节点信息"""
    url = f"{FIGMA_API_BASE}/files/{file_key}"
    if node_id:
        url += f"/nodes?ids={node_id}"
    
    headers = {
        "X-Figma-Token": FIGMA_ACCESS_TOKEN
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取 Figma 节点失败: {e}")
        if hasattr(e.response, 'text'):
            print(f"响应内容: {e.response.text}")
        return None


def get_image_urls(file_key, node_ids, scale=3):
    """获取图片导出 URL"""
    url = f"{FIGMA_API_BASE}/images/{file_key}"
    params = {
        "ids": ",".join(node_ids),
        "format": "png",
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
        print(f"❌ 获取图片 URL 失败: {e}")
        if hasattr(e.response, 'text'):
            print(f"响应内容: {e.response.text}")
        return None


def download_image(url, output_path):
    """下载图片到指定路径"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 下载图片
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ 下载成功: {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ 下载失败 {output_path}: {e}")
        return False


def find_background_node(nodes_data):
    """查找背景节点"""
    # 这里需要根据实际的节点结构来查找
    # 通常背景是最大的矩形或图片节点
    if not nodes_data or 'nodes' not in nodes_data:
        return None
    
    # 尝试查找背景节点（通常是最大的矩形）
    # 这需要根据实际 Figma 文件结构调整
    return None


def find_back_button_node(nodes_data):
    """查找返回按钮节点"""
    # 这里需要根据实际的节点结构来查找
    # 返回按钮通常是小的图标或组件
    if not nodes_data or 'nodes' not in nodes_data:
        return None
    
    # 尝试查找返回按钮节点
    # 这需要根据实际 Figma 文件结构调整
    return None


def main():
    print("🚀 开始从 Figma 下载图片资源...")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    
    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 获取文件节点信息
    print(f"\n📥 获取 Figma 文件节点信息...")
    nodes_data = get_file_nodes(FIGMA_FILE_KEY, FIGMA_NODE_ID)
    
    if not nodes_data:
        print("❌ 无法获取节点信息，请检查：")
        print("   1. FIGMA_ACCESS_TOKEN 是否正确")
        print("   2. 文件权限是否足够")
        print("   3. 网络连接是否正常")
        return False
    
    print("✅ 节点信息获取成功")
    print(f"📄 节点数据: {json.dumps(nodes_data, indent=2, ensure_ascii=False)}")
    
    # 注意：由于无法直接访问 Figma 文件，这里需要手动指定节点 ID
    # 或者通过分析 nodes_data 来找到对应的节点
    
    print("\n⚠️  由于无法直接访问 Figma 文件，请手动执行以下步骤：")
    print("   1. 在 Figma 中打开设计文件")
    print("   2. 选择背景图层，在右侧面板查看节点 ID")
    print("   3. 选择返回按钮，在右侧面板查看节点 ID")
    print("   4. 修改脚本中的节点 ID，然后重新运行")
    
    # 示例：如果你知道节点 ID，可以这样下载
    # background_node_id = "618:12345"  # 替换为实际的背景节点 ID
    # back_button_node_id = "618:12346"  # 替换为实际的返回按钮节点 ID
    
    # node_ids = [background_node_id, back_button_node_id]
    # image_urls = get_image_urls(FIGMA_FILE_KEY, node_ids, scale=3)
    
    # if image_urls and 'images' in image_urls:
    #     # 下载背景图
    #     if background_node_id in image_urls['images']:
    #         bg_url = image_urls['images'][background_node_id]
    #         download_image(bg_url, OUTPUT_DIR / "account_login_background@3x.png")
    #     
    #     # 下载返回按钮
    #     if back_button_node_id in image_urls['images']:
    #         btn_url = image_urls['images'][back_button_node_id]
    #         download_image(btn_url, OUTPUT_DIR / "account_login_back_button.png")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
