"""Stickman fight animation -> frames piped into ffmpeg.

Usage: python3 fight.py out.mp4
"""
import math, random, subprocess, sys, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1280, 720          # output size
SS = 2                    # supersampling
RW, RH = W * SS, H * SS
S = RW / 1920.0           # author in 1920x1080 coordinates
FPS = 30
GROUND = 900
random.seed(7)

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ---------------------------------------------------------------- skeleton
L = dict(torso=110, neck=14, head=30, ua=62, fa=58, th=76, sh=76)

BASE = dict(lift=0, rot=0, t=5, ua1=40, fa1=150, ua2=20, fa2=165, th1=22, sh1=5, th2=-20, sh2=-25)
POSES = {
    "guard":   {},
    "walkA":   dict(th1=32, sh1=12, th2=-26, sh2=-45),
    "walkB":   dict(th1=-12, sh1=-35, th2=26, sh2=10),
    "runA":    dict(t=20, th1=60, sh1=-10, th2=-40, sh2=-70, ua1=-30, fa1=60, ua2=70, fa2=150),
    "runB":    dict(t=20, th1=-35, sh1=-80, th2=55, sh2=-5, ua1=70, fa1=150, ua2=-30, fa2=60),
    "jab":     dict(t=15, ua1=95, fa1=93, th1=35, sh1=10, th2=-28, sh2=-28),
    "cross":   dict(t=22, ua1=45, fa1=160, ua2=96, fa2=94, th1=35, sh1=15, th2=-30, sh2=-25),
    "block":   dict(t=-6, ua1=65, fa1=172, ua2=55, fa2=168, th1=15, sh1=0, th2=-25, sh2=-35),
    "kick":    dict(t=-28, ua1=60, fa1=130, ua2=-50, fa2=-70, th1=108, sh1=112, th2=-4, sh2=-4),
    "kick2":   dict(t=-32, ua1=-40, fa1=-60, ua2=60, fa2=120, th1=-10, sh1=-10, th2=112, sh2=118),
    "chamber": dict(t=-10, ua1=50, fa1=140, ua2=10, fa2=150, th1=10, sh1=0, th2=95, sh2=-40),
    "duck":    dict(t=40, ua1=70, fa1=160, ua2=50, fa2=165, th1=80, sh1=-5, th2=25, sh2=-85),
    "upper":   dict(t=-8, ua1=118, fa1=165, ua2=10, fa2=150, th1=18, sh1=10, th2=-28, sh2=-15),
    "hit":     dict(t=-32, ua1=-35, fa1=15, ua2=-70, fa2=-30, th1=25, sh1=10, th2=-15, sh2=-20),
    "fly":     dict(t=-10, ua1=-120, fa1=-150, ua2=-150, fa2=-170, th1=40, sh1=-10, th2=10, sh2=-40),
    "lying":   dict(rot=-90, t=0, ua1=-170, fa1=-175, ua2=-160, fa2=-170, th1=5, sh1=0, th2=-5, sh2=0),
    "crouch":  dict(t=30, ua1=60, fa1=150, ua2=30, fa2=160, th1=95, sh1=-10, th2=60, sh2=-60),
    "fkick":   dict(t=-22, ua1=40, fa1=120, ua2=-60, fa2=-20, th1=95, sh1=93, th2=-10, sh2=-95),
    "cheer":   dict(t=-5, ua1=160, fa1=175, ua2=150, fa2=170, th1=15, sh1=5, th2=-15, sh2=-5),
}


def pose(name, **kw):
    p = dict(BASE); p.update(POSES[name]); p.update(kw); return p


def ease(u):
    return u * u * (3 - 2 * u)


