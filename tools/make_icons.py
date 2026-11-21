# -*- coding: utf-8 -*-
"""앱 아이콘 만들기 (홈 화면에 추가했을 때 보이는 아이콘).

  python -I tools/make_icons.py

교회 로고의 그림 부분만 떼어내어, 초록 바탕 + 크림 원 위에 올립니다.
 - icon-192 / icon-512            : 보통 아이콘 (그대로 보이므로 원을 크게)
 - icon-maskable-192 / -512       : 안드로이드가 둥글게 잘라내는 아이콘
   (가운데 지름 80% 안에 들어가야 안 잘립니다)
"""
import io, os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, 'assets')

GREEN_TOP = (58, 128, 92)
GREEN_BOT = (26, 66, 46)
CREAM = (250, 246, 237)


def logo_mark():
    """로고 이미지에서 글자를 뺀 그림(마크)만 잘라냅니다."""
    im = Image.open(os.path.join(A, 'logo.png')).convert('RGB')
    w, h = im.size
    px = im.load()

    def is_ink(x, y):
        r, g, b = px[x, y]
        return abs(r - 249) > 22 or abs(g - 245) > 22 or abs(b - 236) > 22

    # 세로로 그림 영역(첫 번째 덩어리) 찾기
    rows = [any(is_ink(x, y) for x in range(0, w, 3)) for y in range(h)]
    top = rows.index(True)
    bot = top
    while bot < h and rows[bot]:
        bot += 1
    # 가로 범위
    cols = [any(is_ink(x, y) for y in range(top, bot, 3)) for x in range(w)]
    left = cols.index(True)
    right = w - 1 - cols[::-1].index(True)

    mark = im.crop((left, top, right + 1, bot))
    # 크림 배경을 투명으로
    mark = mark.convert('RGBA')
    mp = mark.load()
    for y in range(mark.height):
        for x in range(mark.width):
            r, g, b, _ = mp[x, y]
            if abs(r - 249) <= 18 and abs(g - 245) <= 18 and abs(b - 236) <= 18:
                mp[x, y] = (r, g, b, 0)
    return mark


def build(size, circle_ratio, mark_ratio, out):
    S = size * 4                      # 4배로 그린 뒤 줄여서 테두리를 매끄럽게
    img = Image.new('RGB', (S, S))
    d = ImageDraw.Draw(img)

    # 초록 그라데이션 바탕 (위가 밝고 아래가 깊게)
    for y in range(S):
        t = y / (S - 1)
        d.line([(0, y), (S, y)], fill=(
            int(GREEN_TOP[0] + (GREEN_BOT[0] - GREEN_TOP[0]) * t),
            int(GREEN_TOP[1] + (GREEN_BOT[1] - GREEN_TOP[1]) * t),
            int(GREEN_TOP[2] + (GREEN_BOT[2] - GREEN_TOP[2]) * t)))

    img = img.convert('RGBA')
    r = int(S * circle_ratio / 2)
    cx = cy = S // 2

    # 원 아래로 옅은 그림자
    sh = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse(
        [cx - r, cy - r + int(S * .02), cx + r, cy + r + int(S * .02)],
        fill=(0, 0, 0, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(S * .022))
    img.alpha_composite(sh)

    # 크림 원
    circle = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(circle).ellipse([cx - r, cy - r, cx + r, cy + r], fill=CREAM + (255,))
    img.alpha_composite(circle)

    # 로고 마크
    m = logo_mark()
    target = int(2 * r * mark_ratio)
    scale = target / max(m.size)
    m = m.resize((max(1, int(m.width * scale)), max(1, int(m.height * scale))), Image.LANCZOS)
    img.alpha_composite(m, (cx - m.width // 2, cy - m.height // 2))

    img = img.resize((size, size), Image.LANCZOS).convert('RGB')
    img.save(os.path.join(A, out), quality=95)
    return out


if __name__ == '__main__':
    made = []
    made.append(build(512, 0.86, 0.74, 'icon-512.png'))
    made.append(build(192, 0.86, 0.74, 'icon-192.png'))
    made.append(build(512, 0.72, 0.74, 'icon-maskable-512.png'))
    made.append(build(192, 0.72, 0.74, 'icon-maskable-192.png'))
    for f in made:
        print(f, str(round(os.path.getsize(os.path.join(A, f)) / 1024)) + 'KB')
