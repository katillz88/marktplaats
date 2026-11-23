"""Shared helpers for the 5-second YouTube Shorts demos: video writer + audio synth."""
import math, os, subprocess, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 720, 1280          # 9:16 Shorts
SS = 2                    # supersampling factor for smooth edges
RW, RH = W * SS, H * SS
FPS = 30
SR = 44100
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_fc = {}


def font(size, bold=True):
    k = (size, bold)
    if k not in _fc: _fc[k] = ImageFont.truetype(FONT_B if bold else FONT_R, int(size * SS))
    return _fc[k]


def text(d, xy, s, size, fill=(255, 255, 255), anchor="mm", stroke=0, stroke_fill=(0, 0, 0), bold=True):
    d.text((xy[0] * SS, xy[1] * SS), s, font=font(size, bold), fill=fill, anchor=anchor,
           stroke_width=int(stroke * SS), stroke_fill=stroke_fill)


def ease(u):
    u = min(max(u, 0), 1); return u * u * (3 - 2 * u)


def ease_out_back(u):
    u = min(max(u, 0), 1); c = 1.7; return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2


class Video:
    """with Video('out.mp4', seconds) as v: v.add(img)  ...  v.audio = numpy array"""
    def __init__(self, path, seconds=5.0):
        self.path, self.seconds = path, seconds
        self.nframes = int(seconds * FPS)
        self.audio = np.zeros(int(seconds * SR))
        self.tmp = tempfile.mkdtemp()
        self.silent = os.path.join(self.tmp, "v.mp4")
        self.p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                   "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt",
                                   "yuv420p", "-crf", "18", self.silent], stdin=subprocess.PIPE)

    def add(self, img):
        if img.size != (W, H): img = img.resize((W, H), Image.LANCZOS)
        self.p.stdin.write(img.convert("RGB").tobytes())

    def sfx(self, t, sig, gain=1.0):
        i = int(t * SR)
        if i >= len(self.audio): return
        j = min(len(self.audio), i + len(sig)); self.audio[i:j] += sig[:j - i] * gain

    def __enter__(self): return self

    def __exit__(self, *a):
        self.p.stdin.close(); self.p.wait()
        a = self.audio.copy()
        fo = int(0.25 * SR); a[-fo:] *= np.linspace(1, 0, fo)
        a = np.tanh(a * 1.1) * 0.9
        pcm = (a * 32767).astype(np.int16)
        wav = os.path.join(self.tmp, "a.wav")
        with wave.open(wav, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", self.silent, "-i", wav, "-map", "0:v",
                        "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", self.path],
                       check=True)


# ---------------------------------------------------------------- audio synth
rng = np.random.default_rng(3)


def tax(d): return np.arange(int(d * SR)) / SR


def env(d, a=0.003, dec=0.2):
    t = tax(d); return np.minimum(t / a, 1) * np.exp(-t / dec)


def lowpass(x, cutoff):
    # FFT brick-ish lowpass (fast)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4); return np.fft.irfft(X, len(x))


def noise(d): return rng.uniform(-1, 1, int(d * SR))


def sweep(f0, f1, d):
    t = tax(d); f = f0 * (f1 / f0) ** (t / d); return np.sin(2 * np.pi * np.cumsum(f) / SR)


def tone(freq, d, dec=0.4, harm=((1, 1), (2, 0.3), (3, 0.12))):
    t = tax(d); return sum(a * np.sin(2 * np.pi * freq * h * t) for h, a in harm) * env(d, 0.004, dec)


def pluck(freq, d=0.6): return tone(freq, d, 0.18, ((1, 1), (2, 0.5), (3, 0.25), (4, 0.1))) * 0.5


def click(freq=2000, d=0.04): return (np.sin(2 * np.pi * freq * tax(d)) * env(d, 0.0005, 0.008)) * 0.6


def kick(): return sweep(140, 40, 0.3) * env(0.3, 0.001, 0.08)


def snare(): return lowpass(noise(0.2), 6000) * env(0.2, 0.001, 0.05) * 0.5


def hat():
    n = noise(0.05); return (n - lowpass(n, 7000)) * env(0.05, 0.0005, 0.012) * 0.5


def whoosh(d=0.4):
    t = tax(d); return lowpass(noise(d), 1500) * np.sin(np.pi * t / d) ** 2 * 1.2


def ding(): return tone(1318.5, 1.2, 0.5, ((1, 1), (2.76, 0.4), (5.4, 0.2))) * 0.35


def note(n): return 440 * 2 ** ((n - 69) / 12)   # MIDI -> Hz


def beat(seconds, bpm=120, swing=False, kick_steps=(0, 8), snare_steps=(4, 12), hats=True, gain=0.5):
    out = np.zeros(int(seconds * SR)); step = 60 / bpm / 4
    for s in range(int(seconds / step)):
        at = s * step; ps = s % 16; i = int(at * SR)
        for sig, cond, g in ((kick(), ps in kick_steps, 0.9), (snare(), ps in snare_steps, 0.8),
                             (hat(), hats and ps % 2 == 0, 0.4)):
            if cond:
                j = min(len(out), i + len(sig)); out[i:j] += sig[:j - i] * g
    return out * gain


def pad(freqs, d, gain=0.12):
    t = tax(d)
    s = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.003 * t) for f in freqs)
    e = np.minimum(t / 0.6, 1) * np.minimum((d - t) / 0.6, 1)
    return s * e * gain


def vgradient(w, h, top, bot):
    a = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top)[None, None, :] * (1 - a) + np.array(bot)[None, None, :] * a)
    return Image.fromarray(np.repeat(arr, w, axis=1).astype(np.uint8))