class Fighter:
    def __init__(self, name, color, facing, keys):
        self.name, self.color, self.f = name, color, facing
        self.dark = tuple(int(c * 0.62) for c in color)
        # keys: (time, posename, overrides). carry x forward.
        out, lastx = [], None
        for t, nm, ov in keys:
            ov = dict(ov)
            if "x" not in ov: ov["x"] = lastx
            lastx = ov["x"]
            out.append((t, pose(nm, **ov)))
        self.keys = out

    def params(self, t):
        k = self.keys
        if t <= k[0][0]: return dict(k[0][1])
        if t >= k[-1][0]: return dict(k[-1][1])
        for i in range(len(k) - 1):
            t0, p0 = k[i]; t1, p1 = k[i + 1]
            if t0 <= t <= t1:
                u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1
                return {a: p0[a] + (p1[a] - p0[a]) * u for a in p0}

    def joints(self, t):
        p = self.params(t); f = self.f
        def down(o, ang, ln):  # ang from straight down, + = forward
            a = math.radians(ang); return (o[0] + math.sin(a) * ln * f, o[1] + math.cos(a) * ln)
        hip = (0.0, 0.0)
        a = math.radians(p["t"])
        top = (math.sin(a) * L["torso"] * f, -math.cos(a) * L["torso"])
        sh = (math.sin(a) * (L["torso"] - 6) * f, -math.cos(a) * (L["torso"] - 6))
        hd = (top[0] + math.sin(a) * (L["neck"] + L["head"]) * f,
              top[1] - math.cos(a) * (L["neck"] + L["head"]))
        J = dict(hip=hip, top=top, head=hd)
        J["elb1"] = down(sh, p["ua1"], L["ua"]); J["fist1"] = down(J["elb1"], p["fa1"], L["fa"])
        J["elb2"] = down(sh, p["ua2"], L["ua"]); J["fist2"] = down(J["elb2"], p["fa2"], L["fa"])
        J["knee1"] = down(hip, p["th1"], L["th"]); J["foot1"] = down(J["knee1"], p["sh1"], L["sh"])
        J["knee2"] = down(hip, p["th2"], L["th"]); J["foot2"] = down(J["knee2"], p["sh2"], L["sh"])
        J["sh"] = sh
        # whole-body rotation (+ = forward)
        r = math.radians(p["rot"]) * f
        cr, sr = math.cos(r), math.sin(r)
        for k2, (x, y) in J.items():
            J[k2] = (x * cr - y * sr, x * sr + y * cr)
        # snap lowest point to ground - lift
        low = max(max(y for k2, (x, y) in J.items() if k2 != "head"), J["head"][1] + L["head"])
        oy = GROUND - p["lift"] - low
        return {k2: (x + p["x"], y + oy) for k2, (x, y) in J.items()}


# ---------------------------------------------------------------- choreography
BLUE = Fighter("BLUE", (40, 125, 255), 1, [
    (0.0, "guard", dict(x=480)), (0.35, "guard", dict(lift=14)), (0.7, "guard", {}),
    (1.0, "guard", dict(x=520)), (1.25, "walkA", dict(x=630)), (1.5, "walkB", dict(x=740)),
    (1.75, "guard", dict(x=820)),
    (1.9, "guard", {}), (2.0, "jab", dict(x=865)), (2.2, "guard", dict(x=835)),
    (2.35, "guard", {}), (2.45, "cross", dict(x=875)), (2.65, "guard", dict(x=840)),
    (2.78, "guard", {}), (2.88, "duck", dict(x=830)), (3.2, "duck", dict(x=900)),
    (3.38, "upper", dict(x=985, lift=25)), (3.6, "guard", dict(x=950)),
    (4.2, "guard", dict(x=920, lift=14)), (4.5, "guard", {}), (5.0, "cheer", {}),
    (5.6, "guard", {}), (6.4, "guard", dict(x=880)),
    (6.52, "hit", dict(x=840, lift=40, rot=-25)), (6.85, "fly", dict(x=700, lift=110, rot=-70)),
    (7.15, "lying", dict(x=600, rot=-90)), (7.9, "lying", {}),
    (8.1, "crouch", dict(x=610, lift=90, rot=-20)), (8.35, "crouch", dict(x=630, rot=0)),
    (8.6, "guard", dict(x=650)), (8.85, "walkA", dict(x=720)), (9.05, "guard", dict(x=780)),
    (9.15, "jab", dict(x=820)), (9.3, "guard", dict(x=790)),
    (9.42, "block", dict(x=780)), (9.55, "guard", {}),
    (9.65, "cross", dict(x=830)), (9.8, "guard", dict(x=800)),
    (9.95, "chamber", dict(x=810)), (10.08, "kick2", dict(x=850)), (10.4, "kick2", {}),
    (10.7, "guard", dict(x=840)), (11.3, "cheer", {}), (11.7, "guard", dict(lift=10)),
    (12.1, "cheer", {}), (12.5, "guard", {}), (12.9, "cheer", {}),
])

