from lib import *
import random
from PIL import ImageFilter

random.seed(5)
WX0, WY0, WX1, WY1 = 90, 230, 630, 860       # window

# --- static layers
def city_layer():
    img = Image.new("RGB", (RW, RH), (14, 16, 40))
    d = ImageDraw.Draw(img)
    for y in range(WY0, WY1):
        u = (y - WY0) / (WY1 - WY0)
        d.line([(WX0 * SS, y * SS), (WX1 * SS, y * SS)], fill=(int(30 + 40 * u), int(25 + 20 * u), int(70 + 30 * u)), width=SS)
    # bokeh city lights
    for _ in range(70):
        x = random.uniform(WX0, WX1); y = random.uniform(WY0 + 250, WY1); r = random.uniform(8, 26)
        c = random.choice([(255, 190, 110), (255, 140, 170), (130, 180, 255), (255, 230, 150)])
        d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=c)
    return img.filter(ImageFilter.GaussianBlur(10 * SS))


city = city_layer()
room = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
rd = ImageDraw.Draw(room)
rd.rectangle([0, 0, RW, RH], fill=(28, 22, 38, 255))
rd.rectangle([WX0 * SS, WY0 * SS, WX1 * SS, WY1 * SS], fill=(0, 0, 0, 0))
fr = (52, 40, 58, 255)
rd.rectangle([(WX0 - 18) * SS, (WY0 - 18) * SS, (WX1 + 18) * SS, (WY1 + 18) * SS], outline=fr, width=18 * SS)
rd.rectangle([(WX0 + WX1) / 2 * SS - 7 * SS, WY0 * SS, (WX0 + WX1) / 2 * SS + 7 * SS, WY1 * SS], fill=fr)
rd.rectangle([WX0 * SS, (WY0 + WY1) / 2 * SS - 7 * SS, WX1 * SS, (WY0 + WY1) / 2 * SS + 7 * SS], fill=fr)
# desk
rd.rectangle([0, 960 * SS, RW, RH], fill=(48, 32, 34, 255))
rd.rectangle([0, 950 * SS, RW, 975 * SS], fill=(70, 46, 44, 255))
# lamp
rd.polygon([(470 * SS, 760 * SS), (600 * SS, 760 * SS), (565 * SS, 690 * SS), (505 * SS, 690 * SS)], fill=(240, 170, 90, 255))
rd.line([(535 * SS, 760 * SS), (535 * SS, 950 * SS)], fill=(30, 24, 30, 255), width=8 * SS)
rd.ellipse([495 * SS, 940 * SS, 575 * SS, 960 * SS], fill=(30, 24, 30, 255))
# mug
rd.rounded_rectangle([170 * SS, 870 * SS, 250 * SS, 955 * SS], radius=10 * SS, fill=(200, 110, 90, 255))
rd.arc([235 * SS, 885 * SS, 280 * SS, 935 * SS], -90, 90, fill=(200, 110, 90, 255), width=9 * SS)
# books
for i, (c, h) in enumerate([((90, 120, 170), 22), ((160, 90, 110), 18), ((110, 150, 110), 26)]):
    y = 950 - sum(x[1] for x in [((0,), 22), ((0,), 18), ((0,), 26)][:i + 1])
    rd.rectangle([300 * SS, y * SS, (420 - i * 12) * SS, (y + h) * SS], fill=c + (255,))
# lamp glow
glow = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([340 * SS, 700 * SS, 730 * SS, 1100 * SS], fill=(255, 170, 80, 70))
glow = glow.filter(ImageFilter.GaussianBlur(60 * SS))

drops = [dict(x=random.uniform(WX0, WX1), y=random.uniform(WY0, WY1), r=random.uniform(3, 7),
              v=random.uniform(0, 60)) for _ in range(60)]
streaks = [dict(x=random.uniform(WX0, WX1), y=random.uniform(WY0, WY1), sp=random.uniform(900, 1400)) for _ in range(90)]

with Video("7_lofi.mp4") as v:
    # music: Fmaj7 - Em7 - Dm7 - Cmaj7 rhodes-ish chords, slow swung drums, rain, vinyl crackle
    chords = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]
    for i, ch in enumerate(chords * 2):
        for n in ch:
            v.sfx(i * 1.25, tone(note(n + 12), 1.4, 0.9, ((1, 1), (2, 0.15), (3, 0.05))) * 0.1)
    v.audio += beat(5, bpm=78, kick_steps=(0, 7, 10), snare_steps=(4, 12), gain=0.3)
    rain = lowpass(noise(5), 3000) * 0.08
    v.audio += rain[:len(v.audio)]
    crackle = np.zeros(len(v.audio)); idx = rng.integers(0, len(crackle), 250); crackle[idx] = rng.uniform(-0.25, 0.25, 250)
    v.audio += crackle
    v.audio = lowpass(v.audio, 5500)
    for f in range(v.nframes):
        t = f / FPS
        img = city.copy().convert("RGBA")
        d = ImageDraw.Draw(img, "RGBA")
        for s in streaks:
            y = (s["y"] + s["sp"] * t - WY0) % (WY1 - WY0) + WY0
            d.line([(s["x"] - 6) * SS, (y - 40) * SS, s["x"] * SS, y * SS], fill=(200, 210, 255, 70), width=2 * SS)
        for dr in drops:
            y = dr["y"] + dr["v"] * t
            if y > WY1: continue
            r = dr["r"]
            d.ellipse([(dr["x"] - r) * SS, (y - r * 1.2) * SS, (dr["x"] + r) * SS, (y + r) * SS], fill=(220, 230, 255, 90))
        img.alpha_composite(room); img.alpha_composite(glow)
        d = ImageDraw.Draw(img, "RGBA")
        # steam
        for k in range(3):
            pts = [((210 + k * 14 + math.sin(t * 2 + j * 0.5 + k) * 8) * SS, (860 - j * 10) * SS) for j in range(9)]
            d.line(pts, fill=(255, 255, 255, 60), width=4 * SS, joint="curve")
        text(d, (W / 2, 110), "lofi beats", 58, (255, 215, 170))
        text(d, (W / 2, 170), "om bij te studeren", 32, (210, 190, 220), bold=False)
        text(d, (W / 2, 1120), "🌧" if False else "regen  ·  chill  ·  focus", 28, (180, 160, 190), bold=False)
        v.add(img)
