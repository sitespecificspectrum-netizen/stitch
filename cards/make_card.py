#!/usr/bin/env python3
"""소드코스트 캐릭터 카드 십자수 도안 생성기 (100 x 180칸).

사용법:
  python3 cards/make_card.py 티플링 바드          # 종족 + 직업
  python3 cards/make_card.py half-orc paladin
  python3 cards/make_card.py 아울베어              # 몬스터 이름
  python3 cards/make_card.py elf wizard --hair 321 --skin 3064 --bg forest
  python3 cards/make_card.py --list              # 쓸 수 있는 이름 보기
  python3 cards/make_card.py --all               # 전부 만들고 gallery_*.png 생성

결과 (cards/out/):
  <이름>.png         1칸 = 1픽셀 원본 (앱의 "이미지 고르기"로 불러오기)
  <이름>_x8.png      8배 미리보기
  <이름>_colors.txt  DMC 번호별 땀 수
모든 색은 dmc.js 의 DMC 실 색만 사용한다.
"""
import argparse, os, re, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 100, 180

_src = open(os.path.join(HERE, '..', 'dmc.js'), encoding='utf-8').read()
DMC = {c: (n, h) for c, n, h in re.findall(r'\["([^"]+)","([^"]+)","([0-9A-Fa-f]{6})"\]', _src)}


def C(code):
    h = DMC[str(code)][1]
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


RGB2CODE = {}
for _c in DMC:
    RGB2CODE.setdefault(C(_c)[:3], _c)

K = C(310)  # 외곽선


class Layer:
    """투명 레이어에 도형을 그리고, 마지막에 외곽선을 둘러 합성한다."""

    def __init__(self):
        self.im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def el(self, cx, cy, rx, ry, col):
        self.d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=C(col))

    def rect(self, x0, y0, x1, y1, col):
        self.d.rectangle([x0, y0, x1, y1], fill=C(col))

    def poly(self, pts, col):
        self.d.polygon(pts, fill=C(col))

    def line(self, pts, col, w=1):
        self.d.line(pts, fill=C(col), width=w)

    def px(self, pts, col):
        for p in pts:
            self.d.point(p, fill=C(col))

    def curve(self, pts, r0, r1, col, steps=40):
        """굵기가 r0 -> r1 로 변하는 곡선 (2차/3차 베지에)."""
        n = len(pts) - 1
        for i in range(steps + 1):
            t = i / steps
            ps = [tuple(map(float, p)) for p in pts]
            while len(ps) > 1:
                ps = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for a, b in zip(ps, ps[1:])]
            r = r0 + (r1 - r0) * t
            x, y = ps[0]
            self.d.ellipse([round(x - r), round(y - r), round(x + r), round(y + r)], fill=C(col))

    def mirror(self):
        """왼쪽 절반(x<50)을 오른쪽으로 대칭 복사."""
        a = np.array(self.im)
        a[:, 50:] = a[:, 49::-1]
        self.im = Image.fromarray(a)
        self.d = ImageDraw.Draw(self.im)

    def outlined(self, col=310):
        a = np.array(self.im)
        m = a[..., 3] > 0
        g = np.zeros_like(m)
        g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
        a[g & ~m] = C(col)
        return Image.fromarray(a)

    def onto(self, base, outline=310):
        im = self.outlined(outline) if outline else self.im
        base.alpha_composite(im)


FONT = {
 'A': ["01110","10001","10001","11111","10001","10001","10001"],
 'B': ["11110","10001","10001","11110","10001","10001","11110"],
 'C': ["01111","10000","10000","10000","10000","10000","01111"],
 'D': ["11110","10001","10001","10001","10001","10001","11110"],
 'E': ["11111","10000","10000","11110","10000","10000","11111"],
 'F': ["11111","10000","10000","11110","10000","10000","10000"],
 'G': ["01111","10000","10000","10011","10001","10001","01111"],
 'H': ["10001","10001","10001","11111","10001","10001","10001"],
 'I': ["111","010","010","010","010","010","111"],
 'K': ["10001","10010","10100","11000","10100","10010","10001"],
 'L': ["10000","10000","10000","10000","10000","10000","11111"],
 'M': ["10001","11011","10101","10101","10001","10001","10001"],
 'N': ["10001","11001","10101","10101","10011","10001","10001"],
 'O': ["01110","10001","10001","10001","10001","10001","01110"],
 'P': ["11110","10001","10001","11110","10000","10000","10000"],
 'R': ["11110","10001","10001","11110","10100","10010","10001"],
 'S': ["01111","10000","10000","01110","00001","00001","11110"],
 'T': ["11111","00100","00100","00100","00100","00100","00100"],
 'U': ["10001","10001","10001","10001","10001","10001","01110"],
 'V': ["10001","10001","10001","10001","01010","01010","00100"],
 'W': ["10001","10001","10001","10101","10101","11011","10001"],
 'Y': ["10001","10001","01010","00100","00100","00100","00100"],
 'J': ["00111","00001","00001","00001","00001","10001","01110"],
 'Q': ["01110","10001","10001","10001","10101","10010","01101"],
 'X': ["10001","10001","01010","00100","01010","10001","10001"],
 'Z': ["11111","00001","00010","00100","01000","10000","11111"],
 '-': ["000","000","000","111","000","000","000"],
 ' ': ["00","00","00","00","00","00","00"],
}


def bands(base, stops):
    """세로 그라데이션: [(시작 y, 색), ...]. 경계 2줄은 체크무늬로 섞는다."""
    d = ImageDraw.Draw(base)
    for i, (y, col) in enumerate(stops):
        y1 = stops[i + 1][0] if i + 1 < len(stops) else H
        d.rectangle([0, y, W, y1], fill=C(col))
        if i:
            prev = stops[i - 1][1]
            for yy in (y - 2, y - 1, y, y + 1):
                for x in range(W):
                    near = yy < y
                    on = (x + yy) % 2 == 0 if yy in (y - 1, y) else (x % 2 == 0 and yy % 2 == 0) != near
                    if yy in (y - 2, y + 1):
                        on = (x + 2 * yy) % 4 == 0
                        d.point((x, yy), fill=C(col if near and on else prev if (not near and on) else (prev if near else col)))
                    else:
                        d.point((x, yy), fill=C(col if on else prev))


def frame(base, col, col2):
    d = ImageDraw.Draw(base)
    d.rectangle([0, 0, W - 1, H - 1], outline=K)
    d.rectangle([1, 1, W - 2, H - 2], outline=C(col))
    d.rectangle([2, 2, W - 3, H - 3], outline=C(col2))
    d.rectangle([3, 3, W - 4, H - 4], outline=K)
    for x, y in ((1, 1), (W - 2, 1), (1, H - 2), (W - 2, H - 2)):
        d.point((x, y), fill=K)
    for x, y in ((4, 4), (W - 5, 4), (4, H - 5), (W - 5, H - 5)):
        d.point((x, y), fill=K)


def new():
    return Image.new('RGBA', (W, H), K)


TEXT_FITS = [([3] * 5, 3), ([3] * 5, 2), ([2] * 5, 2), ([2] * 5, 1), ([2, 1, 2, 1, 2], 1), ([1] * 5, 1)]


def text(base, s, y, top, bottom, maxsx=2, sy=2):
    """가운데 정렬 글자. 폭(88칸)에 맞는 가장 큰 크기를 고른다."""
    def width(ws, gap):
        return sum(sum(ws[:len(FONT[ch][0])]) + gap for ch in s) - gap
    ws, gap = next(((w, g) for w, g in TEXT_FITS if w[0] <= maxsx and width(w, g) <= 88), TEXT_FITS[-1])
    x = (W - width(ws, gap)) // 2
    L = Layer()
    for ch in s:
        g = FONT[ch]
        cw = ws[:len(g[0])]
        for r, row in enumerate(g):
            xx = x
            for c, v in enumerate(row):
                if v == '1':
                    L.rect(xx, y + r * sy, xx + cw[c] - 1, y + r * sy + sy - 1, top if r < 4 else bottom)
                xx += cw[c]
        x += sum(cw) + gap
    a = np.array(L.im); m = a[..., 3] > 0
    g = np.zeros_like(m)
    for dy in (-1, 0, 1, 2):
        for dx in (-1, 0, 1):
            g |= np.roll(np.roll(m, dy, 0), dx, 1)
    a[g & ~m] = K
    base.alpha_composite(Image.fromarray(a))


def title(im, lines, tcol):
    if len(lines) == 1:
        text(im, lines[0], 139, tcol[0], tcol[1], 3, 3)
    else:
        text(im, lines[0], 131, tcol[0], tcol[1], 2, 2)
        text(im, lines[1], 151, tcol[2] if len(tcol) > 2 else tcol[0], tcol[3] if len(tcol) > 2 else tcol[1], 3, 3)


def sparkle(d, x, y, col, big=True):
    d.point((x, y), fill=C(col))
    if big:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            d.point((x + dx, y + dy), fill=C(col))


# ================================================================ 배경
def bg_forest(im):
    """네버윈터 숲의 밤"""
    bands(im, [(0, 823), (30, 796), (58, 798), (84, 809)])
    d = ImageDraw.Draw(im)
    d.ellipse([70, 12, 84, 26], fill=C(3078)); d.ellipse([67, 10, 79, 22], fill=C(823))
    for x, y in ((14, 14), (30, 9), (46, 20), (58, 11), (90, 34), (10, 38), (22, 28), (88, 8)):
        d.point((x, y), fill=C(3078))
    for cx, top in ((10, 62), (30, 70), (52, 66), (72, 72), (92, 60)):
        for k in range(4):
            yy = top + k * 9
            d.polygon([(cx, yy), (cx - 6 - k * 3, yy + 14), (cx + 6 + k * 3, yy + 14)], fill=C(500))
    for cx, top in ((2, 40), (97, 44)):
        for k in range(6):
            yy = top + k * 11
            d.polygon([(cx, yy), (cx - 7 - k * 3, yy + 16), (cx + 7 + k * 3, yy + 16)], fill=C(890))
    d.rectangle([0, 108, W, H], fill=C(986))
    d.rectangle([0, 122, W, H], fill=C(890))
    for x in range(4, 96, 3):
        d.point((x, 108 - (x * 7) % 3), fill=C(986))
        d.point((x + 1, 121 - (x * 5) % 2), fill=C(986))
    for x, y in ((12, 114), (26, 118), (80, 113), (90, 119), (70, 117)):
        d.line([(x, y), (x, y - 2)], fill=C(988)); d.point((x + 1, y - 1), fill=C(988))


