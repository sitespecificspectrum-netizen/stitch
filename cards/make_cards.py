#!/usr/bin/env python3
"""소드코스트 캐릭터 카드 십자수 도안 생성기 (100 x 180칸).

실행: python3 cards/make_cards.py
결과: cards/<이름>.png (1칸 = 1픽셀), cards/<이름>_x8.png (미리보기),
      cards/<이름>_colors.txt (DMC 번호별 땀 수)
모든 색은 dmc.js 의 DMC 실 색만 사용한다.
"""
import json, os, re
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
 ' ': ["00","00","00","00","00","00","00"],
}


def text(base, s, y, top, bottom, sx=2, sy=2, gap=None):
    """가운데 정렬 글자. 위쪽은 top 색, 아래쪽은 bottom 색, 검은 외곽선."""
    gap = sx if gap is None else gap
    width = sum(len(FONT[ch][0]) * sx + gap for ch in s) - gap
    x = (W - width) // 2
    L = Layer()
    for ch in s:
        g = FONT[ch]
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == '1':
                    L.rect(x + c * sx, y + r * sy, x + c * sx + sx - 1, y + r * sy + sy - 1,
                           top if r < 4 else bottom)
        x += len(g[0]) * sx + gap
    # 8방향 외곽선 + 아래 그림자
    a = np.array(L.im); m = a[..., 3] > 0
    g = np.zeros_like(m)
    for dy in (-1, 0, 1, 2):
        for dx in (-1, 0, 1):
            g |= np.roll(np.roll(m, dy, 0), dx, 1)
    a[g & ~m] = K
    base.alpha_composite(Image.fromarray(a))


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


# ---------------------------------------------------------------- 아울베어
def owlbear():
    im = new()
    bands(im, [(0, 823), (30, 796), (58, 798), (84, 809)])
    d = ImageDraw.Draw(im)
    # 달, 별
    d.ellipse([70, 12, 84, 26], fill=C(3078)); d.ellipse([67, 10, 79, 22], fill=C(823))
    for x, y in ((14, 14), (30, 9), (46, 20), (58, 11), (90, 34), (10, 38), (22, 28), (88, 8)):
        d.point((x, y), fill=C(3078))
    # 네버윈터 숲: 먼 나무, 가까운 나무
    for cx, top, col in ((10, 62, 500), (30, 70, 500), (52, 66, 500), (72, 72, 500), (92, 60, 500)):
        for k in range(4):
            yy = top + k * 9
            d.polygon([(cx, yy), (cx - 6 - k * 3, yy + 14), (cx + 6 + k * 3, yy + 14)], fill=C(col))
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

    L = Layer()
    # 발
    L.el(35, 119, 10, 5, 801); L.el(65, 119, 10, 5, 801)
    # 몸통
    L.el(50, 92, 30, 28, 801); L.el(49, 90, 28, 26, 433)
    L.el(50, 96, 18, 20, 435); L.el(50, 94, 16, 18, 437)
    for i, (x, y) in enumerate([(42, 84), (50, 86), (58, 84), (38, 93), (46, 95), (54, 95), (62, 93),
                                (42, 103), (50, 105), (58, 103), (46, 112), (54, 112)]):
        L.px([(x - 1, y), (x, y + 1), (x + 1, y)], 435)
    # 팔
    L.el(21, 92, 8, 17, 801); L.el(79, 92, 8, 17, 801)
    L.el(20, 90, 5, 13, 433); L.el(78, 90, 5, 13, 433)
    # 귀깃
    L.poly([(30, 40), (23, 19), (42, 32)], 801); L.poly([(70, 40), (77, 19), (58, 32)], 801)
    L.poly([(30, 36), (26, 24), (37, 32)], 433); L.poly([(70, 36), (74, 24), (63, 32)], 433)
    # 머리
    L.el(50, 51, 26, 21, 801); L.el(50, 49, 25, 19, 433)
    L.el(39, 52, 12, 12, 437); L.el(61, 52, 12, 12, 437)
    L.el(39, 52, 7, 7, 972); L.el(61, 52, 7, 7, 972)
    L.el(39, 52, 6, 6, 444); L.el(61, 52, 6, 6, 444)
    L.el(40, 52, 3, 3, 310); L.el(60, 52, 3, 3, 310)
    L.px([(39, 50), (59, 50)], 'B5200')
    # 눈썹
    L.line([(29, 41), (38, 43), (46, 47)], 801, 2); L.line([(71, 41), (62, 43), (54, 47)], 801, 2)
    # 부리
    L.poly([(45, 57), (55, 57), (50, 70)], 740); L.poly([(47, 62), (53, 62), (50, 70)], 921)
    L.px([(49, 59), (51, 59)], 310)
    L.onto(im)
    # 발톱 (외곽선 뒤에 덧그림)
    d = ImageDraw.Draw(im)
    for x in (28, 33, 38, 62, 67, 72):
        d.line([(x, 121), (x, 124)], fill=C(739)); d.point((x, 125), fill=K)
    for x in (16, 20, 24, 76, 80, 84):
        d.line([(x, 107), (x, 110)], fill=C(739)); d.point((x, 111), fill=K)
    text(im, "OWL", 131, 743, 740, 3, 2)
    text(im, "BEAR", 151, 743, 740, 3, 3)
    frame(im, 783, 780)
    return im