RED = Fighter("RED", (240, 55, 60), -1, [
    (0.0, "guard", dict(x=1440)), (0.35, "guard", dict(lift=14)), (0.7, "guard", {}),
    (1.0, "guard", dict(x=1400)), (1.25, "walkA", dict(x=1290)), (1.5, "walkB", dict(x=1180)),
    (1.75, "guard", dict(x=1100)),
    (1.92, "block", {}), (2.1, "block", {}), (2.25, "guard", {}),
    (2.38, "block", {}), (2.55, "block", {}), (2.68, "guard", {}),
    (2.9, "kick", dict(x=1075)), (3.15, "guard", dict(x=1080)), (3.32, "guard", dict(x=1045)),
    (3.42, "hit", dict(x=1150, lift=40, rot=-20)), (3.75, "fly", dict(x=1340, lift=160, rot=-65)),
    (4.1, "lying", dict(x=1500, rot=-90)), (4.9, "lying", {}),
    (5.25, "crouch", dict(x=1480, rot=-10)), (5.6, "guard", dict(x=1450)),
    (5.8, "runA", dict(x=1360)), (5.95, "runB", dict(x=1270)), (6.1, "runA", dict(x=1180)),
    (6.25, "crouch", dict(x=1120)), (6.5, "fkick", dict(x=990, lift=130)),
    (6.8, "crouch", dict(x=960)), (7.05, "guard", dict(x=980)),
    (7.4, "cheer", {}), (7.75, "guard", {}), (8.1, "cheer", {}), (8.5, "guard", {}),
    (8.85, "walkB", dict(x=1020)), (9.05, "guard", dict(x=1000)),
    (9.12, "block", {}), (9.3, "guard", {}),
    (9.42, "jab", dict(x=960)), (9.55, "guard", dict(x=990)),
    (9.68, "hit", dict(x=1010, rot=-10)), (9.85, "guard", dict(x=1000)),
    (10.0, "guard", {}), (10.1, "hit", dict(x=1060, lift=50, rot=-30)),
    (10.55, "fly", dict(x=1330, lift=170, rot=-75)), (11.0, "lying", dict(x=1560, rot=-90)),
    (11.15, "lying", dict(x=1580, lift=12, rot=-90)), (11.3, "lying", dict(x=1590, rot=-90)),
])
FIGHTERS = [BLUE, RED]

# events: (story_time, fighter, point, kind, damage_to)
EVENTS = [
    (2.0, BLUE, "fist1", "block", None),
    (2.45, BLUE, "fist2", "block", None),
    (2.9, RED, "foot1", "whoosh", None),
    (3.38, BLUE, "fist1", "hit", ("RED", 30)),
    (4.1, RED, "hip", "land", None),
    (6.5, RED, "foot1", "hit", ("BLUE", 35)),
    (7.15, BLUE, "hip", "land", None),
    (9.15, BLUE, "fist1", "block", None),
    (9.42, RED, "fist1", "block", None),
    (9.65, BLUE, "fist2", "hit", ("RED", 15)),
    (10.08, BLUE, "foot2", "bighit", ("RED", 55)),
    (11.0, RED, "hip", "land", None),
]

# ---------------------------------------------------------------- time remap (slow-mo)
SLOW_A, SLOW_B, SLOW_K = 9.95, 10.35, 0.3
SLOW_OUT = (SLOW_B - SLOW_A) / SLOW_K
STORY_END = 13.6


def story(o):
    if o < SLOW_A: return o
    if o < SLOW_A + SLOW_OUT: return SLOW_A + (o - SLOW_A) * SLOW_K
    return o - SLOW_OUT + (SLOW_B - SLOW_A)


def out_time(s):
    if s < SLOW_A: return s
    if s < SLOW_B: return SLOW_A + (s - SLOW_A) / SLOW_K
    return s + SLOW_OUT - (SLOW_B - SLOW_A)


OUT_END = out_time(STORY_END)

# ---------------------------------------------------------------- precompute events
for i, (t, fg, pt, kind, dmg) in enumerate(EVENTS):
    pos = fg.joints(t)[pt]
    if kind == "land": pos = (pos[0], GROUND)
    EVENTS[i] = dict(t=t, pos=pos, kind=kind, dmg=dmg, seed=i)


