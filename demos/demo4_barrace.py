from lib import *

# Illustrative demo data (not real statistics) - labelled as such in the video.
YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
DATA = {
    "Gaming":    [90, 100, 108, 115, 120, 126, 130],
    "Koken":     [60, 72, 80, 84, 90, 95, 98],
    "Tech":      [70, 78, 86, 96, 110, 122, 136],
    "Muziek":    [100, 104, 107, 110, 112, 114, 116],
    "Sport":     [55, 66, 82, 90, 96, 103, 108],
    "Animatie":  [30, 45, 65, 88, 112, 140, 165],
    "Reizen":    [50, 35, 58, 74, 86, 92, 96],
    "Shorts":    [10, 30, 60, 95, 130, 160, 190],
}
COL = {"Gaming": (120, 90, 255), "Koken": (255, 150, 60), "Tech": (60, 170, 255), "Muziek": (255, 80, 140),
       "Sport": (70, 210, 120), "Animatie": (255, 210, 60), "Reizen": (90, 220, 220), "Shorts": (255, 70, 70)}
TOP = 6
T0, T1 = 0.4, 4.4
X0, BAR_W, Y0, ROW = 190, 390, 330, 120


def values(ft):
    u = min(max((ft - T0) / (T1 - T0), 0), 1) * (len(YEARS) - 1)
    i = min(int(u), len(YEARS) - 2); f = ease(u - i)
    return {k: v[i] + (v[i + 1] - v[i]) * f for k, v in DATA.items()}, YEARS[0] + u


bg = vgradient(RW, RH, (16, 18, 34), (6, 6, 14))
rank_pos = {k: 10.0 for k in DATA}
prev_leader = None
with Video("4_bar_race.mp4") as v:
    v.audio += beat(5, bpm=110, kick_steps=(0, 6, 8), gain=0.35)
    v.audio += pad([note(57), note(64), note(69)], 5, 0.04)
    for f in range(v.nframes):
        ft = f / FPS
        vals, yr = values(ft)
        order = sorted(vals, key=lambda k: -vals[k])
        for r, k in enumerate(order):
            rank_pos[k] += (r - rank_pos[k]) * 0.25 if f else (r - rank_pos[k])
        if prev_leader and order[0] != prev_leader:
            v.sfx(ft, whoosh(0.35), 0.6); v.sfx(ft, click(1500, 0.06), 0.8)
        prev_leader = order[0]
        mx = max(vals.values())
        img = bg.copy(); d = ImageDraw.Draw(img, "RGBA")
        text(d, (W / 2, 110), "Grootste YouTube-", 50, (255, 255, 255), stroke=4)
        text(d, (W / 2, 175), "niches", 50, (255, 255, 255), stroke=4)
        text(d, (W / 2, 235), "voorbeelddata / demo", 24, (170, 170, 190), bold=False)
        for k in DATA:
            rp = rank_pos[k]
            if rp > TOP - 0.01: continue
            y = Y0 + rp * ROW
            w = max(8, BAR_W * vals[k] / mx)
            c = COL[k]
            d.rounded_rectangle([X0 * SS, y * SS, (X0 + w) * SS, (y + 86) * SS], radius=14 * SS, fill=c)
            text(d, (X0 - 16, y + 43), k, 30, (235, 235, 245), anchor="rm")
            text(d, (X0 + w + 12, y + 43), f"{vals[k]:.0f}M", 28, c, anchor="lm")
        text(d, (W - 50, 1150), f"{int(yr)}", 120, (70, 72, 100), anchor="rm")
        v.add(img)