# ---------------------------------------------------------------- 젤라틴 큐브
def cube():
    im = new()
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
    # 횃불
    for cx in (13, 87):
        T = Layer()
        T.rect(cx - 1, 34, cx + 1, 48, 801); T.rect(cx - 3, 32, cx + 3, 35, 414)
        T.poly([(cx - 4, 32), (cx, 18), (cx + 4, 32)], 740)
        T.poly([(cx - 2, 32), (cx, 24), (cx + 2, 32)], 444)
        T.onto(im)
        for x, y in ((cx - 6, 22), (cx + 6, 26), (cx, 14), (cx + 3, 17)):
            d.point((x, y), fill=C(740))

    L = Layer()
    L.el(50, 108, 36, 6, 700)                                   # 바닥 점액
    L.rect(19, 54, 69, 106, 704)                                # 앞면
    L.poly([(19, 54), (31, 40), (81, 40), (69, 54)], 907)       # 윗면
    L.poly([(69, 54), (81, 40), (81, 92), (69, 106)], 702)      # 옆면
    L.line([(19, 54), (69, 54)], 772); L.line([(69, 54), (69, 106)], 700)
    L.line([(69, 54), (81, 40)], 772)
    # 반사광
    for k in range(5):
        L.line([(23 + k, 70 - k * 2), (27 + k, 62 - k * 2)], 772)
    L.line([(24, 76), (24, 80)], 772)
    L.line([(36, 44), (48, 44)], 772); L.line([(74, 50), (78, 46)], 704)
    # 방울
    for x, y in ((60, 62), (30, 92), (63, 84), (44, 60), (75, 70)):
        L.px([(x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)], 772)
    # 흘러내림
    L.rect(26, 106, 28, 110, 704); L.rect(55, 106, 58, 111, 704); L.rect(74, 99, 76, 106, 702)
    L.onto(im)

    # 삼켜진 것들: 해골, 뼈, 검, 금화, 투구
    I = Layer()
    I.el(38, 74, 7, 6, 'B5200'); I.rect(34, 78, 42, 82, 'B5200')
    I.rect(34, 73, 36, 75, 700); I.rect(40, 73, 42, 75, 700); I.px([(38, 77)], 700)
    I.px([(35, 82), (37, 82), (39, 82), (41, 82)], 700)
    I.line([(28, 98), (40, 92)], 'B5200', 2)
    I.el(28, 98, 1, 1, 'B5200'); I.el(41, 91, 1, 1, 'B5200')
    I.line([(46, 99), (62, 66)], 415, 2); I.line([(45, 96), (51, 100)], 783, 2)
    I.line([(43, 103), (46, 99)], 801, 2)
    for x, y in ((54, 101), (60, 99), (64, 102), (57, 96)):
        I.el(x, y, 2, 1, 444); I.px([(x + 1, y + 1)], 972)
    I.el(57, 80, 5, 4, 414); I.rect(52, 80, 62, 82, 414); I.line([(53, 79), (60, 79)], 415)
    im.alpha_composite(I.im)

    text(im, "GELATINOUS", 130, 907, 704, 1, 2)
    text(im, "CUBE", 149, 907, 704, 3, 3)
    frame(im, 702, 700)
    return im


