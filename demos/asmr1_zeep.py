from lib import *
import random

random.seed(2)
BX0, BX1, BY0, BY1 = 110, 420, 700, 900       # soap block front face
DEPTH = (60, -45)                              # top/side face offset
LAYERS = [((255, 182, 200), 0.36), ((255, 244, 225), 0.26), ((196, 170, 255), 0.38)]
S = 26                                         # slice thickness
CUT_T0, CUT_DT, NCUTS = 0.3, 0.92, 5
PILE_X = 450


def shade(c, k): return tuple(min(255, int(v * k)) for v in c)
def P(pts): return [(x * SS, y * SS) for x, y in pts]


def rot(pts, cx, cy, a):
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


def strips(x0, x1):
    out = []; y = BY0
    for c, frac in LAYERS:
        h = (BY1 - BY0) * frac; out.append(([(x0, y), (x1, y), (x1, y + h), (x0, y + h)], c)); y += h
    return out


def scrape(d=0.46):
    t = tax(d); n = noise(d)
    hi = n - lowpass(n, 2500)
    grain = (rng.random(len(t)) < 0.025) * rng.uniform(0.5, 1.5, len(t))
    grain = np.convolve(grain, np.exp(-np.arange(60) / 8), mode="same") * np.sign(n)
    return (hi * 0.3 + grain * 0.45) * np.sin(np.pi * t / d) ** 0.7


def tap(): return (lowpass(noise(0.12), 900) * env(0.12, 0.001, 0.02)
                   + np.sin(2 * np.pi * 170 * tax(0.12)) * env(0.12, 0.001, 0.03)) * 0.6


bg = vgradient(RW, RH, (240, 228, 238), (208, 192, 214))
bd = ImageDraw.Draw(bg)
bd.rectangle([0, 900 * SS, RW, RH], fill=(232, 222, 214))
bd.rectangle([0, 896 * SS, RW, 906 * SS], fill=(214, 200, 192))
shav = [dict(vx=random.uniform(-150, 150), vy=random.uniform(-320, -120), c=random.choice([LAYERS[0][0], LAYERS[2][0], LAYERS[1][0]]))
        for _ in range(14)]

with Video("asmr1_zeep.mp4") as v:
    v.audio += lowpass(noise(5), 400) * 0.01
    for i in range(NCUTS):
        t0 = CUT_T0 + i * CUT_DT
        v.sfx(t0, scrape(), 0.9); v.sfx(t0 + CUT_DT * 0.5 + 0.22, tap(), 0.7)
    for f in range(v.nframes):
        t = f / FPS
        img = bg.copy(); d = ImageDraw.Draw(img, "RGBA")
        j_act = int((t - CUT_T0) // CUT_DT) if t >= CUT_T0 else -1
        ph = ((t - CUT_T0) % CUT_DT) / CUT_DT if t >= CUT_T0 else 0
        detached = [j for j in range(NCUTS) if t >= CUT_T0 + (j + 0.5) * CUT_DT]
        right = BX1 - len(detached) * S
        # falling / fallen slices
        for j in detached:
            fall = ease((t - CUT_T0 - (j + 0.5) * CUT_DT) / 0.24)
            sx0 = BX1 - (j + 1) * S
            ang = fall * math.pi / 2
            dx = (PILE_X - (sx0 + S)) * fall; dy = -j * (S - 2) * fall
            for pts, c in strips(sx0, sx0 + S):
                p = rot(pts, sx0 + S, BY1, ang)
                p = [(x + dx, y + dy) for x, y in p]
                d.polygon(P(p), fill=c, outline=shade(c, 0.88))
        # block
        top = [(BX0, BY0), (right, BY0), (right + DEPTH[0], BY0 + DEPTH[1]), (BX0 + DEPTH[0], BY0 + DEPTH[1])]
        d.polygon(P(top), fill=shade(LAYERS[0][0], 1.05))
        y = BY0
        for c, frac in LAYERS:
            h = (BY1 - BY0) * frac
            d.polygon(P([(right, y), (right + DEPTH[0], y + DEPTH[1]), (right + DEPTH[0], y + h + DEPTH[1]), (right, y + h)]),
                      fill=shade(c, 0.9)); y += h
        for pts, c in strips(BX0, right): d.polygon(P(pts), fill=c)
        # knife
        if 0 <= j_act < NCUTS:
            kx = BX1 - (j_act + 1) * S
            if ph < 0.5: prog = ease(ph / 0.5)
            else: prog = 1 - ease((ph - 0.5) / 0.5)
            blade_len = BY1 - BY0 + 70
            bottom = (BY0 - 120) + (BY1 - (BY0 - 120)) * prog
            if ph < 0.5:
                d.line(P([(kx, BY0), (kx, max(BY0, bottom))]), fill=(160, 120, 150, 150), width=2 * SS)
                u = ph * CUT_DT
                for s in shav:
                    sx = kx + s["vx"] * u; sy = BY0 + DEPTH[1] / 2 + s["vy"] * u + 1100 * u * u
                    if sy < BY1: d.ellipse([(sx - 3) * SS, (sy - 3) * SS, (sx + 3) * SS, (sy + 3) * SS], fill=s["c"])
            if ph >= 0.5: kx -= 0       # lift straight up
            blade = [(kx - 2, bottom - blade_len), (kx + 16, bottom - blade_len), (kx + 16, bottom - 20), (kx - 2, bottom)]
            d.polygon(P(blade), fill=(200, 206, 218))
            d.polygon(P([(kx - 2, bottom - blade_len), (kx + 3, bottom - blade_len), (kx + 3, bottom - 4), (kx - 2, bottom)]),
                      fill=(250, 252, 255))
            d.rounded_rectangle([(kx - 6) * SS, (bottom - blade_len - 150) * SS, (kx + 24) * SS, (bottom - blade_len) * SS],
                                radius=10 * SS, fill=(80, 56, 66))
        text(d, (W / 2, 150), "ASMR", 74, (120, 90, 130))
        text(d, (W / 2, 225), "zeep snijden", 40, (150, 120, 160), bold=False)
        v.add(img)
