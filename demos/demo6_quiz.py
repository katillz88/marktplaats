from lib import *

FLAG = [(22, 155, 98), (255, 255, 255), (255, 136, 62)]    # Ireland: green-white-orange
OPTIONS = ["Ivoorkust", "Ierland", "Italië"]
CORRECT = 1
REVEAL = 3.7

bg = vgradient(RW, RH, (60, 30, 140), (20, 10, 50))
with Video("6_quiz.mp4") as v:
    v.audio += beat(5, bpm=128, snare_steps=(4, 12), gain=0.25)
    for k in range(3): v.sfx(0.7 + k * 1.0, click(1200 if k < 2 else 1600, 0.08), 1.0)
    v.sfx(REVEAL, ding(), 1.0); v.sfx(REVEAL, pad([note(72), note(76), note(79)], 1.3, 0.12))
    v.sfx(0.0, whoosh(0.4), 0.6)
    for f in range(v.nframes):
        t = f / FPS
        img = bg.copy(); d = ImageDraw.Draw(img, "RGBA")
        text(d, (W / 2, 110), "RAAD DE VLAG", 62, (255, 230, 80), stroke=6, stroke_fill=(20, 10, 40))
        text(d, (W / 2, 175), "Vraag 1 / 10", 30, (200, 190, 255))
        # flag slides in with a wave
        u = ease_out_back(t / 0.5)
        fx0, fy0, fw, fh = 110 + (1 - u) * 600, 260, 500, 330
        sw = fw / 3
        for i, c in enumerate(FLAG):
            for k in range(10):
                x = fx0 + i * sw + k * sw / 10
                off = math.sin(t * 6 + (i * 10 + k) * 0.25) * 8
                d.rectangle([x * SS, (fy0 + off) * SS, (x + sw / 10 + 1) * SS, (fy0 + fh + off) * SS], fill=c)
        # countdown
        if t < REVEAL:
            n = 3 - int((t - 0.7) // 1.0) if t >= 0.7 else 3
            n = max(n, 1)
            ph = ((t - 0.7) % 1.0) if t >= 0.7 else 0
            r = 70 + 12 * (1 - ease(ph * 3))
            d.ellipse([(W / 2 - r) * SS, (700 - r) * SS, (W / 2 + r) * SS, (700 + r) * SS], fill=(255, 255, 255, 40),
                      outline=(255, 255, 255), width=5 * SS)
            arc = 360 * (1 - (t / REVEAL))
            d.arc([(W / 2 - 80) * SS, (620) * SS, (W / 2 + 80) * SS, (780) * SS], -90, -90 + arc, fill=(255, 230, 80), width=10 * SS)
            text(d, (W / 2, 700), str(n), 90, (255, 255, 255))
        else:
            k = ease_out_back((t - REVEAL) / 0.35)
            text(d, (W / 2, 700), "IERLAND!", int(40 + 34 * k), (90, 230, 130), stroke=6, stroke_fill=(20, 10, 40))
        for i, o in enumerate(OPTIONS):
            y = 850 + i * 125
            ok = t >= REVEAL and i == CORRECT
            wrong = t >= REVEAL and i != CORRECT
            fill = (60, 200, 110) if ok else ((255, 255, 255, 60) if wrong else (255, 255, 255, 235))
            tc = (255, 255, 255) if ok else ((255, 255, 255, 120) if wrong else (40, 20, 90))
            slide = ease((t - 0.3 - i * 0.12) / 0.4)
            x0 = 90 - (1 - slide) * 700
            d.rounded_rectangle([x0 * SS, y * SS, (x0 + 540) * SS, (y + 95) * SS], radius=47 * SS, fill=fill)
            text(d, (x0 + 60, y + 48), "ABC"[i], 40, tc)
            text(d, (x0 + 300, y + 48), o, 40, tc)
        v.add(img)
