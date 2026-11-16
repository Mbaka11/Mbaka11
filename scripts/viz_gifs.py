"""Generate dark data-viz GIFs: brain point cloud, RL reward curve, decision tree."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, N = 360, 300, 60
BG = (13, 17, 23)
rng = np.random.default_rng(7)
try: FONT = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 11)
except Exception: FONT = ImageFont.load_default()

def save(frames, name):
    q = [f.convert("RGB").quantize(64, method=Image.Quantize.MEDIANCUT) for f in frames]
    q[0].save(f"assets/{name}.gif", save_all=True, append_images=q[1:], duration=60, loop=0, optimize=True)

def glow(img, pts):  # pts: (x,y,r,color,alpha)
    layer = Image.new("RGB", img.size, (0, 0, 0)); d = ImageDraw.Draw(layer)
    for x, y, r, c in pts: d.ellipse((x - r, y - r, x + r, y + r), fill=c)
    layer = layer.filter(ImageFilter.GaussianBlur(3))
    from PIL import ImageChops
    return ImageChops.add(img, layer)

# ---------- 1. brain ----------
def brain_pts(n=2600):
    p = []
    while len(p) < n:
        v = rng.normal(size=3); v /= np.linalg.norm(v)
        side = rng.choice([-1, 1])
        x, y, z = v[0] * 0.55 + side * 0.5, v[1] * 0.75, v[2] * 1.05
        r = 1 + 0.07 * math.sin(9 * z + 3 * x) * math.sin(8 * y)   # gyri
        p.append((x * r, y * r + 0.1, z * r))
    for _ in range(450):  # cerebellum + stem
        v = rng.normal(size=3); v /= np.linalg.norm(v)
        p.append((v[0] * 0.55, v[1] * 0.28 - 0.55, v[2] * 0.4 - 0.7))
    for _ in range(120):
        p.append((rng.normal(0, .06), rng.uniform(-1.0, -0.5), rng.normal(0, .06) - 0.45))
    return np.array(p)

def brain():
    P = brain_pts(); frames = []
    labels = [("policy", 0.5, 0.45, 0.2), ("hidden 3", -0.6, 0.2, 0.5), ("reward", 0.1, -0.5, -0.5)]
    for i in range(N):
        a = 2 * math.pi * i / N; c, s = math.cos(a), math.sin(a)
        x = P[:, 0] * c + P[:, 2] * s; z = -P[:, 0] * s + P[:, 2] * c; y = P[:, 1]
        sx, sy = W / 2 + x * 105, H / 2 - y * 105 + 5
        pulse = (np.sin(P[:, 2] * 4 + P[:, 0] * 3 - 2 * a) > 0.93)
        img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
        for k in np.argsort(z):
            t = (z[k] + 1.3) / 2.6; v = int(35 + 105 * t)
            col = (60, 255, 140) if pulse[k] else (v, v, v)
            r = 1.4 if pulse[k] else 1 + t * 0.6
            d.ellipse((sx[k] - r, sy[k] - r, sx[k] + r, sy[k] + r), fill=col)
        img = glow(img, [(sx[k], sy[k], 3, (20, 110, 60)) for k in np.where(pulse)[0][::3]])
        d = ImageDraw.Draw(img)
        for name, lx, ly, lz in labels:
            X = lx * c + lz * s; Z = -lx * s + lz * c
            if Z > -0.2:
                px, py = W / 2 + X * 105, H / 2 - ly * 105 + 5
                d.line((px, py, px + 22, py - 16), fill=(90, 90, 90))
                d.text((px + 24, py - 26), name, font=FONT, fill=(200, 255, 220))
        frames.append(img)
    save(frames, "brain")

# ---------- 2. RL reward curve ----------
def reward():
    T = np.linspace(0, 1, 200)
    base = 1 - np.exp(-4 * T)
    runs = [base * (0.8 + 0.1 * k) + rng.normal(0, 0.04, 200).cumsum() * 0.02 + rng.normal(0, 0.06, 200) * (1 - T * 0.6) for k in range(4)]
    best = runs[3]; best_s = np.convolve(best, np.ones(9) / 9, mode="same")
    frames = []; L, R, Tp, B = 40, W - 16, 34, H - 40
    for i in range(N + 20):
        m = int(min(i, N) / N * 199) + 1
        img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
        for gy in range(5):
            y = Tp + (B - Tp) * gy / 4; d.line((L, y, R, y), fill=(28, 34, 42))
        d.line((L, B, R, B), fill=(70, 70, 70)); d.line((L, Tp, L, B), fill=(70, 70, 70))
        d.text((L, 10), "episode return", font=FONT, fill=(139, 148, 158))
        d.text((R - 70, B + 8), "steps  →", font=FONT, fill=(139, 148, 158))
        def pt(k, arr): return (L + (R - L) * T[k], B - (B - Tp) * (np.clip(arr[k], 0, 1.15) / 1.15))
        for r, col in zip(runs[:3], [(40, 60, 90), (60, 50, 90), (40, 90, 80)]):
            d.line([pt(k, r) for k in range(m)], fill=col, width=1)
        d.line([pt(k, best) for k in range(m)], fill=(30, 90, 60), width=1)
        d.line([pt(k, best_s) for k in range(m)], fill=(60, 255, 140), width=2)
        x, y = pt(m - 1, best_s)
        img = glow(img, [(x, y, 4, (40, 160, 90))]); d = ImageDraw.Draw(img)
        d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(220, 255, 235))
        d.text((x - 62 if x > R - 80 else x + 8, y - 18), f"return {best_s[m-1]*100:.0f}", font=FONT, fill=(200, 255, 220))
        frames.append(img)
    save(frames, "reward")

# ---------- 3. decision tree ----------
def tree():
    segs = []
    def grow(x, y, ang, ln, depth, d0):
        x2, y2 = x + ln * math.cos(ang), y - ln * math.sin(ang)
        segs.append((x, y, x2, y2, d0, depth))
        if depth < 6:
            for da in (-0.5, 0.5):
                grow(x2, y2, ang + da + rng.normal(0, 0.12), ln * 0.74, depth + 1, d0 + 1)
    grow(W / 2, H - 20, math.pi / 2, 62, 0, 0)
    names = {1: "obs[3] < 0.2", 2: "q(a₀) > q(a₁)", 3: "reward > τ"}
    frames = []
    for i in range(N + 20):
        prog = min(i / (N * 0.8), 1) * 7
        img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
        pts = []
        for x1, y1, x2, y2, d0, dep in segs:
            f = np.clip(prog - d0, 0, 1)
            if f <= 0: continue
            xe, ye = x1 + (x2 - x1) * f, y1 + (y2 - y1) * f
            g = int(70 + 185 * (dep / 6)); d.line((x1, y1, xe, ye), fill=(30, g, 90 + int(40 * dep / 6)), width=max(1, 4 - dep // 2))
            if dep >= 5 and f >= 1: pts.append((xe, ye, 3, (20, 130, 70)))
        img = glow(img, pts); d = ImageDraw.Draw(img)
        done = set()
        for x1, y1, x2, y2, d0, dep in segs:
            if np.clip(prog - d0, 0, 1) >= 1 and dep in names and dep not in done and x2 > W / 2 - 1:
                done.add(dep)
                d.rectangle((x2 + 3, y2 - 7, x2 + 3 + 6 * len(names[dep]), y2 + 6), outline=(60, 90, 70))
                d.text((x2 + 6, y2 - 6), names[dep], font=FONT, fill=(200, 255, 220))
        frames.append(img)
    save(frames, "tree")

if __name__ == "__main__":
    brain(); reward(); tree()
