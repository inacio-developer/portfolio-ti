"""Gera ícones em estilo "desenho à mão" (traço preto fino, levemente tremido).

Uso:  python tools/doodle_icons.py
Saída: assets/img/icons/<nome>.png          (ícone solto, fundo transparente)
       assets/img/icons/framed/<nome>.png   (ícone dentro do quadrinho pendurado)
"""
import math
import random
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "assets" / "img" / "icons"
SIZE = 512          # tamanho final (px)
SS = 4              # supersampling p/ antialias
INK = (34, 30, 28, 255)
FONT = "C:/Windows/Fonts/segoepr.ttf"
FONT_B = "C:/Windows/Fonts/segoeprb.ttf"


class Doodle:
    """Canvas em unidades 0..100 (x) com traço tremido."""

    def __init__(self, w=100, h=100, px=SIZE, seed=1):
        self.w, self.h = w, h
        self.k = px * SS / w
        self.img = Image.new("RGBA", (int(w * self.k), int(h * self.k)), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.rng = random.Random(seed)
        self.tf = [(0.0, 0.0, 1.0)]  # pilha de (dx, dy, escala)
        self.width = 1.0

    # ---------- transformações ----------
    def push(self, dx, dy, s):
        ox, oy, os_ = self.tf[-1]
        self.tf.append((ox + dx * os_, oy + dy * os_, os_ * s))

    def pop(self):
        self.tf.pop()

    def _p(self, x, y):
        ox, oy, s = self.tf[-1]
        return ((ox + x * s) * self.k, (oy + y * s) * self.k)

    # ---------- primitivas ----------
    def _wobble(self, pts, amp=0.35):
        pts = [(float(x), float(y)) for x, y in pts]
        if len(pts) < 2:
            return pts
        res, step = [], 0.8
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
            for i in range(n):
                t = i / n
                res.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
        res.append(pts[-1])
        f1, f2 = self.rng.uniform(0.08, 0.16), self.rng.uniform(0.25, 0.45)
        p1, p2 = self.rng.uniform(0, 6.3), self.rng.uniform(0, 6.3)
        out, s = [], 0.0
        for i, (x, y) in enumerate(res):
            a = res[max(i - 1, 0)]
            b = res[min(i + 1, len(res) - 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L, dx / L
            if i:
                s += math.hypot(x - res[i - 1][0], y - res[i - 1][1])
            o = amp * (0.65 * math.sin(s * f1 + p1) + 0.35 * math.sin(s * f2 + p2))
            out.append((x + nx * o, y + ny * o))
        return out

    def line(self, pts, w=None, wobble=0.35, closed=False):
        pts = list(pts)
        if closed:
            pts = pts + [pts[0], pts[1] if len(pts) > 1 else pts[0]]
        pts = self._wobble(pts, wobble)
        w = (w or self.width) * self.tf[-1][2] * self.k
        P = [self._p(x, y) for x, y in pts]
        self.d.line(P, fill=INK, width=max(1, int(w)), joint="curve")
        r = w / 2
        for x, y in (P[0], P[-1]):
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=INK)

    def seg(self, x0, y0, x1, y1, **kw):
        self.line([(x0, y0), (x1, y1)], **kw)

    def poly(self, pts, **kw):
        self.line(pts, closed=True, **kw)

    def ellipse_pts(self, cx, cy, rx, ry, a0=0, a1=2 * math.pi, n=None):
        n = n or max(24, int((rx + ry) * abs(a1 - a0) * 1.2))
        return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
                for i in range(n + 1)]

    def ellipse(self, cx, cy, rx, ry, **kw):
        a0 = self.rng.uniform(0, 6.3)
        self.line(self.ellipse_pts(cx, cy, rx, ry, a0, a0 + 2 * math.pi + 0.18), **kw)

    def circle(self, cx, cy, r, **kw):
        self.ellipse(cx, cy, r, r, **kw)

    def arc(self, cx, cy, rx, ry, a0, a1, **kw):
        self.line(self.ellipse_pts(cx, cy, rx, ry, math.radians(a0), math.radians(a1)), **kw)

    def bez(self, *ctrl, n=40):
        pts = []
        for i in range(n + 1):
            t = i / n
            c = list(ctrl)
            while len(c) > 1:
                c = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for a, b in zip(c, c[1:])]
            pts.append(c[0])
        return pts

    def curve(self, *ctrl, **kw):
        self.line(self.bez(*ctrl), **kw)

    def rect(self, x0, y0, x1, y1, **kw):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], **kw)

    def rrect(self, x0, y0, x1, y1, r, **kw):
        pts = []
        for cx, cy, a in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            pts += self.ellipse_pts(cx, cy, r, r, math.radians(a), math.radians(a + 90), n=10)
        self.poly(pts, **kw)

    def fill(self, pts):
        self.d.polygon([self._p(x, y) for x, y in pts], fill=INK)

    def dot(self, x, y, r=1.2):
        self.fill(self.ellipse_pts(x, y, r, r, n=20))

    def hatch(self, x0, y0, x1, y1, gap=3, angle=45, clip=None, w=0.6):
        """Hachura em linhas paralelas; clip = função (x,y)->bool."""
        a = math.radians(angle)
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy, dx
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        R = math.hypot(x1 - x0, y1 - y0) / 2
        o = -R
        while o <= R:
            seg, cur = [], []
            t = -R
            while t <= R:
                x, y = cx + nx * o + dx * t, cy + ny * o + dy * t
                inside = x0 <= x <= x1 and y0 <= y <= y1 and (clip is None or clip(x, y))
                if inside:
                    cur.append((x, y))
                elif cur:
                    seg.append(cur); cur = []
                t += 0.5
            if cur:
                seg.append(cur)
            for s in seg:
                if len(s) > 2:
                    self.line([s[0], s[-1]], w=w, wobble=0.15)
            o += gap

    def text(self, x, y, s, size=10, bold=False, anchor="mm"):
        ox, oy, sc = self.tf[-1]
        f = ImageFont.truetype(FONT_B if bold else FONT, int(size * sc * self.k))
        self.d.text(self._p(x, y), s, font=f, fill=INK, anchor=anchor)

    def save(self, path):
        out = self.img.resize((int(self.w * SIZE / 100), int(self.h * SIZE / 100)), Image.LANCZOS)
        path.parent.mkdir(parents=True, exist_ok=True)
        # no Windows o arquivo às vezes fica preso por um instante (antivírus/preview); tenta de novo
        for attempt in range(8):
            try:
                out.save(path)
                return
            except OSError:
                if attempt == 7:
                    raise
                time.sleep(0.25)


def inside_poly(pts):
    def f(x, y):
        c = False
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
                c = not c
        return c
    return f


def shield_pts(d, top=14, bot=90, l=20, r=80):
    mid = (l + r) / 2
    left = d.bez((l, top), (l, 60), (l + 8, 75), (mid, bot), n=30)
    right = d.bez((mid, bot), (r - 8, 75), (r, 60), (r, top), n=30)
    return left + right[1:]


# ======================= ÍCONES =======================
ICONS = {}


def icon(name):
    def deco(fn):
        ICONS[name] = fn
        return fn
    return deco


# ---------- escudos ----------
@icon("escudo-palmeiras")
def _(d):
    sh = shield_pts(d)
    d.poly(sh, w=1.3)
    d.poly(shield_pts(d, 18, 85, 24, 76), w=0.7)
    d.circle(50, 46, 20, w=1.1)
    d.circle(50, 46, 16.5, w=0.6)
    d.text(50, 46, "P", size=24, bold=True)
    for x in (37, 50, 63):
        star(d, x, 75 if x == 50 else 72, 3)


def star(d, cx, cy, r, filled=False):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    if filled:
        d.fill(pts)
    d.poly(pts, w=0.6)


@icon("escudo-barcelona")
def _(d):
    sh = d.bez((22, 22), (22, 12), (34, 10), (50, 16), n=20) + d.bez((50, 16), (66, 10), (78, 12), (78, 22), n=20)[1:]
    body = d.bez((78, 22), (80, 62), (66, 82), (50, 92), n=30) + d.bez((50, 92), (34, 82), (20, 62), (22, 22), n=30)[1:]
    pts = sh + body[1:]
    d.poly(pts, w=1.3)
    d.seg(21, 40, 79, 40)
    d.seg(50, 16, 50, 40)
    # cruz (esq) e listras diagonais (dir)
    d.seg(36, 18, 36, 38, w=1.6); d.seg(24, 28, 48, 28, w=1.6)
    d.hatch(51, 16, 79, 40, gap=3.2, angle=60, clip=inside_poly(pts))
    # faixa com letras
    d.rrect(28, 41.5, 72, 50, 2, w=0.8)
    d.text(50, 45.8, "FCB", size=6.5, bold=True)
    # listras verticais embaixo
    clip = inside_poly(pts)
    for x in range(28, 76, 6):
        col = [(x, y) for y in range(51, 93) if clip(x, y)]
        if col:
            d.seg(x, col[0][1] + 0.5, x, col[-1][1] - 0.5, w=0.8)
    d.circle(50, 66, 6.5, w=1.0)
    d.fill(d.ellipse_pts(50, 66, 6.5, 6.5))
    d.circle(50, 66, 5.3, w=0.0001)
    pent(d, 50, 66, 2.2, color=None)


def pent(d, cx, cy, r, color=INK):
    pts = [(cx + r * math.cos(-math.pi / 2 + i * 2 * math.pi / 5), cy + r * math.sin(-math.pi / 2 + i * 2 * math.pi / 5))
           for i in range(5)]
    d.d.polygon([d._p(*p) for p in pts], fill=(255, 255, 255, 255) if color is None else color)
    return pts


@icon("escudo-liverpool")
def _(d):
    sh = shield_pts(d, 18, 92, 22, 78)
    d.poly(sh, w=1.3)
    d.seg(22, 25, 78, 25, w=0.7)
    d.text(50, 21.6, "L F C", size=5.5, bold=True)
    # pássaro genérico (de perfil, olhando p/ esquerda)
    d.curve((40, 42), (38, 36), (44, 32), (48, 36))               # cabeça
    d.curve((48, 36), (52, 40), (54, 46), (60, 50), w=1.0)          # costas
    d.curve((40, 42), (42, 50), (46, 56), (56, 58), w=1.0)          # peito
    d.curve((56, 58), (60, 58), (62, 54), (60, 50))
    d.poly([(40, 39), (33, 40.5), (40, 42)], w=0.9)                 # bico
    d.dot(43.5, 37.5, 0.9)
    d.curve((48, 44), (56, 38), (62, 32), (68, 30), w=0.9)          # asa
    d.curve((68, 30), (64, 38), (60, 44), (52, 48), w=0.9)
    d.curve((60, 50), (66, 54), (68, 60), (66, 64), w=0.9)          # cauda
    d.seg(50, 58, 49, 66); d.seg(54, 58, 55, 66)                    # pernas
    d.seg(47, 66, 51, 66, w=0.7); d.seg(53, 66, 57, 66, w=0.7)
    d.curve((32, 43), (30, 47), (34, 49), (37, 46), w=0.7)          # raminho no bico
    # chamas laterais simplificadas
    for x in (28, 72):
        d.curve((x, 80), (x - 3, 72), (x + 3, 68), (x, 60), w=0.8)
    d.rrect(32, 72, 68, 79, 2, w=0.8)
    d.text(50, 75.6, "YNWA", size=5, bold=True)


@icon("escudo-celtics")
def _(d):
    d.circle(50, 50, 38, w=1.3)
    d.circle(50, 50, 32, w=0.7)
    d.text(50, 22.5, "BOSTON", size=5.2, bold=True)
    # trevo
    for ang in (-90, 30, 150):
        a = math.radians(ang)
        cx, cy = 50 + 9 * math.cos(a), 47 + 9 * math.sin(a)
        heart(d, cx, cy, 8, ang + 90)
    d.curve((50, 50), (52, 60), (56, 66), (60, 70), w=1.4)
    # bola de basquete pequena
    d.circle(68, 68, 7, w=0.9)
    d.seg(61, 68, 75, 68, w=0.6); d.seg(68, 61, 68, 75, w=0.6)
    d.arc(62, 68, 3.5, 6, -70, 70, w=0.6); d.arc(74, 68, 3.5, 6, 110, 250, w=0.6)


def heart(d, cx, cy, s, rot=0):
    pts = []
    for i in range(60):
        t = 2 * math.pi * i / 60
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        x, y = x / 32 * s * 2, y / 32 * s * 2
        r = math.radians(rot)
        pts.append((cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r)))
    d.poly(pts, w=1.0)


