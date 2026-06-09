"""
CharaSorter アイコン生成スクリプト
sort_ui.ico を生成する

デザイン: キャラリスト（カラーアバター×3 + 名前バー）+ ソートバッジ
"""
from PIL import Image, ImageDraw
import math

def make_icon(size=256):
    # 4倍サイズで描画 → LANCZOS縮小でアンチエイリアス
    SCALE = 4
    s = size * SCALE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # ── 背景 ──────────────────────────────────────
    d.rounded_rectangle([0, 0, s-1, s-1],
                        radius=int(s * 0.16),
                        fill=(20, 16, 42))

    # ── キャラリスト（3行） ──────────────────────
    AVATAR_COLORS = [
        (210, 130, 255),   # 紫
        ( 90, 190, 255),   # 水色
        (255, 130, 160),   # ピンク
    ]
    # 各行の名前バー幅（右端からの割合、異なる長さで自然感を出す）
    BAR_RATIOS = [0.72, 0.54, 0.44]

    pad_x   = int(s * 0.10)
    pad_top = int(s * 0.11)
    # 下部はバッジ用に確保
    pad_bot = int(s * 0.12)

    list_h = s - pad_top - pad_bot
    row_h  = list_h // 3
    av_r   = int(row_h * 0.33)          # アバター半径
    av_cx  = pad_x + av_r               # アバター中心X（左端から）

    for i, (color, bar_ratio) in enumerate(zip(AVATAR_COLORS, BAR_RATIOS)):
        cy = pad_top + i * row_h + row_h // 2   # 行の中心Y

        # ─ アバター: 髪（上の楕円）→ 顔（円）の順で描画 ─
        hair_w = int(av_r * 1.5)
        hair_h = int(av_r * 0.55)
        # 髪は顔円の上端ぴったりに接する位置
        d.ellipse([av_cx - hair_w // 2,  cy - av_r - hair_h,
                   av_cx + hair_w // 2,  cy - av_r],
                  fill=color)
        # 顔円
        d.ellipse([av_cx - av_r, cy - av_r,
                   av_cx + av_r, cy + av_r],
                  fill=color)
        # 顔のハイライト（左上に小さな白楕円）
        hl_rx = max(2, int(av_r * 0.28))
        hl_ry = max(2, int(av_r * 0.22))
        hl_cx = av_cx - int(av_r * 0.30)
        hl_cy = cy     - int(av_r * 0.28)
        d.ellipse([hl_cx - hl_rx, hl_cy - hl_ry,
                   hl_cx + hl_rx, hl_cy + hl_ry],
                  fill=(255, 255, 255, 140))

        # ─ 名前バー ─
        bar_x1 = av_cx + av_r + int(s * 0.055)
        bar_x2 = int(bar_x1 + (s - pad_x - bar_x1) * bar_ratio)
        bh = int(row_h * 0.20)          # バー高さの半分
        br = max(2, bh // 2)
        d.rounded_rectangle([bar_x1, cy - bh, bar_x2, cy + bh],
                            radius=br, fill=(58, 46, 82))

        # ─ 行区切り線（最終行以外） ─
        if i < 2:
            div_y = pad_top + (i + 1) * row_h
            d.line([(pad_x, div_y), (s - pad_x, div_y)],
                   fill=(40, 32, 62), width=max(1, s // 180))

    # ── ソートバッジ（右下）──────────────────────
    # 矢印は数学的に円の中心に完全センタリング
    b_r  = int(s * 0.195)               # バッジ半径
    bcx  = s - b_r - int(s * 0.045)    # バッジ中心X
    bcy  = s - b_r - int(s * 0.045)    # バッジ中心Y

    # 円（グリーン）
    d.ellipse([bcx - b_r, bcy - b_r, bcx + b_r, bcy + b_r],
              fill=(48, 190, 90))

    # 矢印パラメータ
    aw  = int(b_r * 0.54)   # 矢印頭の幅（半分）
    ah  = int(b_r * 0.30)   # 矢印頭の高さ
    sw  = max(1, int(b_r * 0.16))  # 茎の幅（半分）
    stm = int(b_r * 0.30)   # 茎の長さ
    gap = int(b_r * 0.12)   # 上下矢印の間隔

    # 全体の高さ = 頭 + 茎 + gap + 茎 + 頭
    total_h = ah + stm + gap + stm + ah
    # 上端Y（これで上下矢印セット全体がbcyを中心に対称になる）
    top_y = bcy - total_h // 2

    # ↑ 上矢印（頭が上）
    up_head_top = top_y
    up_head_bot = top_y + ah
    up_stem_bot = up_head_bot + stm
    d.polygon([
        (bcx,        up_head_top),
        (bcx - aw,   up_head_bot),
        (bcx + aw,   up_head_bot),
    ], fill="white")
    d.rectangle([bcx - sw, up_head_bot, bcx + sw, up_stem_bot], fill="white")

    # ↓ 下矢印（頭が下）
    dn_stem_top = up_stem_bot + gap
    dn_head_top = dn_stem_top + stm
    dn_head_bot = dn_head_top + ah
    d.rectangle([bcx - sw, dn_stem_top, bcx + sw, dn_head_top], fill="white")
    d.polygon([
        (bcx,        dn_head_bot),
        (bcx - aw,   dn_head_top),
        (bcx + aw,   dn_head_top),
    ], fill="white")

    # 元サイズに縮小（ここでアンチエイリアスが効く）
    return img.resize((size, size), Image.LANCZOS)


def main():
    base = make_icon(256)
    sizes = [256, 128, 64, 48, 32, 16]
    icons = [base.resize((sz, sz), Image.LANCZOS) for sz in sizes]
    import pathlib
    here = pathlib.Path(__file__).parent
    out = here / "sort_ui.ico"
    icons[0].save(str(out), format="ICO", sizes=[(sz, sz) for sz in sizes],
                  append_images=icons[1:])
    print(f"Saved: {out}")
    base.save(str(here / "sort_ui_preview.png"))
    print("Preview saved.")

if __name__ == "__main__":
    main()
