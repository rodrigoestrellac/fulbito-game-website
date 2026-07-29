#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera propuestas de logo con la API de Gemini (la misma clave que usa la app
para los merges de cracks: GOOGLE_AI_API_KEY en fulbito/.env).

    python tools/gen_logo.py            # las 4 variantes, modelo pro
    python tools/gen_logo.py --flash    # más barato, para iterar prompts
    python tools/gen_logo.py --solo 2   # una sola variante

Las imágenes salen a tools/logo_candidatos/. NO se commitean: son material de
trabajo. La que se elija se limpia y va a assets/brand/.

⚠️ CUESTA PLATA: gemini-3-pro-image ~USD 0.15 por imagen, gemini-2.5-flash-image
   ~USD 0.04. Cuatro variantes en pro = ~USD 0.60.

⚠️ NADA DE MARCAS: los prompts describen el patrón de paneles de la pelota
   (formas curvas tipo hélice) SIN nombrar ninguna marca. No pedir "adidas",
   "Teamgeist", ni un club — el sitio es público y ese es justo el riesgo que
   estamos evitando (ver README § Chequeo de marcas).
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
WEB = AQUI.parent
RAIZ = WEB.parent
SALIDA = AQUI / "logo_candidatos"

MODELO_PRO = "gemini-3-pro-image"
MODELO_FLASH = "gemini-2.5-flash-image"

# La paleta va EXPLÍCITA en cada prompt: es la misma del juego y de la app, y sin
# los hex el modelo se va a un dorado naranja.
PALETA = ("Strict palette, no other colors: cream #F0EDE4, gold #C9A94E, "
          "light gold #E8D48B, deep night green #0D1B0F.")
# Fondo plano y saturado para poder recortarlo después sin halo.
FONDO = ("The background must be one completely flat, uniform, solid pure magenta "
         "#FF00FF, edge to edge, with no gradient, no texture, no vignette and no "
         "shadow touching it.")

VARIANTES = [
    ("1-pelota-arcade",
     "A single soccer ball emblem for a video game logo, seen straight on. "
     "The ball is built from six curved propeller-shaped panels that meet at the "
     "poles, drawn as bold flat shapes. Chunky flat vector illustration with a "
     "thick dark outline, a hard-edged highlight on the upper left and no "
     "gradients — the look of a 1990s arcade cabinet emblem. "
     f"{PALETA} No text, no letters, no ground shadow. {FONDO}"),

    ("2-pelota-relieve",
     "A single soccer ball emblem for a video game logo, seen straight on, built "
     "from six curved propeller-shaped panels. Solid gold ball with the panel "
     "seams cut out in deep night green. It has a hard offset extrusion below and "
     "to the right, like an extruded arcade logo, giving it depth with flat color "
     "only — no soft shadows, no gradients, no bevel gloss. "
     f"{PALETA} No text, no letters. {FONDO}"),

    ("3-lockup",
     "A video game logo lockup. The word FULBITO in a very bold condensed "
     "uppercase sans-serif, wide letter spacing, cream colored, with a hard flat "
     "gold extrusion offset down-right behind the letters — an arcade title "
     "treatment, flat colors only, no glow and no gradient. To the right of the "
     "word sits a soccer ball emblem built from six curved propeller-shaped "
     "panels, in gold. Under the word, a thin gold rule followed by the words THE "
     "GAME in small widely-spaced gold uppercase letters. "
     f"Spell it exactly FULBITO and THE GAME. {PALETA} {FONDO}"),

    # ── Ronda 2 (Rodrigo: "la pelota no es la teamgeist, es una pelota vintage").
    #    La 1 quedo linda pero con paneles curvos anchos: lee medio a pelota de
    #    voley. Estas tres van a lo seguro sobre "esto es una pelota de futbol".
    ("5-clasica",
     "A single classic soccer ball emblem for a video game logo, seen straight on: "
     "the traditional pattern of regular pentagons and hexagons. Bold flat vector "
     "illustration with a thick dark outline around the ball and around every panel, "
     "flat colors only, no gradients and no gloss — the weight of an arcade cabinet "
     "emblem. The pentagons are deep night green, the hexagons alternate cream and "
     f"gold. {PALETA} No text, no letters, no ground shadow. {FONDO}"),

    ("6-turbina",
     "A single soccer ball emblem for a video game logo, seen straight on. Its "
     "surface is made of interlocking curved panels of two kinds: peanut-shaped "
     "panels and three-armed turbine-shaped panels, fitted together with no straight "
     "seams anywhere — a modern thermally-bonded ball. Bold flat vector "
     "illustration, thick dark outline, flat colors only, no gradients, no gloss. "
     f"Cream ball, seams and panel outlines in deep night green, gold accents. {PALETA} "
     f"No text, no letters, no ground shadow. {FONDO}"),

    ("7-vintage",
     "A single vintage 1950s leather soccer ball emblem for a video game logo, seen "
     "straight on: eighteen long rectangular leather panels in six groups of three, "
     "with visible stitching and a laced opening. Bold flat vector illustration with "
     "a thick dark outline, flat colors only, no gradients and no photographic "
     "texture — an arcade emblem, not a photo. Warm gold and cream leather, seams in "
     f"deep night green. {PALETA} No text, no letters, no ground shadow. {FONDO}"),

    ("4-escudo",
     "A football crest emblem for a video game logo: a simple shield shape "
     "outlined in gold, containing a soccer ball built from six curved "
     "propeller-shaped panels, with two crossed floodlight masts behind it. Flat "
     "vector illustration, bold thick outlines, flat colors only, no gradients, no "
     "gloss, no realistic lighting. Invented emblem — it must not resemble any "
     f"real club, league or company badge, and must contain no text. {PALETA} {FONDO}"),
]


