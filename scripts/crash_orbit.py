"""Orbit AI-tool logos around Crash's head. Output: assets/crash.gif"""
import math, io, fitz
from PIL import Image, ImageSequence, ImageEnhance

LOGOS = ["claude-color", "openai", "gemini-color", "deepseek-color"]
SIZE = 56

def logo(name):
    svg = open(f"assets/logos/{name}.svg", encoding="utf-8").read().replace("currentColor", "#10a37f" if name == "openai" else "#000")
    import re
    if name.startswith("gemini"): svg = re.sub(r"url\(#[^)]*\)", "#4285f4", svg)
    svg = svg.replace('height="1em"', 'height="128"').replace('width="1em"', 'width="128"')
    doc = fitz.open(stream=svg.encode(), filetype="svg")
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(128 / doc[0].rect.width, 128 / doc[0].rect.width), alpha=True)
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGBA")

src = Image.open("assets/crash_orig.gif")
frames = [f.convert("RGBA") for f in ImageSequence.Iterator(src)]
n = len(frames)
# head centre per frame: centroid of the top slice of the character
cs = []
for f in frames:
    a = f.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    bb = a.getbbox() or (0, 0, 464, 464)
    top = a.crop((0, bb[1], 464, bb[1] + (bb[3] - bb[1]) // 4))
    tb = top.getbbox() or bb
    cs.append(((tb[0] + tb[2]) / 2, bb[1] + (bb[3] - bb[1]) * 0.12))
sm = []
for i in range(n):
    w = [cs[(i + k) % n] for k in range(-4, 5)]
    sm.append((sum(p[0] for p in w) / 9, sum(p[1] for p in w) / 9))

imgs = [logo(l) for l in LOGOS]
CW, CH = 464, 464
PAD_T, PAD_B = 70, 30
out = []
for i, f in enumerate(frames):
    cx, cy = sm[i]
    items = []
    for k, im in enumerate(imgs):
        ang = 2 * math.pi * (i / n) + 2 * math.pi * k / len(imgs)
        x = cx + 105 * math.cos(ang)
        y = cy - 38 + 22 * math.sin(ang)   # tilted ellipse = 3D ring
        depth = math.sin(ang)               # >0 front, <0 behind
        s = SIZE * (0.8 + 0.25 * depth)
        items.append((depth, x, y, s, im))
    canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    def put(it):
        d, x, y, s, im = it
        t = im.resize((int(s), int(s)), Image.Resampling.LANCZOS)
        if d < 0:
            t.putalpha(t.getchannel("A").point(lambda v: int(v * 0.65)))
        canvas.alpha_composite(t, (int(x - s / 2), int(y - s / 2)))
    for it in sorted(items):
        if it[0] < 0: put(it)
    canvas.alpha_composite(f)
    for it in sorted(items):
        if it[0] >= 0: put(it)
    out.append(canvas)

bb = None
for o in out:
    b = o.getchannel("A").point(lambda v: 255 if v > 10 else 0).getbbox()
    bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
box = (max(bb[0] - 8, 0), max(bb[1] - 8, 0), min(bb[2] + 8, CW), min(bb[3] + 8, CH))
out = [o.crop(box) for o in out]
out[0].save("assets/crash.gif", save_all=True, append_images=out[1:], duration=src.info.get("duration", 70), loop=0, disposal=2, optimize=True)
print(box, len(out))
