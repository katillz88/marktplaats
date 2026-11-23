import os; os.environ["LANDSCAPE"] = "1"
from lib import *
import random

random.seed(3)
EX, EY = 640, 470            # egg center
HATCH = 2.9
NAME = "BLOBBY"
BODY = (178, 140, 255)


def P(pts): return [(x * SS, y * SS) for x, y in pts]


def rot(pts, cx, cy, a):
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


def egg_shape(cx, cy, w=125, h=165, n=80):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        k = 1 - 0.18 * math.sin(a) if math.sin(a) < 0 else 1    # narrower top
        pts.append((cx + math.cos(a) * w * k, cy + math.sin(a) * h))
    return pts


CRACK = [(EX - 125, EY - 10), (EX - 85, EY - 40), (EX - 50, EY + 5), (EX - 15, EY - 45), (EX + 20, EY + 0),
         (EX + 55, EY - 40), (EX + 90, EY + 0), (EX + 125, EY - 25)]
SPOTS = [(-50, -60, 22), (40, -95, 16), (60, 30, 26), (-60, 70, 18), (5, 110, 14), (-15, 0, 12)]


def wobble_angle(t):
    if t < 0.4: return 0
    if t >= HATCH: return 0
    amp = 0.05 + 0.18 * (t - 0.4) / (HATCH - 0.4)
    return math.sin((t - 0.4) * 14) * amp


def draw_egg(d, t, a, crack_u):
    pts = rot(egg_shape(EX, EY), EX, EY + 160, a)
    d.polygon(P(pts), fill=(255, 250, 235), outline=(90, 70, 90), width=5 * SS)
    for sx, sy, r in SPOTS:
        cx, cy = rot([(EX + sx, EY + sy)], EX, EY + 160, a)[0]
        d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=(120, 220, 190))
    if crack_u > 0:
        n = max(2, int(len(CRACK) * crack_u))
        cp = rot(CRACK[:n], EX, EY + 160, a)
        d.line(P(cp), fill=(90, 70, 90), width=5 * SS, joint="curve")


def draw_monster(d, t, cx, base_y, squash, blink):
    w = 120 * (1 + squash * 0.25); h = 115 * (1 - squash * 0.25)
    top = base_y - 2 * h
    # ears / little horns
    for s in (-1, 1):
        d.polygon(P([(cx + s * 55, top + 30), (cx + s * 95, top - 40), (cx + s * 105, top + 50)]), fill=BODY, outline=(70, 50, 110), width=4 * SS)
    # feet
    for s in (-1, 1):
        d.ellipse([(cx + s * 60 - 32) * SS, (base_y - 24) * SS, (cx + s * 60 + 32) * SS, (base_y + 10) * SS], fill=(150, 110, 235), outline=(70, 50, 110), width=4 * SS)
    d.ellipse([(cx - w) * SS, top * SS, (cx + w) * SS, base_y * SS], fill=BODY, outline=(70, 50, 110), width=5 * SS)
    d.ellipse([(cx - w * 0.6) * SS, (top + h * 0.9) * SS, (cx + w * 0.6) * SS, (base_y - 8) * SS], fill=(210, 190, 255))
    # eyes
    ey = top + h * 0.75
    for s in (-1, 1):
        ex = cx + s * 45
        if blink:
            d.arc([(ex - 26) * SS, (ey - 10) * SS, (ex + 26) * SS, (ey + 20) * SS], 200, 340, fill=(40, 30, 60), width=6 * SS)
        else:
            d.ellipse([(ex - 30) * SS, (ey - 34) * SS, (ex + 30) * SS, (ey + 34) * SS], fill=(255, 255, 255), outline=(40, 30, 60), width=4 * SS)
            d.ellipse([(ex - 17 + s * 3) * SS, (ey - 16) * SS, (ex + 17 + s * 3) * SS, (ey + 22) * SS], fill=(40, 30, 60))
            d.ellipse([(ex - 9 + s * 3) * SS, (ey - 10) * SS, (ex + 1 + s * 3) * SS, (ey) * SS], fill=(255, 255, 255))
        d.ellipse([(ex + s * 22 - 18) * SS, (ey + 34) * SS, (ex + s * 22 + 18) * SS, (ey + 50) * SS], fill=(255, 150, 190))
    # smile
    d.arc([(cx - 28) * SS, (ey + 18) * SS, (cx + 28) * SS, (ey + 60) * SS], 20, 160, fill=(40, 30, 60), width=6 * SS)


def sky():
    img = vgradient(RW, RH, (140, 210, 255), (215, 240, 255))
    d = ImageDraw.Draw(img)
    for cx, cy, s in ((200, 130, 1.0), (1040, 100, 0.8), (760, 190, 0.6)):
        for dx, dy, r in ((0, 0, 50), (45, -20, 60), (95, 0, 48), (45, 15, 50)):
            d.ellipse([(cx + dx * s - r * s) * SS, (cy + dy * s - r * s) * SS, (cx + dx * s + r * s) * SS, (cy + dy * s + r * s) * SS], fill=(255, 255, 255))
    d.ellipse([-300 * SS, 560 * SS, 900 * SS, 1100 * SS], fill=(120, 205, 110))
    d.ellipse([500 * SS, 580 * SS, 1600 * SS, 1100 * SS], fill=(105, 190, 95))
    for x, y, c in ((150, 640, (255, 120, 150)), (260, 680, (255, 220, 90)), (1060, 650, (255, 255, 255)), (1180, 690, (255, 140, 200))):
        for k in range(5):
            a = k * 2 * math.pi / 5
            d.ellipse([(x + math.cos(a) * 9 - 7) * SS, (y + math.sin(a) * 9 - 7) * SS, (x + math.cos(a) * 9 + 7) * SS, (y + math.sin(a) * 9 + 7) * SS], fill=c)
        d.ellipse([(x - 6) * SS, (y - 6) * SS, (x + 6) * SS, (y + 6) * SS], fill=(255, 200, 60))
    return img


