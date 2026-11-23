from lib import *
import random

random.seed(11)
COLORS = [("ROOD", (240, 60, 60)), ("BLAUW", (50, 130, 255)), ("GROEN", (50, 200, 90)),
          ("GEEL", (250, 210, 40)), ("PAARS", (170, 80, 240)), ("ORANJE", (255, 140, 30))]
R, PR = 17, 8
X0, X1, FINISH = 50, 670, 1130
G, START = 1700, 0.6
pegs = []
for row, y in enumerate(range(330, 1060, 72)):
    off = 40 if row % 2 else 0
    for x in range(X0 + 40 + off, X1 - 20, 80):
        pegs.append((x, y))

marbles = [dict(name=n, col=c, x=250 + i * 44 + random.uniform(-3, 3), y=240, vx=0, vy=0, fin=None, trail=[])
           for i, (n, c) in enumerate(COLORS)]
hits = []   # (time, pitch)


def step(t, dt):
    for m in marbles:
        if m["fin"] is not None:
            m["vy"] *= 0.8; m["vx"] *= 0.8; m["y"] = min(m["y"] + m["vy"] * dt, FINISH + 60); continue
        m["vy"] += G * dt; m["x"] += m["vx"] * dt; m["y"] += m["vy"] * dt
        if m["x"] < X0 + R: m["x"] = X0 + R; m["vx"] = abs(m["vx"]) * 0.6
        if m["x"] > X1 - R: m["x"] = X1 - R; m["vx"] = -abs(m["vx"]) * 0.6
        for px, py in pegs:
            dx, dy = m["x"] - px, m["y"] - py; dd = dx * dx + dy * dy
            if dd < (R + PR) ** 2:
                dist = math.sqrt(dd) or 0.01; nx, ny = dx / dist, dy / dist
                m["x"] = px + nx * (R + PR); m["y"] = py + ny * (R + PR)
                vn = m["vx"] * nx + m["vy"] * ny
                if vn < 0:
                    m["vx"] -= 1.55 * vn * nx; m["vy"] -= 1.55 * vn * ny
                    m["vx"] += random.uniform(-25, 25)
                    if -vn > 150: hits.append((t, py))
        if m["y"] > FINISH: m["fin"] = t
    for i in range(len(marbles)):
        for j in range(i + 1, len(marbles)):
            a, b = marbles[i], marbles[j]
            dx, dy = b["x"] - a["x"], b["y"] - a["y"]; dd = dx * dx + dy * dy
            if 0 < dd < (2 * R) ** 2:
                dist = math.sqrt(dd); nx, ny = dx / dist, dy / dist; ov = 2 * R - dist
                a["x"] -= nx * ov / 2; a["y"] -= ny * ov / 2; b["x"] += nx * ov / 2; b["y"] += ny * ov / 2
                rel = (b["vx"] - a["vx"]) * nx + (b["vy"] - a["vy"]) * ny
                if rel < 0:
                    imp = -rel * 0.9
                    a["vx"] -= imp * nx; a["vy"] -= imp * ny; b["vx"] += imp * nx; b["vy"] += imp * ny


def draw_marble(d, m, x, y):
    s = SS; c = m["col"]
    d.ellipse([(x - R) * s, (y - R) * s, (x + R) * s, (y + R) * s], fill=c, outline=(20, 20, 30), width=3 * s)
    d.ellipse([(x - R * 0.5) * s, (y - R * 0.6) * s, (x - R * 0.05) * s, (y - R * 0.15) * s], fill=(255, 255, 255, 170))


bg = vgradient(RW, RH, (20, 24, 48), (8, 10, 22))
bd = ImageDraw.Draw(bg)
bd.rectangle([X0 * SS, 200 * SS, X1 * SS, (FINISH + 90) * SS], fill=(30, 36, 70))
for px, py in pegs:
    bd.ellipse([(px - PR) * SS, (py - PR) * SS, (px + PR) * SS, (py + PR) * SS], fill=(200, 210, 240))
for k in range((X1 - X0) // 20):   # checkered finish line
    for r2 in range(2):
        col = (255, 255, 255) if (k + r2) % 2 else (20, 20, 20)
        bd.rectangle([(X0 + k * 20) * SS, (FINISH + r2 * 12) * SS, (X0 + k * 20 + 20) * SS, (FINISH + 12 + r2 * 12) * SS], fill=col)

with Video("2_marble_race.mp4") as v:
    v.audio += beat(5, bpm=140, gain=0.35)
    dt = 1 / FPS / 8; t = 0.0; winner = None; last_hit = -1
    for f in range(v.nframes):
        ft = f / FPS
        while t < ft:
            if t >= START: step(t, dt)
            t += dt
        img = bg.copy(); d = ImageDraw.Draw(img, "RGBA")
        for m in marbles:
            m["trail"] = (m["trail"] + [(m["x"], m["y"])])[-8:]
            for k, (tx, ty) in enumerate(m["trail"][:-1]):
                rr = R * (k + 1) / 10
                d.ellipse([(tx - rr) * SS, (ty - rr) * SS, (tx + rr) * SS, (ty + rr) * SS], fill=m["col"] + (50,))
        for m in marbles: draw_marble(d, m, m["x"], m["y"])
        # leaderboard
        order = sorted(marbles, key=lambda m: (m["fin"] if m["fin"] is not None else 99, -m["y"]))
        text(d, (W / 2, 80), "MARBLE RACE", 62, (255, 230, 80), stroke=6, stroke_fill=(10, 10, 30))
        lead = order[0]
        text(d, (W / 2, 150), f"Leider: {lead['name']}", 36, lead["col"], stroke=4, stroke_fill=(10, 10, 30))
        if ft < START:
            text(d, (W / 2, 640), "KLAAR?", 90, (255, 255, 255), stroke=8, stroke_fill=(10, 10, 30))
        fins = [m for m in marbles if m["fin"] is not None]
        if fins:
            w = min(fins, key=lambda m: m["fin"])
            if winner is None:
                winner = w; v.sfx(w["fin"], ding(), 1.0); v.sfx(w["fin"], pad([note(72), note(76), note(79)], 1.5, 0.15))
            u = ease_out_back((ft - winner["fin"]) / 0.35)
            d.rounded_rectangle([90 * SS, 560 * SS, 630 * SS, 760 * SS], radius=30 * SS, fill=(10, 10, 30, 220))
            text(d, (W / 2, 610), "WINNAAR!", int(40 + 20 * u), (255, 255, 255))
            text(d, (W / 2, 700), winner["name"], int(50 + 30 * u), winner["col"], stroke=4, stroke_fill=(255, 255, 255))
        v.add(img)
    # peg click sounds (rate-limited)
    pent = [72, 74, 76, 79, 81, 84, 86]
    for ht, py in hits:
        if ht - last_hit > 0.035:
            v.sfx(ht, click(note(pent[int(py / 72) % 7]) * 2, 0.05), 0.5); last_hit = ht
print("winner", winner["name"] if winner else None, "at", winner["fin"] if winner else None)