def leer_clave():
    """Saca GOOGLE_AI_API_KEY del .env de la app. No la imprime nunca."""
    env = RAIZ / "fulbito" / ".env"
    if not env.exists():
        sys.exit("No encuentro %s" % env)
    for linea in env.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r'\s*(?:export\s+)?GOOGLE_AI_API_KEY\s*=\s*(.+)\s*$', linea)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    sys.exit("GOOGLE_AI_API_KEY no está en %s" % env)


def generar(clave, modelo, prompt):
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           "%s:generateContent" % modelo)
    cuerpo = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"],
                             "imageConfig": {"aspectRatio": "1:1"}},
    }).encode()
    pedido = urllib.request.Request(
        url, data=cuerpo,
        headers={"Content-Type": "application/json", "x-goog-api-key": clave})
    try:
        with urllib.request.urlopen(pedido, timeout=180) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        # el detalle del error de la API sirve; la clave no aparece en el body
        sys.exit("HTTP %s: %s" % (e.code, e.read().decode("utf-8", "replace")[:600]))

    for cand in data.get("candidates", []):
        for parte in cand.get("content", {}).get("parts", []):
            blob = parte.get("inlineData") or parte.get("inline_data")
            if blob and blob.get("data"):
                return base64.b64decode(blob["data"])
    sys.exit("La respuesta no trajo imagen: %s" % json.dumps(data)[:600])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flash", action="store_true", help="modelo barato")
    ap.add_argument("--solo", type=int, help="generar sólo esa variante (1-4)")
    args = ap.parse_args()

    modelo = MODELO_FLASH if args.flash else MODELO_PRO
    clave = leer_clave()
    SALIDA.mkdir(exist_ok=True)

    tareas = VARIANTES
    if args.solo:
        tareas = [VARIANTES[args.solo - 1]]

    for nombre, prompt in tareas:
        png = generar(clave, modelo, prompt)
        destino = SALIDA / ("%s.png" % nombre)
        destino.write_bytes(png)
        print("  %-20s %6d KB  %s" % (nombre, len(png) // 1024, destino))

    print("\n%d imagen(es) con %s. Costo aprox: USD %.2f"
          % (len(tareas), modelo, len(tareas) * (0.04 if args.flash else 0.15)))


if __name__ == "__main__":
    main()
