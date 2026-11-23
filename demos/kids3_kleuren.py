import os; os.environ["LANDSCAPE"] = "1"
from lib import *
import random

random.seed(6)
COLS = [("ROOD", (240, 60, 70)), ("BLAUW", (50, 120, 240)), ("GEEL", (250, 205, 30)), ("GROEN", (60, 190, 90))]
GROUND = 600
R = 70
SEG = 1.15                    # seconds per colour
X_START, X_END = 180, 1100


def P(pts): return [(x * SS, y * SS) for x, y in pts]


def ball_state(t):
    """ball bounces once per colour segment, moving left -> right"""
    i = min(int(t // SEG), len(COLS) - 1)
    u = ((t - i * SEG) % SEG) / SEG
    x = X_START + (X_END - X_START) * min(t / (SEG * len(COLS)), 1)
    h = 240 * 4 * u * (1 - u)                    # parabola, lands at u=0 and u=1
    y = GROUND - R - h
    squash = max(0, 1 - min(u, 1 - u) / 0.07) * 0.35   # squash near the ground
    return i, x, y, squash


bg = vgradient(RW, RH, (255, 248, 236), (255, 236, 220))
bd = ImageDraw.Draw(bg)
bd.rectangle([0, GROUND * SS, RW, RH], fill=(255, 226, 200))
bd.line([(0, GROUND * SS), (RW, GROUND * SS)], fill=(235, 190, 160), width=6 * SS)


def boing(f0=200): return sweep(f0, f0 * 3, 0.25) * env(0.25, 0.003, 0.12) * 0.5


splats = []
with Video("kids3_kleuren.mp4") as v:
    melody = [67, 72, 76, 79]
    for i in range(len(COLS) + 1):
        tb = i * SEG
        if tb < 5:
            v.sfx(tb, boing(200 + i * 30), 0.9)
        if i < len(COLS):
            v.sfx(tb + 0.05, pluck(note(melody[i])), 0.9); v.sfx(tb + 0.05, pluck(note(melody[i] - 12)), 0.4)
    v.audio += beat(5, bpm=104, kick_steps=(0, 8), snare_steps=(4, 12), gain=0.15)
    for f in range(v.nframes):
        t = f / FPS
        i, x, y, sq = ball_state(t)
        name, c = COLS[i]
        # paint splats left on the floor at every landing
        for k in range(i + 1):
            if len(splats) <= k:
                sx = X_START + (X_END - X_START) * (k * SEG) / (SEG * len(COLS))
                splats.append((sx, COLS[k][1], [(random.uniform(-1, 1), random.uniform(0.3, 1)) for _ in range(7)]))
        img = bg.copy(); d = ImageDraw.Draw(img, "RGBA")
        for k, (sx, sc, drops) in enumerate(splats):
            age = t - k * SEG
            g = ease(min(age / 0.2, 1))
            d.ellipse([(sx - 90 * g) * SS, (GROUND - 8) * SS, (sx + 90 * g) * SS, (GROUND + 14) * SS], fill=sc)
            for dx, dy in drops:
                if age < 0.5:
                    px = sx + dx * 160 * age * 2; py = GROUND - 10 - math.sin(min(age / 0.5, 1) * math.pi) * 70 * dy
                    d.ellipse([(px - 9) * SS, (py - 9) * SS, (px + 9) * SS, (py + 9) * SS], fill=sc)
        # shadow
        hgt = GROUND - R - y
        sw = 70 * (1 - hgt / 600)
        d.ellipse([(x - sw) * SS, (GROUND - 6) * SS, (x + sw) * SS, (GROUND + 6) * SS], fill=(0, 0, 0, 40))
        # ball with squash & stretch
        rx = R * (1 + sq); ry = R * (1 - sq)
        cy = GROUND - ry if sq > 0 else y
        d.ellipse([(x - rx) * SS, (cy - ry) * SS, (x + rx) * SS, (cy + ry) * SS], fill=c, outline=tuple(int(v * 0.75) for v in c), width=5 * SS)
        d.ellipse([(x - rx * 0.55) * SS, (cy - ry * 0.65) * SS, (x - rx * 0.1) * SS, (cy - ry * 0.25) * SS], fill=(255, 255, 255, 150))
        # face
        for s in (-1, 1):
            d.ellipse([(x + s * 22 - 9) * SS, (cy - 18) * SS, (x + s * 22 + 9) * SS, (cy + 2) * SS], fill=(30, 30, 40))
        d.arc([(x - 22) * SS, (cy - 6) * SS, (x + 22) * SS, (cy + 26) * SS], 20, 160, fill=(30, 30, 40), width=5 * SS)
        # word
        u = (t - i * SEG)
        k = ease_out_back(min(u / 0.3, 1))
        text(d, (W / 2, 140), name, int(50 + 60 * k), c, stroke=8, stroke_fill=(255, 255, 255))
        text(d, (W / 2, 50), "Welke kleur is de bal?", 34, (150, 110, 90), bold=False)
        v.add(img)