# ---------------------------------------------------------------- 티플링 바드
def tiefling():
    im = new()
    bands(im, [(0, 550), (26, 552), (50, 3607), (70, 3341), (86, 743)])
    d = ImageDraw.Draw(im)
    for x, y in ((12, 10), (28, 18), (44, 8), (66, 14), (84, 9), (90, 24), (18, 32), (74, 30)):
        d.point((x, y), fill=C(3078))
    # 발더스 게이트 스카이라인
    sky = [(4, 96, 14, 84), (14, 96, 22, 74), (22, 96, 34, 88), (34, 96, 40, 66), (40, 96, 52, 82),
           (52, 96, 60, 90), (60, 96, 70, 70), (70, 96, 82, 86), (82, 96, 96, 78)]
    for x0, y0, x1, y1 in sky:
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

    L = Layer()
    # 꼬리
    L.curve([(56, 96), (80, 104), (84, 80), (76, 70)], 2, 1, 321)
    L.poly([(76, 62), (71, 71), (81, 71)], 321)
    # 다리, 장화
    L.rect(41, 98, 47, 113, 3799); L.rect(53, 98, 59, 113, 3799)
    L.el(42, 116, 6, 3, 801); L.el(58, 116, 6, 3, 801)
    L.rect(40, 108, 48, 113, 801); L.rect(52, 108, 60, 113, 801)
    # 몸
    L.poly([(40, 70), (60, 70), (64, 99), (36, 99)], 796)
    L.poly([(47, 70), (53, 70), (50, 80)], 'B5200')
    L.rect(37, 94, 63, 96, 783); L.rect(48, 93, 52, 97, 972)
    L.line([(36, 99), (64, 99)], 783)
    # 뿔 (뒤)
    L.curve([(37, 44), (26, 40), (24, 26), (33, 20)], 4, 1, 739)
    L.curve([(63, 44), (74, 40), (76, 26), (67, 20)], 4, 1, 739)
    for x, y in ((28, 36), (27, 30), (29, 25), (72, 36), (73, 30), (71, 25)):
        L.line([(x - 1, y), (x + 1, y)], 437)
    # 귀
    L.poly([(34, 54), (24, 49), (34, 60)], 321); L.poly([(66, 54), (76, 49), (66, 60)], 321)
    # 머리
    L.el(50, 51, 18, 16, 550)
    L.el(50, 56, 15, 12, 321)
    L.poly([(33, 50), (36, 40), (50, 37), (64, 40), (67, 50), (60, 46), (55, 50), (48, 45), (42, 50), (38, 47)], 550)
    L.line([(40, 40), (47, 38)], 552); L.line([(42, 43), (46, 42)], 552)
    # 얼굴
    L.rect(40, 54, 44, 57, 444); L.rect(56, 54, 60, 57, 444)
    L.px([(42, 55), (58, 55)], 'B5200')
    L.line([(39, 52), (45, 53)], 310); L.line([(61, 52), (55, 53)], 310)
    L.line([(46, 62), (49, 64), (52, 64), (55, 62)], 815)
    L.px([(47, 64)], 'B5200')
    L.px([(37, 60), (38, 60), (62, 60), (63, 60)], 3328)
    L.onto(im)

    # 류트와 팔 (앞)
    U = Layer()
    U.line([(52, 86), (27, 71)], 801, 3)
    U.rect(23, 67, 28, 71, 801)
    U.el(57, 89, 11, 9, 435); U.el(58, 90, 9, 7, 437); U.el(56, 88, 3, 3, 801)
    U.line([(30, 73), (64, 93)], 739)
    U.px([(22, 67), (22, 70), (29, 66)], 783)
    U.curve([(39, 72), (33, 80), (36, 79)], 3, 3, 796)
    U.el(37, 78, 3, 3, 321)
    U.curve([(61, 72), (68, 82), (64, 90)], 3, 3, 796)
    U.el(63, 91, 3, 3, 321)
    U.onto(im)
    d = ImageDraw.Draw(im)
    for x, y in ((12, 60), (86, 56), (16, 100)):   # 음표
        d.rectangle([x, y + 5, x + 2, y + 7], fill=C(3078)); d.line([(x + 2, y), (x + 2, y + 6)], fill=C(3078))
        d.line([(x + 2, y), (x + 5, y + 2)], fill=C(3078))

    text(im, "TIEFLING", 130, 3607, 718, 2, 2, gap=1)
    text(im, "BARD", 151, 743, 972, 3, 3)
    frame(im, 3607, 718)
    return im