def health(name, s):
    hp = 100.0
    for e in EVENTS:
        if e["dmg"] and e["dmg"][0] == name and s >= e["t"]:
            hp -= e["dmg"][1]
    return max(hp, 0)


def health_lag(name, s):
    hp = 100.0
    for e in EVENTS:
        if e["dmg"] and e["dmg"][0] == name:
            u = min(max((s - e["t"] - 0.25) / 0.6, 0), 1)
            hp -= e["dmg"][1] * u
    return max(hp, 0)

# ---------------------------------------------------------------- background
def make_bg():
    bg = Image.new("RGB", (RW, RH))
    d = ImageDraw.Draw(bg)
    top, bot = (28, 18, 60), (255, 120, 70)
    gy = int(GROUND * S)
    for y in range(gy):
        u = (y / gy) ** 1.4
        d.line([(0, y), (RW, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * u) for i in range(3)))
    # sun
    cx, cy, r = int(960 * S), int(700 * S), int(170 * S)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 200, 110))
    # city silhouettes (two layers)
    rnd = random.Random(3)
    for layer, col, hmin, hmax in [(0, (90, 45, 90), 120, 330), (1, (52, 26, 62), 60, 220)]:
        x = -20
        while x < 1940:
            w = rnd.randint(60, 140); h = rnd.randint(hmin, hmax)
            d.rectangle([int(x * S), int((GROUND - h) * S), int((x + w) * S), gy], fill=col)
            if layer == 1:
                for wy in range(GROUND - h + 20, GROUND - 20, 34):
                    for wx in range(x + 12, x + w - 16, 26):
                        if rnd.random() < 0.3:
                            d.rectangle([int(wx * S), int(wy * S), int((wx + 10) * S), int((wy + 14) * S)],
                                        fill=(255, 210, 120))
            x += w + rnd.randint(-10, 10)
    # ground
    d.rectangle([0, gy, RW, RH], fill=(30, 20, 34))
    d.line([(0, gy), (RW, gy)], fill=(240, 150, 90), width=int(4 * S))
    for x in range(0, 1920, 90):
        d.line([(int(x * S), int((GROUND + 40) * S)), (int((x + 40) * S), int((GROUND + 40) * S))],
               fill=(55, 40, 60), width=int(3 * S))
    return bg


# ---------------------------------------------------------------- drawing
def P(pt, off):
    return (pt[0] * S + off[0], pt[1] * S + off[1])


def draw_fighter(d, fg, s, off, alpha_col=None, width=15):
    J = fg.joints(s)
    col = alpha_col or fg.color
    dark = alpha_col or fg.dark
    w = int(width * S)
    def seg(a, b, c):
        d.line([P(J[a], off), P(J[b], off)], fill=c, width=w)
        r = w / 2
        for k in (a, b):
            x, y = P(J[k], off); d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    seg("sh", "elb2", dark); seg("elb2", "fist2", dark)
    seg("hip", "knee2", dark); seg("knee2", "foot2", dark)
    seg("hip", "top", col)
    seg("hip", "knee1", col); seg("knee1", "foot1", col)
    hx, hy = P(J["head"], off); r = L["head"] * S
    if not alpha_col:
        # headband tails streaming behind
        tx = hx - fg.f * r * 0.9
        wob = math.sin(s * 14 + fg.f) * 8 * S
        d.line([(tx, hy - r * 0.35), (tx - fg.f * 38 * S, hy - r * 0.2 + wob)], fill=(255, 255, 255), width=int(6 * S))
        d.line([(tx, hy - r * 0.35), (tx - fg.f * 30 * S, hy + r * 0.15 + wob)], fill=(255, 255, 255), width=int(6 * S))
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=col)
    if not alpha_col:
        d.line([(hx - r * 0.95, hy - r * 0.35), (hx + r * 0.95, hy - r * 0.35)], fill=(255, 255, 255), width=int(7 * S))
        # eye
        ex = hx + fg.f * r * 0.45; ey = hy - r * 0.02; er = 4.5 * S
        d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(15, 15, 25))
    seg("sh", "elb1", col); seg("elb1", "fist1", col)
    if not alpha_col:
        for k in ("fist1", "fist2"):
            x, y = P(J[k], off); rr = 11 * S
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col if k == "fist1" else dark)


