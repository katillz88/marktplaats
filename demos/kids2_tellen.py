import os; os.environ["LANDSCAPE"] = "1"
from lib import *

N = 5
T0, DT = 0.5, 0.7
XS = [200 + i * 220 for i in range(N)]
WATER_Y = 520
WORDS = ["één", "twee", "drie", "vier", "vijf"]


def P(pts): return [(x * SS, y * SS) for x, y in pts]


def duck(d, x, y, s=1.0, flap=0.0):
    c, dk = (255, 214, 50), (230, 170, 20)
    d.ellipse([(x - 70 * s) * SS, (y - 40 * s) * SS, (x + 60 * s) * SS, (y + 40 * s) * SS], fill=c, outline=dk, width=4 * SS)
    d.polygon(P([(x - 70 * s, y - 10 * s), (x - 100 * s, y - 40 * s), (x - 72 * s, y + 8 * s)]), fill=c, outline=dk)
    wy = y - 5 * s - flap * 20 * s
    d.ellipse([(x - 30 * s) * SS, (wy - 18 * s) * SS, (x + 30 * s) * SS, (wy + 18 * s) * SS], fill=dk)
    hx, hy = x + 45 * s, y - 60 * s
    d.ellipse([(hx - 38 * s) * SS, (hy - 38 * s) * SS, (hx + 38 * s) * SS, (hy + 38 * s) * SS], fill=c, outline=dk, width=4 * SS)
    d.polygon(P([(hx + 28 * s, hy - 2 * s), (hx + 68 * s, hy + 6 * s), (hx + 28 * s, hy + 16 * s)]), fill=(255, 130, 40))
    d.ellipse([(hx + 4 * s) * SS, (hy - 16 * s) * SS, (hx + 20 * s) * SS, (hy) * SS], fill=(30, 30, 40))
    d.ellipse([(hx + 8 * s) * SS, (hy - 13 * s) * SS, (hx + 13 * s) * SS, (hy - 8 * s) * SS], fill=(255, 255, 255))
    d.ellipse([(hx - 10 * s) * SS, (hy + 8 * s) * SS, (hx + 8 * s) * SS, (hy + 18 * s) * SS], fill=(255, 160, 170))


bg = vgradient(RW, RH, (150, 215, 255), (225, 245, 255))
bd = ImageDraw.Draw(bg)
bd.ellipse([1050 * SS, 40 * SS, 1190 * SS, 180 * SS], fill=(255, 225, 90))
bd.rectangle([0, WATER_Y * SS, RW, RH], fill=(80, 170, 235))
for k in range(9):
    y = WATER_Y + 30 + k * 22
    for x in range(-40 + (k % 2) * 60, 1300, 120):
        bd.arc([x * SS, y * SS, (x + 60) * SS, (y + 16) * SS], 200, 340, fill=(150, 210, 250), width=3 * SS)


def plop(): return (sweep(300, 900, 0.15) * env(0.15, 0.002, 0.04) + lowpass(noise(0.15), 1200) * env(0.15, 0.002, 0.05) * 0.4) * 0.7


with Video("kids2_tellen.mp4") as v:
    scale_notes = [60, 62, 64, 65, 67]
    for i in range(N):
        t = T0 + i * DT
        v.sfx(t, plop(), 0.8); v.sfx(t + 0.08, pluck(note(scale_notes[i] + 12)), 1.0)
    v.sfx(T0 + N * DT + 0.1, ding(), 0.9)
    for i, n in enumerate([72, 76, 79, 84]): v.sfx(T0 + N * DT + 0.15 + i * 0.1, pluck(note(n)), 0.7)
    v.audio += beat(5, bpm=120, kick_steps=(0, 8), snare_steps=(4, 12), gain=0.18)
    for f in range(v.nframes):
        t = f / FPS
        img = bg.copy(); d = ImageDraw.Draw(img, "RGBA")
        count = sum(1 for i in range(N) if t >= T0 + i * DT)
        for i in range(count):
            u = (t - T0 - i * DT)
            drop = 1 - ease(min(u / 0.3, 1))
            bob = math.sin(t * 4 + i) * 5
            sq = math.exp(-u * 6) * math.sin(u * 30) * 0.12 if u > 0.3 else 0
            y = WATER_Y + bob - drop * 420
            duck(d, XS[i], y, 1.0 + sq, flap=max(0, math.sin(t * 20)) if drop > 0 else 0)
            if u < 0.6:   # splash
                k = u / 0.6
                for s in (-1, 1):
                    for j in range(3):
                        sx = XS[i] + s * (40 + j * 25) * (0.5 + k); sy = WATER_Y + 30 - math.sin(k * math.pi) * (40 + j * 15)
                        d.ellipse([(sx - 7) * SS, (sy - 7) * SS, (sx + 7) * SS, (sy + 7) * SS], fill=(200, 235, 255, int(255 * (1 - k))))
            nk = ease_out_back(min(u / 0.35, 1))
            text(d, (XS[i] + 10, WATER_Y - 170), str(i + 1), int(30 + 40 * nk), (255, 255, 255), stroke=6, stroke_fill=(255, 120, 60))
        if count:
            u = t - (T0 + (count - 1) * DT)
            k = ease_out_back(min(u / 0.3, 1))
            if count < N or u < 0.5:
                text(d, (W / 2, 90), WORDS[count - 1] + "!", int(40 + 30 * k), (255, 120, 60), stroke=7, stroke_fill=(255, 255, 255))
            else:
                text(d, (W / 2, 90), "5 eendjes!", int(70 + 6 * math.sin(t * 8)), (255, 120, 60), stroke=7, stroke_fill=(255, 255, 255))
        else:
            text(d, (W / 2, 90), "Tel je mee?", 66, (255, 120, 60), stroke=7, stroke_fill=(255, 255, 255))
        v.add(img)
