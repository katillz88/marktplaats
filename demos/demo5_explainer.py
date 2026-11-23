from lib import *

A, B, C = (260, 760), (500, 760), (260, 580)        # right angle at A; b = AB (4), a = AC (3)
SQ_A = [C, A, (80, 760), (80, 580)]
SQ_B = [A, B, (500, 1000), (260, 1000)]
SQ_C = [C, B, (680, 520), (440, 340)]
COLA, COLB, COLC = (255, 120, 90), (80, 170, 255), (255, 210, 70)


def P(p): return (p[0] * SS, p[1] * SS)


def lerp(p, q, u): return (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)


def square(d, pts, n, col, u, label, lu):
    if u <= 0: return
    # grow from the triangle side outward
    p0, p1, p2, p3 = pts
    q2, q3 = lerp(p1, p2, u), lerp(p0, p3, u)
    d.polygon([P(p0), P(p1), P(q2), P(q3)], fill=col + (110,))
    for k in range(1, n):
        f = k / n
        d.line([P(lerp(p0, p1, f)), P(lerp(q3, q2, f))], fill=col + (200,), width=2 * SS)
        if f <= u:
            d.line([P(lerp(p0, q3, f / u)), P(lerp(p1, q2, f / u))], fill=col + (200,), width=2 * SS)
    d.polygon([P(p0), P(p1), P(q2), P(q3)], outline=col, width=4 * SS)
    if lu > 0:
        cx = sum(p[0] for p in pts) / 4; cy = sum(p[1] for p in pts) / 4
        text(d, (cx, cy), label, int(20 + 22 * ease_out_back(lu)), (255, 255, 255), stroke=4, stroke_fill=(10, 10, 30))


bg = vgradient(RW, RH, (14, 22, 40), (5, 8, 16))
with Video("5_uitleg.mp4") as v:
    v.sfx(0, pad([note(48), note(55), note(64)], 2.5, 0.06))
    v.sfx(2.5, pad([note(53), note(57), note(65)], 2.5, 0.06))
    for t0, n in ((0.0, 60), (0.9, 64), (1.7, 67), (2.5, 72), (3.5, 76)):
        v.sfx(t0, pluck(note(n)), 0.8)
    v.sfx(3.6, ding(), 0.9)
    for f in range(v.nframes):
        t = f / FPS
        img = bg.copy(); d = ImageDraw.Draw(img, "RGBA")
        text(d, (W / 2, 120), "Pythagoras", 64, (255, 255, 255), stroke=5, stroke_fill=(0, 0, 0))
        text(d, (W / 2, 190), "in 5 seconden", 36, (160, 190, 255))
        square(d, SQ_A, 3, COLA, ease((t - 0.9) / 0.6), "9", (t - 1.3) / 0.4)
        square(d, SQ_B, 4, COLB, ease((t - 1.7) / 0.6), "16", (t - 2.1) / 0.4)
        square(d, SQ_C, 5, COLC, ease((t - 2.5) / 0.8), "25", (t - 3.0) / 0.4)
        # triangle drawn progressively
        u = ease(t / 0.8)
        segs = [(A, B), (B, C), (C, A)]
        for i, (p, q) in enumerate(segs):
            su = min(max(u * 3 - i, 0), 1)
            if su > 0: d.line([P(p), P(lerp(p, q, su))], fill=(255, 255, 255), width=6 * SS)
        if u >= 1:
            d.rectangle([A[0] * SS, (A[1] - 24) * SS, (A[0] + 24) * SS, A[1] * SS], outline=(255, 255, 255), width=3 * SS)
            text(d, (A[0] - 22, (A[1] + C[1]) / 2), "a", 34, COLA)
            text(d, ((A[0] + B[0]) / 2, A[1] + 26), "b", 34, COLB)
            text(d, ((B[0] + C[0]) / 2 - 18, (B[1] + C[1]) / 2 + 22), "c", 34, COLC)
        if t > 3.5:
            k = ease_out_back((t - 3.5) / 0.4)
            d.rounded_rectangle([70 * SS, 1060 * SS, 650 * SS, 1220 * SS], radius=24 * SS, fill=(0, 0, 0, 170))
            text(d, (W / 2, 1105), "a² + b² = c²", int(30 + 22 * k), (255, 255, 255))
            text(d, (W / 2, 1175), "9 + 16 = 25", int(24 + 16 * k), COLC)
        v.add(img)