def bg_dungeon(im):
    """언더마운틴 던전"""
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 104], fill=C(317))
    for row, y in enumerate(range(4, 104, 10)):
        d.line([(0, y), (W, y)], fill=C(3799))
        for x in range(4 + (row % 2) * 9, W, 18):
            d.line([(x, y), (x, y + 10)], fill=C(3799))
    for x, y in ((14, 18), (62, 9), (88, 47), (30, 29), (9, 68), (76, 27), (46, 16)):
        d.line([(x, y), (x + 3, y)], fill=C(414))
    d.rectangle([0, 104, W, H], fill=C(3799))
    for y in (112, 124):
        d.line([(0, y), (W, y)], fill=C(317))
    for x in range(-20, 120, 22):
        d.line([(x, 124), (x + 8, 104)], fill=C(317))
    d.rectangle([0, 125, W, H], fill=C(3799))
    for cx in (11, 89):
        T = Layer()
        T.rect(cx - 1, 30, cx + 1, 44, 801); T.rect(cx - 3, 28, cx + 3, 31, 414)
        T.poly([(cx - 4, 28), (cx, 14), (cx + 4, 28)], 740)
        T.poly([(cx - 2, 28), (cx, 20), (cx + 2, 28)], 444)
        T.onto(im)
        for x, y in ((cx - 6, 18), (cx + 6, 22), (cx, 10), (cx + 3, 13)):
            d.point((x, y), fill=C(740))


def bg_city(im):
    """해 질 녘의 발더스 게이트"""
    bands(im, [(0, 550), (26, 552), (50, 3607), (70, 3341), (86, 743)])
    d = ImageDraw.Draw(im)
    for x, y in ((12, 10), (28, 18), (44, 8), (66, 14), (84, 9), (90, 24), (18, 32), (74, 30)):
        d.point((x, y), fill=C(3078))
    for x0, x1, y1 in ((4, 14, 84), (14, 22, 74), (22, 34, 88), (34, 40, 66), (40, 52, 82),
                       (52, 60, 90), (60, 70, 70), (70, 82, 86), (82, 96, 78)):
        d.rectangle([x0, y1, x1, 110], fill=C(939))
    for cx, y, w in ((18, 74, 5), (37, 66, 4), (65, 70, 6), (89, 78, 8)):
        d.polygon([(cx - w, y), (cx, y - w - 4), (cx + w, y)], fill=C(939))
    for x in range(22, 34, 4):
        d.rectangle([x, 85, x + 1, 87], fill=C(939))
    for x, y in ((16, 80), (19, 88), (36, 72), (36, 80), (63, 76), (66, 84), (44, 88), (86, 84), (91, 90),
                 (8, 90), (74, 92), (26, 94), (56, 95)):
        d.rectangle([x, y, x + 1, y + 1], fill=C(743))
    d.rectangle([0, 108, W, H], fill=C(3799))
    for y in range(111, 128, 5):
        for x in range((y % 2) * 5, W, 10):
            d.line([(x, y), (x + 5, y)], fill=C(317))


def bg_coast(im):
    """소드코스트 절벽과 바다"""
    bands(im, [(0, 798), (22, 809), (48, 3325), (70, 3756)])
    d = ImageDraw.Draw(im)
    for cx, cy in ((22, 16), (70, 30)):
        d.ellipse([cx - 9, cy - 3, cx + 9, cy + 3], fill=C('B5200'))
        d.ellipse([cx - 4, cy - 6, cx + 5, cy + 2], fill=C('B5200'))
    d.rectangle([0, 78, W, 108], fill=C(798))
    for y in range(81, 108, 5):
        for x in range((y * 3) % 11, W, 14):
            d.line([(x, y), (x + 4, y)], fill=C(3325))
    d.polygon([(0, 50), (12, 54), (16, 66), (17, 108), (0, 108)], fill=C(3064))
    d.polygon([(0, 50), (12, 54), (14, 58), (0, 56)], fill=C(988))
    for x, y in ((5, 66), (10, 78), (4, 88), (11, 96), (8, 72)):
        d.line([(x, y), (x + 3, y + 3)], fill=C(632))
    d.polygon([(86, 62), (86, 72), (94, 72)], fill=C('B5200')); d.polygon([(85, 64), (85, 72), (80, 72)], fill=C('B5200'))
    d.polygon([(78, 74), (96, 74), (93, 78), (81, 78)], fill=C(801))
    d.rectangle([0, 106, W, H], fill=C(988))
    d.rectangle([0, 124, W, H], fill=C(986))
    for x in range(3, 98, 5):
        d.line([(x, 112 + (x * 7) % 9), (x, 110 + (x * 7) % 9)], fill=C(986))
        d.point((x + 2, 124 - (x % 3)), fill=C(986))


