from flask import Flask, render_template, request
from PIL import Image, ImageDraw, ImageFont
import os, uuid, math, random

app = Flask(__name__)

# ---------------- CONFIG ----------------
OUTPUT_FOLDER = "static/output"
WIDTH, HEIGHT = 800, 450
BASE_FONT_SIZE = 70
PADDING = 40
FONT_PATH = r"C:\Windows\Fonts\arialbd.ttf"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---------------- TEXT UTIL ----------------
def draw_multiline_text(draw, text, font, x, y, fill):
    words = text.split(" ")
    lines, line = [], ""

    for word in words:
        test = line + word + " "
        if draw.textlength(test, font=font) < WIDTH - 2 * PADDING:
            line = test
        else:
            lines.append(line)
            line = word + " "
    lines.append(line)

    y_cursor = y
    for l in lines:
        w = draw.textlength(l, font=font)
        x_pos = (WIDTH - w) // 2
        draw.text((x_pos, y_cursor), l, fill=fill, font=font)
        y_cursor += font.size + 6

def text_block_height(text, font, draw):
    lines = 1
    current = ""
    for word in text.split(" "):
        test = current + word + " "
        if draw.textlength(test, font=font) < WIDTH - 2 * PADDING:
            current = test
        else:
            lines += 1
            current = word + " "
    return lines * (font.size + 6)

# ---------------- BACKGROUNDS (10) ----------------
def bg_solid(img, c): img.paste(c, [0, 0, WIDTH, HEIGHT])

def bg_gradient(img, c1, c2):
    d = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        r = int(c1[0] + (c2[0] - c1[0]) * y / HEIGHT)
        g = int(c1[1] + (c2[1] - c1[1]) * y / HEIGHT)
        b = int(c1[2] + (c2[2] - c1[2]) * y / HEIGHT)
        d.line([(0, y), (WIDTH, y)], fill=(r, g, b))

BACKGROUND_LIST = [
    lambda img, i: bg_gradient(img, (20,20,60), (60,20,80)),
    lambda img, i: bg_gradient(img, (0,0,0), (40,40,40)),
    lambda img, i: bg_gradient(img, (0,40,80), (0,10,30)),
    lambda img, i: bg_gradient(img, (60,0,0), (20,0,0)),
    lambda img, i: bg_gradient(img, (0,60,40), (0,20,20)),
    lambda img, i: bg_solid(img, (15,15,15)),
    lambda img, i: bg_solid(img, (30,0,60)),
    lambda img, i: bg_solid(img, (0,50,50)),
    lambda img, i: bg_solid(img, (70,30,0)),
    lambda img, i: bg_solid(img, (10,10,40)),
]

# ---------------- SAFE TEXT MOTIONS (5) ----------------
def motion_static(draw, text, font, frame):
    y = (HEIGHT - text_h) // 2
    draw_multiline_text(draw, text, font, 0, y, (255,255,255))

def motion_wave(draw, text, font, frame):
    offset = int(math.sin(frame / 3) * 12)
    y = max(PADDING, min(HEIGHT - text_h - PADDING, center_y + offset))
    draw_multiline_text(draw, text, font, 0, y, (255,215,0))

def motion_slide_up(draw, text, font, frame):
    y = HEIGHT - frame * 18
    y = max(PADDING, min(HEIGHT - text_h - PADDING, y))
    draw_multiline_text(draw, text, font, 0, y, (0,255,255))

def motion_slide_down(draw, text, font, frame):
    y = frame * 18 - text_h
    y = max(PADDING, min(HEIGHT - text_h - PADDING, y))
    draw_multiline_text(draw, text, font, 0, y, (200,255,200))

def motion_pulse(draw, text, font, frame):
    size = BASE_FONT_SIZE + int(math.sin(frame / 2) * 6)
    f = ImageFont.truetype(FONT_PATH, size)
    h = text_block_height(text, f, draw)
    y = (HEIGHT - h) // 2
    draw_multiline_text(draw, text, f, 0, y, (255,100,100))

MOTION_LIST = [
    motion_static,
    motion_wave,
    motion_slide_up,
    motion_slide_down,
    motion_pulse,
]

# ---------------- ROUTE ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    gifs = []

    if request.method == "POST":
        text = request.form["prompt"]
        font = ImageFont.truetype(FONT_PATH, BASE_FONT_SIZE)

        global text_h, center_y
        dummy = Image.new("RGB", (WIDTH, HEIGHT))
        d = ImageDraw.Draw(dummy)
        text_h = text_block_height(text, font, d)
        center_y = (HEIGHT - text_h) // 2

        style_count = 0

        for bg_id, bg in enumerate(BACKGROUND_LIST):
            for motion_id, motion in enumerate(MOTION_LIST):
                frames = []
                for i in range(25):
                    img = Image.new("RGB", (WIDTH, HEIGHT))
                    bg(img, i)
                    draw = ImageDraw.Draw(img)
                    motion(draw, text, font, i)
                    frames.append(img)

                name = f"Style {bg_id*5 + motion_id + 1}"
                fname = f"gif_{uuid.uuid4()}.gif"
                path = os.path.join(OUTPUT_FOLDER, fname)

                frames[0].save(
                    path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=120,
                    loop=0
                )

                gifs.append({"name": name, "path": path})
                style_count += 1

        # LIMIT TO 50 GIFs
        gifs = gifs[:50]

    return render_template("index.html", gifs=gifs)

if __name__ == "__main__":
    app.run(debug=True)
