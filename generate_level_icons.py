#!/usr/bin/env python3
"""
生成 1–120 级等级图标 PNG（135×60px 及 @2x、@3x）。

规范：
- 基础尺寸 135×60
- 左侧徽章：六边形金色边框 + 中心宝石（按区间配色）
- 右侧：底色渐变 + 白色数字 + 2px 金色描边
- 每 20 级一切换配色

依赖：pip install Pillow

用法：
  python scripts/generate_level_icons.py
  # 输出：
  #   level_icons/level_001.png .. level_120.png         (1x, 135×60)
  #   level_icons/2.0x/level_001.png .. level_120.png    (2x, 270×120)
  #   level_icons/3.0x/level_001.png .. level_120.png    (3x, 405×180)
"""

from pathlib import Path
import math
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("请先安装 Pillow: pip install Pillow", file=sys.stderr)
    sys.exit(1)

# 规范尺寸（1x）
W, H = 135, 60
# 分辨率倍数与子目录（Flutter 资源变体）
VARIANTS = [
    (1, None),       # 1x 放在根目录
    (2, "2.0x"),     # 2x 放在 2.0x/
    (3, "3.0x"),     # 3x 放在 3.0x/
]
GOLD_BORDER = (0xD4, 0xA8, 0x4B)
GOLD_STROKE = (0xFB, 0xBF, 0x24)
WHITE = (0xFF, 0xFF, 0xFF)

# 六段配色：(底色, 宝石色)
SEGMENTS = [
    ((0x5A, 0x2D, 0x81), (0xA8, 0x55, 0xF7)),   # 1-20  深紫 / 亮紫
    ((0x1E, 0x3A, 0x8A), (0x3B, 0x82, 0xF6)),   # 21-40 深蓝 / 天蓝
    ((0x16, 0x65, 0x34), (0x22, 0xC5, 0x5E)),   # 41-60 深绿 / 翠绿
    ((0x92, 0x40, 0x0E), (0xF9, 0x73, 0x16)),   # 61-80 深橙 / 琥珀
    ((0x99, 0x1B, 0x1B), (0xEF, 0x44, 0x44)),   # 81-100 深红 / 红宝石
    ((0x85, 0x4D, 0x0E), (0xFB, 0xBF, 0x24)),   # 101-120 深金 / 亮金
]


