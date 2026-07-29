#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera TODOS los assets binarios del sitio a partir de lo que ya existe en los
otros repos. Idempotente: se puede correr las veces que haga falta.

    python tools/build_assets.py

Produce:
    assets/brand/pelota.webp       el mark de la pelota, con alfa
    assets/brand/*.png|ico|jpg     favicons, apple-touch, og-image, ícono del instalador
    assets/roster/*.webp           retratos recortados a busto, 480x480
    assets/firmas/*.webp           los mismos retratos a 720x720, p/ las tarjetas grandes
    assets/img/*.webp              capturas del juego, máx 1600 de ancho

⚠️ CHEQUEO DE MARCAS: este script NO valida marcas registradas. Toda captura
   nueva que se agregue a SHOTS o ROSTER hay que mirarla con zoom ANTES
   (escudos de clubes, logos de sponsors). Ver README § Chequeo de marcas.
   El modelo `rc3b` del juego tiene el escudo del Real Madrid y el logo de
   adidas horneados en la textura: no entra ni en ROSTER ni en SHOTS.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(HERE)
RAIZ = os.path.abspath(os.path.join(WEB, ".."))
CAPS = os.path.join(RAIZ, "game-unity", "captures")
FONT_OSWALD = os.path.join(RAIZ, "fulbito", "api", "assets", "fonts", "Oswald-Bold.ttf")
# El mark de la pelota Teamgeist es el MISMO de la app (fulbito/src/assets):
# el sitio del juego hereda la identidad, no inventa una nueva.
# Ícono original: Javier Flowers / Noun Project — crédito en el footer del sitio.
# El mark de la pelota lo genero Gemini (tools/gen_logo.py, variante
# "1-pelota-arcade", modelo gemini-3-pro-image) sobre un fondo magenta plano que
# este script recorta. Es la pelota de Fulbito con el contorno grueso y el peso de
# un emblema de arcade, para que pegue con el relieve del wordmark.
# El mark de linea de la app (fulbito/src/assets/teamgeist.png) quedo como
# alternativa: cambiar MARK_SRC y volver a correr el script.
MARK_SRC = os.path.join(HERE, "pelota-fuente.png")
MARK_CHROMA = True     # el fuente viene con fondo magenta a recortar

ORO = (201, 169, 78)
NOCHE = (13, 27, 15)
CAL = (240, 237, 228)

# ── Retratos del roster ──────────────────────────────────────────────────────
# (archivo en captures/, slug de salida). El slug es SIEMPRE el apodo in-game:
# nunca un apellido real, ni acá ni en el alt-text (ver README § Chequeo).
# El árbitro (pierluigi_check_front.png) queda AFUERA a propósito: es la
# caricatura más reconocible del juego y no aporta a la grilla.
ROSTER = [
    ("pulga", "la-pulga"), ("haaland", "el-vikingo"), ("maldini", "il-capitano"),
    ("dibu", "dibu"), ("neuer", "manuelito"), ("zizou", "zizou"),
    ("beckham", "david"), ("neymarfix", "ney"), ("riquelme", "el-torero"),
    ("diegote", "diegote"), ("dienton", "dienton"), ("cuti", "cuti"),
    ("licha", "the-butcher"), ("toro", "el-toro"), ("iniesta", "el-cerebro"),
    ("puyol", "tarzan"), ("r9", "fenomeno"), ("dutch", "el-holandes"),
    ("batigol", "batigol"), ("bruja", "la-bruja"), ("lucky", "lucky"),
    ("arana", "la-arana"),
]
# ventana del busto dentro del render 640x720 (cabeza + hombros, sin los brazos
# en T-pose, que arrancan cerca de y=430)
BUST = (135, 55, 505, 425)
BUST_OUT = 480

# Los tres retratos que van GRANDES en las tarjetas de jugadas firma. Se sacan
# de la misma fuente que el roster pero a 720 para que no queden blandos.
# ⚠️ Antes esta sección usaba las capturas m24n_* del sim de firmas: salen a
# 1280x720 SIN antialias (PocSetup.ShotWithCam) y se veían pixeladas. Los
# retratos son renders limpios y aguantan cualquier tamaño.
FIRMAS_BIG = [("haaland", "el-vikingo"), ("toro", "el-toro"), ("maldini", "il-capitano")]
FIRMA_OUT = 720

# ── Capturas ─────────────────────────────────────────────────────────────────
SHOTS = [
    ("postfx_tv_ON", "cancha-noche"),
    ("postfx_cerca_ON", "saque-del-medio"),
    ("postfx_gol_ON", "gol"),
    ("m15_menu_bg", "menu"),
    ("m3_save_5", "atajada"),
    ("m7_match_mid", "partido"),
]
SHOT_MAX_W = 1600


def out(*parts):
    p = os.path.join(WEB, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def recortar(src_id, slug, carpeta, lado):
    p = os.path.join(CAPS, src_id + "_check_front.png")
    if not os.path.exists(p):
        print("  FALTA", p)
        return
    im = Image.open(p).convert("RGB").crop(BUST).resize((lado, lado), Image.LANCZOS)
    im.save(out("assets", carpeta, slug + ".webp"), "WEBP", quality=84, method=6)


def build_roster():
    for src, slug in ROSTER:
        recortar(src, slug, "roster", BUST_OUT)
    for src, slug in FIRMAS_BIG:
        recortar(src, slug, "firmas", FIRMA_OUT)
    print("roster: %d retratos + %d grandes" % (len(ROSTER), len(FIRMAS_BIG)))


def desenfoque_tribuna(im):
    """La tribuna es una textura de sprites de baja resolucion: estirada a todo
    el hero se lee como bloques. Un desenfoque GRADUADO (fuerte arriba, nulo a la
    altura del cesped) la convierte en profundidad de campo — que es lo que haria
    una camara de verdad — y deja la cancha nitida."""
    borroso = im.filter(ImageFilter.GaussianBlur(3.2))
    h = im.height
    corte = int(h * 0.30)          # donde termina la tribuna en esta camara
    mascara = Image.new("L", (1, h))
    for y in range(h):
        t = min(1.0, max(0.0, (corte - y) / (corte * 0.55)))
        mascara.putpixel((0, y), int(255 * t))
    return Image.composite(borroso, im, mascara.resize(im.size))


def build_shots():
    for src, slug in SHOTS:
        p = os.path.join(CAPS, src + ".png")
        if not os.path.exists(p):
            print("  FALTA", p)
            continue
        im = Image.open(p).convert("RGB")
        if slug == "cancha-noche":
            im = desenfoque_tribuna(im)
        if im.width > SHOT_MAX_W:
            im = im.resize((SHOT_MAX_W, round(im.height * SHOT_MAX_W / im.width)),
                           Image.LANCZOS)
        im.save(out("assets", "img", slug + ".webp"), "WEBP", quality=80, method=6)
    print("capturas:", len(SHOTS))


# ── El mark de la pelota ─────────────────────────────────────────────────────
def mark(size, color=ORO):
    """El Teamgeist de la app, recoloreado y con alfa. La fuente es line-art
    negro sobre blanco: la tinta pasa a ser el alfa, así queda con los bordes
    suaves y sirve sobre cualquier fondo."""
    if not os.path.exists(MARK_SRC):
        print("!! falta", MARK_SRC)
        sys.exit(1)
    src = Image.open(MARK_SRC)
    if src.mode in ("RGBA", "LA"):
        # si ya viene con alfa, el blanco de atrás no existe: uso la luminancia
        # del compuesto sobre blanco
        fondo = Image.new("RGB", src.size, (255, 255, 255))
        fondo.paste(src, (0, 0), src.getchannel("A"))
        src = fondo
    if MARK_CHROMA:
        return _sacar_croma(src.convert("RGB"), size)
    tinta = src.convert("L").point(lambda v: 255 - v)          # negro -> opaco
    # el line-art es fino: al lado de un Oswald 700 enorme se ve anemico
    tinta = tinta.filter(ImageFilter.MaxFilter(7))
    im = Image.new("RGBA", src.size, color + (0,))
    im.putalpha(tinta)
    return im.resize((size, size), Image.LANCZOS)


def _sacar_croma(src, size, tol=(52, 128)):
    """Recorta el fondo plano del PNG que devuelve Gemini. La clave se toma del
    borde de la imagen (no se hardcodea el magenta: el modelo no clava el hex).
    Despues se ERODA el alfa un pixel, que es lo que mata el fleco de color que
    queda en el antialias del contorno."""
    import collections
    a = src.load()
    W, H = src.size
    borde = [a[x, 0] for x in range(0, W, 4)] + [a[x, H - 1] for x in range(0, W, 4)]           + [a[0, y] for y in range(0, H, 4)] + [a[W - 1, y] for y in range(0, H, 4)]
    clave = collections.Counter(borde).most_common(1)[0][0]

    dist = Image.new("L", src.size)
    dp = dist.load()
    t0, t1 = tol
    for y in range(H):
        for x in range(W):
            r, g, b = a[x, y]
            d = ((r - clave[0]) ** 2 + (g - clave[1]) ** 2 + (b - clave[2]) ** 2) ** 0.5
            dp[x, y] = 0 if d <= t0 else (255 if d >= t1 else int(255 * (d - t0) / (t1 - t0)))
    dist = dist.filter(ImageFilter.MinFilter(3))

    im = src.convert("RGBA")
    im.putalpha(dist)
    caja = dist.point(lambda v: 255 if v > 24 else 0).getbbox()
    if caja:
        im = im.crop(caja)
    lado = max(im.size)
    lienzo = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    lienzo.alpha_composite(im, ((lado - im.width) // 2, (lado - im.height) // 2))
    return lienzo.resize((size, size), Image.LANCZOS)


def icon_tile(size, radio=0.22, ss=4):
    """Ícono de app: baldosa verde noche + borde dorado + el mark."""
    S = size * ss
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * radio), fill=NOCHE)
    if radio:
        b = int(S * .02)
        d.rounded_rectangle([b, b, S - 1 - b, S - 1 - b], radius=int(S * radio * .92),
                            outline=ORO, width=max(1, int(S * .022)))
    m = mark(int(S * 0.70))
    im.alpha_composite(m, ((S - m.width) // 2, (S - m.height) // 2))
    return im.resize((size, size), Image.LANCZOS)


FAVICON_SVG_TPL = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#0D1B0F"/>
  <rect x="1.5" y="1.5" width="61" height="61" rx="12.5" fill="none" stroke="#C9A94E" stroke-width="2"/>
  <image x="10" y="10" width="44" height="44" href="data:image/png;base64,%s"/>
</svg>
"""


def build_brand():
    import base64
    from io import BytesIO

    m = mark(512)
    m.save(out("assets", "brand", "pelota.webp"), "WEBP", quality=90, method=6, lossless=False)

    # favicon SVG: el mark embebido en PNG dentro del SVG. Es un archivo solo,
    # sin dependencias, y el navegador lo escala sin perder nitidez en la baldosa.
    buf = BytesIO()
    mark(128).save(buf, "PNG", optimize=True)
    open(out("assets", "brand", "favicon.svg"), "w", encoding="utf-8").write(
        FAVICON_SVG_TPL % base64.b64encode(buf.getvalue()).decode())

    icon_tile(32).save(out("assets", "brand", "favicon-32.png"))
    icon_tile(180, radio=0.0).save(out("assets", "brand", "apple-touch-180.png"))
    icon_tile(256).save(out("assets", "brand", "fulbito.ico"),
                        sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    build_og()
    print("brand: pelota.webp, favicon.svg, favicon-32, apple-touch-180, fulbito.ico, og-image")


def build_og():
    """1200x630 — el wordmark sobre la cancha de noche, oscurecida."""
    W, H = 1200, 630
    base = Image.open(os.path.join(CAPS, "postfx_tv_ON.png")).convert("RGB")
    s = max(W / base.width, H / base.height)
    base = base.resize((round(base.width * s), round(base.height * s)), Image.LANCZOS)
    x = (base.width - W) // 2
    y = int((base.height - H) * 0.35)
    im = base.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(1.2))

    veil = Image.new("L", (1, H))
    for i in range(H):
        veil.putpixel((0, i), int(150 + 95 * (i / (H - 1)) ** 1.6))
    im = Image.composite(Image.new("RGB", (W, H), NOCHE), im, veil.resize((W, H)))
    im = im.convert("RGBA")

    d = ImageDraw.Draw(im)
    f_big = ImageFont.truetype(FONT_OSWALD, 148)
    f_sub = ImageFont.truetype(FONT_OSWALD, 44)
    f_tag = ImageFont.truetype(FONT_OSWALD, 34)

    def tracked(xy, text, font, fill, track, sombra=None):
        cx, cy = xy
        for ch in text:
            if sombra:
                d.text((cx + sombra[0], cy + sombra[1]), ch, font=font, fill=sombra[2])
            d.text((cx, cy), ch, font=font, fill=fill)
            cx += d.textlength(ch, font=font) + track
        return cx - track

    left, top = 82, 250
    # el relieve dorado es el mismo gesto que el wordmark del sitio (CSS): la
    # letra crema con una sombra dura dorada abajo a la derecha
    end = tracked((left, top), "FULBITO", f_big, CAL, 9, sombra=(6, 7, ORO))
    m = mark(112)
    im.alpha_composite(m, (int(end) + 30, top + 34))

    d.line([(left, top + 196), (left + 108, top + 196)], fill=ORO, width=5)
    tracked((left + 128, top + 176), "THE GAME", f_sub, ORO, 13)
    tracked((left, top + 250), "FÚTBOL ARCADE 7v7 · GRATIS · WINDOWS Y MAC", f_tag,
            (168, 178, 165), 2.5)

    im.convert("RGB").save(out("assets", "brand", "og-image.jpg"), "JPEG",
                           quality=86, optimize=True)


if __name__ == "__main__":
    build_brand()
    build_roster()
    build_shots()
    print("listo")
