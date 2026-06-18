#!/usr/bin/env python3
"""
CRT Captcha Generator
=====================
Génère un captcha HTML/Canvas façon télévision cathodique à partir d'un texte.

Principe de sécurité :
- Le texte est rendu pixel par pixel sur N tranches par cycle (défaut: 4)
- Chaque tranche = pixels réels + bruit aléatoire de même intensité et même nombre
- Le bruit est régénéré aléatoirement à CHAQUE cycle côté navigateur
- La somme statistique des frames ne révèle jamais le texte (bruit non-stationnaire)
- Seule la persistance rétinienne humaine (~80ms) permet de lire l'image

Usage :
    python3 crt_captcha_generator.py "TEXTE" [options]

Exemples :
    python3 crt_captcha_generator.py "443"
    python3 crt_captcha_generator.py "AB12" --slices 6 --scale 8 --color "255,200,80"
    python3 crt_captcha_generator.py "Hello" --font /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
    python3 crt_captcha_generator.py "7K9X" --output mon_captcha.html
"""

import argparse
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont


# ─── Rendu du texte en pixels ────────────────────────────────────────────────

def text_to_pixels(text: str, font_path: str, font_size: int, padding: int = 4):
    """
    Rend le texte avec la police donnée et retourne :
    - la liste des coordonnées (x, y) des pixels sombres (le texte)
    - la largeur et hauteur de l'image source
    """
    font = ImageFont.truetype(font_path, font_size)

    # Mesure la bounding box du texte
    dummy = Image.new("L", (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0] + padding * 2
    h = bbox[3] - bbox[1] + padding * 2

    # Rendu sur fond blanc, texte noir
    img = Image.new("L", (w, h), color=255)
    draw = ImageDraw.Draw(img)
    draw.text((padding - bbox[0], padding - bbox[1]), text, font=font, fill=0)

    import numpy as np
    arr = np.array(img)
    pixels = []
    for py in range(h):
        for px in range(w):
            if arr[py, px] < 128:
                pixels.append([px, py])

    return pixels, w, h


# ─── Génération du HTML ───────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CRT Captcha</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #080808;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    font-family: 'Courier New', monospace;
    gap: 20px;
  }}
  .label {{
    font-size: 10px;
    letter-spacing: 5px;
    text-transform: uppercase;
    color: rgba({pr},{pg},{pb},0.3);
  }}
  canvas {{
    image-rendering: pixelated;
    border: 1px solid rgba({pr},{pg},{pb},0.08);
    box-shadow: 0 0 60px rgba({pr},{pg},{pb},0.04);
  }}
  .hint {{
    font-size: 10px;
    letter-spacing: 3px;
    color: rgba({pr},{pg},{pb},0.15);
  }}
</style>
</head>
<body>

<div class="label">Vérification humaine</div>
<canvas id="c"></canvas>
<div class="hint">Que voyez-vous ?</div>

<script>
// ── Paramètres ────────────────────────────────────────────────────────────────
const ORIG_W    = {orig_w};      // largeur source (px)
const ORIG_H    = {orig_h};      // hauteur source (px)
const SCALE     = {scale};       // agrandissement de chaque pixel
const N_SLICES  = {n_slices};    // tranches par cycle (plus = moins visible par frame)
const FRAME_MS  = {frame_ms};    // délai entre frames en ms (min GIF = 20ms)
const [PR,PG,PB] = [{pr},{pg},{pb}]; // couleur phosphore

// ── Pixels du texte (coordonnées source [x, y]) ───────────────────────────────
const DIGIT_PIXELS = {pixels_json};

// ── Setup canvas ─────────────────────────────────────────────────────────────
const W = ORIG_W * SCALE, H = ORIG_H * SCALE;
const canvas = document.getElementById('c');
canvas.width  = W;
canvas.height = H;
const ctx = canvas.getContext('2d');

// ── Découpe en tranches aléatoires ────────────────────────────────────────────
const N = DIGIT_PIXELS.length;
const perSlice = Math.ceil(N / N_SLICES);

function shuffle(arr) {{
  for (let i = arr.length - 1; i > 0; i--) {{
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }}
  return arr;
}}

let slices = [];
function rebuildSlices() {{
  // Nouvel ordre aléatoire à chaque cycle → bruit non-stationnaire
  const order = shuffle([...Array(N).keys()]);
  slices = [];
  for (let s = 0; s < N_SLICES; s++) {{
    slices.push(order.slice(s * perSlice, (s + 1) * perSlice).map(i => DIGIT_PIXELS[i]));
  }}
}}
rebuildSlices();

// ── Boucle d'animation ────────────────────────────────────────────────────────
let slice = 0;
let lastTime = 0;

