# Synthesizes the 15s showreel soundtrack (120 BPM, 1 beat = 0.5s) so every cut lands on a hit.
# Usage: python3 soundtrack.py  → soundtrack.wav
import numpy as np, wave

SR, DUR = 44100, 15.0
N = int(SR * DUR)
L = np.zeros(N); R = np.zeros(N)
rs = np.random.default_rng(3)

def note(n):  # MIDI → Hz
    return 440.0 * 2 ** ((n - 69) / 12)

def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N: return
    sig = sig[: N - i] * gain
    L[i:i + len(sig)] += sig * np.sqrt(0.5 * (1 - pan))
    R[i:i + len(sig)] += sig * np.sqrt(0.5 * (1 + pan))

def tt(d): return np.arange(int(d * SR)) / SR

def lowpass(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / fc) ** 4), len(x))

def highpass(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X * (f / fc) ** 2 / np.sqrt(1 + (f / fc) ** 4), len(x))

def bandpass(x, lo, hi): return lowpass(highpass(x, lo), hi)

# ---------- instruments ----------
def kick(d=0.45, punch=1.0):
    t = tt(d); f = 45 + 120 * np.exp(-t * 32)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 7) * punch
    click = bandpass(rs.standard_normal(len(t)), 1500, 6000) * np.exp(-t * 300) * 0.4
    return np.tanh((body + click) * 1.6)

def clap(d=0.3):
    t = tt(d); n = bandpass(rs.standard_normal(len(t)), 900, 5000)
    env = np.exp(-t * 16) + 0.6 * (np.exp(-np.maximum(t - .011, 0) * 60) * (t > .011)) + 0.5 * (np.exp(-np.maximum(t - .022, 0) * 60) * (t > .022))
    return n * env * 0.5 + np.sin(2 * np.pi * 185 * t) * np.exp(-t * 30) * 0.3

def hat(d=0.06, open_=False):
    t = tt(0.35 if open_ else d); n = highpass(rs.standard_normal(len(t)), 7000)
    return n * np.exp(-t * (9 if open_ else 70)) * 0.35

def saw(f, t, detune=0.0):
    ph = (f * (1 + detune)) * t
    return 2 * (ph - np.floor(ph + 0.5))

def pluck(n, d=0.6, bright=4000):
    t = tt(d); f = note(n)
    s = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.3 * np.exp(-t * (5 + 3 * k)) for k in range(1, 7))
    return lowpass(s, bright) * 0.5

def bell(n, d=3.0):
    t = tt(d); f = note(n)
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 1.6) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3.2)
            + 0.25 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 6)) * 0.35

def pad(chord, d, cutoff=1800):
    t = tt(d); s = np.zeros(len(t))
    for n in chord:
        for dt in (-0.006, 0.0, 0.007): s += saw(note(n), t, dt)
    env = np.minimum(1, t / 0.08) * np.minimum(1, (d - t) / 0.12)
    return lowpass(s / (len(chord) * 3), cutoff) * env * 0.5

def bass(n, d):
    t = tt(d); f = note(n)
    s = np.sin(2 * np.pi * f * t) + 0.35 * lowpass(saw(f, t), 400)
    return s * np.minimum(1, t / 0.01) * np.minimum(1, (d - t) / 0.03) * 0.55

def riser(d, f0=200, f1=2400):
    t = tt(d); x = t / d
    f = f0 * (f1 / f0) ** (x ** 2); tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    n = rs.standard_normal(len(t)); n = highpass(n, 800) * (x ** 3)
    return (tone * x ** 2 + n * 0.35) * 0.6

def whoosh(d=0.35, lo=300, hi=5000):
    t = tt(d); n = bandpass(rs.standard_normal(len(t)), lo, hi)
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return n * env * 0.5

def impact(d=2.5, size=1.0):
    t = tt(d); f = 32 + 90 * np.exp(-t * 14)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    crash = highpass(rs.standard_normal(len(t)), 3000) * np.exp(-t * 2.6) * 0.3
    return np.tanh((boom * 1.4 + crash) * size) * 0.9

def blip(f=1800, d=0.04):
    t = tt(d); return np.sin(2 * np.pi * f * t) * np.exp(-t * 90) * 0.18

def clack(d=0.05):
    t = tt(d); return bandpass(rs.standard_normal(len(t)), 1500, 6000) * np.exp(-t * 120) * 0.35

# ---------- arrangement ----------
B = 0.5
CH = {'Am': [57, 60, 64, 69], 'F': [53, 57, 60, 65], 'C': [48, 55, 60, 64], 'G': [55, 59, 62, 67], 'E': [52, 56, 59, 64], 'Fmaj7': [53, 57, 60, 64, 69], 'Cadd9': [48, 55, 62, 64, 67]}
ROOT = {'Am': 33, 'F': 29, 'C': 36, 'G': 31, 'E': 28, 'Fmaj7': 29, 'Cadd9': 36}
prog = [(0, 2, 'Am'), (2, 4, 'F'), (4, 6, 'C'), (6, 8, 'G'), (8, 10, 'Am'), (10, 11, 'F'), (11, 12, 'G'), (12, 12.4, 'E'), (13, 13.95, 'Fmaj7')]
for a, b, c in prog:
    add(pad(CH[c], b - a, 900 if a < 2 else 2400), a, 0.55 if a < 2 else 0.42)

# 0–2 prologue: ticking hats, plucks on each word, riser into the name
for i in range(16): add(hat(), i * B / 4 + 0.0, 0.25 + 0.2 * (i % 2 == 0), pan=0.3)
for t0, n in [(0.0, 69), (0.5, 72), (1.0, 76), (1.5, 81)]:
    add(pluck(n), t0, 0.9); add(kick(punch=.8), t0, 0.55 if t0 else 0.4)
