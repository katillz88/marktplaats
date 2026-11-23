"""Synthesize the fight soundtrack (music + sound effects) from scratch with numpy.

Usage: python3 sound.py cues.json out.wav
No external audio or services: every sound is generated here.
"""
import json, sys, wave
import numpy as np

SR = 44100
rng = np.random.default_rng(1)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def env(dur, attack=0.002, decay=0.2):
    t = t_axis(dur)
    return np.minimum(t / attack, 1) * np.exp(-t / decay)


def lowpass(x, cutoff):
    # simple one-pole low-pass
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc; y[i] = acc
    return y


def noise(dur):
    return rng.uniform(-1, 1, int(dur * SR))


def sweep(f0, f1, dur):
    t = t_axis(dur)
    f = f0 * (f1 / f0) ** (t / dur)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


# ---------------------------------------------------------------- sound effects
def sfx_hit():
    d = 0.45
    thump = sweep(160, 45, d) * env(d, decay=0.09)
    crack = lowpass(noise(d), 3500) * env(d, 0.0005, 0.025) * 1.6
    return np.tanh((thump + crack) * 2.2) * 0.9


def sfx_bighit():
    d = 2.0
    boom = sweep(110, 28, d) * env(d, 0.002, 0.45)
    crack = lowpass(noise(d), 4000) * env(d, 0.0005, 0.05) * 2.0
    rumble = lowpass(noise(d), 120) * env(d, 0.01, 0.6) * 6
    return np.tanh((boom + crack + rumble) * 2.5) * 0.95


def sfx_block():
    d = 0.25
    thud = sweep(220, 110, d) * env(d, decay=0.04)
    tap = lowpass(noise(d), 1800) * env(d, 0.0005, 0.015)
    return (thud + tap) * 0.6


def sfx_whoosh():
    d = 0.35
    t = t_axis(d)
    shape = np.sin(np.pi * t / d) ** 2
    n = noise(d)
    lo = lowpass(n, 600); hi = lowpass(n, 2500)
    mix = lo + (hi - lo) * (t / d)          # brightens as it passes
    return mix * shape * 1.4


def sfx_land():
    d = 0.8
    thump = sweep(90, 35, d) * env(d, 0.003, 0.14)
    dust = lowpass(noise(d), 700) * env(d, 0.005, 0.18) * 1.5
    return np.tanh((thump + dust) * 2) * 0.85


def sfx_bell():
    d = 1.6
    t = t_axis(d)
    tone = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((880, 1), (2210, 0.5), (3520, 0.25), (1320, 0.3)))
    return tone * env(d, 0.001, 0.5) * 0.3


def sfx_ko():
    # "ding ding" boxing bell
    b = sfx_bell(); gap = int(0.35 * SR)
    out = np.zeros(len(b) + gap); out[:len(b)] += b; out[gap:] += b
    return out


SFX = dict(hit=sfx_hit, bighit=sfx_bighit, block=sfx_block, whoosh=sfx_whoosh, land=sfx_land, ko=sfx_ko)
VOL = dict(hit=1.0, bighit=1.1, block=0.9, whoosh=0.6, land=1.0, ko=0.8)


# ---------------------------------------------------------------- music: drum & bass loop
def kick():
    d = 0.3; return sweep(130, 40, d) * env(d, 0.001, 0.08)


def snare():
    d = 0.2
    return (lowpass(noise(d), 5000) * env(d, 0.001, 0.05) + np.sin(2 * np.pi * 190 * t_axis(d)) * env(d, 0.001, 0.04)) * 0.6


def hat():
    d = 0.05; n = noise(d); return (n - lowpass(n, 6000)) * env(d, 0.0005, 0.012) * 0.5


def bass_note(freq, dur):
    t = t_axis(dur)
    saw = 2 * ((t * freq) % 1) - 1
    return lowpass(saw, 400) * np.minimum(t / 0.005, 1) * np.exp(-t / (dur * 0.8)) * 0.5


def music(duration, bpm=170):
    beat = 60 / bpm
    out = np.zeros(int((duration + 1) * SR))
    K, Sn, Hh = kick(), snare(), hat()
    def put(sig, at, g=1.0):
        i = int(at * SR); j = min(len(out), i + len(sig)); out[i:j] += sig[:j - i] * g
    # 2-bar breakbeat pattern in 8ths: K . . S . K S . | K . K S . . S .
    kick_steps = [0, 5, 8, 10]; snare_steps = [3, 6, 11, 14]
    roots = [55.0, 55.0, 65.41, 49.0]    # A1 A1 C2 G1, one per bar
    step = beat / 2; bar_steps = 16; n_steps = int(duration / step)
    for s in range(n_steps):
        at = s * step; ps = s % bar_steps
        if ps in kick_steps: put(K, at, 0.9)
        if ps in snare_steps: put(Sn, at, 0.8)
        put(Hh, at, 0.6 if s % 2 else 0.35)
        if s % 2 == 0:
            root = roots[(s // bar_steps) % len(roots)]
            put(bass_note(root * (2 if ps in (6, 14) else 1), step * 1.8), at, 0.8)
    return out


# ---------------------------------------------------------------- mix
def main(cues_file, out_file):
    c = json.load(open(cues_file))
    dur = c["duration"]
    n = int(dur * SR)
    mix = np.zeros(n + SR * 3)
    m = music(dur) * 0.35
    fade = np.ones(len(m)); fo = int(1.2 * SR); end = n
    fade[end - fo:end] = np.linspace(1, 0, fo); fade[end:] = 0
    fade[:int(0.5 * SR)] = np.linspace(0, 1, int(0.5 * SR))
    mix[:len(m)] += (m * fade)[:len(mix)]
    cache = {}
    for cue in c["cues"]:
        k = cue["kind"]
        if k not in SFX: continue
        if k not in cache: cache[k] = SFX[k]()
        s = cache[k] * VOL[k]; i = int(cue["t"] * SR)
        mix[i:i + len(s)] += s[:len(mix) - i]
    mix = mix[:n]
    mix = np.tanh(mix * 1.1) * 0.9          # soft limiter
    pcm = (mix * 32767).astype(np.int16)
    stereo = np.repeat(pcm[:, None], 2, axis=1)
    with wave.open(out_file, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(stereo.tobytes())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