# ---------- esportes ----------
def basketball(d, cx, cy, r, w=1.2):
    d.circle(cx, cy, r, w=w)
    d.seg(cx - r, cy, cx + r, cy, w=w * 0.75)
    d.seg(cx, cy - r, cx, cy + r, w=w * 0.75)
    d.arc(cx - r * 0.95, cy, r * 0.55, r * 0.88, -75, 75, w=w * 0.75)
    d.arc(cx + r * 0.95, cy, r * 0.55, r * 0.88, 105, 255, w=w * 0.75)


@icon("basquete")
def _(d):
    # aro + rede
    d.rect(30, 8, 70, 32, w=1.0)
    d.rect(42, 18, 58, 30, w=0.7)
    d.ellipse(50, 33, 12, 2.5, w=1.1)
    for i in range(6):
        x = 38 + i * 4.8
        d.seg(x, 34, 44 + i * 2.4, 46, w=0.6)
    d.seg(43, 46, 57, 46, w=0.6)
    basketball(d, 50, 70, 17)
    for y in (58, 66, 74):
        d.seg(18, y + 6, 26, y + 2, w=0.7)


@icon("futebol")
def _(d):
    cx, cy, r = 50, 46, 30
    d.circle(cx, cy, r, w=1.3)
    p = pent(d, cx, cy, 9)
    d.poly(p, w=0.8)
    for i, (x, y) in enumerate(p):
        a = math.atan2(y - cy, x - cx)
        ex, ey = cx + math.cos(a) * 20, cy + math.sin(a) * 20
        d.seg(x, y, ex, ey, w=0.8)
        q = pent(d, cx + math.cos(a) * 26, cy + math.sin(a) * 26, 5.5)
        clip = lambda X, Y: math.hypot(X - cx, Y - cy) < r
        d.fill([pt for pt in q if clip(*pt)] or q)
        d.seg(ex, ey, cx + math.cos(a + 0.6) * r, cy + math.sin(a + 0.6) * r, w=0.8)
        d.seg(ex, ey, cx + math.cos(a - 0.6) * r, cy + math.sin(a - 0.6) * r, w=0.8)
    d.circle(cx, cy, r, w=1.3)
    # grama
    d.line([(14, 86), (86, 86)], w=0.9)
    for x in range(18, 84, 6):
        d.seg(x, 86, x + 1.5, 82, w=0.6); d.seg(x + 2, 86, x + 2.5, 83, w=0.6)


@icon("esportes")
def _(d):
    # troféu
    d.line(d.bez((32, 18), (32, 46), (40, 56), (50, 56)) + d.bez((50, 56), (60, 56), (68, 46), (68, 18))[1:], w=1.3)
    d.seg(30, 18, 70, 18, w=1.3)
    d.curve((32, 24), (20, 22), (20, 38), (35, 40), w=1.0)
    d.curve((68, 24), (80, 22), (80, 38), (65, 40), w=1.0)
    d.seg(48, 56, 47, 68, w=1.0); d.seg(52, 56, 53, 68, w=1.0)
    d.rect(38, 68, 62, 74, w=1.1)
    d.rect(34, 74, 66, 82, w=1.1)
    star(d, 50, 34, 7)
    d.text(50, 78.3, "1º", size=5, bold=True)
    # bolinhas
    d.circle(18, 80, 5, w=0.8); d.seg(13, 80, 23, 80, w=0.5); d.seg(18, 75, 18, 85, w=0.5)
    d.circle(82, 80, 5, w=0.8); d.dot(82, 80, 1.6)
    for a in (200, 250, 300, 340):
        r = math.radians(a)
        d.seg(50 + 24 * math.cos(r), 34 + 24 * math.sin(r), 50 + 30 * math.cos(r), 34 + 30 * math.sin(r), w=0.6)


# ---------- one piece ----------
def straw_hat(d, cx, cy, s=1.0, w=1.0):
    d.push(cx - 50 * s, cy - 50 * s, s)
    d.ellipse(50, 60, 42, 13, w=w * 1.2)              # aba
    d.ellipse(50, 60, 34, 8.5, w=w * 0.5)
    d.curve((27, 57), (24, 14), (76, 14), (73, 57), w=w * 1.2)  # copa
    # faixa
    top = d.bez((26.5, 45), (34, 41), (66, 41), (73.5, 45))
    bot = d.bez((27, 56), (34, 61), (66, 61), (73, 56))
    d.line(top, w=w); d.line(bot, w=w)
    d.hatch(25, 42, 75, 61, gap=1.6, angle=70, clip=inside_poly(top + bot[::-1]), w=0.5)
    # trama da palha
    for i in range(8):
        x = 31 + i * 5.5
        d.seg(x, 26 + abs(50 - x) * 0.45, x - 1, 40, w=0.35)
    for a in range(200, 345, 14):
        r = math.radians(a)
        d.seg(50 + 34 * math.cos(r), 60 + 8.5 * math.sin(r), 50 + 41 * math.cos(r), 60 + 12.5 * math.sin(r), w=0.4)
    for a in range(20, 165, 14):
        r = math.radians(a)
        d.seg(50 + 34 * math.cos(r), 60 + 8.5 * math.sin(r), 50 + 41 * math.cos(r), 60 + 12.5 * math.sin(r), w=0.4)
    d.pop()


@icon("chapeu-luffy")
def _(d):
    straw_hat(d, 50, 46, 1.0)
    d.curve((20, 82), (40, 78), (60, 78), (80, 82), w=0.6)


@icon("mangas-one-piece")
def _(d):
    books = [(22, 70, 80, 82, "ONE PIECE  1"), (26, 58, 82, 70, "ONE PIECE  2"), (20, 46, 76, 58, "ONE PIECE  3")]
    for x0, y0, x1, y1, t in books:
        d.rect(x0, y0, x1, y1, w=1.1)
        d.seg(x0 + 6, y0, x0 + 6, y1, w=0.6)
        d.text((x0 + x1) / 2 + 3, (y0 + y1) / 2, t, size=4.6, bold=True)
    # volume em pé
    d.poly([(80, 82), (86, 34), (96, 35), (90, 83)], w=1.1)
    d.seg(83, 40, 92, 41, w=0.5); d.seg(81, 76, 90, 77, w=0.5)
    straw_hat(d, 48, 30, 0.42)
    d.seg(10, 83, 96, 83, w=0.9)


# ---------- séries ----------
@icon("series")
def _(d):
    d.rrect(14, 30, 86, 84, 6, w=1.3)
    d.rrect(20, 36, 68, 78, 5, w=1.0)
    d.seg(50, 30, 38, 12, w=0.9); d.seg(50, 30, 64, 10, w=0.9)
    d.dot(38, 12, 1.6); d.dot(64, 10, 1.6)
    d.circle(77, 46, 3.5, w=0.8); d.circle(77, 58, 3.5, w=0.8)
    for y in (66, 70, 74):
        d.seg(73, y, 81, y, w=0.5)
    d.seg(22, 84, 18, 90, w=1.0); d.seg(78, 84, 82, 90, w=1.0)
    d.poly([(40, 50), (40, 64), (52, 57)], w=0.9)
    d.arc(29, 44, 4, 4, 180, 270, w=0.5)


@icon("series-the-office")
def _(d):
    # grampeador dentro de gelatina
    d.rrect(18, 34, 82, 78, 9, w=1.2)
    d.curve((22, 40), (30, 36), (70, 36), (78, 40), w=0.5)
    d.curve((24, 72), (24, 60), (24, 50), (26, 44), w=0.5)
    d.seg(72, 42, 76, 50, w=0.5)
    # grampeador
    d.poly([(30, 62), (70, 62), (70, 66), (30, 66)], w=1.0)
    d.poly([(32, 62), (36, 52), (68, 54), (68, 62)], w=1.0)
    d.circle(34, 60, 1.8, w=0.6)
    # prato
    d.ellipse(50, 82, 40, 5, w=1.1)
    # gotinhas/brilho
    d.seg(78, 26, 80, 22, w=0.6); d.seg(84, 30, 88, 28, w=0.6); d.seg(72, 24, 72, 20, w=0.6)


@icon("series-himym")
def _(d):
    # guarda-chuva aberto
    cx, top = 50, 18
    d.line(d.ellipse_pts(cx, 48, 36, 30, math.pi, 2 * math.pi), w=1.3)
    sc = [(14, 48), (26, 48), (38, 48), (50, 48), (62, 48), (74, 48), (86, 48)]
    for a, b in zip(sc, sc[1:]):
        d.curve(a, ((a[0] + b[0]) / 2, 43), b, w=1.0)
    for x in (26, 38, 62, 74):
        d.curve((cx, top), ((cx + x) / 2, 28), (x, 48), w=0.6)
    d.seg(cx, top, cx, 47, w=0.6)
    d.seg(cx, top, cx, top - 5, w=1.0)
    d.seg(cx, 48, cx, 80, w=1.2)
    d.arc(cx - 5, 80, 5, 5, 0, 180, w=1.2)
    for x, y in ((18, 64), (30, 72), (72, 66), (84, 76), (62, 84), (20, 84)):
        d.curve((x, y - 3), (x - 1.5, y), (x + 1.5, y), (x, y - 3), w=0.7)
        d.arc(x, y, 1.6, 1.6, 0, 180, w=0.7)


@icon("series-arrested-development")
def _(d):
    # barraquinha de banana congelada
    d.rect(22, 50, 78, 86, w=1.2)
    d.seg(18, 50, 82, 50, w=1.2)
    d.poly([(18, 50), (24, 34), (76, 34), (82, 50)], w=1.1)
    for i in range(1, 7):
        x0 = 18 + i * 64 / 7
        x1 = 24 + i * 52 / 7
        d.seg(x0, 50, x1, 34, w=0.8)
    for i in range(0, 7, 2):
        a0, a1 = 18 + i * 64 / 7, 18 + (i + 1) * 64 / 7
        b0, b1 = 24 + i * 52 / 7, 24 + (i + 1) * 52 / 7
        d.hatch(min(a0, b0), 34, max(a1, b1), 50, gap=1.6, angle=-60,
                clip=inside_poly([(a0, 50), (b0, 34), (b1, 34), (a1, 50)]), w=0.45)
    d.seg(26, 34, 26, 50, w=0.6); d.seg(74, 34, 74, 50, w=0.6)
    d.rect(28, 58, 72, 72, w=0.8)
    d.text(50, 65, "$ BANANA", size=5.4, bold=True)
    # banana no palito no topo
    d.seg(50, 34, 50, 26, w=1.0)
    ban_l = d.bez((46, 26), (42, 16), (44, 8), (50, 4), n=20)
    ban_r = d.bez((50, 4), (52, 10), (54, 18), (54, 26), n=20)
    d.poly(ban_l + ban_r[1:] + [(46, 26)], w=1.0)
    d.hatch(40, 4, 56, 15, gap=1.3, angle=30, clip=inside_poly(ban_l + ban_r[1:]), w=0.45)
    d.seg(14, 86, 86, 86, w=0.9)


@icon("series-modern-family")
def _(d):
    d.poly([(16, 48), (50, 20), (84, 48)], w=1.3)
    d.rect(22, 46, 78, 86, w=1.2)
    d.rect(62, 22, 70, 36, w=1.0)
    d.rect(44, 64, 56, 86, w=1.0); d.dot(54, 75, 0.8)
    for x in (28, 64):
        d.rect(x, 54, x + 10, 62, w=0.8); d.seg(x + 5, 54, x + 5, 62, w=0.5); d.seg(x, 58, x + 10, 58, w=0.5)
    heart(d, 50, 40, 5)
    # família: 3 bonequinhos
    for x, h in ((86, 10), (92, 7), (80, 12)):
        pass
    d.seg(8, 86, 92, 86, w=0.9)
    for x in (12, 88):
        d.circle(x, 74, 4, w=0.8)
        d.seg(x, 78, x, 86, w=0.8)


@icon("series-abbott")
def _(d):
    # quadro-negro + maçã + livros
    d.rect(14, 12, 86, 52, w=1.2)
    d.rect(18, 16, 82, 48, w=0.6)
    d.text(42, 31, "A B C", size=10)
    d.text(70, 37, "1+1", size=6)
    d.seg(14, 52, 14, 58, w=0.8); d.seg(86, 52, 86, 58, w=0.8)
    d.rect(26, 74, 74, 82, w=1.0); d.rect(30, 66, 70, 74, w=1.0)
    d.seg(34, 66, 34, 74, w=0.5); d.seg(30, 78, 70, 78, w=0.4)
    # maçã
    ap = d.bez((50, 52), (44, 48), (36, 54), (40, 62), n=20) + d.bez((40, 62), (43, 68), (48, 66), (50, 65), n=20)[1:] \
        + d.bez((50, 65), (52, 66), (57, 68), (60, 62), n=20)[1:] + d.bez((60, 62), (64, 54), (56, 48), (50, 52), n=20)[1:]
    d.poly(ap, w=1.1)
    d.curve((50, 52), (50, 48), (52, 46), w=0.9)
    d.curve((52, 48), (56, 44), (60, 46), (52, 48), w=0.7)
    d.arc(45, 56, 2, 3, 180, 260, w=0.5)