def star(cx, cy, r1, r2, n, rot):
    pts = []
    for i in range(n * 2):
        a = rot + math.pi * i / n
        r = r1 if i % 2 == 0 else r2
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def draw_effects(d, s, off):
    for e in EVENTS:
        dt = s - e["t"]
        x, y = P(e["pos"], off)
        k = e["kind"]
        if k in ("hit", "bighit", "block") and 0 <= dt < 0.45:
            big = {"block": 0.55, "hit": 1.0, "bighit": 1.5}[k]
            u = dt / 0.45
            if dt < 0.12:
                r1 = (70 + 160 * dt / 0.12) * S * big
                d.polygon(star(x, y, r1, r1 * 0.42, 9, e["seed"]), fill=(255, 245, 160))
                d.polygon(star(x, y, r1 * 0.6, r1 * 0.25, 9, e["seed"] + 0.3), fill=(255, 255, 255))
            rr = (40 + 260 * u) * S * big
            d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(255, 255, 255), width=max(1, int(10 * (1 - u) * S)))
            rnd = random.Random(e["seed"])
            for _ in range(int(14 * big)):
                a = rnd.uniform(0, 2 * math.pi); sp = rnd.uniform(250, 700) * big
                px = x + math.cos(a) * sp * dt * S; py = y + (math.sin(a) * sp * dt + 900 * dt * dt) * S
                ln = 22 * (1 - u) * S
                d.line([(px, py), (px - math.cos(a) * ln, py - math.sin(a) * ln)], fill=(255, 220, 90), width=int(5 * S))
        if k == "whoosh" and -0.15 <= dt < 0.15:
            u = (dt + 0.15) / 0.3
            for i in range(3):
                rr = (150 + i * 30) * S
                d.arc([x - rr, y - rr * 0.6, x + rr, y + rr * 0.6], 180 + 40 * u, 280 + 40 * u,
                      fill=(255, 255, 255), width=int(4 * S))
        if k == "land" and 0 <= dt < 0.8:
            u = dt / 0.8
            rnd = random.Random(e["seed"])
            for _ in range(16):
                vx = rnd.uniform(-420, 420); vy = rnd.uniform(-160, -40)
                px = x + vx * dt * S; py = y + (vy * dt + 250 * dt * dt) * S
                rr = (14 + 40 * u) * S * rnd.uniform(0.6, 1.2)
                c = int(150 - 60 * u)
                d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=(c, c - 20, c))


def shake(s):
    sx = sy = 0.0
    for e in EVENTS:
        dt = s - e["t"]
        amp = {"hit": 18, "bighit": 32, "land": 12, "block": 5}.get(e["kind"], 0)
        if amp and 0 <= dt < 0.35:
            a = amp * (1 - dt / 0.35) * S
            sx += math.sin(dt * 90 + e["seed"]) * a; sy += math.cos(dt * 77 + e["seed"]) * a
    return sx, sy


def draw_hud(d, s, fonts):
    fb, fbig, ftitle = fonts
    for side, fg in ((0, BLUE), (1, RED)):
        bw, bh, y = 700 * S, 34 * S, 50 * S
        x0 = 70 * S if side == 0 else RW - 70 * S - bw
        d.rectangle([x0 - 5 * S, y - 5 * S, x0 + bw + 5 * S, y + bh + 5 * S], fill=(15, 10, 20))
        hp, lag = health(fg.name, s) / 100, health_lag(fg.name, s) / 100
        def bar(frac, col):
            if frac <= 0: return
            if side == 0: d.rectangle([x0 + bw * (1 - frac), y, x0 + bw, y + bh], fill=col)
            else: d.rectangle([x0, y, x0 + bw * frac, y + bh], fill=col)
        bar(lag, (255, 255, 255)); bar(hp, (255, 210, 60) if hp > 0.3 else (255, 80, 60))
        tx = x0 if side == 0 else x0 + bw
        d.text((tx, y + bh + 14 * S), fg.name, font=fb, fill=fg.color, anchor="la" if side == 0 else "ra",
               stroke_width=int(4 * S), stroke_fill=(15, 10, 20))
    # VS
    d.text((RW / 2, y + bh / 2), "VS", font=fb, fill=(255, 255, 255), anchor="mm",
           stroke_width=int(4 * S), stroke_fill=(15, 10, 20))


