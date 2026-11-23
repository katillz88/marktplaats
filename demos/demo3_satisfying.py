from lib import *
import colorsys

CX, CY, RING = 360, 690, 300
MELODY = [64, 67, 71, 72, 71, 67, 64, 62, 64, 67, 72, 76, 74, 72, 71, 67, 69, 71, 72, 74, 76, 79, 81, 84] * 3
G = 1800
ball = dict(x=CX + 40, y=CY - 150, vx=260, vy=0, r=18)
bounces = []
trail = []


def hue(i, s=0.75, v=1.0):
    r, g, b = colorsys.hsv_to_rgb((i * 0.045) % 1, s, v); return (int(r * 255), int(g * 255), int(b * 255))


bg = vgradient(RW, RH, (12, 8, 28), (2, 2, 8))
with Video("3_satisfying.mp4") as v:
    dt = 1 / FPS / 10; t = 0
    for f in range(v.nframes):
        ft = f / FPS
        while t < ft:
            b = ball
            b["vy"] += G * dt; b["x"] += b["vx"] * dt; b["y"] += b["vy"] * dt
            dx, dy = b["x"] - CX, b["y"] - CY; dist = math.hypot(dx, dy)
            lim = RING - b["r"]
            if dist > lim:
                nx, ny = dx / dist, dy / dist
                b["x"] = CX + nx * lim; b["y"] = CY + ny * lim
                vn = b["vx"] * nx + b["vy"] * ny
                b["vx"] -= 2 * vn * nx; b["vy"] -= 2 * vn * ny
                sp = math.hypot(b["vx"], b["vy"]); boost = max(sp, 1500) / sp
                b["vx"] *= boost; b["vy"] *= boost
                n = len(bounces)
                if bounces and t - bounces[-1][0] < 0.08: t += dt; continue
                bounces.append((t, b["x"], b["y"], n))
                b["r"] = min(b["r"] + 8, RING * 0.8)
                v.sfx(t, pluck(note(MELODY[n % len(MELODY)])), 0.9)
                v.sfx(t, pluck(note(MELODY[n % len(MELODY)] - 12)), 0.35)
            t += dt
        trail.append((ball["x"], ball["y"], ball["r"], len(bounces)))
        trail[:] = trail[-14:]
        img = bg.copy(); d = ImageDraw.Draw(img, "RGBA")
        n = len(bounces)
        # ring glow
        for k, a in ((14, 40), (8, 80), (3, 255)):
            col = hue(n) + (a,)
            d.ellipse([(CX - RING - k) * SS, (CY - RING - k) * SS, (CX + RING + k) * SS, (CY + RING + k) * SS],
                      outline=col, width=int(k * 1.2 * SS) or SS)
        # ripples at bounce points
        for bt, bx, by, bi in bounces[-6:]:
            u = (ft - bt) / 0.5
            if 0 <= u < 1:
                rr = 20 + 90 * u
                d.ellipse([(bx - rr) * SS, (by - rr) * SS, (bx + rr) * SS, (by + rr) * SS],
                          outline=hue(bi) + (int(255 * (1 - u)),), width=int(5 * SS))
        # trail
        for k, (tx, ty, tr, ti) in enumerate(trail):
            a = int(200 * (k + 1) / len(trail))
            d.ellipse([(tx - tr) * SS, (ty - tr) * SS, (tx + tr) * SS, (ty + tr) * SS], fill=hue(ti, 0.8, 0.9) + (a // 3,))
        x, y, r = ball["x"], ball["y"], ball["r"]
        d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=hue(n), outline=(255, 255, 255), width=3 * SS)
        text(d, (W / 2, 160), "Hij groeit bij", 54, (255, 255, 255), stroke=5, stroke_fill=(0, 0, 0))
        text(d, (W / 2, 230), "elke stuit...", 54, (255, 255, 255), stroke=5, stroke_fill=(0, 0, 0))
        text(d, (W / 2, 1130), f"{n}", 110, hue(n), stroke=6, stroke_fill=(0, 0, 0))
        v.add(img)
    v.audio += pad([note(52), note(59), note(64)], 5, 0.05)
print("bounces", len(bounces))
