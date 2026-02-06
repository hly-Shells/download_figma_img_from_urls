#!/usr/bin/env python3
"""
本地压缩服务：接收 POST 的图片二进制，用 TinyPNG 压缩后返回。
供 Figma 插件「压缩服务 URL」调用：在插件里填 http://localhost:8765/compress 即可。
依赖：pip install flask requests
环境变量：TINYPNG_API_KEY（或当前目录 .env 中的 TINYPNG_API_KEY）
"""
import os
import sys

try:
    from flask import Flask, request, Response
    import requests
except ImportError:
    print("请安装依赖: pip install flask requests")
    sys.exit(1)

TINYPNG_SHRINK = "https://api.tinify.com/shrink"
app = Flask(__name__)


def _load_key():
    key = os.environ.get("TINYPNG_API_KEY")
    if key:
        return key
    try:
        from pathlib import Path
        p = Path(__file__).resolve().parent.parent / ".env"
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("TINYPNG_API_KEY=") and "=" in line:
                    v = line.split("=", 1)[1].strip().strip("'\"").strip()
                    if v:
                        return v
    except Exception:
        pass
    return None


@app.route("/compress", methods=["POST"])
def compress():
    api_key = _load_key()
    if not api_key:
        return Response("TINYPNG_API_KEY 未设置", status=500)
    data = request.get_data()
    if not data:
        return Response("body 为空", status=400)
    try:
        r = requests.post(
            TINYPNG_SHRINK,
            auth=("api", api_key),
            data=data,
            timeout=30,
        )
        if r.status_code != 201:
            return Response(r.text or "TinyPNG 错误", status=r.status_code)
        out_url = r.json().get("output", {}).get("url")
        if not out_url:
            return Response("TinyPNG 未返回 output.url", status=502)
        r2 = requests.get(out_url, timeout=30)
        r2.raise_for_status()
        return Response(r2.content, mimetype=request.content_type or "image/png")
    except requests.RequestException as e:
        return Response(str(e), status=502)


@app.route("/")
def index():
    return "POST /compress with image bytes to get compressed image. TINYPNG_API_KEY required."


if __name__ == "__main__":
    print("压缩服务: http://127.0.0.1:8765/compress")
    print("在 Figma 插件「压缩服务 URL」中填写: http://localhost:8765/compress")
    app.run(host="127.0.0.1", port=8765)