@icon("series-adults")
def _(d):
    # sofá + caixa de pizza (vida de 20 e poucos)
    d.rrect(16, 44, 84, 58, 4, w=1.1)
    d.rrect(10, 52, 22, 78, 4, w=1.1); d.rrect(78, 52, 90, 78, 4, w=1.1)
    d.rect(22, 58, 78, 72, w=1.1)
    d.seg(50, 58, 50, 72, w=0.6)
    d.seg(14, 78, 14, 84, w=1.0); d.seg(86, 78, 86, 84, w=1.0)
    # fatia de pizza flutuando + caneca
    sl = [(36, 36), (50, 10), (64, 36)]
    d.poly(sl, w=1.1); d.curve((35, 36), (50, 41), (65, 36), w=1.6)
    d.circle(50, 21, 2, w=0.6); d.circle(45, 30, 1.8, w=0.6); d.circle(56, 29, 1.8, w=0.6)
    d.rect(70, 34, 80, 44, w=0.9); d.arc(80, 39, 3, 3, -90, 90, w=0.8)
    d.curve((73, 31), (71, 27), (75, 25), (73, 21), w=0.5); d.curve((77, 31), (75, 27), (79, 25), (77, 21), w=0.5)
    d.seg(8, 84, 92, 84, w=0.8)


# ---------- jogos ----------
def controller(d, cx, cy, s=1.0):
    d.push(cx - 50 * s, cy - 50 * s, s)
    body = d.bez((24, 38), (40, 34), (60, 34), (76, 38), n=20) + d.bez((76, 38), (88, 40), (94, 70), (84, 72), n=20)[1:] \
        + d.bez((84, 72), (76, 74), (70, 60), (60, 58), n=20)[1:] + d.bez((60, 58), (52, 57), (48, 57), (40, 58), n=10)[1:] \
        + d.bez((40, 58), (30, 60), (24, 74), (16, 72), n=20)[1:] + d.bez((16, 72), (6, 70), (12, 40), (24, 38), n=20)[1:]
    d.poly(body, w=1.3)
    d.poly([(25, 44), (29, 44), (29, 48), (33, 48), (33, 52), (29, 52), (29, 56), (25, 56), (25, 52), (21, 52), (21, 48), (25, 48)], w=0.9)
    for x, y in ((72, 44), (78, 49), (66, 49), (72, 54)):
        d.circle(x, y, 2.4, w=0.8)
    d.circle(40, 52, 3.5, w=0.8); d.circle(60, 52, 3.5, w=0.8)
    d.seg(45, 43, 48, 43, w=0.7); d.seg(52, 43, 55, 43, w=0.7)
    d.pop()


@icon("jogos")
def _(d):
    controller(d, 50, 52)
    for (x, y) in ((22, 22), (78, 20), (50, 14)):
        star(d, x, y, 3)


@icon("jogos-fifa")
def _(d):
    controller(d, 46, 60, 0.85)
    cx, cy, r = 74, 24, 13
    d.circle(cx, cy, r, w=1.1)
    p = pent(d, cx, cy, 4.2)
    d.fill(p)
    for i, (x, y) in enumerate(p):
        a = math.atan2(y - cy, x - cx)
        d.seg(x, y, cx + math.cos(a) * r, cy + math.sin(a) * r, w=0.6)
    for y in (18, 24, 30):
        d.seg(52, y + 2, 58, y, w=0.6)


@icon("jogos-lol")
def _(d):
    # espada + escudo redondo + cristal (pegada de MOBA)
    d.circle(36, 58, 22, w=1.3)
    d.circle(36, 58, 17, w=0.6)
    d.circle(36, 58, 5, w=1.0)
    for a in range(0, 360, 45):
        r = math.radians(a)
        d.seg(36 + 7 * math.cos(r), 58 + 7 * math.sin(r), 36 + 15 * math.cos(r), 58 + 15 * math.sin(r), w=0.5)
    # espada diagonal
    d.poly([(54, 50), (82, 14), (86, 12), (84, 18), (58, 54)], w=1.1)
    d.seg(48, 46, 62, 58, w=1.4)
    d.seg(54, 56, 46, 66, w=1.6)
    d.dot(45, 67, 1.6)
    # cristal
    d.poly([(78, 62), (84, 72), (78, 88), (72, 72)], w=1.0)
    d.seg(72, 72, 84, 72, w=0.6); d.seg(78, 62, 78, 88, w=0.5)
    for a in (30, 150, 270):
        pass