bg = sky()
shells = [dict(vx=random.uniform(-500, 500), vy=random.uniform(-700, -350), va=random.uniform(-8, 8),
               pts=[(random.uniform(-40, 40), random.uniform(-40, 40)) for _ in range(4)]) for _ in range(10)]
sparkles = [dict(a=random.uniform(0, 2 * math.pi), sp=random.uniform(150, 380), c=random.choice([(255, 220, 80), (255, 140, 200), (140, 220, 255)])) for _ in range(18)]


def knock():
    return (sweep(500, 300, 0.07) * env(0.07, 0.001, 0.02) + lowpass(noise(0.07), 2500) * env(0.07, 0.001, 0.01)) * 0.6


def crack(): return (noise(0.12) - lowpass(noise(0.12), 2000)) * env(0.12, 0.0005, 0.02) * 0.9


def boing(): return sweep(180, 620, 0.35) * env(0.35, 0.005, 0.2) * 0.5


with Video("kids1_monster_ei.mp4") as v:
    for i, n in enumerate([60, 64, 67, 64, 62, 65, 69, 65]):
        v.sfx(i * 0.36, pluck(note(n)), 0.25)
    t = 0.4
    while t < HATCH:
        v.sfx(t, knock(), 0.7); t += 0.45 - 0.25 * (t - 0.4) / (HATCH - 0.4)
    v.sfx(1.8, crack(), 0.8); v.sfx(2.4, crack(), 0.9)
    v.sfx(HATCH, crack(), 1.0); v.sfx(HATCH, whoosh(0.3), 0.6)
    v.sfx(HATCH + 0.08, boing(), 1.0)
    for i, n in enumerate([72, 76, 79, 84]): v.sfx(HATCH + 0.15 + i * 0.09, pluck(note(n)), 0.7)
    v.sfx(HATCH + 0.6, pad([note(60), note(64), note(67)], 1.4, 0.08))
    for f in range(v.nframes):
        t = f / FPS
        img = bg.copy(); d = ImageDraw.Draw(img, "RGBA")
        d.ellipse([(EX - 150) * SS, (EY + 145) * SS, (EX + 150) * SS, (EY + 180) * SS], fill=(60, 120, 60, 90))
        if t < HATCH:
            crack_u = 0 if t < 1.8 else min(1, (t - 1.8) / 1.0)
            draw_egg(d, t, wobble_angle(t), crack_u)
            text(d, (W / 2, 80), "Wat zit er in het ei?", 54, (255, 255, 255), stroke=6, stroke_fill=(90, 70, 140))
        else:
            u = t - HATCH
            # bottom half of the shell stays
            half = [p for p in egg_shape(EX, EY) if p[1] > EY - 10]
            # monster pops up with squash & stretch
            jump = max(0, math.sin(min(u / 0.55, 1) * math.pi)) * 140 if u < 0.55 else 0
            squash = 0.5 * math.exp(-u * 5) * math.cos(u * 22) if u > 0.4 else -0.3 * (1 - u / 0.4)
            base = EY + 150 - jump
            blink = 1.9 < u < 2.0
            # bottom shell slides to the left, monster jumps out to the right and lands on the grass
            so = -230 * ease(u / 0.5)
            half_s = [(x + so, y) for x, y in half]
            d.polygon(P(half_s + [(EX + 125 + so, EY - 10)]), fill=(255, 250, 235), outline=(90, 70, 90), width=5 * SS)
            zig = [(EX - 125 + so + k * 25, EY - 10 + (18 if k % 2 else -12)) for k in range(11)]
            d.line(P(zig), fill=(90, 70, 90), width=5 * SS)
            mx = EX + 90 * ease(u / 0.55)
            draw_monster(d, t, mx, base, squash, blink)
            for s in shells:
                sx = EX + s["vx"] * u; sy = EY - 60 + s["vy"] * u + 1400 * u * u
                if sy < 800:
                    pts = rot([(sx + x, sy + y) for x, y in s["pts"]], sx, sy, s["va"] * u)
                    d.polygon(P(pts), fill=(255, 250, 235), outline=(90, 70, 90), width=3 * SS)
            for sp in sparkles:
                if u < 1.2:
                    r = sp["sp"] * min(u, 0.6) * 1.5
                    sx = EX + math.cos(sp["a"]) * r; sy = EY - 40 + math.sin(sp["a"]) * r
                    sz = 14 * (1 - u / 1.2)
                    d.polygon(P([(sx, sy - sz), (sx + sz * 0.3, sy - sz * 0.3), (sx + sz, sy), (sx + sz * 0.3, sy + sz * 0.3),
                                 (sx, sy + sz), (sx - sz * 0.3, sy + sz * 0.3), (sx - sz, sy), (sx - sz * 0.3, sy - sz * 0.3)]), fill=sp["c"])
            if u > 0.5:
                k = ease_out_back((u - 0.5) / 0.4)
                text(d, (W / 2, 70), "Het is...", 40, (255, 255, 255), stroke=5, stroke_fill=(90, 70, 140))
                text(d, (W / 2, 135), NAME + "!", int(30 + 46 * k), (255, 230, 90), stroke=7, stroke_fill=(110, 70, 170))
        v.add(img)