def bg_snow(im):
    """아이스윈드 데일의 설산과 오로라"""
    bands(im, [(0, 939), (34, 823), (64, 796)])
    d = ImageDraw.Draw(im)
    for x, y in ((8, 8), (24, 30), (40, 6), (60, 26), (78, 10), (92, 20), (50, 40), (14, 46), (86, 44)):
        d.point((x, y), fill=C('B5200'))
    for x in range(4, 96):
        y = 20 + round(5 * np.sin(x / 9.0))
        d.line([(x, y), (x, y + 2 + (x % 3))], fill=C(964))
        if x % 2:
            d.point((x, y + 6 + (x % 4)), fill=C(3846))
    for cx, top, w in ((14, 56, 26), (46, 46, 34), (82, 52, 30)):
        d.polygon([(cx, top), (cx - w, 110), (cx + w, 110)], fill=C(161))
        d.polygon([(cx, top), (cx - w // 3, top + 16), (cx - w // 8, top + 12), (cx + w // 10, top + 18),
                   (cx + w // 3, top + 16)], fill=C('B5200'))
    d.rectangle([0, 106, W, H], fill=C('B5200'))
    d.rectangle([0, 124, W, H], fill=C(3325))
    for x in range(2, 98, 4):
        d.point((x, 123 - (x * 3) % 2), fill=C(3325)); d.point((x + 2, 125), fill=C('B5200'))
    for x, y in ((10, 112), (30, 118), (72, 111), (88, 117)):
        d.line([(x, y), (x + 4, y)], fill=C(3325))


def bg_mountain(im):
    """소드 산맥의 한낮"""
    bands(im, [(0, 3325), (30, 3756), (62, 'B5200')])
    d = ImageDraw.Draw(im)
    d.ellipse([72, 10, 86, 24], fill=C(743)); d.ellipse([74, 12, 84, 22], fill=C(3078))
    for cx, top, w in ((18, 50, 30), (56, 40, 34), (90, 56, 26)):
        d.polygon([(cx, top), (cx - w, 110), (cx + w, 110)], fill=C(414))
        d.polygon([(cx, top), (cx + w, 110), (cx + w // 4, 110)], fill=C(317))
        d.polygon([(cx, top), (cx - w // 3, top + 15), (cx - w // 8, top + 11), (cx + w // 10, top + 17),
                   (cx + w // 3, top + 15)], fill=C('B5200'))
    for cx in (6, 30, 70, 94):
        d.ellipse([cx - 22, 94, cx + 22, 124], fill=C(988))
    d.rectangle([0, 108, W, H], fill=C(988))
    d.rectangle([0, 124, W, H], fill=C(986))
    for x in range(3, 98, 5):
        d.line([(x, 113 + (x * 7) % 8), (x, 111 + (x * 7) % 8)], fill=C(986))
        d.point((x + 2, 124 - (x % 3)), fill=C(986))
    for x, y in ((14, 116), (84, 113), (26, 120)):
        d.point((x, y), fill=C(743)); d.point((x, y + 1), fill=C(986))


def bg_arcane(im):
    """캔들킵의 탑과 별밤"""
    bands(im, [(0, 939), (36, 823), (66, 333), (90, 552)])
    d = ImageDraw.Draw(im)
    d.ellipse([10, 10, 30, 30], fill=C(3078))
    for x, y in ((16, 16), (22, 24), (24, 15)):
        d.point((x, y), fill=C(743))
    for x, y in ((40, 8), (54, 18), (66, 9), (80, 22), (90, 10), (36, 30), (72, 36), (88, 44), (8, 44), (46, 44)):
        sparkle(d, x, y, 3078, (x + y) % 3 == 0)
    for x0, x1, top in ((0, 12, 82), (12, 20, 60), (20, 30, 88), (72, 80, 84), (80, 90, 54), (90, 100, 78)):
        d.rectangle([x0, top, x1, 110], fill=C(939))
    for cx, y, w in ((16, 60, 5), (85, 54, 6)):
        d.polygon([(cx - w, y), (cx, y - w - 6), (cx + w, y)], fill=C(939))
    for x, y in ((15, 68), (15, 78), (84, 62), (84, 74), (86, 88), (5, 90), (94, 86), (24, 96), (75, 92)):
        d.rectangle([x, y, x + 1, y + 2], fill=C(743))
    d.rectangle([0, 108, W, H], fill=C(939))
    for y in range(112, 128, 6):
        for x in range((y % 4) * 3, W, 12):
            d.line([(x, y), (x + 4, y)], fill=C(333))


BGS = {'forest': bg_forest, 'dungeon': bg_dungeon, 'city': bg_city, 'coast': bg_coast,
       'snow': bg_snow, 'mountain': bg_mountain, 'arcane': bg_arcane}


# ================================================================ 종족
RACE_BASE = dict(ll=15, th=29, bw=10, skin=945, shade=3064, blush=3328, hair=801, hair2=433, brow=801,
                 style='short', ears='round', face='normal')
RACES = {
    'human':      dict(title='HUMAN'),
    'elf':        dict(title='ELF', skin=951, hair=3820, hair2=3078, brow=780, style='long', ears='long'),
    'half-elf':   dict(title='HALF-ELF', hair=919, hair2=921, brow=919, style='medium', ears='point'),
    'dwarf':      dict(title='DWARF', ll=10, th=28, bw=14, hair=921, hair2=740, brow=919, beard=True, nose=True),
    'halfling':   dict(title='HALFLING', ll=9, th=24, bw=9, hair=433, hair2=435, style='curly', ears='point',
                       barefoot=True),
    'gnome':      dict(title='GNOME', ll=8, th=22, bw=9, hair='B5200', hair2=415, brow=414, style='spiky',
                       ears='point', nose=True),
    'half-orc':   dict(title='HALF-ORC', th=32, bw=13, skin=3347, shade=3346, blush=3346, hair=3799, hair2=317,
                       brow=310, style='topknot', ears='point', face='orc'),
    'tiefling':   dict(title='TIEFLING', skin=321, shade=815, blush=3328, hair=550, hair2=552, brow=310,
                       style='long', ears='long', face='glow', horns=True, tail='spade'),
    'drow':       dict(title='DROW', skin=3041, shade=3740, blush=3740, hair='B5200', hair2=415, brow='B5200',
                       style='long', ears='long', face='drow'),
    'dragonborn': dict(title='DRAGONBORN', th=32, bw=12, skin=921, shade=919, blush=919, belly=742,
                       style='bald', ears='fin', face='dragon', tail='thick'),
    'goblin':     dict(title='GOBLIN', ll=8, th=22, bw=9, skin=989, shade=986, blush=986, style='bald',
                       ears='huge', face='goblin'),
    # 몬스터용
    'illithid':   dict(title='MIND FLAYER', skin=554, shade=553, blush=553, style='bald', ears='none',
                       face='illithid'),
    'skeleton':   dict(title='SKELETON', skin='B5200', shade=415, blush='B5200', style='bald', ears='none',
                       face='skull'),
}
HIDDEN_RACES = ('illithid', 'skeleton')


class Rig:
    """치비 인물 뼈대. 종족이 체형/머리를, 직업이 옷/도구/배경을 정한다."""
    cx, feet = 50, 116

    def __init__(s, race, cls, skin=None, hair=None):
        r = dict(RACE_BASE); r.update(RACES[race])
        if skin:
            r['skin'] = skin
        if hair:
            r['hair'] = r['hair2'] = hair
        s.r, s.c = r, cls
        s.bw, s.th, s.ll = r['bw'], r['th'], r['ll']
        s.hip = s.feet - s.ll
        s.sy = s.hip - s.th
        s.hc = s.sy - 19
        s.skin, s.shade = r['skin'], r['shade']
        s.LH = (s.cx - s.bw - 12, s.sy + 15)
        s.RH = (s.cx + s.bw + 12, s.sy + 15)

    # ---- 몸
    def legs(s, L):
        lx = 6 + (s.bw - 10) // 2
        bare = s.r.get('barefoot') or s.c.barefoot
        col = s.skin if s.c.legs == 'skin' else s.c.legs
        for sg in (-1, 1):
            x = s.cx + sg * lx
            L.rect(x - 3, s.hip - 2, x + 3, s.feet - 3, col)
            if bare:
                L.rect(x - 3, s.feet - 6, x + 3, s.feet - 3, s.skin)
                L.el(x + sg, s.feet, 6, 3, s.skin)
                L.px([(x + sg * 4, s.feet + 1), (x + sg * 2, s.feet + 2)], s.shade)
            else:
                L.rect(x - 4, s.feet - 8, x + 4, s.feet - 3, s.c.boots)
                L.el(x + sg, s.feet, 6, 3, s.c.boots)

    def torso(s, L, col):
        L.poly([(s.cx - s.bw, s.sy), (s.cx + s.bw, s.sy), (s.cx + s.bw + 3, s.hip), (s.cx - s.bw - 3, s.hip)], col)

    def robe(s, L, col, trim=None):
        y = s.feet - 2
        L.poly([(s.cx - s.bw, s.sy), (s.cx + s.bw, s.sy), (s.cx + s.bw + 6, y), (s.cx - s.bw - 6, y)], col)
        if trim:
            L.rect(s.cx - s.bw - 6, y - 2, s.cx + s.bw + 6, y - 1, trim)

    def belt(s, L, col, buckle=783, dy=6):
        y = s.hip - dy
        L.rect(s.cx - s.bw - 2, y, s.cx + s.bw + 2, y + 2, col)
        L.rect(s.cx - 2, y - 1, s.cx + 2, y + 3, buckle)

    def pauldrons(s, L, col, trim=None):
        for sg in (-1, 1):
            L.el(s.cx + sg * (s.bw + 1), s.sy + 3, 6, 5, col)
            if trim:
                L.line([(s.cx + sg * (s.bw + 1) - 5, s.sy + 6), (s.cx + sg * (s.bw + 1) + 5, s.sy + 6)], trim)

    def cloak(s, B, col):
        B.poly([(s.cx - s.bw - 3, s.sy + 1), (s.cx + s.bw + 3, s.sy + 1),
                (s.cx + s.bw + 10, s.feet - 5), (s.cx - s.bw - 10, s.feet - 5)], col)

    def arm(s, F, side, hand, sleeve):
        x0, y0 = s.cx + side * (s.bw + 1), s.sy + 4
        mx, my = (x0 + hand[0]) / 2 + side * 3, (y0 + hand[1]) / 2 + 3
        F.curve([(x0, y0), (mx, my), hand], 3, 3, s.skin if sleeve == 'skin' else sleeve, steps=24)

    def hand(s, F, p, col=None):
        F.el(p[0], p[1], 3, 3, col or s.skin)

    # ---- 꼬리
    def race_back(s, B):
        cx, hip, t = s.cx, s.hip, s.r.get('tail')
        if t == 'spade':
            B.curve([(cx + 6, hip - 4), (cx + 32, hip + 6), (cx + 37, hip - 18), (cx + 29, hip - 28)], 2, 1, s.skin)
            B.poly([(cx + 29, hip - 36), (cx + 24, hip - 27), (cx + 34, hip - 27)], s.skin)
        elif t == 'thick':
            B.curve([(cx + 4, hip - 3), (cx + 30, hip + 12), (cx + 40, hip - 4), (cx + 34, hip - 16)], 5, 1, s.skin)

    # ---- 머리
    def head(s, L):
        r, cx, hc, sk, sh = s.r, s.cx, s.hc, s.skin, s.shade
        hair, hair2, st = r['hair'], r['hair2'], r['style']
        if st in ('long', 'medium'):
            b = 26 if st == 'long' else 17
            L.poly([(cx - 18, hc), (cx + 18, hc), (cx + 19, hc + b - 2), (cx + 13, hc + b),
                    (cx - 13, hc + b), (cx - 19, hc + b - 2)], hair)
        if r['face'] == 'illithid':
            L.el(cx, hc - 3, 17, 19, sk)
            L.line([(cx - 8, hc - 17), (cx - 3, hc - 19)], sh); L.line([(cx - 11, hc - 12), (cx - 9, hc - 14)], sh)
        else:
            L.el(cx, hc, 18, 16, sk if st in ('bald', 'topknot') else hair)
        s.c.hood(s, L)
        L.el(cx, hc + 5, 15, 12, sk)
        # 앞머리
        if st in ('short', 'long', 'medium'):
            L.poly([(cx + x, hc + y) for x, y in ((-17, -1), (-14, -11), (0, -14), (14, -11), (17, -1), (10, -5),
                                                  (5, -1), (-2, -6), (-8, -1), (-12, -4))], hair)
            L.line([(cx - 10, hc - 11), (cx - 3, hc - 13)], hair2); L.line([(cx - 8, hc - 8), (cx - 4, hc - 9)], hair2)
        elif st == 'curly':
            for x, y in ((-15, -5), (-10, -12), (-3, -15), (4, -15), (11, -12), (16, -5), (-9, -5), (-3, -7), (3, -7), (9, -5)):
                L.el(cx + x, hc + y, 4, 4, hair)
            L.px([(cx - 10, hc - 13), (cx - 3, hc - 16), (cx + 4, hc - 16), (cx - 9, hc - 6), (cx + 3, hc - 8)], hair2)
        elif st == 'spiky':
            for i in (-12, -6, 0, 6, 12):
                L.poly([(cx + i - 5, hc - 9), (cx + i, hc - 23 + abs(i) // 2), (cx + i + 5, hc - 9)], hair)
            L.poly([(cx - 17, hc - 1), (cx - 14, hc - 10), (cx + 14, hc - 10), (cx + 17, hc - 1), (cx + 11, hc - 5),
                    (cx + 6, hc - 2), (cx, hc - 6), (cx - 6, hc - 2), (cx - 11, hc - 5)], hair)
            L.line([(cx - 6, hc - 14), (cx - 6, hc - 11)], hair2); L.line([(cx + 6, hc - 14), (cx + 6, hc - 11)], hair2)
        elif st == 'topknot':
            L.el(cx, hc - 11, 8, 6, hair); L.el(cx, hc - 19, 4, 4, hair); L.rect(cx - 2, hc - 16, cx + 2, hc - 15, 321)
        s.c.hat(s, L)
        # 귀
        e = r['ears']
        for sg in (-1, 1):
            if e == 'round':
                L.el(cx + sg * 17, hc + 6, 3, 3, sk)
            elif e in ('point', 'long', 'huge'):
                n, up = {'point': (23, 0), 'long': (28, -3), 'huge': (33, -5)}[e]
                L.poly([(cx + sg * 15, hc + 2), (cx + sg * n, hc + up), (cx + sg * 15, hc + 10)], sk)
                L.line([(cx + sg * 17, hc + 5), (cx + sg * (n - 5), hc + up + 3)], sh)
            elif e == 'fin':
                L.poly([(cx + sg * 15, hc + 1), (cx + sg * 24, hc - 3), (cx + sg * 21, hc + 3), (cx + sg * 25, hc + 6),
                        (cx + sg * 15, hc + 9)], sh)
        if r.get('horns'):
            for sg in (-1, 1):
                L.curve([(cx + sg * 13, hc - 7), (cx + sg * 24, hc - 11), (cx + sg * 26, hc - 25), (cx + sg * 17, hc - 31)],
                        4, 1, 739)
                for x, y in ((22, -15), (23, -21), (21, -26)):
                    L.line([(cx + sg * x - 1, hc + y), (cx + sg * x + 1, hc + y)], 437)
        getattr(s, 'face_' + r['face'])(L)
        if r.get('nose'):
            L.el(cx, hc + 9, 3, 2, sh); L.px([(cx - 1, hc + 8)], sk)
        if r.get('beard'):
            L.poly([(cx + x, hc + y) for x, y in ((-17, 6), (-10, 8), (-4, 11), (4, 11), (10, 8), (17, 6), (17, 22),
                                                  (10, 36), (0, 42), (-10, 36), (-17, 22))], hair)
            L.line([(cx - 6, hc + 11), (cx, hc + 13), (cx + 6, hc + 11)], r['brow'], 2)
            for x, b in ((-12, 28), (-6, 34), (6, 34), (12, 28)):
                L.line([(cx + x, hc + 15), (cx + x, hc + b)], r['brow'])
            L.line([(cx - 14, hc + 10), (cx - 14, hc + 20)], hair2); L.line([(cx + 14, hc + 10), (cx + 14, hc + 20)], hair2)
            L.line([(cx, hc + 17), (cx, hc + 36)], hair2)
            L.rect(cx - 3, hc + 37, cx + 3, hc + 39, 783); L.poly([(cx - 3, hc + 40), (cx + 3, hc + 40), (cx, hc + 46)], hair)

    def _eyes(s, L, col, w=4, pupil=None):
        cx, hc = s.cx, s.hc
        for sg in (-1, 1):
            x0 = cx + sg * 7 if sg > 0 else cx - 6 - w
            L.rect(x0, hc + 3, x0 + w - 1, hc + 6, col)
            if pupil:
                L.rect(x0 + w // 2, hc + 3, x0 + w // 2, hc + 6, pupil)
            else:
                L.px([(x0 + (0 if sg < 0 else 0), hc + 3)], 'B5200')

    def _brows(s, L, angry=False):
        cx, hc = s.cx, s.hc
        for sg in (-1, 1):
            L.line([(cx + sg * 11, hc + (0 if angry else 1)), (cx + sg * 5, hc + (2 if angry else 1))], s.r['brow'])

    def _smile(s, L, col=None):
        cx, hc = s.cx, s.hc
        L.line([(cx - 4, hc + 11), (cx - 1, hc + 13), (cx + 2, hc + 13), (cx + 5, hc + 11)], col or s.shade)

    def _blush(s, L):
        cx, hc = s.cx, s.hc
        L.px([(cx - 13, hc + 9), (cx - 12, hc + 9), (cx + 12, hc + 9), (cx + 13, hc + 9)], s.r['blush'])

    def face_normal(s, L):
        s._eyes(L, 310); s._brows(L); s._blush(L)
        if not s.r.get('beard'):
            s._smile(L, 3328 if s.shade == 3064 else s.shade)

    def face_glow(s, L):
        s._eyes(L, 444, 5); s._brows(L, True); s._smile(L); s._blush(L)
        L.px([(s.cx - 3, s.hc + 13)], 'B5200')

    def face_drow(s, L):
        s._eyes(L, 321); s._brows(L); s._smile(L)

    def face_orc(s, L):
        cx, hc = s.cx, s.hc
        s._eyes(L, 310); s._brows(L, True)
        L.line([(cx - 5, hc + 12), (cx + 5, hc + 12)], s.shade)
        for sg in (-1, 1):
            L.rect(cx + sg * 6 - (1 if sg > 0 else 0), hc + 9, cx + sg * 6 + (0 if sg > 0 else 1), hc + 12, 'B5200')

    def face_goblin(s, L):
        cx, hc = s.cx, s.hc
        s._eyes(L, 444, 5, 310)
        L.el(cx, hc + 9, 2, 2, s.shade)
        L.rect(cx - 6, hc + 12, cx + 6, hc + 13, 310)
        L.px([(cx - 5, hc + 12), (cx - 2, hc + 12), (cx + 2, hc + 12), (cx + 5, hc + 12), (cx, hc + 13)], 'B5200')

    def face_dragon(s, L):
        cx, hc = s.cx, s.hc
        for sg in (-1, 1):                                     # 뿔
            L.poly([(cx + sg * 6, hc - 13), (cx + sg * 14, hc - 26), (cx + sg * 15, hc - 9)], 739)
            L.poly([(cx + sg * 15, hc - 8), (cx + sg * 23, hc - 16), (cx + sg * 18, hc - 2)], 739)
        L.el(cx, hc + 10, 10, 7, s.r.get('belly', s.shade))     # 주둥이
        L.px([(cx - 3, hc + 7), (cx + 3, hc + 7)], 310)
        L.line([(cx - 6, hc + 12), (cx, hc + 14), (cx + 6, hc + 12)], s.shade)
        L.px([(cx - 5, hc + 13), (cx + 5, hc + 13)], 'B5200')
        s._eyes(L, 444, 4, 310)
        for sg in (-1, 1):
            L.line([(cx + sg * 12, hc), (cx + sg * 5, hc + 2)], s.shade, 2)
        L.px([(cx - 3, hc - 9), (cx + 3, hc - 9), (cx, hc - 5), (cx - 7, hc - 4), (cx + 7, hc - 4)], s.shade)

    def face_illithid(s, L):
        cx, hc = s.cx, s.hc
        for sg in (-1, 1):
            L.poly([(cx + sg * 5, hc + 5), (cx + sg * 12, hc + 1), (cx + sg * 11, hc + 5), (cx + sg * 6, hc + 7)], 'B5200')
        for i, x in enumerate((-9, -3, 3, 9)):
            sg = -1 if x < 0 else 1
            ln = 26 if abs(x) == 3 else 19
            L.curve([(cx + x, hc + 12), (cx + x + sg * 5, hc + 12 + ln // 2), (cx + x - sg * 4, hc + 12 + ln),
                     (cx + x + sg * 3, hc + 14 + ln)], 3, 1, s.skin, 40)
            L.px([(cx + x, hc + 19), (cx + x + sg, hc + 24), (cx + x + sg, hc + 29)], s.shade)

    def face_skull(s, L):
        cx, hc = s.cx, s.hc
        for sg in (-1, 1):
            L.el(cx + sg * 7, hc + 4, 4, 4, 310)
            L.px([(cx + sg * 7, hc + 4)], 321)
        L.poly([(cx, hc + 8), (cx - 2, hc + 11), (cx + 2, hc + 11)], 310)
        L.rect(cx - 7, hc + 13, cx + 7, hc + 13, 310)
        for x in range(-6, 7, 3):
            L.rect(cx + x, hc + 12, cx + x, hc + 15, 310)
        L.line([(cx - 14, hc + 8), (cx - 11, hc + 11)], s.shade); L.line([(cx + 14, hc + 8), (cx + 11, hc + 11)], s.shade)

    def draw(s, im):
        B = Layer(); s.c.back(s, B); s.race_back(B); B.onto(im)
        L = Layer(); s.legs(L); s.c.body(s, L); s.head(L); L.onto(im)
        F = Layer(); s.c.front(s, F); F.onto(im)
        s.c.fx(s, im)


# ================================================================ 직업
class Cls:
    title = ''; bg = 'coast'; legs = 3799; boots = 801; barefoot = False
    frame = (783, 780); tcol = (743, 740)
    def back(s, R, B): pass
    def body(s, R, L): pass
    def hood(s, R, L): pass
    def hat(s, R, L): pass
    def front(s, R, F): pass
    def fx(s, R, im): pass


def sword(F, hx, hy, ln=28, blade=415, guard=783):
    F.rect(hx - 1, hy - ln - 3, hx + 1, hy - 4, blade)
    F.poly([(hx - 1, hy - ln - 3), (hx, hy - ln - 7), (hx + 1, hy - ln - 3)], blade)
    F.line([(hx - 1, hy - ln - 2), (hx - 1, hy - 5)], 'B5200')
    F.rect(hx - 5, hy - 4, hx + 5, hy - 3, guard)
    F.rect(hx - 1, hy - 2, hx + 1, hy + 5, 801); F.rect(hx - 1, hy + 6, hx + 1, hy + 7, guard)


def round_shield(F, x, y, rim, face, emblem):
    F.el(x, y, 12, 13, rim); F.el(x, y, 10, 11, face)
    emblem(F, x, y)


class Fighter(Cls):
    title = 'FIGHTER'; bg = 'coast'; legs = 317; boots = 801; frame = (415, 414); tcol = (743, 740, 'B5200', 415)
    def body(s, R, L):
        cx, sy, bw = R.cx, R.sy, R.bw
        R.torso(L, 414)
        L.poly([(cx - bw + 3, sy + 2), (cx + bw - 3, sy + 2), (cx + bw - 2, sy + 13), (cx - bw + 2, sy + 13)], 415)
        L.line([(cx, sy + 3), (cx, sy + 12)], 414)
        L.rect(cx - bw - 3, R.hip - 3, cx + bw + 3, R.hip, 317)
        R.belt(L, 801); R.pauldrons(L, 415, 414)
    def hat(s, R, L):
        cx, hc = R.cx, R.hc
        L.curve([(cx, hc - 17), (cx + 5, hc - 28), (cx + 16, hc - 24)], 3, 2, 321)
        L.poly([(cx - 18, hc - 1), (cx - 17, hc - 10), (cx - 10, hc - 17), (cx + 10, hc - 17), (cx + 17, hc - 10),
                (cx + 18, hc - 1)], 415)
        L.rect(cx - 18, hc - 4, cx + 18, hc - 1, 414); L.rect(cx - 1, hc - 17, cx + 1, hc + 5, 414)
        L.line([(cx - 13, hc - 8), (cx - 9, hc - 13)], 'B5200')
        L.px([(cx - 14, hc - 3), (cx - 7, hc - 3), (cx + 7, hc - 3), (cx + 14, hc - 3)], 783)
    def front(s, R, F):
        R.arm(F, -1, R.LH, 414); sword(F, *R.LH); R.hand(F, R.LH)
        x, y = R.cx + R.bw + 7, R.sy + 18
        def emblem(F, x, y):
            F.poly([(x - 8, y - 4), (x, y + 4), (x + 8, y - 4), (x + 8, y + 1), (x, y + 9), (x - 8, y + 1)], 'B5200')
            F.el(x, y - 5, 2, 2, 783)
        round_shield(F, x, y, 414, 321, emblem)


class Wizard(Cls):
    title = 'WIZARD'; bg = 'arcane'; boots = 801; frame = (798, 796); tcol = (3325, 798, 743, 972)
    def body(s, R, L):
        cx, sy = R.cx, R.sy
        R.robe(L, 796, 783); R.belt(L, 783, 444, dy=R.ll + 4)
        L.poly([(cx - 4, sy), (cx + 4, sy), (cx, sy + 6)], 783)
        for x, y in ((-6, 12), (5, 30), (-8, 34), (8, 16), (2, 38)):
            if sy + y < R.feet - 6:
                L.px([(cx + x, sy + y)], 743)
    def hat(s, R, L):
        cx, hc = R.cx, R.hc
        L.poly([(cx - 13, hc - 9), (cx + 13, hc - 9), (cx + 5, hc - 30), (cx + 11, hc - 36), (cx + 1, hc - 34)], 796)
        L.el(cx, hc - 8, 22, 4, 796); L.rect(cx - 12, hc - 13, cx + 12, hc - 11, 783)
        L.px([(cx - 3, hc - 20), (cx + 4, hc - 25), (cx + 5, hc - 17), (cx - 6, hc - 16)], 743)
        L.line([(cx - 20, hc - 7), (cx + 20, hc - 7)], 798)
    def front(s, R, F):
        hx, hy = R.LH
        R.arm(F, -1, R.LH, 796)
        F.rect(hx - 1, hy - 34, hx + 1, R.feet + 1, 801)
        F.poly([(hx - 4, hy - 34), (hx - 5, hy - 39), (hx, hy - 36), (hx + 5, hy - 39), (hx + 4, hy - 34)], 783)
        F.el(hx, hy - 40, 4, 4, 996); F.px([(hx - 1, hy - 42), (hx - 2, hy - 41)], 'B5200')
        R.hand(F, R.LH)
        s.rh = (R.cx + R.bw + 10, R.sy + 6)
        R.arm(F, 1, s.rh, 796); R.hand(F, s.rh)
    def fx(s, R, im):
        d = ImageDraw.Draw(im); x, y = s.rh
        for dx, dy, c, big in ((2, -9, 996, True), (8, -4, 743, False), (-4, -14, 743, True), (7, -15, 'B5200', False),
                               (11, -10, 996, False)):
            sparkle(d, x + dx, y + dy, c, big)
        hx, hy = R.LH
        for dx, dy in ((-7, -43), (6, -46), (0, -48)):
            sparkle(d, hx + dx, hy + dy, 3846, False)


class Rogue(Cls):
    title = 'ROGUE'; bg = 'city'; legs = 3799; boots = 938; frame = (414, 317); tcol = (415, 414, 3328, 321)
    def back(s, R, B): R.cloak(B, 317)
    def body(s, R, L):
        cx, sy, bw = R.cx, R.sy, R.bw
        R.torso(L, 801)
        L.line([(cx - bw, sy + 2), (cx + bw + 1, R.hip - 8)], 938, 2)
        for y in range(sy + 6, R.hip - 8, 5):
            L.px([(cx - bw + 3, y)], 783)
        R.belt(L, 938, 783)
        L.rect(cx - bw, sy, cx + bw, sy + 3, 815); L.poly([(cx - 3, sy + 3), (cx + 4, sy + 3), (cx + 2, sy + 9)], 815)
    def hood(s, R, L):
        L.el(R.cx, R.hc - 1, 20, 18, 317)
        L.poly([(R.cx - 20, R.hc), (R.cx + 20, R.hc), (R.cx + 16, R.hc + 15), (R.cx - 16, R.hc + 15)], 317)
    def front(s, R, F):
        l = (R.cx - R.bw - 10, R.sy + 10); r = (R.cx + R.bw + 10, R.sy + 16)
        R.arm(F, -1, l, 801); R.arm(F, 1, r, 801)
        for (hx, hy), sg in ((l, -1), (r, 1)):
            F.poly([(hx - 1, hy - 4), (hx - 1, hy - 13), (hx, hy - 16), (hx + 1, hy - 13), (hx + 1, hy - 4)], 415)
            F.line([(hx - 1, hy - 12), (hx - 1, hy - 5)], 'B5200')
            F.rect(hx - 3, hy - 4, hx + 3, hy - 3, 783); F.rect(hx - 1, hy - 2, hx + 1, hy + 4, 938)
            R.hand(F, (hx, hy))


class Cleric(Cls):
    title = 'CLERIC'; bg = 'coast'; legs = 317; boots = 801; frame = (415, 414); tcol = (743, 740, 'B5200', 415)
    def body(s, R, L):
        cx, sy, bw = R.cx, R.sy, R.bw
        R.torso(L, 414)
        for y in range(sy + 3, R.hip - 1, 3):
            for x in range(cx - bw - 1 + (y % 2) * 2, cx + bw + 2, 4):
                L.px([(x, y)], 415)
        L.poly([(cx - 6, sy), (cx + 6, sy), (cx + 8, R.hip + 3), (cx - 8, R.hip + 3)], 'B5200')
        L.rect(cx - 1, sy + 5, cx + 1, sy + 15, 783); L.rect(cx - 4, sy + 8, cx + 4, sy + 10, 783)
        R.belt(L, 801); R.pauldrons(L, 415, 414)
    def hat(s, R, L):
        cx, hc = R.cx, R.hc
        L.line([(cx - 14, hc - 6), (cx + 14, hc - 6)], 783); L.rect(cx - 1, hc - 8, cx + 1, hc - 6, 996)
    def front(s, R, F):
        hx, hy = R.LH
        R.arm(F, -1, R.LH, 414)
        F.rect(hx - 1, hy - 22, hx + 1, hy + 6, 801)
        F.el(hx, hy - 26, 5, 5, 414); F.el(hx - 1, hy - 27, 3, 3, 415)
        for dx, dy in ((-6, -26), (6, -26), (0, -32), (-4, -30), (4, -30), (-4, -22), (4, -22)):
            F.rect(hx + dx - 1, hy + dy - 1, hx + dx + 1, hy + dy + 1, 414)
        R.hand(F, R.LH)
        def emblem(F, x, y):
            F.rect(x - 1, y - 8, x + 1, y + 8, 444); F.rect(x - 6, y - 4, x + 6, y - 2, 444)
        round_shield(F, R.cx + R.bw + 7, R.sy + 18, 783, 796, emblem)


class Bard(Cls):
    title = 'BARD'; bg = 'city'; legs = 796; boots = 801; frame = (3607, 718); tcol = (3607, 718, 743, 972)
    def body(s, R, L):
        cx, sy, bw = R.cx, R.sy, R.bw
        R.torso(L, 718)
        L.poly([(cx - 4, sy), (cx + 4, sy), (cx, sy + 9)], 'B5200')
        L.line([(cx - bw - 3, R.hip), (cx + bw + 3, R.hip)], 783)
        R.belt(L, 783, 972)
        for y in range(sy + 11, R.hip - 8, 4):
            L.px([(cx, y)], 783)
    def hat(s, R, L):
        cx, hc = R.cx, R.hc
        L.curve([(cx + 9, hc - 13), (cx + 20, hc - 20), (cx + 24, hc - 31)], 2, 1, 'B5200')
        L.el(cx - 1, hc - 13, 17, 6, 718); L.el(cx - 4, hc - 16, 12, 5, 3607)
        L.el(cx + 9, hc - 12, 2, 2, 783)
    def front(s, R, F):
        cx, sy, bw = R.cx, R.sy, R.bw
        F.line([(cx + 2, sy + 16), (cx - 23, sy + 1)], 801, 3)
        F.rect(cx - 27, sy - 3, cx - 22, sy + 1, 801)
        F.el(cx + 7, sy + 19, 11, 9, 435); F.el(cx + 8, sy + 20, 9, 7, 437); F.el(cx + 6, sy + 18, 3, 3, 801)
        F.line([(cx - 20, sy + 3), (cx + 14, sy + 23)], 739)
        F.px([(cx - 28, sy - 3), (cx - 28, sy), (cx - 21, sy - 4)], 783)
        l = (cx - bw - 3, sy + 8); r = (cx + bw + 3, sy + 21)
        F.curve([(cx - bw - 1, sy + 3), (cx - bw - 7, sy + 10), l], 3, 3, 718, 20); R.hand(F, l)
        F.curve([(cx + bw + 1, sy + 3), (cx + bw + 8, sy + 12), r], 3, 3, 718, 20); R.hand(F, r)
    def fx(s, R, im):
        d = ImageDraw.Draw(im)
        for x, y in ((10, R.sy - 12), (87, R.sy - 22), (84, R.sy + 2)):
            d.rectangle([x, y + 5, x + 2, y + 7], fill=C(3078)); d.line([(x + 2, y), (x + 2, y + 6)], fill=C(3078))
            d.line([(x + 2, y), (x + 5, y + 2)], fill=C(3078))


class Ranger(Cls):
    title = 'RANGER'; bg = 'forest'; legs = 801; boots = 938; frame = (988, 986); tcol = (3348, 988, 743, 972)
    def back(s, R, B):
        cx, sy, bw = R.cx, R.sy, R.bw
        B.poly([(cx + bw - 1, sy - 7), (cx + bw + 6, sy - 9), (cx + bw + 9, sy + 9), (cx + bw + 2, sy + 11)], 801)
        for dx in (0, 3, 6):
            B.line([(cx + bw + dx, sy - 9), (cx + bw + dx + 2, sy - 16)], 739)
            B.rect(cx + bw + dx + 1, sy - 18, cx + bw + dx + 3, sy - 15, 321)
        R.cloak(B, 986)
    def body(s, R, L):
        cx, sy, bw = R.cx, R.sy, R.bw
        R.torso(L, 988)
        L.poly([(cx - bw + 2, sy + 2), (cx - 2, sy + 2), (cx - 3, R.hip - 7), (cx - bw, R.hip - 7)], 433)
        L.poly([(cx + bw - 2, sy + 2), (cx + 2, sy + 2), (cx + 3, R.hip - 7), (cx + bw, R.hip - 7)], 433)
        L.line([(cx + bw, sy + 1), (cx - bw - 1, R.hip - 9)], 801, 2)
        R.belt(L, 801)
        L.rect(cx - bw, sy, cx + bw, sy + 2, 986)
    def hood(s, R, L):
        L.el(R.cx, R.hc - 1, 20, 18, 986)
        L.poly([(R.cx - 20, R.hc), (R.cx + 20, R.hc), (R.cx + 16, R.hc + 15), (R.cx - 16, R.hc + 15)], 986)
        L.poly([(R.cx - 4, R.hc - 18), (R.cx, R.hc - 23), (R.cx + 4, R.hc - 18)], 986)
    def front(s, R, F):
        hx, hy = R.LH
        R.arm(F, -1, R.LH, 988)
        bx = hx + 4
        F.curve([(bx - 1, hy - 26), (bx - 15, hy), (bx - 1, hy + 26)], 1, 1, 801, 60)
        F.line([(bx - 1, hy - 26), (bx - 1, hy + 26)], 739)
        R.hand(F, (hx, hy))
        r = (R.cx + R.bw + 10, R.sy + 14)
        R.arm(F, 1, r, 988)
        F.line([(r[0], r[1] + 8), (r[0], r[1] - 18)], 739)
        F.poly([(r[0] - 2, r[1] - 18), (r[0], r[1] - 23), (r[0] + 2, r[1] - 18)], 415)
        F.rect(r[0] - 1, r[1] + 5, r[0] + 1, r[1] + 9, 321)
        R.hand(F, r)


class Paladin(Cls):
    title = 'PALADIN'; bg = 'mountain'; legs = 414; boots = 317; frame = (783, 780); tcol = ('B5200', 415, 743, 972)
    def back(s, R, B): R.cloak(B, 796)
    def body(s, R, L):
        cx, sy, bw = R.cx, R.sy, R.bw
        R.torso(L, 415)
        L.poly([(cx - bw + 2, sy + 2), (cx + bw - 2, sy + 2), (cx + bw - 1, sy + 12), (cx - bw + 1, sy + 12)], 'B5200')
        L.line([(cx - bw - 1, sy + 14), (cx + bw + 1, sy + 14)], 783)
        L.rect(cx - bw - 3, R.hip - 3, cx + bw + 3, R.hip, 414); L.line([(cx - bw - 3, R.hip), (cx + bw + 3, R.hip)], 783)
        R.belt(L, 783, 444); R.pauldrons(L, 'B5200', 783)
        L.rect(cx - bw, sy, cx + bw, sy + 1, 783)
    def hat(s, R, L):
        cx, hc = R.cx, R.hc
        L.line([(cx - 14, hc - 6), (cx + 14, hc - 6)], 783); L.px([(cx, hc - 7), (cx, hc - 8)], 444)
    def front(s, R, F):
        cx, y = R.cx, R.sy + 11
        R.arm(F, -1, (cx - 4, y), 415); R.arm(F, 1, (cx + 4, y), 415)
        F.rect(cx - 2, y + 5, cx + 2, R.feet - 4, 415)
        F.poly([(cx - 2, R.feet - 4), (cx + 2, R.feet - 4), (cx, R.feet + 1)], 415)
        F.line([(cx, y + 6), (cx, R.feet - 3)], 'B5200')
        F.rect(cx - 9, y + 3, cx + 9, y + 5, 783); F.rect(cx - 1, y - 7, cx + 1, y + 2, 801)
        F.el(cx, y - 8, 2, 2, 783)
        R.hand(F, (cx - 4, y)); R.hand(F, (cx + 4, y))
    def fx(s, R, im):
        d = ImageDraw.Draw(im)
        for dx, dy in ((-12, 22), (13, 30), (-9, 38)):
            if R.sy + dy < R.feet - 6:
                sparkle(d, R.cx + dx, R.sy + dy, 3078, False)


class Barbarian(Cls):
    title = 'BARBARIAN'; bg = 'snow'; legs = 'skin'; boots = 433; frame = (435, 433); tcol = (3325, 809, 3328, 321)
    def body(s, R, L):
        cx, sy, bw = R.cx, R.sy, R.bw
        R.torso(L, R.skin)
        L.line([(cx - 6, sy + 13), (cx - 1, sy + 14)], R.shade); L.line([(cx + 6, sy + 13), (cx + 1, sy + 14)], R.shade)
        L.px([(cx, sy + 19), (cx, sy + 20)], R.shade)
        L.poly([(cx - bw - 3, R.hip - 9), (cx + bw + 3, R.hip - 9), (cx + bw + 4, R.hip + 3), (cx + 4, R.hip + 5),
                (cx, R.hip + 2), (cx - 4, R.hip + 5), (cx - bw - 4, R.hip + 3)], 433)
        for x in range(cx - bw - 1, cx + bw + 2, 4):
            L.px([(x, R.hip - 3), (x + 2, R.hip)], 435)
        R.belt(L, 801, 739, dy=10)
        L.el(cx, sy + 2, bw + 6, 5, 435)
        for x in range(cx - bw - 4, cx + bw + 5, 3):
            L.px([(x, sy + 3), (x + 1, sy + 5)], 433)
    def hat(s, R, L):
        cx, hc = R.cx, R.hc
        L.line([(cx - 13, hc + 8), (cx - 8, hc + 8)], 796); L.line([(cx + 8, hc + 8), (cx + 13, hc + 8)], 796)
    def front(s, R, F):
        hx, hy = R.LH
        R.arm(F, -1, R.LH, 'skin')
        F.rect(hx - 1, hy - 32, hx + 1, hy + 16, 801)
        F.poly([(hx + 2, hy - 33), (hx + 11, hy - 38), (hx + 13, hy - 28), (hx + 11, hy - 19), (hx + 2, hy - 24)], 415)
        F.poly([(hx - 2, hy - 33), (hx - 11, hy - 38), (hx - 13, hy - 28), (hx - 11, hy - 19), (hx - 2, hy - 24)], 414)
        F.line([(hx + 11, hy - 36), (hx + 12, hy - 28), (hx + 11, hy - 21)], 'B5200')
        F.rect(hx - 2, hy - 30, hx + 2, hy - 27, 783)
        R.hand(F, R.LH)
        r = (R.cx + R.bw + 10, R.sy + 2)
        R.arm(F, 1, r, 'skin'); R.hand(F, r)
        F.rect(r[0] - 3, r[1] + 4, r[0] + 3, r[1] + 5, 783)


class Druid(Cls):
    title = 'DRUID'; bg = 'forest'; boots = 801; frame = (988, 986); tcol = (3348, 988, 743, 972)
    def body(s, R, L):
        cx, sy, bw = R.cx, R.sy, R.bw
        R.robe(L, 433, 801)
        L.poly([(cx - bw - 2, sy), (cx + bw + 2, sy), (cx + bw + 3, sy + 8), (cx, sy + 13), (cx - bw - 3, sy + 8)], 986)
        L.px([(cx - 5, sy + 4), (cx + 4, sy + 6), (cx, sy + 9), (cx + 7, sy + 3), (cx - 8, sy + 6)], 988)
        R.belt(L, 739, 739, dy=R.ll + 4)
        L.line([(cx + 2, R.hip - R.ll - 2), (cx + 3, R.hip - R.ll + 5)], 739)
    def hat(s, R, L):
        cx, hc = R.cx, R.hc
        for sg in (-1, 1):
            L.curve([(cx + sg * 9, hc - 12), (cx + sg * 12, hc - 22), (cx + sg * 20, hc - 28)], 2, 1, 739, 24)
            L.line([(cx + sg * 12, hc - 20), (cx + sg * 8, hc - 27)], 739, 2)
            L.line([(cx + sg * 16, hc - 25), (cx + sg * 22, hc - 22)], 739, 2)
        L.line([(cx - 14, hc - 7), (cx + 14, hc - 7)], 986)
        for x in (-12, -6, 0, 6, 12):
            L.px([(cx + x, hc - 8), (cx + x + 1, hc - 9)], 988)
    def front(s, R, F):
        hx, hy = R.LH
        R.arm(F, -1, R.LH, 433)
        F.rect(hx - 1, hy - 30, hx + 1, R.feet + 1, 801)
        F.curve([(hx, hy - 30), (hx - 1, hy - 40), (hx + 8, hy - 40), (hx + 6, hy - 33)], 1, 1, 801, 30)
        for dx, dy in ((-4, -36), (9, -38), (3, -43), (-3, -20), (3, -8)):
            F.rect(hx + dx - 1, hy + dy, hx + dx + 1, hy + dy + 1, 988); F.px([(hx + dx, hy + dy - 1)], 3348)
        R.hand(F, R.LH)
        s.rh = (R.cx + R.bw + 10, R.sy + 8)
        R.arm(F, 1, s.rh, 433); R.hand(F, s.rh)
        x, y = s.rh
        F.poly([(x - 4, y - 5), (x - 3, y - 12), (x, y - 16), (x + 3, y - 12), (x + 4, y - 5)], 988)
        F.poly([(x - 2, y - 5), (x, y - 12), (x + 2, y - 5)], 3348)
    def fx(s, R, im):
        d = ImageDraw.Draw(im); x, y = s.rh
        for dx, dy in ((-7, -18), (7, -20), (1, -24)):
            sparkle(d, x + dx, y + dy, 3348, False)


class Monk(Cls):
    title = 'MONK'; bg = 'mountain'; legs = 921; boots = 801; barefoot = True
    frame = (740, 921); tcol = (743, 740, 'B5200', 415)
    def body(s, R, L):
        cx, sy, bw = R.cx, R.sy, R.bw
        R.torso(L, 740)
        L.poly([(cx - 5, sy), (cx + 5, sy), (cx, sy + 11)], R.skin)
        L.line([(cx - 5, sy), (cx, sy + 11)], 921); L.line([(cx + 5, sy), (cx, sy + 11)], 921)
        L.rect(cx - bw - 2, R.hip - 9, cx + bw + 2, R.hip - 6, 815)
        L.poly([(cx + 3, R.hip - 6), (cx + 7, R.hip - 6), (cx + 9, R.hip + 5), (cx + 4, R.hip + 5)], 815)
        L.line([(cx - bw - 3, R.hip), (cx + bw + 3, R.hip)], 921)
    def hat(s, R, L):
        cx, hc = R.cx, R.hc
        L.rect(cx - 15, hc - 6, cx + 15, hc - 4, 815)
        L.curve([(cx + 15, hc - 5), (cx + 22, hc - 2), (cx + 25, hc + 6)], 1, 1, 815, 20)
        L.curve([(cx + 15, hc - 5), (cx + 24, hc - 7), (cx + 28, hc - 2)], 1, 1, 815, 20)
    def front(s, R, F):
        l = (R.cx - R.bw - 11, R.sy + 6); r = (R.cx + R.bw + 9, R.sy + 16)
        R.arm(F, -1, l, 'skin'); R.arm(F, 1, r, 'skin')
        for p in (l, r):
            F.el(p[0], p[1], 4, 4, 739); F.line([(p[0] - 3, p[1]), (p[0] + 3, p[1])], 437)
    def fx(s, R, im):
        d = ImageDraw.Draw(im); x, y = R.cx - R.bw - 11, R.sy + 6
        for dx, dy in ((-7, -5), (-8, 3), (-3, -8)):
            if x + dx > 5:
                sparkle(d, x + dx, y + dy, 3846, False)


def flame(F, x, y, a=740, b=444):
    F.poly([(x - 5, y), (x - 4, y - 7), (x - 1, y - 5), (x + 1, y - 13), (x + 4, y - 6), (x + 5, y)], a)
    F.poly([(x - 2, y), (x, y - 7), (x + 2, y)], b)
    F.el(x, y, 5, 3, a); F.el(x, y, 2, 2, b)


class Sorcerer(Cls):
    title = 'SORCERER'; bg = 'arcane'; boots = 938; frame = (321, 815); tcol = (743, 740, 3328, 321)
    def body(s, R, L):
        cx, sy, bw = R.cx, R.sy, R.bw
        R.robe(L, 815, 783)
        L.poly([(cx - 5, sy), (cx + 5, sy), (cx, sy + 8)], 783)
        L.line([(cx, sy + 9), (cx, R.feet - 5)], 783)
        R.belt(L, 743, 444, dy=R.ll + 4)
        L.rect(cx - bw, sy, cx - bw + 2, sy + 2, 783); L.rect(cx + bw - 2, sy, cx + bw, sy + 2, 783)
    def front(s, R, F):
        for sg in (-1, 1):
            h = (R.cx + sg * (R.bw + 11), R.sy + 5)
            R.arm(F, sg, h, 815); R.hand(F, h)
            flame(F, h[0], h[1] - 7)
    def fx(s, R, im):
        d = ImageDraw.Draw(im)
        for sg in (-1, 1):
            x, y = R.cx + sg * (R.bw + 11), R.sy - 2
            for dx, dy in ((-5, -16), (4, -19), (0, -23)):
                d.point((x + dx, y + dy), fill=C(740))


class Warlock(Cls):
    title = 'WARLOCK'; bg = 'arcane'; boots = 938; frame = (552, 550); tcol = (554, 552, 964, 3846)
    def back(s, R, B):
        cx, sy, bw = R.cx, R.sy, R.bw
        B.poly([(cx - bw - 8, sy - 10), (cx - bw, sy + 2), (cx + bw, sy + 2), (cx + bw + 8, sy - 10),
                (cx + bw + 10, R.feet - 5), (cx - bw - 10, R.feet - 5)], 550)
    def body(s, R, L):
        cx, sy, bw = R.cx, R.sy, R.bw
        R.robe(L, 3799, 552)
        L.poly([(cx - 5, sy), (cx + 5, sy), (cx, sy + 7)], 552)
        L.line([(cx - 3, sy + 8), (cx, sy + 13), (cx + 3, sy + 8)], 783)
        L.el(cx, sy + 14, 2, 2, 3846)
        R.belt(L, 552, 783, dy=R.ll + 4)
    def front(s, R, F):
        l = (R.cx - R.bw - 5, R.sy + 15)
        R.arm(F, -1, l, 3799)
        F.rect(l[0] - 6, l[1] - 6, l[0] + 3, l[1] + 5, 550); F.rect(l[0] - 5, l[1] - 5, l[0] - 4, l[1] + 4, 552)
        F.el(l[0] - 0, l[1] - 1, 2, 2, 3846); F.px([(l[0] + 2, l[1] - 5), (l[0] + 2, l[1] + 4)], 783)
        R.hand(F, (l[0] + 3, l[1] + 3))
        s.rh = (R.cx + R.bw + 10, R.sy + 7)
        R.arm(F, 1, s.rh, 3799); R.hand(F, s.rh)
        x, y = s.rh
        F.el(x, y - 10, 5, 5, 552); F.el(x, y - 10, 3, 3, 3846); F.px([(x - 1, y - 11)], 'B5200')
    def fx(s, R, im):
        d = ImageDraw.Draw(im); x, y = s.rh
        for dx, dy, big in ((-8, -14, False), (8, -16, True), (0, -20, False), (9, -6, False)):
            sparkle(d, x + dx, y + dy, 3846, big)


class Flayer(Cls):
    """마인드 플레이어 전용 로브"""
    title = ''; bg = 'dungeon'; boots = 938; frame = (552, 550); tcol = (554, 552)
    def back(s, R, B):
        cx, sy, bw = R.cx, R.sy, R.bw
        B.poly([(cx - bw - 10, sy - 14), (cx - bw, sy + 2), (cx + bw, sy + 2), (cx + bw + 10, sy - 14),
                (cx + bw + 9, R.feet - 5), (cx - bw - 9, R.feet - 5)], 550)
    def body(s, R, L):
        cx, sy = R.cx, R.sy
        R.robe(L, 3799, 783)
        L.line([(cx, sy + 20), (cx, R.feet - 5)], 552)
        R.belt(L, 783, 996, dy=R.ll + 2)
    def front(s, R, F):
        for sg in (-1, 1):
            h = (R.cx + sg * (R.bw + 11), R.sy + 7)
            R.arm(F, sg, h, 3799); R.hand(F, h)
            for k in (-1, 0, 1):
                F.line([(h[0] + k * 2, h[1] - 3), (h[0] + k * 3, h[1] - 7)], R.skin)
    def fx(s, R, im):
        d = ImageDraw.Draw(im)
        for r_ in (24, 30):
            d.arc([R.cx - r_, R.hc - r_ - 2, R.cx + r_, R.hc + r_ - 2], 200, 250, fill=C(996))
            d.arc([R.cx - r_, R.hc - r_ - 2, R.cx + r_, R.hc + r_ - 2], 290, 340, fill=C(996))


class Raider(Rogue):
    """고블린 약탈자 (후드 없음)"""
    title = ''; bg = 'forest'; frame = (988, 986); tcol = (3348, 988)
    def back(s, R, B): pass
    def hood(s, R, L): pass


CLASSES = {c.title.lower(): c for c in (Fighter, Wizard, Rogue, Cleric, Bard, Ranger, Paladin, Barbarian, Druid,
                                        Monk, Sorcerer, Warlock)}


def character(race, cls, skin=None, hair=None, bg=None, lines=None):
    c = (CLASSES[cls] if isinstance(cls, str) else cls)()
    im = new()
    BGS[bg or c.bg](im)
    Rig(race, c, skin, hair).draw(im)
    title(im, lines or [RACES[race]['title'], c.title], c.tcol)
    frame(im, *c.frame)
    return im


# ================================================================ 몬스터
def owlbear(bg=None):
    im = new(); BGS[bg or 'forest'](im)
    L = Layer()
    L.el(35, 119, 10, 5, 801); L.el(65, 119, 10, 5, 801)
    L.el(50, 92, 30, 28, 801); L.el(49, 90, 28, 26, 433)
    L.el(50, 96, 18, 20, 435); L.el(50, 94, 16, 18, 437)
    for x, y in [(42, 84), (50, 86), (58, 84), (38, 93), (46, 95), (54, 95), (62, 93),
                 (42, 103), (50, 105), (58, 103), (46, 112), (54, 112)]:
        L.px([(x - 1, y), (x, y + 1), (x + 1, y)], 435)
    L.el(21, 92, 8, 17, 801); L.el(79, 92, 8, 17, 801)
    L.el(20, 90, 5, 13, 433); L.el(78, 90, 5, 13, 433)
    L.poly([(30, 40), (23, 19), (42, 32)], 801); L.poly([(70, 40), (77, 19), (58, 32)], 801)
    L.poly([(30, 36), (26, 24), (37, 32)], 433); L.poly([(70, 36), (74, 24), (63, 32)], 433)
    L.el(50, 51, 26, 21, 801); L.el(50, 49, 25, 19, 433)
    L.el(39, 52, 12, 12, 437); L.el(61, 52, 12, 12, 437)
    L.el(39, 52, 7, 7, 972); L.el(61, 52, 7, 7, 972)
    L.el(39, 52, 6, 6, 444); L.el(61, 52, 6, 6, 444)
    L.el(40, 52, 3, 3, 310); L.el(60, 52, 3, 3, 310)
    L.px([(39, 50), (59, 50)], 'B5200')
    L.line([(29, 41), (38, 43), (46, 47)], 801, 2); L.line([(71, 41), (62, 43), (54, 47)], 801, 2)
    L.poly([(45, 57), (55, 57), (50, 70)], 740); L.poly([(47, 62), (53, 62), (50, 70)], 921)
    L.px([(49, 59), (51, 59)], 310)
    L.onto(im)
    d = ImageDraw.Draw(im)
    for x in (28, 33, 38, 62, 67, 72):
        d.line([(x, 121), (x, 124)], fill=C(739)); d.point((x, 125), fill=K)
    for x in (16, 20, 24, 76, 80, 84):
        d.line([(x, 107), (x, 110)], fill=C(739)); d.point((x, 111), fill=K)
    title(im, ['OWL', 'BEAR'], (743, 740))
    frame(im, 783, 780)
    return im


def gelatinous_cube(bg=None):
    im = new(); BGS[bg or 'dungeon'](im)
    L = Layer()
    L.el(50, 108, 36, 6, 700)
    L.rect(19, 54, 69, 106, 704)
    L.poly([(19, 54), (31, 40), (81, 40), (69, 54)], 907)
    L.poly([(69, 54), (81, 40), (81, 92), (69, 106)], 702)
    L.line([(19, 54), (69, 54)], 772); L.line([(69, 54), (69, 106)], 700); L.line([(69, 54), (81, 40)], 772)
    for k in range(5):
        L.line([(23 + k, 70 - k * 2), (27 + k, 62 - k * 2)], 772)
    L.line([(24, 76), (24, 80)], 772); L.line([(36, 44), (48, 44)], 772); L.line([(74, 50), (78, 46)], 704)
    for x, y in ((60, 62), (30, 92), (63, 84), (44, 60), (75, 70)):
        L.px([(x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)], 772)
    L.rect(26, 106, 28, 110, 704); L.rect(55, 106, 58, 111, 704); L.rect(74, 99, 76, 106, 702)
    L.onto(im)
    I = Layer()
    I.el(38, 74, 7, 6, 'B5200'); I.rect(34, 78, 42, 82, 'B5200')
    I.rect(34, 73, 36, 75, 700); I.rect(40, 73, 42, 75, 700); I.px([(38, 77)], 700)
    I.px([(35, 82), (37, 82), (39, 82), (41, 82)], 700)
    I.line([(28, 98), (40, 92)], 'B5200', 2); I.el(28, 98, 1, 1, 'B5200'); I.el(41, 91, 1, 1, 'B5200')
    I.line([(46, 99), (62, 66)], 415, 2); I.line([(45, 96), (51, 100)], 783, 2); I.line([(43, 103), (46, 99)], 801, 2)
    for x, y in ((54, 101), (60, 99), (64, 102), (57, 96)):
        I.el(x, y, 2, 1, 444); I.px([(x + 1, y + 1)], 972)
    I.el(57, 80, 5, 4, 414); I.rect(52, 80, 62, 82, 414); I.line([(53, 79), (60, 79)], 415)
    im.alpha_composite(I.im)
    title(im, ['GELATINOUS', 'CUBE'], (907, 704))
    frame(im, 702, 700)
    return im


def red_dragon(bg=None):
    im = new(); BGS[bg or 'mountain'](im)
    B = Layer()
    B.poly([(34, 74), (6, 34), (10, 58), (3, 60), (10, 72), (5, 78), (14, 86), (30, 92)], 815)   # 날개
    B.poly([(32, 76), (10, 42), (14, 62), (9, 64), (15, 72), (12, 78), (18, 83), (30, 88)], 321)
    B.line([(32, 76), (14, 62)], 815); B.line([(32, 78), (15, 72)], 815)
    B.mirror()
    B.curve([(62, 106), (88, 122), (96, 100), (88, 92)], 5, 1, 321)                              # 꼬리
    B.poly([(88, 84), (83, 93), (93, 93)], 815)
    B.el(50, 118, 34, 6, 783)                                                                    # 보물 더미
    B.onto(im)
    L = Layer()
    L.el(36, 117, 9, 5, 815); L.el(64, 117, 9, 5, 815)
    L.el(50, 94, 23, 24, 815); L.el(49, 92, 21, 22, 321)
    L.el(50, 98, 12, 17, 743)
    for y in range(86, 114, 4):
        L.line([(50 - 10 + abs(y - 98) // 3, y), (50 + 10 - abs(y - 98) // 3, y)], 972)
    L.el(29, 94, 5, 9, 321); L.el(71, 94, 5, 9, 321)
    for sg in (-1, 1):                                                                           # 뿔
        L.curve([(50 + sg * 13, 40), (50 + sg * 20, 30), (50 + sg * 18, 18)], 4, 1, 739, 24)
    for x in (-6, 0, 6):
        L.poly([(50 + x - 3, 36), (50 + x, 29), (50 + x + 3, 36)], 815)
    L.el(50, 52, 23, 18, 815); L.el(50, 50, 22, 16, 321)
    L.el(50, 60, 13, 8, 3328)
    L.px([(45, 56), (55, 56)], 310)
    L.line([(40, 63), (50, 66), (60, 63)], 815)
    L.px([(43, 65), (57, 65), (47, 66), (53, 66)], 'B5200')
    for sg in (-1, 1):
        L.el(50 + sg * 10, 47, 4, 4, 444); L.rect(50 + sg * 10, 44, 50 + sg * 10, 50, 310)
        L.line([(50 + sg * 16, 40), (50 + sg * 6, 44)], 815, 2)
    L.px([(44, 40), (56, 40), (50, 42)], 815)
    L.onto(im)
    d = ImageDraw.Draw(im)
    for x, y in ((22, 116), (30, 121), (44, 122), (58, 121), (70, 122), (79, 117), (38, 119), (66, 118)):
        d.rectangle([x, y, x + 1, y], fill=C(444))
    for x, y in ((26, 119), (74, 120), (50, 121)):
        d.point((x, y), fill=C(321))
    for x in (30, 28, 70, 72):
        d.point((x, 104), fill=C(739))
    title(im, ['RED', 'DRAGON'], (3328, 321, 743, 972))
    frame(im, 321, 815)
    return im


MONSTERS = {
    'owlbear': owlbear,
    'gelatinous cube': gelatinous_cube,
    'red dragon': red_dragon,
    'mind flayer': lambda bg=None: character('illithid', Flayer, bg=bg, lines=['MIND', 'FLAYER']),
    'skeleton': lambda bg=None: character('skeleton', 'fighter', bg=bg or 'dungeon', lines=['SKELETON']),
    'goblin': lambda bg=None: character('goblin', Raider, bg=bg, lines=['GOBLIN']),
}

# ================================================================ 이름 해석
KO = {
    '인간': 'human', '휴먼': 'human', '엘프': 'elf', '하프엘프': 'half-elf', '드워프': 'dwarf', '하플링': 'halfling',
    '노움': 'gnome', '하프오크': 'half-orc', '티플링': 'tiefling', '드로우': 'drow', '드래곤본': 'dragonborn',
    '고블린': 'goblin',
    '파이터': 'fighter', '전사': 'fighter', '위저드': 'wizard', '마법사': 'wizard', '로그': 'rogue', '도적': 'rogue',
    '클레릭': 'cleric', '성직자': 'cleric', '바드': 'bard', '레인저': 'ranger', '팔라딘': 'paladin', '성기사': 'paladin',
    '바바리안': 'barbarian', '야만전사': 'barbarian', '드루이드': 'druid', '몽크': 'monk', '수도승': 'monk',
    '소서러': 'sorcerer', '워락': 'warlock',
    '아울베어': 'owlbear', '젤라틴큐브': 'gelatinous cube', '레드드래곤': 'red dragon', '마인드플레이어': 'mind flayer',
    '스켈레톤': 'skeleton', '해골': 'skeleton',
}


def norm(s):
    return re.sub(r'[\s\-_]+', '', s.lower())


def resolve(words):
    """['티플링','바드'] -> ('char','tiefling','bard') / ['아울베어'] -> ('monster','owlbear')"""
    key = norm(''.join(words))
    table = {norm(k): v for k, v in KO.items()}
    for group in (MONSTERS, RACES, CLASSES):
        table.update({norm(k): k for k in group})
    races = {k: v for k, v in table.items() if v in RACES and v not in HIDDEN_RACES}
    for rk, race in sorted(races.items(), key=lambda t: -len(t[0])):
        if key.startswith(rk) and table.get(key[len(rk):]) in CLASSES:
            return ('char', race, table[key[len(rk):]])
        if key.endswith(rk) and table.get(key[:-len(rk)]) in CLASSES:
            return ('char', race, table[key[:-len(rk)]])
    if table.get(key) in MONSTERS:
        return ('monster', table[key])
    return None


def save(name, im, extras=True):
    out = os.path.join(HERE, 'out'); os.makedirs(out, exist_ok=True)
    rgb = im.convert('RGB')
    a = np.array(rgb).reshape(-1, 3)
    cols, counts = np.unique(a, axis=0, return_counts=True)
    lines = []
    for c, n in sorted(zip(map(tuple, cols.tolist()), counts.tolist()), key=lambda t: -t[1]):
        assert c in RGB2CODE, f'{name}: DMC 에 없는 색 {c}'
        code = RGB2CODE[c]
        lines.append(f'DMC {code:<6} {DMC[code][0]:<32} #{DMC[code][1]}  {n:>5}땀')
    rgb.save(os.path.join(out, f'{name}.png'))
    if extras:
        rgb.resize((W * 8, H * 8), Image.NEAREST).save(os.path.join(out, f'{name}_x8.png'))
        with open(os.path.join(out, f'{name}_colors.txt'), 'w', encoding='utf-8') as f:
            f.write(f'{name}  {W} x {H}칸  {len(lines)}색\n' + '\n'.join(lines) + '\n')
    return rgb, len(lines)


def sheet(cards, cols, path, scale=2):
    rows = (len(cards) + cols - 1) // cols
    sh = Image.new('RGB', (cols * (W + 4) + 4, rows * (H + 4) + 4), (40, 40, 40))
    for i, im in enumerate(cards):
        sh.paste(im, (4 + (i % cols) * (W + 4), 4 + (i // cols) * (H + 4)))
    sh.resize((sh.width * scale, sh.height * scale), Image.NEAREST).save(path)


def main():
    ap = argparse.ArgumentParser(description='소드코스트 캐릭터 카드 십자수 도안 (100x180칸)')
    ap.add_argument('name', nargs='*', help='종족 직업 (예: 티플링 바드) 또는 몬스터 이름 (예: 아울베어)')
    ap.add_argument('--skin', help='피부색 DMC 번호')
    ap.add_argument('--hair', help='머리색 DMC 번호')
    ap.add_argument('--bg', choices=sorted(BGS), help='배경 바꾸기')
    ap.add_argument('--list', action='store_true', help='쓸 수 있는 이름 보기')
    ap.add_argument('--all', action='store_true', help='모든 조합 생성 + gallery_*.png')
    a = ap.parse_args()
    races = [r for r in RACES if r not in HIDDEN_RACES]
    if a.list or not (a.name or a.all):
        ko = lambda v: '/'.join(k for k, x in KO.items() if x == v)
        print('종족  :', ', '.join(f'{r}({ko(r)})' for r in races))
        print('직업  :', ', '.join(f'{c}({ko(c)})' for c in CLASSES))
        print('몬스터:', ', '.join(f'{m}({ko(m)})' if ko(m) else m for m in MONSTERS))
        print('배경  :', ', '.join(f'{k} - {f.__doc__}' for k, f in BGS.items()))
        return
    if a.all:
        for c in CLASSES:
            row = [save(f'{norm(r)}_{c}', character(r, c), extras=False)[0] for r in races]
            sheet(row, len(races), os.path.join(HERE, f'gallery_{c}.png'), 1)
        mons = [save(m.replace(' ', '_'), f(), extras=False)[0] for m, f in MONSTERS.items()]
        sheet(mons, len(mons), os.path.join(HERE, 'gallery_monsters.png'), 1)
        print(len(races) * len(CLASSES) + len(MONSTERS), '장 생성 -> cards/out/, cards/gallery_*.png')
        return
    r = resolve(a.name)
    if not r:
        sys.exit(f'알 수 없는 이름: {" ".join(a.name)}  (--list 로 목록 확인)')
    if r[0] == 'char':
        name, im = f'{norm(r[1])}_{r[2]}', character(r[1], r[2], a.skin, a.hair, a.bg)
    else:
        name, im = r[1].replace(' ', '_'), MONSTERS[r[1]](a.bg)
    _, n = save(name, im)
    print(f'cards/out/{name}.png  ({n}색)')


if __name__ == '__main__':
    main()