# ---------- TI ----------
@icon("ti")
def _(d):
    d.rrect(22, 22, 78, 62, 3, w=1.3)
    d.rrect(26, 26, 74, 58, 2, w=0.7)
    d.poly([(22, 62), (78, 62), (90, 76), (10, 76)], w=1.2)
    d.seg(42, 70, 58, 70, w=0.7)
    for y in (66,):
        for x in range(20, 80, 6):
            d.seg(x, y, x + 3, y, w=0.4)
    d.text(50, 41, "</>", size=13, bold=True)
    # engrenagem
    gx, gy, gr = 82, 20, 6
    pts = []
    for i in range(16):
        a = i * math.pi / 8
        rr = gr + (2 if (i // 2) % 2 == 0 else 0)
        pts.append((gx + rr * math.cos(a), gy + rr * math.sin(a)))
    d.poly(pts, w=0.8); d.circle(gx, gy, 2, w=0.6)
    d.text(17, 15, "01", size=5); d.text(14, 88, "10", size=4)


# ---------- música ----------
@icon("musica")
def _(d):
    # fone
    d.arc(50, 52, 28, 30, 180, 360, w=1.4)
    d.arc(50, 52, 24, 26, 185, 355, w=0.6)
    d.rrect(16, 50, 28, 74, 5, w=1.2); d.rrect(72, 50, 84, 74, 5, w=1.2)
    d.rrect(20, 54, 26, 70, 2, w=0.5); d.rrect(74, 54, 80, 70, 2, w=0.5)
    # notas
    d.ellipse(42, 70, 4, 3, w=1.0); d.fill(d.ellipse_pts(42, 70, 4, 3))
    d.ellipse(56, 66, 4, 3, w=1.0); d.fill(d.ellipse_pts(56, 66, 4, 3))
    d.seg(45.6, 70, 45.6, 48, w=1.0); d.seg(59.6, 66, 59.6, 44, w=1.0)
    d.poly([(45.6, 48), (59.6, 44), (59.6, 48), (45.6, 52)], w=0.8)
    d.fill([(45.6, 48), (59.6, 44), (59.6, 48), (45.6, 52)])
    d.ellipse(84, 26, 2.6, 2, w=0.8); d.fill(d.ellipse_pts(84, 26, 2.6, 2))
    d.seg(86.4, 26, 86.4, 14, w=0.8); d.curve((86.4, 14), (90, 16), (89, 20), w=0.8)


# ---------- robôs ----------
@icon("robos")
def _(d):
    d.seg(50, 18, 50, 10, w=1.0); d.circle(50, 8, 2.5, w=1.0)
    d.rrect(30, 18, 70, 46, 6, w=1.3)
    d.circle(41, 31, 5, w=1.0); d.dot(42, 32, 1.8)
    d.circle(59, 31, 5, w=1.0); d.dot(60, 32, 1.8)
    d.arc(50, 37, 6, 4, 20, 160, w=0.9)
    d.rect(26, 28, 30, 36, w=0.8); d.rect(70, 28, 74, 36, w=0.8)
    d.seg(46, 46, 46, 50, w=0.8); d.seg(54, 46, 54, 50, w=0.8)
    d.rrect(32, 50, 68, 78, 4, w=1.3)
    heart(d, 50, 61, 5)
    d.circle(40, 72, 1.6, w=0.6); d.circle(46, 72, 1.6, w=0.6); d.seg(53, 72, 62, 72, w=0.6)
    d.curve((32, 56), (24, 58), (20, 64), (18, 70), w=1.1); d.circle(17, 72, 2.4, w=0.9)
    d.curve((68, 56), (76, 52), (80, 46), (82, 40), w=1.1); d.circle(83, 38, 2.4, w=0.9)
    d.rect(38, 78, 44, 88, w=1.0); d.rect(56, 78, 62, 88, w=1.0)
    d.seg(34, 88, 46, 88, w=1.1); d.seg(54, 88, 66, 88, w=1.1)


# ---------- filmes ----------
@icon("filmes")
def _(d):
    d.rect(18, 42, 82, 84, w=1.3)
    d.poly([(16, 32), (80, 20), (82, 30), (18, 42)], w=1.2)
    d.seg(18, 42, 16, 32, w=1.2)
    for i in range(5):
        x0 = 22 + i * 12
        d.fill([(x0, 31.3 - i * 2.25), (x0 + 6, 30.2 - i * 2.25), (x0 + 9, 38.5 - i * 2.25 - 1.2), (x0 + 3, 39.7 - i * 2.25)])
    d.rect(18, 42, 82, 50, w=0.8)
    for i in range(5):
        d.fill([(22 + i * 12, 42), (28 + i * 12, 42), (25 + i * 12, 50), (19 + i * 12, 50)][:4] if i else
               [(18, 42), (24, 42), (21, 50), (18, 50)])
    d.seg(18, 64, 82, 64, w=0.5)
    d.text(34, 57, "CENA", size=4.5); d.text(66, 57, "TAKE", size=4.5)
    d.text(34, 73, "12", size=7); d.text(66, 73, "3", size=7)
    d.seg(50, 50, 50, 84, w=0.5)


@icon("filmes-misterio")
def _(d):
    d.circle(42, 42, 22, w=1.4)
    d.circle(42, 42, 18, w=0.6)
    d.seg(58, 58, 64, 64, w=2.0)
    d.poly([(62, 66), (66, 62), (86, 82), (82, 86)], w=1.2)
    d.text(42, 43, "?", size=24, bold=True)
    d.arc(42, 42, 14, 14, 200, 250, w=0.6)


@icon("filmes-taxi-driver")
def _(d):
    body = [(10, 64), (12, 52), (26, 50), (34, 38), (66, 38), (74, 50), (90, 52), (92, 64)]
    d.line(body, w=1.3)
    d.seg(10, 64, 18, 64, w=1.3); d.seg(34, 64, 66, 64, w=1.3); d.seg(82, 64, 92, 64, w=1.3)
    d.circle(26, 64, 8, w=1.2); d.circle(26, 64, 3, w=0.7)
    d.circle(74, 64, 8, w=1.2); d.circle(74, 64, 3, w=0.7)
    d.poly([(36, 41), (48, 41), (48, 50), (30, 50)], w=0.8)
    d.poly([(52, 41), (64, 41), (70, 50), (52, 50)], w=0.8)
    d.seg(50, 50, 50, 62, w=0.6)
    d.rect(42, 30, 58, 37, w=0.9)
    d.text(50, 33.4, "TAXI", size=4.5, bold=True)
    # xadrez lateral
    for i in range(10):
        x = 32 + i * 3.6
        if i % 2 == 0:
            d.fill([(x, 54), (x + 3.6, 54), (x + 3.6, 57), (x, 57)])
        else:
            d.fill([(x, 57), (x + 3.6, 57), (x + 3.6, 60), (x, 60)])
    d.seg(32, 54, 68, 54, w=0.5); d.seg(32, 60, 68, 60, w=0.5)
    d.seg(4, 73, 96, 73, w=0.8)
    for x in range(8, 96, 14):
        d.seg(x, 80, x + 7, 80, w=0.7)
    # luzes da cidade
    for x, y in ((14, 22), (22, 16), (80, 18), (88, 26)):
        star(d, x, y, 2)


@icon("filmes-forrest-gump")
def _(d):
    # pena flutuando
    d.curve((24, 60), (36, 40), (54, 24), (76, 12), w=1.1)
    left = d.bez((30, 50), (34, 30), (56, 14), (76, 12), n=30)
    right = d.bez((76, 12), (70, 30), (50, 46), (30, 50), n=30)
    d.line(left, w=1.0); d.line(right, w=1.0)
    for t in range(1, 10):
        tt = t / 10
        x, y = 24 + (76 - 24) * tt, 60 + (12 - 60) * tt
        d.seg(x, y, x - 4, y - 7, w=0.4); d.seg(x, y, x + 6, y + 3, w=0.4)
    d.curve((18, 30), (24, 26), (28, 34), w=0.5); d.curve((80, 34), (86, 30), (90, 38), w=0.5)
    # caixa de bombom
    d.rrect(30, 66, 82, 90, 3, w=1.2)
    d.poly([(28, 66), (40, 58), (90, 58), (84, 66)], w=1.0)
    for x in (40, 50, 60, 70):
        d.circle(x + 2, 62, 3, w=0.7)
    d.rrect(36, 72, 76, 84, 2, w=0.6)
    d.text(56, 78, "bombons", size=4.8)


@icon("filmes-david-gale")
def _(d):
    # fita VHS com "?" + martelo de juiz
    d.rrect(10, 36, 70, 74, 3, w=1.3)
    d.rect(18, 40, 62, 52, w=0.8)
    d.text(40, 46.3, "?", size=8, bold=True)
    d.circle(26, 62, 6, w=1.0); d.circle(54, 62, 6, w=1.0)
    for cx in (26, 54):
        for a in range(0, 360, 60):
            r = math.radians(a)
            d.seg(cx + 2 * math.cos(r), 62 + 2 * math.sin(r), cx + 4 * math.cos(r), 62 + 4 * math.sin(r), w=0.5)
    d.rect(34, 58, 46, 66, w=0.7)
    # martelo
    d.push(0, 0, 1)
    d.poly([(62, 24), (78, 14), (84, 22), (68, 32)], w=1.1)
    d.seg(64, 25.5, 70, 33.5, w=0.6); d.seg(76, 15.5, 82, 23.5, w=0.6)
    d.poly([(72, 24), (74, 22), (92, 46), (90, 48)], w=1.0)
    d.pop()
    d.seg(4, 80, 70, 80, w=0.6)


@icon("filmes-past-lives")
def _(d):
    # escadaria: um bonequinho embaixo, outro em cima, fio entre eles; lua
    steps = [(12, 88)]
    x, y = 12, 88
    for _ in range(7):
        steps += [(x, y - 8), (x + 9, y - 8)]
        x, y = x + 9, y - 8
    d.line(steps, w=1.1)
    d.seg(12, 88, 90, 88, w=1.0)
    d.seg(75, 32, 92, 32, w=0.6)
    person(d, 22, 80, 0.8)
    person(d, 74, 24, 0.8)
    d.line([(24, 70), (40, 56), (52, 50), (64, 30), (72, 16)], w=0.45, wobble=0.9)
    d.arc(22, 16, 8, 8, 60, 300, w=1.0)
    d.arc(26, 16, 7, 7, 75, 285, w=0.6)


def person(d, x, feet, s=1.0):
    h = 22 * s
    d.circle(x, feet - h, 3.2 * s, w=0.9)
    d.seg(x, feet - h + 3.2 * s, x, feet - h * 0.4, w=0.9)
    d.seg(x, feet - h * 0.4, x - 3 * s, feet, w=0.9); d.seg(x, feet - h * 0.4, x + 3 * s, feet, w=0.9)
    d.seg(x, feet - h * 0.75, x - 4 * s, feet - h * 0.45, w=0.9); d.seg(x, feet - h * 0.75, x + 4 * s, feet - h * 0.45, w=0.9)


@icon("filmes-toc-toc")
def _(d):
    # porta com "toc toc" + objetos perfeitamente alinhados
    d.rect(28, 12, 72, 86, w=1.3)
    d.rect(34, 18, 66, 44, w=0.7); d.rect(34, 50, 66, 80, w=0.7)
    d.circle(64, 48, 2.2, w=0.9)
    d.text(17, 30, "toc", size=7); d.text(84, 40, "toc", size=7)
    for y in (24, 26):
        pass
    d.arc(24, 30, 10, 10, -40, 40, w=0.5); d.arc(76, 40, 10, 10, 140, 220, w=0.5)
    d.seg(8, 86, 92, 86, w=0.9)
    for x in (12, 18, 82, 88):
        d.rect(x - 2, 80, x + 2, 86, w=0.6)


@icon("filmes-zodiaco")
def _(d):
    d.circle(50, 34, 20, w=1.4)
    d.seg(50, 8, 50, 60, w=1.4); d.seg(24, 34, 76, 34, w=1.4)
    syms = "ΔΘ+ΞΠΣ⊥ΦΩ◊Λ+ΓΨ⊕Ж"
    rng = random.Random(7)
    for r in range(3):
        for c in range(8):
            d.text(16 + c * 9.7, 68 + r * 8.5, rng.choice(syms), size=5.5)
    d.rect(10, 62, 90, 90, w=0.8)


# ---------- animes ----------
@icon("animes")
def _(d):
    # balão de fala de mangá com "!?" + linhas de ação
    pts = []
    for i in range(24):
        a = i * 2 * math.pi / 24
        rr = 1 if i % 2 == 0 else 0.86
        pts.append((50 + 34 * rr * math.cos(a), 44 + 26 * rr * math.sin(a)))
    d.poly(pts, w=1.2)
    d.poly([(40, 66), (30, 86), (52, 68)], w=1.0)
    d.text(50, 44, "!?", size=24, bold=True)
    for a in range(0, 360, 30):
        r = math.radians(a)
        d.seg(50 + 40 * math.cos(r), 44 + 32 * math.sin(r), 50 + 46 * math.cos(r), 44 + 38 * math.sin(r), w=0.6)


@icon("anime-pokemon")
def _(d):
    # criatura original (bolinha com broto) surgindo no mato alto + "!"
    d.curve((28, 64), (24, 30), (76, 30), (72, 64), w=1.2)
    d.circle(32, 38, 5, w=1.0); d.circle(68, 38, 5, w=1.0)
    d.seg(50, 33, 50, 24, w=1.0)
    d.curve((50, 26), (42, 18), (38, 24), (50, 26), w=0.9)
    d.curve((50, 24), (58, 14), (64, 20), (50, 24), w=0.9)
    d.ellipse(43, 48, 2.2, 3, w=0.8); d.dot(43.4, 48.6, 1.4)
    d.ellipse(57, 48, 2.2, 3, w=0.8); d.dot(57.4, 48.6, 1.4)
    d.arc(50, 54, 3.5, 2.5, 10, 170, w=0.7)
    # mato
    for i in range(14):
        x = 14 + i * 5.4
        h = 22 + (i % 3) * 5
        d.curve((x, 86), (x + 1, 86 - h * 0.6), (x + 4, 86 - h), w=0.9)
        d.curve((x + 4, 86 - h), (x + 3, 86 - h * 0.5), (x + 5, 86), w=0.9)
    d.seg(10, 86, 90, 86, w=1.0)
    d.rrect(78, 8, 90, 26, 3, w=0.9)
    d.text(84, 17, "!", size=11, bold=True)


@icon("anime-hunterxhunter")
def _(d):
    # vara de pescar + boia + anzol
    d.seg(14, 90, 70, 12, w=1.5)
    d.circle(26, 74, 5, w=1.0); d.seg(26, 74, 30, 70, w=0.7)
    d.rect(14, 82, 20, 90, w=0.6)
    d.curve((70, 12), (78, 20), (80, 40), (80, 54), w=0.5, wobble=0.6)
    d.ellipse(80, 60, 4, 6, w=1.0)
    d.seg(76, 60, 84, 60, w=0.8)
    d.hatch(76, 54, 84, 60, gap=1.4, angle=0, clip=lambda x, y: ((x - 80) / 4) ** 2 + ((y - 60) / 6) ** 2 < 1, w=0.45)
    d.seg(80, 66, 80, 74, w=0.5)
    d.arc(77, 76, 3, 3, -20, 180, w=0.9)
    d.seg(80, 76, 80, 74, w=0.9)
    for y in (82, 88):
        d.curve((54, y), (60, y - 3), (66, y), (72, y - 3), w=0.6)
        d.curve((74, y), (80, y - 3), (86, y), (92, y - 3), w=0.6)


@icon("anime-one-piece")
def _(d):
    # barquinho pirata nas ondas com bandeira de caveira genérica
    hull = [(14, 58), (86, 58), (76, 74), (24, 74)]
    d.poly(hull, w=1.3)
    d.seg(18, 64, 82, 64, w=0.5)
    for x in (34, 46, 58, 70):
        d.circle(x, 69, 1.6, w=0.6)
    d.seg(50, 58, 50, 10, w=1.2)
    d.curve((50, 16), (68, 18), (72, 34), (70, 50), w=1.1)
    d.seg(50, 50, 70, 50, w=0.8); d.seg(50, 16, 50, 16)
    d.curve((50, 22), (36, 26), (34, 40), (36, 50), w=1.0); d.seg(36, 50, 50, 50, w=0.8)
    d.poly([(50, 10), (64, 6), (50, 4)], w=0.9)
    # caveirinha genérica na vela
    d.circle(60, 32, 5, w=0.8)
    d.dot(58.3, 31.5, 1.1); d.dot(61.7, 31.5, 1.1)
    d.seg(54, 40, 66, 44, w=0.8); d.seg(54, 44, 66, 40, w=0.8)
    for y in (80, 88):
        for x in range(10, 80, 18):
            d.curve((x, y), (x + 4.5, y - 4), (x + 9, y), (x + 13.5, y - 4), w=0.8)


@icon("anime-naruto")
def _(d):
    # tigela de lámen com narutomaki + hashis
    d.line(d.bez((14, 50), (16, 80), (84, 80), (86, 50)), w=1.3)
    d.ellipse(50, 50, 36, 8, w=1.2)
    d.ellipse(50, 51, 31, 5.5, w=0.5)
    d.rect(40, 77, 60, 82, w=1.0)
    # narutomaki
    d.ellipse(40, 50, 7, 3.5, w=0.9)
    sp = [(40 + 0.7 * t * math.cos(t * 1.2), 50 + 0.35 * t * math.sin(t * 1.2)) for t in [i / 4 for i in range(36)]]
    d.line(sp, w=0.6)
    # ovo
    d.ellipse(58, 49, 6, 3.4, w=0.9); d.ellipse(58, 49, 2.6, 1.6, w=0.6)
    d.fill(d.ellipse_pts(58, 49, 2.6, 1.6))
    # macarrão
    for x in (24, 30, 72, 76):
        d.curve((x, 50), (x + 3, 46), (x - 2, 44), (x + 2, 41), w=0.5)
    d.seg(46, 54, 92, 10, w=1.1); d.seg(52, 54, 96, 16, w=1.1)
    for x in (34, 48, 62):
        d.curve((x, 36), (x - 3, 30), (x + 3, 26), (x, 18), w=0.6)


@icon("anime-fma")
def _(d):
    # círculo de transmutação genérico
    cx, cy = 50, 50
    d.circle(cx, cy, 38, w=1.3)
    d.circle(cx, cy, 33, w=0.8)
    tri = [(cx + 33 * math.cos(math.radians(-90 + i * 120)), cy + 33 * math.sin(math.radians(-90 + i * 120))) for i in range(3)]
    d.poly(tri, w=1.0)
    tri2 = [(cx + 33 * math.cos(math.radians(90 + i * 120)), cy + 33 * math.sin(math.radians(90 + i * 120))) for i in range(3)]
    d.poly(tri2, w=1.0)
    d.circle(cx, cy, 14, w=0.9)
    sq = [(cx + 10 * math.cos(math.radians(45 + i * 90)), cy + 10 * math.sin(math.radians(45 + i * 90))) for i in range(4)]
    d.poly(sq, w=0.8)
    d.circle(cx, cy, 3, w=0.8)
    for i in range(6):
        a = math.radians(-90 + i * 60)
        d.circle(cx + 35.5 * math.cos(a), cy + 35.5 * math.sin(a), 2.2, w=0.6)
    for i in range(24):
        a = math.radians(i * 15 + 7)
        d.seg(cx + 38 * math.cos(a), cy + 38 * math.sin(a), cx + 41 * math.cos(a), cy + 41 * math.sin(a), w=0.5)


# ======================= LOTE 2 =======================
def jersey_bball(d, name, num):
    pts = [(30, 14), (40, 14), (43, 22), (57, 22), (60, 14), (70, 14),
           (71, 26), (78, 36), (78, 88), (22, 88), (22, 36), (29, 26)]
    d.poly(pts, w=1.3)
    d.line([(40, 14), (43, 22), (57, 22), (60, 14)], w=0.6)
    d.curve((29, 26), (31, 32), (25, 36), (22, 36), w=0.6)
    d.curve((71, 26), (69, 32), (75, 36), (78, 36), w=0.6)
    d.seg(22, 82, 78, 82, w=0.6)
    d.text(50, 38, name, size=7.5 if len(name) <= 6 else 6.2, bold=True)
    d.text(50, 62, num, size=24, bold=True)


def jersey_fut(d, name, num):
    pts = [(38, 12), (44, 16), (56, 16), (62, 12), (82, 20), (92, 38), (80, 44),
           (76, 36), (76, 90), (24, 90), (24, 36), (20, 44), (8, 38), (18, 20)]
    d.poly(pts, w=1.3)
    d.curve((44, 16), (47, 19), (53, 19), (56, 16), w=0.6)
    d.seg(24, 36, 24, 24, w=0.5); d.seg(76, 36, 76, 24, w=0.5)
    d.seg(9.5, 35, 21, 41, w=0.5); d.seg(90.5, 35, 79, 41, w=0.5)
    d.text(50, 34, name, size=7.5 if len(name) <= 7 else 6, bold=True)
    d.text(50, 62, num, size=26, bold=True)


BBALL = [("kawhi", "LEONARD", "2"), ("duncan", "DUNCAN", "21"), ("durant", "DURANT", "35"),
         ("tatum", "TATUM", "0"), ("curry", "CURRY", "30"), ("lebron", "JAMES", "23"), ("luka", "DONČIĆ", "77")]
FUT = [("messi", "MESSI", "10"), ("suarez", "SUÁREZ", "9"), ("marcos-assuncao", "ASSUNÇÃO", "20"),
       ("diego-souza", "D. SOUZA", "7"), ("ronaldinho", "RONALDINHO", "10"), ("ronaldo", "RONALDO", "9"),
       ("hazard", "HAZARD", "10"), ("salah", "SALAH", "11"), ("iniesta", "INIESTA", "8"),
       ("barcos", "BARCOS", "9"), ("dudu", "DUDU", "7"),
       ("mane", "MANÉ", "10"), ("firmino", "FIRMINO", "9"), ("gerrard", "GERRARD", "8"),
       ("van-dijk", "VAN DIJK", "4")]
for _slug, _n, _k in BBALL:
    icon(f"jogador-basquete-{_slug}")(lambda d, n=_n, k=_k: jersey_bball(d, n, k))
for _slug, _n, _k in FUT:
    icon(f"jogador-futebol-{_slug}")(lambda d, n=_n, k=_k: jersey_fut(d, n, k))


def glove(d, cx, cy, s, flip=1):
    d.push(cx - 50 * s, cy - 50 * s, s)
    f = lambda x: 50 + (x - 50) * flip
    d.rrect(min(f(34), f(66)), 62, max(f(34), f(66)), 80, 4, w=1.2)
    for i, x in enumerate((36, 44, 52, 60)):
        top = 22 if i in (1, 2) else 28
        d.rrect(min(f(x), f(x + 7)), top, max(f(x), f(x + 7)), 64, 3.5, w=1.1)
    d.rrect(min(f(66), f(78)), 46, max(f(66), f(78)), 56, 4, w=1.1)
    d.seg(f(34), 72, f(66), 72, w=0.6)
    d.pop()


@icon("jogador-futebol-alisson")
def _(d):
    jersey_fut(d, "ALISSON", "1")
    glove(d, 14, 82, 0.28, 1)
    glove(d, 86, 82, 0.28, -1)


@icon("jogador-futebol-marcos")
def _(d):
    jersey_fut(d, "MARCOS", "12")
    glove(d, 14, 82, 0.28, 1)
    glove(d, 86, 82, 0.28, -1)


@icon("zatch-bell")
def _(d):
    # livro de feitiços com raio + faíscas
    d.poly([(24, 20), (72, 14), (78, 80), (30, 88)], w=1.3)
    d.line([(24, 20), (20, 24), (26, 92), (30, 88)], w=1.0)
    bolt = [(54, 26), (40, 52), (50, 52), (42, 76), (64, 44), (53, 44), (60, 26)]
    d.poly(bolt, w=1.1)
    d.hatch(38, 24, 66, 78, gap=1.5, angle=30, w=0.4, clip=inside_poly(bolt))
    for x, y in ((84, 20), (88, 40), (14, 12)):
        star(d, x, y, 3.5)
    d.line([(80, 54), (86, 58), (82, 62), (90, 66)], w=0.7)


# ---------- desenhos / séries da infância ----------
@icon("desenho-pequeno-urso")
def _(d):
    # pote de mel + pegadas de urso
    d.line(d.bez((30, 36), (14, 50), (20, 86), (50, 86)) + d.bez((50, 86), (80, 86), (86, 50), (70, 36))[1:], w=1.3)
    d.ellipse(50, 34, 22, 5, w=1.2)
    d.ellipse(50, 28, 18, 4, w=1.0)
    d.seg(32, 28, 32, 33, w=0.8); d.seg(68, 28, 68, 33, w=0.8)
    d.curve((36, 37), (38, 46), (34, 50), (36, 54), w=0.9)
    d.curve((36, 54), (42, 46), (46, 44), (48, 38), w=0.9)
    d.rrect(36, 56, 64, 72, 3, w=0.8)
    d.text(50, 64, "MEL", size=6.5, bold=True)
    for x, y in ((84, 18), (74, 8)):
        d.ellipse(x, y + 4, 3, 2.4, w=0.8)
        for dx in (-3, 0, 3):
            d.circle(x + dx, y, 1, w=0.6)


@icon("desenho-menino-maluquinho")
def _(d):
    # panela (o "chapéu" mais famoso dos quadrinhos brasileiros)
    d.line(d.bez((24, 40), (24, 78), (76, 78), (76, 40)), w=1.3)
    d.ellipse(50, 40, 26, 7, w=1.3)
    d.ellipse(50, 40, 22, 5, w=0.5)
    d.rrect(76, 38, 96, 44, 3, w=1.1)
    d.circle(92, 41, 1.2, w=0.5)
    d.arc(36, 60, 6, 10, 180, 250, w=0.5)
    d.text(14, 24, "!", size=12, bold=True)
    d.text(86, 22, "?", size=10, bold=True)
    d.curve((10, 86), (30, 84), (70, 84), (90, 86), w=0.6)


@icon("desenho-sete-monstrinhos")
def _(d):
    # um "7" grandão virando monstrinho original (chifres, olhos, dentes)
    d.poly([(22, 22), (78, 22), (78, 32), (52, 88), (38, 88), (62, 34), (22, 34)], w=1.4)
    d.poly([(28, 22), (31, 12), (35, 22)], w=1.0)
    d.poly([(66, 22), (70, 12), (73, 22)], w=1.0)
    d.circle(40, 28, 3, w=0.8); d.dot(40.5, 28.5, 1.4)
    d.circle(54, 28, 3, w=0.8); d.dot(54.5, 28.5, 1.4)
    for x in (45, 49):
        d.poly([(x, 34), (x + 1.5, 37), (x + 3, 34)], w=0.5)
    for i in range(7):
        d.circle(14 + i * 12, 95, 2.2, w=0.6)


@icon("desenho-dragonball")
def _(d):
    # esfera com estrelas + radar
    d.circle(42, 54, 28, w=1.4)
    d.arc(42, 54, 22, 22, 200, 250, w=0.7)
    for x, y in ((34, 48), (50, 48), (36, 64), (50, 64)):
        star(d, x, y, 5.5, filled=True)
    d.rrect(70, 12, 92, 34, 9, w=1.0)
    d.circle(81, 23, 7, w=0.6)
    d.seg(74, 23, 88, 23, w=0.4); d.seg(81, 16, 81, 30, w=0.4)
    d.dot(84, 20, 1.3)
    d.seg(81, 12, 81, 8, w=0.9); d.circle(81, 7, 1.4, w=0.7)


@icon("desenho-caverna-do-dragao")
def _(d):
    # carrinho de montanha-russa indo para uma caverna
    d.line(d.bez((6, 80), (30, 80), (40, 40), (60, 40)) + [(66, 40)], w=1.0)
    d.line(d.bez((6, 86), (32, 86), (42, 46), (60, 46)) + [(66, 46)], w=1.0)
    for t in range(6):
        x = 12 + t * 8
        tt = t / 6
        d.seg(x, 80 - 40 * tt * tt * 1.3, x, 86 - 40 * tt * tt * 1.3, w=0.5)
    cave = d.bez((60, 90), (60, 30), (70, 14), (84, 14), n=20) + d.bez((84, 14), (96, 14), (98, 40), (98, 90), n=20)[1:]
    d.line(cave, w=1.3)
    mouth = d.bez((68, 46), (68, 30), (90, 30), (90, 50), n=20) + [(90, 60), (68, 60)]
    d.poly(mouth, w=0.9)
    d.hatch(66, 30, 92, 60, gap=1.5, angle=40, clip=inside_poly(mouth), w=0.4)
    d.poly([(20, 70), (36, 64), (38, 72), (22, 78)], w=1.2)
    d.circle(25, 79, 2.5, w=0.8); d.circle(35, 75, 2.5, w=0.8)
    d.poly([(22, 70), (21, 62), (27, 60), (28, 68)], w=0.8)
    for x, y in ((14, 18), (36, 12)):
        star(d, x, y, 3)


@icon("desenho-tom-e-jerry")
def _(d):
    # parede de tijolos com toca de rato + queijo
    for y in (14, 28, 42, 56):
        off = 0 if (y // 14) % 2 == 0 else 10
        for x in range(4 + off, 86, 20):
            if not (24 < x < 70 and y >= 42):
                d.rect(x, y, x + 18, y + 12, w=0.35)
    d.seg(4, 82, 96, 82, w=1.1)
    d.seg(4, 76, 96, 76, w=0.6)
    hole = d.bez((34, 82), (34, 50), (66, 50), (66, 82))
    d.line(hole, w=1.3)
    d.hatch(34, 50, 66, 82, gap=1.4, angle=0, clip=inside_poly(hole), w=0.45)
    d.poly([(70, 82), (92, 82), (92, 68), (70, 74)], w=1.1)
    d.line([(70, 74), (86, 64), (92, 68)], w=0.9)
    d.circle(78, 78, 1.6, w=0.6); d.circle(86, 75, 1.4, w=0.6); d.circle(88, 79, 1, w=0.5)


@icon("desenho-looney-tunes")
def _(d):
    # anéis concêntricos + cenoura
    for r in (42, 34, 26, 18):
        d.circle(50, 50, r, w=1.2 if r == 42 else 0.9)
    d.poly([(41, 44), (59, 44), (50.5, 82)], w=1.2)
    for y in (54, 62, 70):
        d.seg(44 + (y - 44) * 0.2, y, 49 + (y - 44) * 0.1, y, w=0.5)
    d.curve((50, 44), (44, 34), (38, 30), w=1.0)
    d.curve((50, 44), (50, 32), (52, 24), w=1.0)
    d.curve((50, 44), (56, 34), (62, 30), w=1.0)


# ---------- pessoal ----------
@icon("scarlett")
def _(d):
    heart(d, 50, 46, 32)
    heart(d, 50, 46, 27)
    d.text(50, 42, "Scarlett", size=11.5, bold=True)
    for x, y, s in ((14, 16, 5), (86, 14, 6), (88, 80, 4), (12, 78, 3.5)):
        heart(d, x, y, s)


@icon("minas-gerais")
def _(d):
    # montanhas, queijo minas e café
    d.line([(4, 56), (22, 30), (34, 44), (52, 16), (70, 42), (82, 30), (96, 52)], w=1.3)
    d.line([(46, 25), (52, 16), (58, 25), (55, 23), (52, 26), (49, 23), (46, 25)], w=0.7)
    d.circle(82, 12, 5, w=0.9)
    d.ellipse(32, 66, 22, 6, w=1.2)
    d.seg(10, 66, 10, 80, w=1.2); d.seg(54, 66, 54, 80, w=1.2)
    d.arc(32, 80, 22, 6, 0, 180, w=1.2)
    d.text(32, 66, "MG", size=6.5, bold=True)
    d.line(d.bez((64, 62), (64, 86), (86, 86), (86, 62)), w=1.1)
    d.seg(64, 62, 86, 62, w=1.1)
    d.arc(88, 70, 4, 5, -90, 90, w=1.0)
    d.ellipse(75, 87, 15, 3, w=0.9)
    for x in (70, 78):
        d.curve((x, 58), (x - 2, 54), (x + 2, 52), (x, 48), w=0.5)


@icon("belo-horizonte")
def _(d):
    # arcos ondulados à beira da lagoa + serra ao fundo
    d.line([(4, 30), (16, 22), (26, 28), (40, 16), (54, 26), (66, 20), (80, 28), (96, 22)], w=0.6)
    xs = [8, 30, 48, 62, 74]
    hs = [28, 22, 18, 16]
    for (a, b), h in zip(zip(xs, xs[1:]), hs):
        d.line(d.bez((a, 66), (a, 66 - h * 1.3), (b, 66 - h * 1.3), (b, 66)), w=1.3)
    d.seg(8, 66, 74, 66, w=1.1)
    d.seg(77, 66, 77, 40, w=1.0); d.seg(77, 40, 92, 36, w=1.0)
    d.seg(92, 36, 92, 66, w=0.8)
    d.seg(84.5, 44, 84.5, 54, w=0.6); d.seg(81, 48, 88, 48, w=0.6)
    for y in (74, 82, 90):
        for x in range(6, 90, 16):
            d.curve((x, y), (x + 4, y - 3), (x + 8, y), (x + 12, y - 3), w=0.6)
    d.text(14, 10, "BH", size=7, bold=True)


# ---------- comidas ----------
@icon("comida-bolo")
def _(d):
    d.ellipse(50, 44, 32, 8, w=1.2)
    d.seg(18, 44, 18, 78, w=1.2); d.seg(82, 44, 82, 78, w=1.2)
    d.arc(50, 78, 32, 8, 0, 180, w=1.2)
    d.line([(18, 50), (24, 58), (30, 52), (38, 60), (46, 53), (54, 61), (62, 53), (70, 60), (76, 52), (82, 58)], w=0.8)
    d.arc(50, 66, 32, 8, 10, 170, w=0.5)
    d.ellipse(50, 86, 42, 6, w=1.0)
    for x in (38, 50, 62):
        d.rect(x - 2, 26, x + 2, 41, w=0.8)
        d.line(d.bez((x, 25), (x - 3, 20), (x, 15)) + d.bez((x, 15), (x + 3, 20), (x, 25))[1:], w=0.7)
    for x, y in ((30, 46), (66, 42), (56, 47)):
        d.dot(x, y, 0.9)


@icon("comida-pao")
def _(d):
    loaf = d.bez((14, 64), (10, 36), (60, 24), (88, 46), n=30) + d.bez((88, 46), (96, 60), (80, 76), (50, 74), n=20)[1:] \
        + d.bez((50, 74), (30, 74), (16, 72), (14, 64), n=20)[1:]
    d.poly(loaf, w=1.3)
    for x in (30, 46, 62):
        d.curve((x - 4, 54), (x, 42), (x + 6, 40), (x + 10, 42), w=1.0)
    d.curve((20, 66), (40, 70), (70, 70), (86, 60), w=0.5)
    d.ellipse(52, 84, 42, 4, w=0.8)
    for x in (24, 74):
        d.curve((x, 24), (x - 2, 20), (x + 2, 16), (x, 12), w=0.5)


@icon("comida-pizza")
def _(d):
    d.circle(50, 50, 38, w=1.3)
    d.circle(50, 50, 32, w=0.7)
    for a in (0, 60, 120, 180, 240, 300):
        r = math.radians(a)
        d.seg(50, 50, 50 + 37 * math.cos(r), 50 + 37 * math.sin(r), w=0.7)
    for x, y in ((40, 34), (62, 36), (68, 56), (56, 68), (36, 64), (28, 46), (52, 44)):
        d.circle(x, y, 3.4, w=0.8)
        d.dot(x + 0.6, y + 0.6, 0.6)
    for x, y in ((46, 26), (72, 46), (24, 58), (44, 76)):
        d.curve((x, y), (x + 2, y - 2), (x + 4, y), w=0.6)


@icon("comida-hamburguer")
def _(d):
    d.line(d.bez((16, 42), (16, 12), (84, 12), (84, 42)) + [(16, 42)], w=1.3)
    for x, y in ((36, 26), (50, 21), (62, 27), (44, 32)):
        d.ellipse(x, y, 1.6, 0.9, w=0.6)
    d.line([(14, 46), (20, 42), (26, 48), (34, 42), (42, 48), (50, 42), (58, 48), (66, 42), (74, 48), (82, 42), (86, 46)], w=0.9)
    d.poly([(18, 50), (82, 50), (74, 58), (64, 52), (52, 60), (40, 52), (28, 58)], w=0.9)
    d.rrect(14, 58, 86, 68, 5, w=1.2)
    d.line(d.bez((16, 72), (16, 88), (84, 88), (84, 72)) + [(16, 72)], w=1.3)


@icon("comida-arroz-e-feijao")
def _(d):
    d.ellipse(48, 58, 42, 20, w=1.3)
    d.ellipse(48, 58, 34, 15, w=0.6)
    rice = d.bez((18, 58), (18, 42), (48, 40), (50, 58), n=20) + d.bez((50, 58), (48, 72), (22, 72), (18, 58), n=20)[1:]
    d.poly(rice, w=0.9)
    rng = random.Random(3)
    for _ in range(26):
        x, y = rng.uniform(23, 46), rng.uniform(49, 66)
        a = rng.uniform(0, 3.1)
        d.seg(x, y, x + 2 * math.cos(a), y + 2 * math.sin(a), w=0.5)
    bean = d.bez((50, 52), (52, 42), (78, 44), (78, 58), n=20) + d.bez((78, 58), (78, 72), (52, 72), (50, 62), n=20)[1:]
    d.poly(bean, w=0.9)
    d.hatch(50, 42, 80, 72, gap=1.8, angle=-35, clip=inside_poly(bean), w=0.45)
    d.seg(90, 32, 92, 80, w=1.0)
    d.ellipse(89.5, 26, 4, 7, w=1.0)
    for x in (34, 48, 62):
        d.curve((x, 32), (x - 3, 26), (x + 3, 22), (x, 16), w=0.5)


@icon("comida-batata-frita")
def _(d):
    for i, x in enumerate(range(28, 72, 7)):
        top = 14 + (i % 3) * 6
        ang = (i - 3) * 1.6
        d.rect(x + ang, top, x + 5 + ang, 54, w=0.9)
    cup = [(22, 44), (78, 44), (70, 90), (30, 90)]
    d.d.polygon([d._p(*p) for p in cup], fill=(255, 255, 255, 255))
    d.poly(cup, w=1.3)
    d.curve((22, 44), (36, 52), (64, 52), (78, 44), w=0.9)
    star(d, 50, 70, 7)


@icon("comida-ovo")
def _(d):
    rng = random.Random(9)
    pts = []
    for i in range(12):
        a = i * 2 * math.pi / 12
        r = 34 + rng.uniform(-6, 5)
        pts.append((50 + r * math.cos(a), 50 + r * 0.8 * math.sin(a)))
    # contorno suave passando pelos pontos (Catmull-Rom)
    smooth = []
    n = len(pts)
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for k in range(12):
            t = k / 12
            smooth.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                       + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
    d.poly(smooth, w=1.3)
    d.circle(47, 49, 12, w=1.2)
    d.arc(47, 49, 8, 8, 200, 260, w=0.6)
    d.ellipse(50, 92, 30, 2, w=0.4)


# ---------- livros ----------
@icon("livros")
def _(d):
    for x, h in ((18, 60), (30, 68), (42, 56), (54, 64)):
        d.rect(x, 88 - h, x + 11, 88, w=1.1)
        d.seg(x, 88 - h + 6, x + 11, 88 - h + 6, w=0.5)
        d.seg(x, 82, x + 11, 82, w=0.5)
    d.poly([(66, 88), (76, 26), (87, 28), (77, 90)], w=1.1)
    d.seg(10, 88, 92, 88, w=1.0)


@icon("livro-os-miseraveis")
def _(d):
    # livro + castiçal de prata
    d.poly([(14, 28), (54, 22), (58, 84), (18, 90)], w=1.3)
    d.line([(14, 28), (10, 32), (14, 94), (18, 90)], w=1.0)
    d.text(35, 42, "Os", size=6)
    d.text(36, 54, "Misera-", size=6.4, bold=True)
    d.text(36, 63, "veis", size=6.4, bold=True)
    d.text(37, 78, "V. Hugo", size=4.5)
    d.ellipse(76, 88, 12, 3, w=1.1)
    d.line(d.bez((68, 87), (74, 80), (74, 66), (74, 51)), w=1.0)
    d.line(d.bez((84, 87), (78, 80), (78, 66), (78, 51)), w=1.0)
    d.ellipse(76, 50, 7, 2, w=1.0)
    d.rect(73, 30, 79, 49, w=1.0)
    d.seg(76, 30, 76, 27, w=0.6)
    d.line(d.bez((76, 27), (72, 22), (76, 14)) + d.bez((76, 14), (80, 22), (76, 27))[1:], w=0.8)


@icon("livro-algoritmos")
def _(d):
    # livro de algoritmos com ratinho original + fluxograma
    d.rect(18, 12, 80, 90, w=1.3)
    d.seg(24, 12, 24, 90, w=0.6)
    d.text(52, 21, "ALGORITMOS", size=6.2, bold=True)
    d.rrect(43, 29, 61, 36, 3, w=0.7)
    d.seg(52, 36, 52, 40, w=0.6)
    d.poly([(52, 40), (60, 45), (52, 50), (44, 45)], w=0.7)
    d.seg(52, 50, 52, 54, w=0.6); d.rect(45, 54, 59, 59, w=0.7)
    d.seg(60, 45, 68, 45, w=0.5); d.seg(68, 45, 68, 32.5, w=0.5); d.seg(68, 32.5, 61, 32.5, w=0.5)
    # ratinho
    d.ellipse(50, 76, 10, 6, w=1.0)
    d.circle(41, 69, 3.2, w=0.8); d.circle(47, 68, 3.2, w=0.8)
    d.poly([(40.5, 75), (34, 78), (40.5, 80)], w=0.8)
    d.dot(34.5, 78, 0.8)
    d.dot(42, 74.5, 0.8)
    d.curve((60, 77), (68, 80), (70, 72), (76, 74), w=0.7)
    d.seg(45, 82, 45, 84, w=0.6); d.seg(55, 82, 55, 84, w=0.6)


# ---------- "..." (continuação / e mais) ----------
@icon("mais")
def _(d):
    for x in (26, 50, 74):
        d.circle(x, 50, 7, w=1.2)
        d.fill(d.ellipse_pts(x, 50, 6.2, 6.2))
    d.curve((14, 72), (36, 80), (64, 80), (84, 72), w=0.8)
    d.poly([(78, 68), (86, 71), (81, 78)], w=0.8)


# ======================= LOTE 3: MÚSICA =======================
def _at(d, cx, cy, s, fn):
    d.push(cx - 50 * s, cy - 50 * s, s)
    fn(d)
    d.pop()


def inst_violao(d):
    up = d.ellipse_pts(50, 50, 14, 13, math.radians(130), math.radians(410))
    low = d.ellipse_pts(50, 72, 19, 17, math.radians(-50), math.radians(230))
    d.line(up, w=1.3); d.line(low, w=1.3)
    d.circle(50, 60, 5, w=1.0)
    d.rect(47.5, 8, 52.5, 46, w=1.0)
    d.rrect(46, 2, 54, 12, 2, w=1.0)
    for y in (16, 24, 32, 40):
        d.seg(47.5, y, 52.5, y, w=0.4)
    d.rect(44, 76, 56, 79, w=0.8)
    for x in (48.5, 50, 51.5):
        d.seg(x, 12, x, 77, w=0.25, wobble=0.05)


def inst_guitarra(d):
    body = d.bez((40, 56), (26, 50), (24, 70), (30, 80), n=20) + d.bez((30, 80), (38, 94), (64, 94), (70, 80), n=20)[1:] \
        + d.bez((70, 80), (76, 68), (70, 54), (62, 50), n=20)[1:] + d.bez((62, 50), (58, 56), (54, 58), (54, 50), n=12)[1:] \
        + [(46, 50)] + d.bez((46, 50), (46, 58), (42, 58), (40, 56), n=10)[1:]
    d.poly(body, w=1.3)
    d.rect(46, 8, 54, 66, w=1.0)
    d.poly([(45, 8), (44, 0), (56, 0), (55, 8)], w=1.0)
    d.rect(42, 68, 58, 72, w=0.8); d.rect(42, 76, 58, 80, w=0.8)
    d.circle(64, 82, 2, w=0.6); d.circle(60, 87, 2, w=0.6)
    d.seg(70, 72, 84, 66, w=0.7)


def inst_pandeiro(d):
    d.circle(50, 50, 34, w=1.4)
    d.circle(50, 50, 28, w=0.8)
    for a in range(0, 360, 45):
        r = math.radians(a + 22)
        x, y = 50 + 31 * math.cos(r), 50 + 31 * math.sin(r)
        d.circle(x, y, 2.6, w=0.7); d.dot(x, y, 0.9)
    d.arc(50, 50, 20, 20, 200, 250, w=0.5)


def inst_mic(d):
    d.circle(50, 26, 16, w=1.3)
    d.hatch(34, 10, 66, 42, gap=3, angle=45, clip=lambda x, y: math.hypot(x - 50, y - 26) < 15, w=0.4)
    d.hatch(34, 10, 66, 42, gap=3, angle=-45, clip=lambda x, y: math.hypot(x - 50, y - 26) < 15, w=0.4)
    d.rect(41, 42, 59, 47, w=1.0)
    d.poly([(43, 47), (57, 47), (54, 94), (46, 94)], w=1.3)
    d.seg(46, 70, 54, 70, w=0.5)


def inst_skate(d):
    d.line(d.bez((8, 52), (10, 44), (16, 46), (22, 50)) + [(78, 50)] + d.bez((78, 50), (84, 46), (90, 44), (92, 52)), w=1.3)
    d.line([(8, 52), (12, 56), (88, 56), (92, 52)], w=1.1)
    d.rect(24, 56, 34, 60, w=0.8); d.rect(66, 56, 76, 60, w=0.8)
    for x in (24, 34, 66, 76):
        d.circle(x, 64, 4, w=1.0)


def inst_estrela(d):
    star(d, 50, 50, 38)
    star(d, 50, 50, 26)


def inst_nota(d):
    d.ellipse(36, 76, 10, 7.5, w=1.2); d.fill(d.ellipse_pts(36, 76, 10, 7.5))
    d.ellipse(70, 68, 10, 7.5, w=1.2); d.fill(d.ellipse_pts(70, 68, 10, 7.5))
    d.seg(45, 76, 45, 18, w=1.4); d.seg(79, 68, 79, 10, w=1.4)
    beam = [(45, 18), (79, 10), (79, 20), (45, 28)]
    d.poly(beam, w=1.0); d.fill(beam)


def vinyl(d, cx, cy, r):
    d.circle(cx, cy, r, w=1.3)
    for k in (0.86, 0.74, 0.62):
        d.circle(cx, cy, r * k, w=0.35)
    d.circle(cx, cy, r * 0.36, w=1.0)
    d.dot(cx, cy, 1.2)
    d.arc(cx, cy, r * 0.8, r * 0.8, 200, 245, w=0.7)


def artist_icon(d, nome, inst):
    vinyl(d, 32, 38, 26)
    _at(d, 78, 38, 0.5, inst)
    linhas = nome.split("\n")
    longest = max(len(l) for l in linhas)
    size = min(10, 150 / max(longest, 1))
    y0 = 80 if len(linhas) == 1 else 76
    for i, l in enumerate(linhas):
        d.text(50, y0 + i * size * 1.15, l, size=size, bold=True)
    d.curve((14, 96), (40, 93), (60, 93), (86, 96), w=0.5)


# ---------- gêneros ----------
@icon("musica-mpb")
def _(d):
    _at(d, 44, 50, 0.95, inst_violao)
    _at(d, 80, 26, 0.3, inst_nota)
    star(d, 18, 20, 3); star(d, 84, 74, 2.5)


@icon("musica-samba")
def _(d):
    _at(d, 44, 54, 0.8, inst_pandeiro)
    d.seg(70, 16, 90, 40, w=1.4)
    d.circle(70, 16, 2.2, w=0.9)
    for (x, y) in ((80, 70), (88, 82)):
        _at(d, x, y, 0.18, inst_nota)
    d.text(16, 14, "♪", size=10)


@icon("musica-pop")
def _(d):
    _at(d, 46, 52, 0.85, inst_mic)
    for x, y, r in ((80, 20, 6), (18, 26, 4.5), (82, 62, 3.5), (16, 70, 3)):
        star(d, x, y, r)
    for a in (-60, -30, 0):
        r = math.radians(a)
        d.seg(46 + 20 * math.cos(r), 26 + 20 * math.sin(r), 46 + 26 * math.cos(r), 26 + 26 * math.sin(r), w=0.6)


@icon("musica-rap")
def _(d):
    # boombox
    d.rrect(8, 34, 92, 80, 5, w=1.4)
    d.line([(26, 34), (30, 18), (70, 18), (74, 34)], w=1.2)
    d.line([(32, 34), (35, 23), (65, 23), (68, 34)], w=0.6)
    for cx in (26, 74):
        d.circle(cx, 60, 13, w=1.2); d.circle(cx, 60, 8, w=0.7); d.dot(cx, 60, 2)
    d.rrect(42, 52, 58, 66, 2, w=0.9)
    d.circle(46.5, 59, 2, w=0.5); d.circle(53.5, 59, 2, w=0.5)
    for x in (42, 47, 52, 57):
        d.rect(x, 40, x + 3, 44, w=0.6)
    d.text(20, 42, "♪", size=6); d.text(84, 26, "♫", size=9)


# ---------- artistas ----------
ARTISTAS = [
    ("paralamas-do-sucesso", "Paralamas\ndo Sucesso", inst_guitarra),
    ("lulu-santos", "Lulu Santos", inst_guitarra),
    ("nando-reis", "Nando Reis", inst_violao),
    ("mac-miller", "Mac Miller", inst_mic),
    ("sza", "SZA", inst_estrela),
    ("gonzaguinha", "Gonzaguinha", inst_violao),
    ("gal-costa", "Gal Costa", inst_violao),
    ("caetano-veloso", "Caetano\nVeloso", inst_violao),
    ("chico-buarque", "Chico\nBuarque", inst_violao),
    ("milton-nascimento", "Milton\nNascimento", inst_violao),
    ("gilberto-gil", "Gilberto Gil", inst_violao),
    ("roberto-carlos", "Roberto\nCarlos", inst_mic),
    ("erasmo-carlos", "Erasmo\nCarlos", inst_guitarra),
    ("humberto-gessinger", "Humberto\nGessinger", inst_guitarra),
    ("sant", "Sant", inst_mic),
    ("racionais", "Racionais", inst_mic),
    ("marcelo-d2", "Marcelo D2", inst_pandeiro),
    ("charlie-brown-jr", "Charlie\nBrown Jr.", inst_skate),
    ("skank", "Skank", inst_guitarra),
    ("alcione", "Alcione", inst_pandeiro),
    ("beth-carvalho", "Beth\nCarvalho", inst_pandeiro),
    ("eminem", "Eminem", inst_mic),
    ("kendrick-lamar", "Kendrick\nLamar", inst_mic),
    ("justin-bieber", "Justin\nBieber", inst_estrela),
    ("michael-jackson", "Michael\nJackson", inst_estrela),
    ("belo", "Belo", inst_pandeiro),
    ("don-l", "Don L", inst_mic),
    ("zeca-pagodinho", "Zeca\nPagodinho", inst_pandeiro),
]
for _slug, _nome, _inst in ARTISTAS:
    icon(f"artista-{_slug}")(lambda d, n=_nome, f=_inst: artist_icon(d, n, f))


# ======================= LOTE 4 =======================
@icon("beyblade")
def _(d):
    # pião de batalha girando: anel de ataque, disco, ponta + linhas de giro e faíscas
    d.ellipse(46, 46, 34, 10, w=1.4)
    pts = []
    for i in range(12):
        a = i * 2 * math.pi / 12
        rr = 34 if i % 2 == 0 else 27
        pts.append((46 + rr * math.cos(a), 46 + rr * 0.3 * math.sin(a)))
    d.poly(pts, w=0.8)
    d.line(d.bez((12, 46), (14, 60), (30, 64), (46, 64)) + d.bez((46, 64), (62, 64), (78, 60), (80, 46))[1:], w=1.3)
    d.ellipse(46, 40, 12, 4, w=1.0)
    d.ellipse(46, 38, 6, 2, w=0.8); d.dot(46, 38, 1)
    d.poly([(36, 64), (56, 64), (48, 82), (44, 82)], w=1.2)
    d.ellipse(46, 88, 26, 4, w=0.5)
    for r, a0, a1 in ((40, 200, 280), (44, 260, 330), (42, 20, 80), (46, 110, 160)):
        d.arc(46, 50, r, r * 0.4, a0, a1, w=0.6)
    for x, y in ((84, 72), (88, 66), (82, 80)):
        d.seg(78, 74, x + 2, y, w=0.6)
    # lançador
    d.rrect(64, 8, 94, 18, 3, w=1.0)
    d.seg(70, 18, 70, 26, w=0.8); d.seg(88, 18, 88, 26, w=0.8)
    d.line([(94, 13), (98, 13)], w=0.8)


@icon("sonho-viajar-o-mundo")
def _(d):
    d.circle(46, 54, 32, w=1.4)
    d.arc(46, 54, 14, 32, -90, 90, w=0.6); d.arc(46, 54, 14, 32, 90, 270, w=0.6)
    d.seg(46, 22, 46, 86, w=0.6); d.seg(14, 54, 78, 54, w=0.6)
    d.arc(46, 54, 30, 10, 180, 360, w=0.5); d.arc(46, 54, 30, 10, 0, 180, w=0.5)
    # rota tracejada + aviãozinho
    path = d.bez((10, 30), (20, 6), (60, 4), (80, 22), n=40)
    for i in range(0, 36, 4):
        d.line(path[i:i + 2 + 1], w=0.6)
    d.push(0, 0, 1)
    d.poly([(80, 22), (90, 28), (86, 30), (82, 26)], w=0.9)
    d.poly([(83, 24), (88, 18), (90, 20), (86, 26)], w=0.8)
    d.poly([(84, 27), (82, 33), (85, 33), (87, 28)], w=0.8)
    d.pop()
    # pinos
    for x, y in ((34, 44), (60, 64)):
        d.circle(x, y - 4, 3, w=0.9); d.seg(x, y - 1, x, y + 3, w=0.9)
    d.seg(28, 92, 64, 92, w=0.6)


@icon("sonho-vida-financeira-saudavel")
def _(d):
    # cofrinho com coração + plantinha crescendo das moedas
    d.push(-7, 0, 0.95)
    body = d.ellipse_pts(46, 60, 30, 22)
    d.poly(body, w=1.4)
    d.poly([(28, 42), (26, 32), (36, 38)], w=1.0)
    d.ellipse(76, 60, 5, 6, w=1.0)
    d.dot(74.5, 58, 0.8); d.dot(77.5, 58, 0.8)
    d.dot(60, 52, 1.3)
    d.rect(36, 34, 52, 37, w=0.9)
    for x in (26, 38, 54, 64):
        d.rect(x, 78, x + 6, 88, w=1.0)
    d.curve((18, 58), (10, 56), (10, 48), (16, 50), w=0.8)
    heart(d, 46, 62, 8)
    d.pop()
    # moedas + broto
    for i in range(3):
        d.ellipse(84, 88 - i * 4, 8, 2.4, w=0.9)
    d.seg(84, 78, 84, 64, w=0.9)
    d.curve((84, 70), (78, 64), (76, 68), (84, 70), w=0.8)
    d.curve((84, 66), (90, 58), (94, 62), (84, 66), w=0.8)
    d.text(84, 12, "$", size=10, bold=True)
    d.curve((6, 92), (40, 94), (70, 94), (96, 92), w=0.5)


@icon("sonho-amigos-e-familia-realizando-sonhos")
def _(d):
    # bonequinhos comemorando, braços pra cima, com estrelas e confete
    for x, s in ((20, 0.9), (38, 1.0), (58, 1.1), (78, 0.85)):
        h = 30 * s
        feet = 86
        d.circle(x, feet - h - 4, 4 * s, w=1.0)
        d.seg(x, feet - h, x, feet - h * 0.4, w=1.0)
        d.seg(x, feet - h * 0.4, x - 4 * s, feet, w=1.0); d.seg(x, feet - h * 0.4, x + 4 * s, feet, w=1.0)
        d.seg(x, feet - h * 0.85, x - 6 * s, feet - h * 1.25, w=1.0)
        d.seg(x, feet - h * 0.85, x + 6 * s, feet - h * 1.25, w=1.0)
    for x, y, r in ((50, 12, 6), (24, 18, 3.5), (78, 16, 4), (90, 40, 2.5), (8, 40, 2.5)):
        star(d, x, y, r, filled=(r < 4))
    for x, y in ((36, 28), (64, 26), (14, 30), (86, 28), (44, 20)):
        d.seg(x, y, x + 2, y + 2, w=0.6)
    d.seg(6, 86, 94, 86, w=0.9)


@icon("sonho-bom-desenvolvedor")
def _(d):
    # escada subindo até uma bandeira com </>
    pts = [(8, 88)]
    x, y = 8, 88
    for _ in range(5):
        pts += [(x, y - 12), (x + 14, y - 12)]
        x, y = x + 14, y - 12
    d.line(pts, w=1.2)
    d.seg(8, 88, 92, 88, w=1.0)
    d.seg(78, 28, 78, 6, w=1.1)
    d.poly([(78, 6), (98, 10), (78, 16)], w=1.0)
    d.text(86, 11, "</>", size=4, bold=True)
    person(d, 30, 64, 0.75)
    for i, lbl in enumerate(("jr", "pl", "sr")):
        d.text(15 + i * 14 + 14, 80 - i * 12, lbl, size=4.2)
    for a in (200, 240, 280, 320):
        r = math.radians(a)
        d.seg(78 + 12 * math.cos(r), 12 + 12 * math.sin(r), 78 + 16 * math.cos(r), 12 + 16 * math.sin(r), w=0.5)


@icon("sonho-solucoes-que-ajudam-pessoas")
def _(d):
    # lâmpada com coração dentro, apoiada em duas mãos
    bulb = d.bez((38, 56), (24, 44), (28, 14), (50, 14), n=24) + d.bez((50, 14), (72, 14), (76, 44), (62, 56), n=24)[1:]
    d.line(bulb, w=1.4)
    d.seg(38, 56, 38, 64, w=1.1); d.seg(62, 56, 62, 64, w=1.1)
    for y in (64, 68, 72):
        d.rrect(38, y, 62, y + 3.6, 1.5, w=0.8)
    heart(d, 50, 36, 9)
    for a in (180, 215, 250, 290, 325, 360):
        r = math.radians(a)
        d.seg(50 + 30 * math.cos(r), 34 + 30 * math.sin(r), 50 + 36 * math.cos(r), 34 + 36 * math.sin(r), w=0.7)
    # mãos
    d.curve((6, 74), (20, 70), (30, 78), (40, 80), w=1.1)
    d.curve((6, 88), (24, 88), (40, 86), (50, 82), w=1.1)
    d.curve((94, 74), (80, 70), (70, 78), (60, 80), w=1.1)
    d.curve((94, 88), (76, 88), (60, 86), (50, 82), w=1.1)
    d.curve((40, 80), (44, 78), (46, 80), (44, 83), w=0.7)
    d.curve((60, 80), (56, 78), (54, 80), (56, 83), w=0.7)


# ======================= LOTE 5: RAFAEL =======================
RCX, RCY = 42, 48  # centro do rosto


def _rafael_base(d, hide_collar=False):
    cx, cy = RCX, RCY
    # rosto (sem o topo, que é cabelo)
    d.arc(cx, cy, 19, 22, -18, 198, w=1.3)
    # orelhas
    d.arc(cx - 19.5, cy + 3, 3.2, 5, 90, 270, w=1.0)
    d.arc(cx + 19.5, cy + 3, 3.2, 5, -90, 90, w=1.0)
    # cabelo: volume em cima, linha de cabelo na testa
    outer = d.ellipse_pts(cx, cy - 4, 21.5, 27, math.radians(195), math.radians(345), n=40)
    hairline = d.bez((cx + 20.8, cy - 11), (cx + 16, cy - 19), (cx - 16, cy - 19), (cx - 20.8, cy - 11), n=30)
    d.line(outer, w=1.2)
    d.line(hairline, w=0.9)
    region = outer + hairline
    clip = inside_poly(region)
    rng = random.Random(42)
    row = 0
    y = cy - 30.5
    while y < cy - 11:
        x = cx - 22 + (row % 2) * 1.2
        while x < cx + 22:
            if clip(x, y):
                a0 = rng.uniform(0, 360)
                d.arc(x, y, 1.05, 0.95, a0, a0 + 290, w=0.5, wobble=0.08)
            x += 2.3
        y += 1.9
        row += 1
    # laterais raspadas (degradê): risquinhos curtos
    for side in (-1, 1):
        for i in range(7):
            y = cy - 12 + i * 1.6
            x = cx + side * (19.6 - i * 0.15)
            d.seg(x, y, x - side * 1.6, y + 0.8, w=0.4)
    # nariz
    d.curve((cx - 1, cy + 2), (cx - 3, cy + 7), (cx - 1, cy + 9), (cx + 2, cy + 8.5), w=0.9)
    # bigode
    d.line(d.bez((cx - 7.5, cy + 17.5), (cx - 7, cy + 12.5), (cx - 3, cy + 11.8), (cx, cy + 12.4), n=20), w=1.5)
    d.line(d.bez((cx, cy + 12.4), (cx + 3, cy + 11.8), (cx + 7, cy + 12.5), (cx + 7.5, cy + 17.5), n=20), w=1.5)
    # cavanhaque
    goat = d.bez((cx - 5, cy + 20), (cx - 4, cy + 24), (cx + 4, cy + 24), (cx + 5, cy + 20), n=16)
    d.hatch(cx - 6, cy + 18, cx + 6, cy + 24, gap=0.9, angle=80,
            clip=inside_poly(goat + [(cx + 3, cy + 18.5), (cx - 3, cy + 18.5)]), w=0.45)
    # pescoço + camiseta
    if not hide_collar:
        d.seg(cx - 6, cy + 20, cx - 6, cy + 28, w=1.0)
        d.seg(cx + 6, cy + 20, cx + 6, cy + 28, w=1.0)
        d.arc(cx, cy + 27, 10, 4, 0, 180, w=1.0)
        d.arc(cx, cy + 27, 10, 6.5, 10, 170, w=0.5)
    d.curve((cx - 10, cy + 28), (cx - 22, cy + 30), (cx - 34, cy + 36), (cx - 38, cy + 52), w=1.3)
    d.curve((cx + 10, cy + 28), (cx + 22, cy + 30), (cx + 34, cy + 36), (cx + 38, cy + 52), w=1.3)
    d.seg(cx - 26, cy + 44, cx - 24, cy + 52, w=0.6)
    d.seg(cx + 26, cy + 44, cx + 24, cy + 52, w=0.6)


@icon("rafael-1-pensando")
def _(d):
    cx, cy = RCX, RCY
    _rafael_base(d, hide_collar=True)
    # sobrancelhas grossas, uma levemente erguida
    d.curve((cx - 12, cy - 6), (cx - 9, cy - 8), (cx - 5, cy - 7.5), w=1.7)
    d.curve((cx + 4, cy - 8), (cx + 8, cy - 10), (cx + 12, cy - 8), w=1.7)
    # olhos olhando pra cima/direita
    d.dot(cx - 7, cy - 2.5, 1.6); d.dot(cx + 9, cy - 3, 1.6)
    # boca fechada pensativa
    d.curve((cx - 3, cy + 16), (cx, cy + 16.4), (cx + 3.5, cy + 15.6), w=0.8)
    # punho no queixo
    fist = d.bez((cx - 9, cy + 24), (cx - 10, cy + 19), (cx + 6, cy + 18), (cx + 8, cy + 22), n=20) \
        + d.bez((cx + 8, cy + 22), (cx + 10, cy + 28), (cx + 6, cy + 33), (cx - 2, cy + 33), n=20)[1:] \
        + d.bez((cx - 2, cy + 33), (cx - 8, cy + 33), (cx - 10, cy + 29), (cx - 9, cy + 24), n=20)[1:]
    d.poly(fist, w=1.2)
    for y in (cy + 24, cy + 27.5, cy + 30.5):
        d.curve((cx - 6, y), (cx - 2, y - 1), (cx + 3, y - 0.5), w=0.6)
    d.curve((cx + 7, cy + 24), (cx + 3, cy + 22), (cx - 2, cy + 22), w=0.7)
    # antebraço + relógio
    d.seg(cx - 7, cy + 32, cx - 13, cy + 52, w=1.2)
    d.seg(cx + 4, cy + 33, cx - 1, cy + 52, w=1.2)
    d.poly([(cx - 9.5, cy + 40), (cx + 2.5, cy + 41), (cx + 1.5, cy + 45), (cx - 10.5, cy + 44)], w=0.9)
    d.hatch(cx - 11, cy + 40, cx + 3, cy + 45, gap=1.2, angle=80,
            clip=inside_poly([(cx - 9.5, cy + 40), (cx + 2.5, cy + 41), (cx + 1.5, cy + 45), (cx - 10.5, cy + 44)]), w=0.4)
    # balão de pensamento "..."
    d.circle(68, 30, 1.4, w=0.7); d.circle(73, 23, 2.2, w=0.8)
    cloud = []
    for i in range(10):
        a = i * 2 * math.pi / 10
        cloud += d.ellipse_pts(84 + 11 * math.cos(a), 11 + 6 * math.sin(a), 4.2, 4.2, a - 1.6, a + 1.6, n=10)
    d.poly(cloud, w=0.9)
    for x in (79, 84, 89):
        d.dot(x, 11, 1.2)


@icon("rafael-2-sorrindo")
def _(d):
    cx, cy = RCX, RCY
    _rafael_base(d)
    # sobrancelhas erguidas/relaxadas
    d.curve((cx - 12, cy - 7), (cx - 9, cy - 10), (cx - 5, cy - 8.5), w=1.7)
    d.curve((cx + 5, cy - 8.5), (cx + 9, cy - 10), (cx + 12, cy - 7), w=1.7)
    # olhos fechadinhos de felicidade
    d.arc(cx - 8, cy - 1, 3, 2.4, 200, 340, w=1.0)
    d.arc(cx + 8, cy - 1, 3, 2.4, 200, 340, w=1.0)
    # bochechas
    d.seg(cx - 14, cy + 6, cx - 12, cy + 7.5, w=0.5); d.seg(cx - 12.5, cy + 5, cx - 10.5, cy + 6.5, w=0.5)
    d.seg(cx + 14, cy + 6, cx + 12, cy + 7.5, w=0.5); d.seg(cx + 12.5, cy + 5, cx + 10.5, cy + 6.5, w=0.5)
    # sorriso aberto
    smile = d.bez((cx - 6, cy + 14.5), (cx - 2, cy + 14), (cx + 2, cy + 14), (cx + 6, cy + 14.5), n=12)         + d.bez((cx + 6, cy + 14.5), (cx + 4, cy + 20), (cx - 4, cy + 20), (cx - 6, cy + 14.5), n=16)[1:]
    d.poly(smile, w=1.0)
    d.curve((cx - 5, cy + 16), (cx, cy + 16.8), (cx + 5, cy + 16), w=0.5)
    # brilhos
    for x, y, r in ((80, 14, 5), (90, 28, 3), (72, 8, 2.5), (10, 14, 3)):
        star(d, x, y, r, filled=(r < 3))


@icon("rafael-3-duvida")
def _(d):
    cx, cy = RCX, RCY
    _rafael_base(d)
    # uma sobrancelha lá em cima, outra franzida
    d.curve((cx - 12, cy - 9), (cx - 9, cy - 14), (cx - 5, cy - 11), w=1.7)
    d.curve((cx + 4, cy - 6), (cx + 8, cy - 6.5), (cx + 12, cy - 8), w=1.7)
    d.circle(cx - 8, cy - 2, 2.6, w=0.8); d.dot(cx - 8, cy - 2, 1.3)
    d.dot(cx + 8, cy - 1.5, 1.5)
    # boca torta
    d.curve((cx - 4, cy + 16.5), (cx - 1, cy + 15.5), (cx + 2, cy + 17), (cx + 5, cy + 15.5), w=0.9)
    # mão coçando a cabeça (braço direito levantado)
    d.curve((cx + 32, cy + 52), (cx + 35, cy + 36), (cx + 33, cy + 20), (cx + 28, cy + 4), w=1.2)
    d.curve((cx + 25, cy + 52), (cx + 28, cy + 36), (cx + 27, cy + 22), (cx + 22, cy + 10), w=1.2)
    hand = d.bez((cx + 22, cy + 10), (cx + 14, cy + 4), (cx + 12, cy - 8), (cx + 18, cy - 12), n=16) \
        + d.bez((cx + 18, cy - 12), (cx + 26, cy - 14), (cx + 32, cy - 4), (cx + 28, cy + 4), n=16)[1:]
    d.line(hand, w=1.1)
    for i in range(3):
        d.curve((cx + 17 + i * 3, cy - 10 - i * 0.5), (cx + 19 + i * 3, cy - 5), (cx + 21 + i * 3, cy - 2), w=0.6)
    d.poly([(cx + 26.5, cy + 25), (cx + 33.5, cy + 24), (cx + 33.5, cy + 28), (cx + 26.5, cy + 29)], w=0.8)
    # gotinha de suor
    d.line(d.bez((cx - 22, cy - 14), (cx - 25, cy - 9), (cx - 25, cy - 6)) + d.bez((cx - 25, cy - 6), (cx - 22, cy - 5), (cx - 22, cy - 14))[1:], w=0.8)
    # "?"
    d.rrect(72, 2, 90, 24, 4, w=1.0)
    d.poly([(76, 24), (74, 30), (81, 24)], w=0.9)
    d.text(81, 13, "?", size=14, bold=True)


# ======================= QUADRINHO PENDURADO =======================
def framed(fn, seed):
    d = Doodle(100, 118, seed=seed)
    d.dot(50, 6, 1.8)
    d.line([(20, 34), (50, 6), (80, 34)], w=0.7)
    d.rect(16, 30, 84, 98, w=1.1)
    d.rect(18.5, 32.5, 81.5, 95.5, w=0.5)
    d.push(22, 36, 0.56)
    d.width = 1.25
    fn(d)
    d.pop()
    return d


def main():
    names = list(ICONS)
    for i, name in enumerate(names):
        d = Doodle(seed=i + 3)
        ICONS[name](d)
        d.save(OUT / f"{name}.png")
        framed(ICONS[name], i + 3).save(OUT / "framed" / f"{name}.png")
    print(f"{len(names)} ícones gerados em {OUT}")


if __name__ == "__main__":
    main()