function drawFrame(ts) {{
  if (ts - lastTime < FRAME_MS) {{ requestAnimationFrame(drawFrame); return; }}
  lastTime = ts;

  // Nouveau cycle → reconstruire les tranches avec un bruit différent
  if (slice === 0) rebuildSlices();

  const imgData = ctx.createImageData(W, H);
  const d = imgData.data;

  // Alpha = 255 partout (fond noir transparent par défaut)
  for (let i = 3; i < d.length; i += 4) d[i] = 255;

  const current = slices[slice];
  const noiseCount = current.length;

  // Pixels réels de cette tranche
  for (const [px, py] of current) {{
    const x0 = px * SCALE, y0 = py * SCALE;
    for (let dy = 0; dy < SCALE; dy++) {{
      for (let dx = 0; dx < SCALE; dx++) {{
        const idx = ((y0 + dy) * W + (x0 + dx)) * 4;
        d[idx]   = PR;
        d[idx+1] = PG;
        d[idx+2] = PB;
      }}
    }}
  }}

  // Bruit aléatoire — même nombre, même couleur, positions fraîches
  // → statistiquement indistinguable du signal sur une frame isolée
  for (let n = 0; n < noiseCount; n++) {{
    const nx = Math.floor(Math.random() * ORIG_W);
    const ny = Math.floor(Math.random() * ORIG_H);
    const x0 = nx * SCALE, y0 = ny * SCALE;
    const idx = (y0 * W + x0) * 4;
    if (d[idx] === 0) {{  // ne pas écraser un pixel réel
      for (let dy = 0; dy < SCALE; dy++) {{
        for (let dx = 0; dx < SCALE; dx++) {{
          const i = ((y0 + dy) * W + (x0 + dx)) * 4;
          d[i]   = PR;
          d[i+1] = PG;
          d[i+2] = PB;
        }}
      }}
    }}
  }}

  ctx.putImageData(imgData, 0, 0);

  slice = (slice + 1) % N_SLICES;
  requestAnimationFrame(drawFrame);
}}

requestAnimationFrame(drawFrame);
</script>
</body>
</html>
"""


def generate_captcha(
    text: str,
    output: str = None,
    font_path: str = None,
    font_size: int = 32,
    scale: int = 8,
    n_slices: int = 4,
    frame_ms: int = 20,
    color: str = "210,255,190",
    padding: int = 8,
):
    """
    Paramètres
    ----------
    text      : texte à afficher (ex: "4B7X")
    output    : chemin de sortie HTML (défaut: captcha_<text>.html)
    font_path : chemin vers une police .ttf/.otf (défaut: DejaVu Sans Mono)
    font_size : taille en points pour le rendu source
    scale     : facteur d'agrandissement de chaque pixel (ex: 8 → bloc 8×8px)
    n_slices  : nombre de tranches par cycle. Plus = moins lisible par frame
                mais cycle plus long. Recommandé : 4-6
    frame_ms  : délai entre frames (ms). Minimum navigateur ≈ 10-16ms
    color     : couleur phosphore "R,G,B" (ex: "210,255,190" = vert CRT)
                autres exemples: "255,200,80" = ambre, "200,220,255" = bleu
    padding   : marge en pixels autour du texte dans l'image source
    """

    # Police par défaut
    if font_path is None:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "/System/Library/Fonts/Courier.ttc",
            "C:/Windows/Fonts/cour.ttf",
        ]
        for c in candidates:
            if os.path.exists(c):
                font_path = c
                break
        if font_path is None:
            raise FileNotFoundError(
                "Aucune police par défaut trouvée. Spécifiez --font /chemin/vers/police.ttf"
            )

    # Rendu du texte
    pixels, orig_w, orig_h = text_to_pixels(text, font_path, font_size, padding)
    if not pixels:
        raise ValueError(f"Aucun pixel détecté pour le texte '{text}'. Vérifiez la police.")

    print(f"Texte      : '{text}'")
    print(f"Taille src : {orig_w}×{orig_h} px")
    print(f"Pixels     : {len(pixels)}")
    print(f"Canvas     : {orig_w * scale}×{orig_h * scale} px")
    print(f"Cycle      : {n_slices} tranches × {frame_ms}ms = {n_slices * frame_ms}ms")

    # Parse couleur
    parts = [int(x.strip()) for x in color.split(",")]
    if len(parts) != 3:
        raise ValueError("--color doit être au format 'R,G,B' ex: '210,255,190'")
    pr, pg, pb = parts

    # Génération HTML
    html = HTML_TEMPLATE.format(
        orig_w=orig_w,
        orig_h=orig_h,
        scale=scale,
        n_slices=n_slices,
        frame_ms=frame_ms,
        pr=pr, pg=pg, pb=pb,
        pixels_json=json.dumps(pixels),
    )

    # Fichier de sortie
    if output is None:
        safe = "".join(c if c.isalnum() else "_" for c in text)
        output = f"captcha_{safe}.html"

    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(output) / 1024
    print(f"Fichier    : {output} ({size_kb:.1f} KB)")
    return output


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Génère un captcha CRT cathodique en HTML/Canvas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("text", help="Texte à afficher dans le captcha")
    parser.add_argument("--output", "-o", default=None,
                        help="Fichier HTML de sortie (défaut: captcha_TEXTE.html)")
    parser.add_argument("--font", default=None,
                        help="Chemin vers une police .ttf/.otf")
    parser.add_argument("--font-size", type=int, default=32,
                        help="Taille de la police en points (défaut: 32)")
    parser.add_argument("--scale", type=int, default=8,
                        help="Agrandissement de chaque pixel (défaut: 8)")
    parser.add_argument("--slices", type=int, default=4,
                        help="Tranches par cycle (défaut: 4, min: 2, max: 8)")
    parser.add_argument("--frame-ms", type=int, default=20,
                        help="Délai entre frames en ms (défaut: 20)")
    parser.add_argument("--color", default="210,255,190",
                        help="Couleur phosphore R,G,B (défaut: '210,255,190' vert CRT)\n"
                             "Ambre: '255,200,80'  Blanc: '240,240,230'  Bleu: '160,200,255'")
    parser.add_argument("--padding", type=int, default=8,
                        help="Marge autour du texte en pixels source (défaut: 8)")

    args = parser.parse_args()

    try:
        generate_captcha(
            text=args.text,
            output=args.output,
            font_path=args.font,
            font_size=args.font_size,
            scale=args.scale,
            n_slices=args.slices,
            frame_ms=args.frame_ms,
            color=args.color,
            padding=args.padding,
        )
    except Exception as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