# ---------------------------------------------------------------- 드워프 클레릭
def dwarf():
    im = new()
    bands(im, [(0, 798), (22, 809), (48, 3325), (70, 3756)])
    d = ImageDraw.Draw(im)
    for cx, cy in ((22, 16), (70, 30)):
        d.ellipse([cx - 9, cy - 3, cx + 9, cy + 3], fill=C('B5200'))
        d.ellipse([cx - 4, cy - 6, cx + 5, cy + 2], fill=C('B5200'))
    # 바다와 절벽
    d.rectangle([0, 78, W, 108], fill=C(798))
    for y in range(81, 108, 5):
        for x in range((y * 3) % 11, W, 14):
            d.line([(x, y), (x + 4, y)], fill=C(3325))
    d.polygon([(0, 50), (16, 54), (24, 66), (26, 108), (0, 108)], fill=C(3064))
    d.polygon([(0, 50), (16, 54), (20, 58), (0, 56)], fill=C(988))
    for x, y in ((6, 66), (14, 78), (4, 88), (18, 94), (10, 72)):
        d.line([(x, y), (x + 3, y + 3)], fill=C(632))
    # 돛단배
    d.polygon([(78, 66), (78, 76), (88, 76)], fill=C('B5200')); d.polygon([(77, 68), (77, 76), (71, 76)], fill=C('B5200'))
    d.polygon([(69, 78), (90, 78), (87, 82), (72, 82)], fill=C(801))
    d.rectangle([0, 106, W, H], fill=C(988))
    d.rectangle([0, 124, W, H], fill=C(986))
    for x in range(3, 98, 5):
        d.line([(x, 112 + (x * 7) % 9), (x, 110 + (x * 7) % 9)], fill=C(986))
        d.point((x + 2, 124 - (x % 3)), fill=C(986))

    L = Layer()
    # 워해머 (뒤)
    L.rect(19, 52, 21, 112, 801)
    L.rect(11, 42, 29, 54, 414); L.rect(11, 42, 29, 44, 415); L.rect(9, 44, 11, 52, 317); L.rect(29, 44, 31, 52, 317)
    L.rect(18, 46, 22, 50, 783)
    # 다리
    L.rect(38, 104, 46, 114, 317); L.rect(54, 104, 62, 114, 317)
    L.el(40, 117, 8, 4, 801); L.el(60, 117, 8, 4, 801)
    # 몸통(갑옷)과 겉옷
    L.poly([(34, 74), (66, 74), (69, 106), (31, 106)], 414)
    L.poly([(42, 74), (58, 74), (60, 106), (40, 106)], 321)
    L.rect(31, 100, 69, 102, 801); L.rect(47, 99, 53, 103, 783)
    # 어깨
    L.el(32, 76, 7, 6, 415); L.el(68, 76, 7, 6, 415)
    L.line([(27, 78), (37, 78)], 414); L.line([(63, 78), (73, 78)], 414)
    # 왼팔 (망치)
    L.rect(26, 80, 32, 92, 414); L.el(20, 92, 4, 4, 945); L.rect(22, 89, 31, 94, 317)
    # 머리
    L.el(50, 56, 17, 14, 945)
    # 투구
    L.poly([(32, 54), (33, 42), (41, 34), (59, 34), (67, 42), (68, 54)], 415)
    L.rect(32, 50, 68, 54, 414); L.rect(48, 34, 52, 60, 414); L.line([(49, 34), (49, 58)], 415)
    L.px([(36, 52), (42, 52), (58, 52), (64, 52)], 783)
    L.line([(36, 44), (40, 39)], 'B5200')
    L.curve([(33, 46), (24, 44), (22, 34)], 3, 1, 739); L.curve([(67, 46), (76, 44), (78, 34)], 3, 1, 739)
    # 얼굴
    L.rect(40, 57, 43, 59, 310); L.rect(57, 57, 60, 59, 310); L.px([(41, 57), (58, 57)], 'B5200')
    L.line([(38, 55), (45, 56)], 919, 2); L.line([(62, 55), (55, 56)], 919, 2)
    L.el(50, 63, 4, 3, 3064); L.px([(49, 62)], 945)
    L.px([(36, 62), (37, 62), (63, 62), (64, 62)], 3328)
    # 수염
    L.poly([(33, 62), (40, 64), (46, 67), (54, 67), (60, 64), (67, 62), (67, 78), (60, 92), (50, 98), (40, 92), (33, 78)], 921)
    L.line([(44, 67), (50, 69), (56, 67)], 919, 2)
    for x in (38, 44, 56, 62):
        L.line([(x, 70), (x, 84 if x in (38, 62) else 90)], 919)
    L.line([(36, 66), (36, 76)], 740); L.line([(64, 66), (64, 76)], 740); L.line([(50, 72), (50, 92)], 740)
    L.rect(47, 93, 53, 95, 783); L.poly([(47, 96), (53, 96), (50, 103)], 921)
    L.onto(im)

    # 방패 (앞)
    S = Layer()
    S.el(73, 92, 13, 14, 783); S.el(73, 92, 11, 12, 796); S.el(73, 92, 10, 11, 798)
    S.rect(72, 83, 74, 101, 444); S.rect(66, 88, 80, 90, 444)   # 성스러운 문장
    S.px([(64, 84), (82, 84), (64, 100), (82, 100)], 415)
    S.onto(im)

    text(im, "DWARF", 131, 743, 740, 2, 2)
    text(im, "CLERIC", 151, 'B5200', 415, 2, 3)
    frame(im, 415, 414)
    return im


