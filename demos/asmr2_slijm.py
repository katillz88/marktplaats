from lib import *
import random

random.seed(8)
CX, CY, R = 360, 780, 230
NPTS = 140
PRESSES = [(0.4, 1.9), (2.4, 3.9)]          # (start, end) of each finger press
glitter = [(random.uniform(0, 2 * math.pi), random.uniform(0, 0.9), random.choice([(255, 255, 255), (255, 230, 140), (200, 255, 255)]))
           for _ in range(70)]
bubbles = [dict(a=random.uniform(-2.6, -0.5), r=random.uniform(0.2, 0.75), s=random.uniform(6, 14),
                pop=random.uniform(1.2, 1.8) + (0 if i < 4 else 2.0)) for i in range(8)]


def press_amount(t):
    for a, b in PRESSES:
        if a <= t <= b:
            u = (t - a) / (b - a)
            if u < 0.45: return ease(u / 0.45)
            if u < 0.6: return 1
            return 1 - ease((u - 0.6) / 0.4)
    return 0.0


def wobble(t):
    # damped wobble after each release
    w = 0
    for a, b in PRESSES:
        if t > b: w += math.sin((t - b) * 18) * math.exp(-(t - b) * 4) * 0.05
    return w


def blob(t, scale=1.0, oy=0):
    p = press_amount(t); wb = wobble(t)
    sx = 1 + 0.22 * p + wb; sy = 1 - 0.30 * p - wb
    pts = []
    for i in range(NPTS):
        a = 2 * math.pi * i / NPTS
        r = R * scale * (1 + 0.025 * math.sin(3 * a + t * 2) + 0.015 * math.sin(5 * a - t * 3))
        dent = p * 0.42 * math.exp(-((a - 1.5 * math.pi) % (2 * math.pi) - 0) ** 2 / 0.08) if True else 0
        da = (a - 1.5 * math.pi + math.pi) % (2 * math.pi) - math.pi
        dent = p * 0.40 * math.exp(-da * da / 0.09)
        x = CX + math.cos(a) * r * sx
        y = CY + R * 0.3 * p * 0.9 + math.sin(a) * r * sy * (1 - dent) + oy   # keep bottom on the table
        pts.append((x, y))
    return pts, p


def squish(d=1.3):
    t = tax(d); n = noise(d)
    # wet squelch: noise through a wobbling low-pass + low gurgles
    seg = []
    out = np.zeros(len(t))
    for k in range(10):
        st = int(rng.uniform(0, d - 0.15) * SR); ln = int(rng.uniform(0.05, 0.14) * SR)
        f0 = rng.uniform(200, 600)
        burst = sweep(f0, f0 * rng.uniform(0.4, 0.8), ln / SR) * env(ln / SR, 0.004, 0.03)
        out[st:st + len(burst)] += burst * rng.uniform(0.3, 0.7)
    wet = lowpass(n, 900) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * t) ** 2) * 0.6
    return (out + wet) * np.sin(np.pi * t / d) ** 0.8


def pop(): return sweep(500, 1600, 0.05) * env(0.05, 0.001, 0.012) * 0.5


bg = vgradient(RW, RH, (250, 238, 244), (232, 214, 232))
bd = ImageDraw.Draw(bg)
bd.rectangle([0, 1010 * SS, RW, RH], fill=(240, 230, 236))
with Video("asmr2_slijm.mp4") as v:
    v.audio += lowpass(noise(5), 400) * 0.01
    for a, b in PRESSES: v.sfx(a + 0.05, squish(b - a), 0.9)
    for bb in bubbles: v.sfx(bb["pop"], pop(), 0.8)
    for f in range(v.nframes):
        t = f / FPS
        img = bg.copy(); d = ImageDraw.Draw(img, "RGBA")
        pts, p = blob(t)
        xs = [x for x, _ in pts]; bot = max(y for _, y in pts)
        d.ellipse([(min(xs) - 10) * SS, (bot - 18) * SS, (max(xs) + 10) * SS, (bot + 18) * SS], fill=(190, 160, 190, 90))
        d.polygon([(x * SS, y * SS) for x, y in pts], fill=(70, 200, 210))
        inner, _ = blob(t, 0.86, -18)
        d.polygon([(x * SS, y * SS) for x, y in inner], fill=(110, 225, 230))
        inner2, _ = blob(t, 0.6, -40)
        d.polygon([(x * SS, y * SS) for x, y in inner2], fill=(150, 238, 240, 150))
        # glitter (moves with the blob)
        sx = (max(xs) - min(xs)) / (2 * R); top = min(y for _, y in pts)
        sy = (bot - top) / (2 * R)
        mid = (bot + top) / 2
        for a, rr, c in glitter:
            gx = CX + math.cos(a) * rr * R * sx; gy = mid + math.sin(a) * rr * R * sy
            tw = 2.5 + 1.5 * math.sin(t * 8 + a * 10)
            d.ellipse([(gx - tw) * SS, (gy - tw) * SS, (gx + tw) * SS, (gy + tw) * SS], fill=c)
        # bubbles: grow under pressure, pop later
        for bb in bubbles:
            if t >= bb["pop"]: continue
            bx = CX + math.cos(bb["a"]) * bb["r"] * R * sx; by = mid + math.sin(bb["a"]) * bb["r"] * R * sy
            br = bb["s"] * (1 + 0.6 * p)
            d.ellipse([(bx - br) * SS, (by - br) * SS, (bx + br) * SS, (by + br) * SS], outline=(255, 255, 255, 200), width=2 * SS)
        for bb in bubbles:
            u = (t - bb["pop"]) / 0.18
            if 0 <= u < 1:
                bx = CX + math.cos(bb["a"]) * bb["r"] * R * sx; by = mid + math.sin(bb["a"]) * bb["r"] * R * sy
                for k in range(6):
                    a = k * math.pi / 3; r1 = bb["s"] * (1 + 1.5 * u); r2 = r1 + 6
                    d.line([((bx + math.cos(a) * r1) * SS, (by + math.sin(a) * r1) * SS),
                            ((bx + math.cos(a) * r2) * SS, (by + math.sin(a) * r2) * SS)], fill=(255, 255, 255, int(255 * (1 - u))), width=2 * SS)
        # gloss highlight
        d.ellipse([(CX - 150 * sx) * SS, (top + 30) * SS, (CX - 40 * sx) * SS, (top + 70) * SS], fill=(255, 255, 255, 150))
        # finger
        fy_top = top - 330 + 0 if p > 0 else None
        if p > 0.01 or any(a - 0.3 < t < a for a, _ in PRESSES):
            pre = 0
            for a, b in PRESSES:
                if a - 0.3 < t < a: pre = 1 - (a - t) / 0.3
            tipy = top + 6 if p > 0.01 else top - 140 * (1 - ease(pre))
            fx = CX
            d.rounded_rectangle([(fx - 46) * SS, (tipy - 300) * SS, (fx + 46) * SS, (tipy + 4) * SS], radius=46 * SS, fill=(244, 196, 170))
            d.rounded_rectangle([(fx - 28) * SS, (tipy - 90) * SS, (fx + 28) * SS, (tipy - 20) * SS], radius=20 * SS, fill=(252, 222, 210))
        text(d, (W / 2, 150), "ASMR", 74, (60, 160, 175))
        text(d, (W / 2, 225), "glitter slijm", 40, (90, 170, 185), bold=False)
        v.add(img)