add(riser(0.75, 300, 3000), 1.25, 0.8); add(whoosh(0.3), 1.8, 0.7, pan=-0.4)

# 2–10.5 main groove
def groove(a, b, half=False):
    t = a
    while t < b - 1e-6:
        k = round((t - a) / B)
        if not half or k % 2 == 0: add(kick(), t, 0.95)
        if (k % 2 == 1 and not half) or (half and k % 4 == 2): add(clap(), t, 0.6, pan=0.1)
        for s in range(4):
            add(hat(), t + s * B / 4, 0.5 if s % 2 else 0.22, pan=-0.25 + 0.5 * (s % 2))
        if k % 4 == 3: add(hat(open_=True), t + B / 2, 0.35, pan=0.3)
        t += B

groove(2, 10.5)
for a, b, c in prog[1:6]:
    t = a
    while t < b - 1e-6:
        for s, off in enumerate([0, 0.75, 1.5, 2.25, 3.0, 3.5]):
            tb = t + off * B / 2
            if tb < b: add(bass(ROOT[c] + (12 if s in (3, 5) else 0), 0.2), tb, 0.8)
        t += 2 * B
for h in (2.0, 4.0): add(impact(1.2, 0.7), h, 0.55)
for h in (5.0, 6.0, 7.0, 8.0): add(impact(0.8, 0.5), h, 0.4)
add(whoosh(0.3), 3.72, 0.8, pan=0.4)
# counter ticks while numbers roll
for s0 in (4.0, 5.0, 6.0, 7.0):
    t, k = s0 + 0.02, 0
    while t < s0 + 0.5:
        add(blip(1400 + 90 * k), t, 1.0, pan=0.5 * np.sin(k)); t += 0.012 + 0.0022 * k * k; k += 1
for h in (4.8, 5.8, 6.8, 7.8): add(whoosh(0.25, 500, 7000), h, 0.8, pan=-0.3)
# journey: whoosh per camera move, pluck per milestone
for i, n in enumerate([69, 72, 76, 79, 81]):
    add(whoosh(0.26, 250, 4000), 7.98 + 0.5 * i, 0.9, pan=-0.6 + 0.3 * i)
    add(pluck(n, 0.5, 6000), 8.22 + 0.5 * i, 0.8, pan=-0.3 + 0.15 * i)
add(riser(0.55, 400, 5000), 10.45, 1.0)

# 11 zoom-through hit, half-time
add(impact(1.6, 1.0), 11.0, 0.5); add(kick(), 11.0, 1.0)
groove(11.0, 12.0, half=True)
for i in range(3): add(whoosh(0.25, 400, 6000), 11.0 + 0.08 * i, 0.6, pan=[-0.7, 0.7, 0][i])
for a, b, c in prog[6:7]: add(bass(ROOT[c], 0.9), a, 0.8)
rev = hat(open_=True)[::-1] * 1.4; add(rev, 12.42 - len(rev) / SR, 1.0)
# 12.0–12.42 bricks stacking + snare roll build
for i in range(34): add(clack(), 12.0 + 0.009 * i + 0.002 * (i % 3), 0.5, pan=np.sin(i))
t, k = 12.1, 0
while t < 12.40: add(clap(0.08), t, 0.25 + 0.5 * (t - 12.1) / 0.3, pan=0.2 * np.sin(k)); t += max(0.018, 0.06 - k * 0.006); k += 1
add(riser(0.4, 600, 6000), 12.0, 0.7)
# 12.42 the wall breaks
add(impact(2.4, 1.3), 12.42, 1.0); add(kick(0.6, 1.2), 12.42, 1.0); add(bass(28, 0.5), 12.42, 1.0)
for i in range(40): add(clack(0.04), 12.44 + (i / 40) ** 1.6 * 0.9, 0.4 * (1 - i / 40), pan=rs.uniform(-.9, .9))
add(whoosh(0.3), 12.8, 0.7, pan=0.5)
# 13–15 finale: melody on the lines, final chord
for i, n in enumerate([76, 74, 72, 74, 76, 79]): add(pluck(n, 0.6, 5000), 13.02 + i * 0.07, 0.35, pan=-0.3 + i * 0.12)
for i, n in enumerate([79, 81, 84]): add(pluck(n, 0.8, 5000), 13.3 + i * 0.12, 0.35)
add(riser(0.5, 500, 4000), 13.45, 0.6)
add(impact(1.2, 0.9), 13.95, 0.8); add(kick(0.6), 13.95, 1.0)
add(pad(CH['Cadd9'], 1.05, 3200), 13.95, 0.7)
for i, n in enumerate([72, 79, 84, 88]): add(bell(n, 1.05), 13.95 + i * 0.05, 0.55, pan=-0.45 + 0.3 * i)
add(bass(24, 1.0), 13.95, 0.9)

# ---------- master: reverb send, glue, fade ----------
def reverb(x, mix=0.18):
    y = np.zeros_like(x)
    for D, g in [(1557, .82), (1617, .81), (1491, .83), (1422, .82), (1277, .8), (1356, .81)]:
        c = x.copy()
        for k in range(D, len(c), D): c[k:k + D] += g * c[k - D:k][: len(c[k:k + D])]
        y += c
    return lowpass(y / 6, 5000) * mix
Lw, Rw = reverb(L), reverb(np.roll(R, 37))
L2, R2 = L + Lw, R + Rw
fade = np.ones(N); fl = int(0.12 * SR); fade[-fl:] = np.linspace(1, 0, fl) ** 2
mix = np.stack([L2, R2], 1) * fade[:, None]
mix = np.tanh(mix / (np.max(np.abs(mix)) * 0.55)) * 0.89
with wave.open('soundtrack.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('peak', np.max(np.abs(mix)))