def text_center(d, txt, font, y, fill, alpha_scale=1.0):
    d.text((RW / 2, y), txt, font=font, fill=fill, anchor="mm", stroke_width=int(10 * S), stroke_fill=(15, 10, 20))


def main(outfile):
    bg = make_bg()
    fonts = (ImageFont.truetype(FONT_B, int(40 * S)), ImageFont.truetype(FONT_B, int(230 * S)),
             ImageFont.truetype(FONT_B, int(120 * S)))
    nframes = int(OUT_END * FPS)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt",
                             "yuv420p", "-crf", "18", "-preset", "medium", outfile], stdin=subprocess.PIPE)
    for fi in range(nframes):
        o = fi / FPS
        s = story(o)
        off = shake(s)
        img = bg.copy()
        # zoom-in during slow-mo
        d = ImageDraw.Draw(img, "RGBA")
        # motion ghosts
        for fg in FIGHTERS:
            for gi, dt in enumerate((0.05, 0.025)):
                c = tuple(int(v * 0.5 + 255 * 0.5) for v in fg.color) + (60 + gi * 40,)
                draw_fighter(d, fg, max(s - dt, 0), off, alpha_col=c)
        # shadows
        for fg in FIGHTERS:
            J = fg.joints(s)
            hx = J["hip"][0] * S + off[0]
            hgt = GROUND - max(J["foot1"][1], J["foot2"][1])
            sw = max(40, 120 - hgt * 0.4) * S
            d.ellipse([hx - sw, GROUND * S - 10 * S + off[1], hx + sw, GROUND * S + 10 * S + off[1]], fill=(0, 0, 0, 110))
        for fg in FIGHTERS:
            draw_fighter(d, fg, s, off)
        draw_effects(d, s, off)
        # slow-mo tint
        if SLOW_A <= s < SLOW_B:
            d.rectangle([0, 0, RW, RH], fill=(255, 255, 255, 22))
            d.rectangle([0, 0, RW, 70 * S], fill=(0, 0, 0, 255)); d.rectangle([0, RH - 70 * S, RW, RH], fill=(0, 0, 0, 255))
        if 3.38 <= s < 3.42 or 10.08 <= s < 10.12 or 6.5 <= s < 6.54:
            d.rectangle([0, 0, RW, RH], fill=(255, 255, 255, 140))
        draw_hud(d, s, fonts)
        # titles
        if s < 1.6:
            a = 1 if s < 1.1 else 1 - (s - 1.1) / 0.5
            sc = 1 + max(0, 0.3 - s) * 1.5
            f = ImageFont.truetype(FONT_B, int(120 * S * sc))
            txt_img = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
            td = ImageDraw.Draw(txt_img)
            text_center(td, "FIGHT!", f, RH * 0.42, (255, 230, 80))
            txt_img.putalpha(txt_img.getchannel("A").point(lambda v: int(v * a)))
            img.paste(txt_img, (0, 0), txt_img)
        if s >= 11.0:
            u = min((s - 11.0) / 0.25, 1)
            sc = 2.2 - 1.2 * ease(u)
            f = ImageFont.truetype(FONT_B, max(10, int(230 * S * sc)))
            text_center(d, "K.O.!", f, RH * 0.40, (255, 60, 50))
            if s >= 11.8:
                text_center(d, "BLUE WINS", fonts[2] if False else ImageFont.truetype(FONT_B, int(80 * S)),
                            RH * 0.58, (90, 160, 255))
        # fade out
        if s > STORY_END - 0.5:
            a = int(255 * min((s - (STORY_END - 0.5)) / 0.5, 1))
            d.rectangle([0, 0, RW, RH], fill=(0, 0, 0, a))
        frame = img.resize((W, H), Image.LANCZOS)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close(); proc.wait()
    # write sound cue sheet (output times)
    cues = [dict(t=round(out_time(e["t"]), 3), kind=e["kind"]) for e in EVENTS]
    cues.append(dict(t=round(out_time(9.98), 3), kind="whoosh"))
    cues.append(dict(t=round(out_time(11.0), 3), kind="ko"))
    with open(outfile.rsplit(".", 1)[0] + "_cues.json", "w") as fh:
        json.dump(dict(duration=OUT_END, cues=cues), fh, indent=1)
    print("frames", nframes, "duration", round(OUT_END, 2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fight.mp4")