def segment_for_level(level: int):
    idx = min(5, (level - 1) // 20)
    return SEGMENTS[idx]


def shield_verts(cx: float, cy: float, r: float):
    """盾形：上宽下尖，与参考图徽章一致。"""
    return [
        (cx - r * 0.88, cy - r * 0.72),
        (cx + r * 0.88, cy - r * 0.72),
        (cx + r * 0.62, cy + r * 0.02),
        (cx, cy + r * 0.88),
        (cx - r * 0.62, cy + r * 0.02),
    ]


def heart_verts(cx: float, cy: float, r: float, n: int = 28):
    """心形多边形近似（参数方程），总高约 2*r、宽约 2*r。"""
    pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        x = 16 * (math.sin(t) ** 3)
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        scale = r / 18.0  # 使心形总高约 2r
        pts.append((cx + x * scale, cy - y * scale))
    return pts


def lighten(rgb: tuple, amount: float) -> tuple:
    return tuple(min(255, int(c + (255 - c) * amount)) for c in rgb)


def darken(rgb: tuple, amount: float) -> tuple:
    return tuple(max(0, int(c * (1 - amount))) for c in rgb)


def draw_icon(level: int, scale: int = 1) -> Image.Image:
    """绘制等级图标（盾形徽章+心形宝石+整图金边+右侧竖纹），与参考图风格一致。"""
    w, h = W * scale, H * scale
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    bg_rgb, gem_rgb = segment_for_level(level)
    badge_w = w * 0.45
    panel_w = w - badge_w
    panel_left = int(badge_w)
    cx, cy = badge_w * 0.5, h * 0.5
    badge_r = min(badge_w * 0.48, h * 0.42)
    corner_r = max(2, h * 0.18)
    radius = int(corner_r)

    # 0) 整体圆角底
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=bg_rgb, outline=None)
    else:
        draw.rectangle([0, 0, w - 1, h - 1], fill=bg_rgb)

    # 1) 右侧数字区竖纹（左略暗→右略亮）
    stripe_count = 8
    stripe_w = panel_w / stripe_count
    for i in range(stripe_count):
        t = i / stripe_count
        shade = tuple(min(255, int(c + (255 - c) * (0.03 + 0.08 * t))) for c in bg_rgb)
        x0 = panel_left + int(i * stripe_w)
        x1 = min(w, x0 + int(stripe_w) + 2)
        draw.rectangle([x0, 0, x1, h - 1], fill=shade)

    # 2) 左侧盾形徽章 + 金边
    verts = shield_verts(cx, cy, badge_r)
    draw.polygon(verts, fill=darken(bg_rgb, 0.12), outline=None)
    draw.polygon(verts, fill=None, outline=GOLD_BORDER, width=max(1, 2 * scale))

    # 3) 中心心形宝石（+ 小高光椭圆在左上）
    gem_r = badge_r * 0.42
    gem_cy = cy - gem_r * 0.12
    heart = heart_verts(cx, gem_cy, gem_r)
    draw.polygon(heart, fill=gem_rgb, outline=None)
    # 左上高光椭圆（近似）
    hl_x0 = int(cx - gem_r * 0.9)
    hl_y0 = int(gem_cy - gem_r * 1.0)
    hl_x1 = int(cx + gem_r * 0.2)
    hl_y1 = int(gem_cy - gem_r * 0.2)
    hi = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hi_d = ImageDraw.Draw(hi)
    hi_d.ellipse([hl_x0, hl_y0, hl_x1, hl_y1], fill=(255, 255, 255, 120))
    # 只保留与心形相交的高光：用心形区域做 mask 再贴回
    mask = Image.new("L", (w, h), 0)
    m_d = ImageDraw.Draw(mask)
    m_d.polygon(heart, fill=255)
    im.paste(hi, (0, 0), mask=mask)

    # 4) 数字：白字 + 金描边（paste 之后重取 draw）
    draw = ImageDraw.Draw(im)
    font_size = int(h * 0.38) if level >= 100 else int(h * 0.48)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
    text = str(level)
    if hasattr(draw, "textbbox"):
        bbox = draw.textbbox((0, 0), text, font=font)
    else:
        bbox = draw.textsize(text, font=font)
        bbox = (0, 0, bbox[0], bbox[1])
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = panel_left + (panel_w - tw) / 2
    ty = (h - th) / 2
    ox, oy = int(tx), int(ty)
    stroke = max(1, 2 * scale)
    for dx in range(-stroke, stroke + 1):
        for dy in range(-stroke, stroke + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((ox + dx, oy + dy), text, font=font, fill=GOLD_STROKE)
    draw.text((ox, oy), text, font=font, fill=WHITE)

    # 5) 整体外圈金色细边（最后画，压在顶层）
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle(
            [0, 0, w - 1, h - 1],
            radius=radius,
            fill=None,
            outline=GOLD_BORDER,
            width=max(1, int(1.5 * scale)),
        )

    return im


def main():
    root = Path(__file__).resolve().parent.parent
    base_out = root / "ugc_flutter" / "assets" / "images" / "level_icons"
    base_out.mkdir(parents=True, exist_ok=True)

    for scale, subdir in VARIANTS:
        out_dir = base_out / subdir if subdir else base_out
        if subdir:
            out_dir.mkdir(parents=True, exist_ok=True)
        for level in range(1, 121):
            im = draw_icon(level, scale=scale)
            path = out_dir / f"level_{level:03d}.png"
            im.save(path, "PNG")
            print(path)
        suffix = f" ({subdir})" if subdir else " (1x)"
        print(f"已生成 120 个图标{suffix} -> {out_dir}")

    print(f"共输出 {len(VARIANTS) * 120} 个 PNG（1x + 2x + 3x）")


if __name__ == "__main__":
    main()