CARDS = {'owlbear': owlbear, 'gelatinous_cube': cube, 'tiefling_bard': tiefling, 'dwarf_cleric': dwarf}


def save(name, im):
    rgb = im.convert('RGB')
    a = np.array(rgb).reshape(-1, 3)
    cols, counts = np.unique(a, axis=0, return_counts=True)
    lines = []
    for c, n in sorted(zip(map(tuple, cols.tolist()), counts.tolist()), key=lambda t: -t[1]):
        assert c in RGB2CODE, f'{name}: DMC 에 없는 색 {c}'
        code = RGB2CODE[c]
        lines.append(f'DMC {code:<6} {DMC[code][0]:<32} #{DMC[code][1]}  {n:>5}땀')
    rgb.save(os.path.join(HERE, f'{name}.png'))
    rgb.resize((W * 8, H * 8), Image.NEAREST).save(os.path.join(HERE, f'{name}_x8.png'))
    with open(os.path.join(HERE, f'{name}_colors.txt'), 'w', encoding='utf-8') as f:
        f.write(f'{name}  {W} x {H}칸  {len(lines)}색\n' + '\n'.join(lines) + '\n')
    return rgb, len(lines)


if __name__ == '__main__':
    sheet = Image.new('RGB', (len(CARDS) * (W + 4) + 4, H + 8), (40, 40, 40))
    for i, (name, fn) in enumerate(CARDS.items()):
        rgb, n = save(name, fn())
        sheet.paste(rgb, (4 + i * (W + 4), 4))
        print(name, n, '색')
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(os.path.join(HERE, 'preview.png'))
