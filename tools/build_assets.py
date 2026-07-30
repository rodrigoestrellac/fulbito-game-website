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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # p/ importar build_icono
HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(HERE)
RAIZ = os.path.abspath(os.path.join(WEB, ".."))
CAPS = os.path.join(RAIZ, "game-unity", "captures")
FONT_OSWALD = os.path.join(RAIZ, "fulbito", "api", "assets", "fonts", "Oswald-Bold.ttf")
# El mark de la pelota Teamgeist es el MISMO de la app (fulbito/src/assets):
# el sitio del juego hereda la identidad, no inventa una nueva.
# Ícono original: Javier Flowers / Noun Project — crédito en el footer del sitio.
# El mark de la pelota es un RENDER 3D del modelo que ya esta en el repo de la
# app: «Adidas Teamgeist Ball (Germany 2006)» de Armellino Raffaele (Sketchfab),
# CC-BY-4.0, con las texturas ya editadas — verificado: los PNG del GLB traen
# solo las formas de los paneles, sin logos ni estrellas. La atribucion CC-BY va
# en el footer del sitio.
#   Se rinde con three.js en tools/render3d/ (ver README § El mark de la pelota).
#   Aca solo se recorta y se escala el PNG con alfa que sale de ahi.
# ⚠️ Vuelto atras (2026-07-29): antes esto usaba una pelota generada por Gemini
#    (tools/gen_logo.py). Quedaba linda pero leia como pelota de VOLEY, y no era
#    la Teamgeist. El script queda por si sirve para otra cosa.
MARK_SRC = os.path.join(HERE, "pelota-fuente.png")

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
    # 30-jul-2026: estos cinco no tenian `_check_front.png` — los modelos se
    # integraron despues de que se dejaran de hacer esos renders a mano. Ahora
    # los genera `game-unity/assets-src/render_check_front.py`.
    ("dinho", "dinho"), ("depaul", "el-motorcito"), ("samu", "samu"),
    ("zlatan", "zlatan"), ("pupi", "el-pupi"),
]
# El sexto hueco, «Rober», SE QUEDA VACIO A PROPOSITO: su modelo es `chibi_rc3b`,
# el unico que tiene el escudo y el logo de adidas horneados en la textura. No se
# publica hasta que esa textura se limpie (ver README § Chequeo de marcas).
# La ventana del busto (cabeza + hombros, sin los brazos en T-pose) NO es fija:
# se MIDE sobre cada render. Antes era la constante BUST = (135, 55, 505, 425),
# calibrada a mano contra los renders viejos de 640x720 — y funcionaba mientras
# todos los retratos salieran del mismo Blender con el mismo encuadre. Dejo de
# funcionar el 30-jul-2026, cuando se agregaron los cinco que faltaban con
# `game-unity/assets-src/render_check_front.py`: ese script encuadra desde el
# bounding box del modelo, asi que el muneco entra mas grande y mas arriba, y la
# ventana fija le cortaba la frente.
# Estas tres fracciones REPRODUCEN la ventana vieja sobre los renders viejos
# (contenido en y 83..636 => lado 370, tope 55, centrado en x=320), asi que las
# 22 figuritas que ya estaban no se mueven un pixel.
BUST_LADO = 0.67    # lado del cuadrado, en alturas de muneco
BUST_TOPE = 0.05    # cuanto aire deja arriba de la cabeza, idem
BUST_OUT = 480

# Los tres retratos que van GRANDES en las tarjetas de jugadas firma. Se sacan
# de la misma fuente que el roster pero a 720 para que no queden blandos.
# ⚠️ Antes esta sección usaba las capturas m24n_* del sim de firmas: salen a
# 1280x720 SIN antialias (PocSetup.ShotWithCam) y se veían pixeladas. Los
# retratos son renders limpios y aguantan cualquier tamaño.
FIRMAS_BIG = [("haaland", "el-vikingo"), ("toro", "el-toro"), ("maldini", "il-capitano")]
FIRMA_OUT = 720

# ── Capturas ─────────────────────────────────────────────────────────────────
# ⚠️ NO USAR LAS `postfx_*`. Son el A/B de post-proceso de `PocSetup.SimPostFxAB`,
# que abre la escena en MODO EDITOR y renderiza sin jugar: ningun Animator tickea,
# el director no avanza y la fisica esta quieta. Las tres capturas que estuvieron
# publicadas hasta el 30-jul-2026 salian de ahi, y por eso se veian mal:
#   · todos los jugadores en T-pose,
#   · el arquero parado en vez de volando,
#   · nadie pateando,
#   · y la pelota en el punto del medio — la seccion "El gol" no tenia ni un gol.
# Encima son de 720p (el resto ya esta en 2560x1440), asi que ademas se veian
# blandas en pantalla retina.
# Las `web_*` salen de `PocSetup.SimWeb`, que corre el partido de verdad (mismo
# loop que SimMatch: tickea director + fisica + Animator uno por uno) y dispara
# atado a lo que pasa. Para regenerarlas:
#     Unity.exe -batchmode -quit -projectPath <FulbitoPenales> \
#               -executeMethod PocSetup.SimWeb
# y despues elegir a mano: salen ~40 y sirven tres.
#
# ⚠️ Al elegir: descartar los frames de SAQUE. Con el juego detenido el blend
# tree queda en Speed=0 y los jugadores aparecen con los brazos en cruz. Hay que
# quedarse con frames de pelota EN MOVIMIENTO.
SHOTS = [
    ("web_tv_08", "cancha-noche"),
    ("web_tiro_07", "muralla"),
    ("web_tiro_03", "gol"),
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
    im = Image.open(p).convert("RGB")
    im.crop(ventana_del_busto(im)).resize((lado, lado), Image.LANCZOS) \
      .save(out("assets", carpeta, slug + ".webp"), "WEBP", quality=84, method=6)


def ventana_del_busto(im):
    """Cuadrado cabeza+hombros, medido sobre el render.

    El fondo de estos renders es un gris plano, asi que el muneco es todo lo que
    se despegue de la esquina. Pero solo se mide el ALTO: horizontalmente se usa
    el centro del CUADRO, no el del bulto, porque los dos pipelines encuadran al
    muneco centrado y con los brazos en T el centro del bulto se corre para el
    lado del que lleva un prop — el martillo del Vikingo lo mueve 40 px, que es
    justo lo que le sacaria de cuadro media cara.
    """
    g = im.convert("L")
    fondo = g.getpixel((2, 2))
    mascara = g.point(lambda v: 255 if abs(v - fondo) > 12 else 0)
    caja = mascara.getbbox()
    if not caja:
        return (0, 0, im.width, im.height)
    _, arriba, _, abajo = caja
    alto = abajo - arriba
    lado = alto * BUST_LADO
    tope = arriba - alto * BUST_TOPE
    # clamp: si el muneco viene pegado al borde de arriba, PIL rellena lo que
    # falta con NEGRO y la figurita sale con una banda encima
    tope = max(0.0, min(tope, im.height - lado))
    cx = im.width / 2
    return (int(cx - lado / 2), int(tope), int(cx + lado / 2), int(tope + lado))


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
    corte = int(h * 0.22)          # donde termina la tribuna en esta camara
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
def mark(size):
    """El render con alfa, recortado a la pelota y centrado en un cuadrado."""
    if not os.path.exists(MARK_SRC):
        print("!! falta", MARK_SRC, "- rendealo con tools/render_pelota.md")
        sys.exit(1)
    im = Image.open(MARK_SRC).convert("RGBA")
    caja = im.split()[-1].getbbox()
    if caja:
        im = im.crop(caja)
    lado = max(im.size)
    lienzo = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    lienzo.alpha_composite(im, ((lado - im.width) // 2, (lado - im.height) // 2))
    return lienzo.resize((size, size), Image.LANCZOS)


def build_brand():
    # el mark suelto: lo usa el wordmark del hero como fallback de la pelota 3D,
    # y la pelotita de la firma del footer
    mark(512).save(out("assets", "brand", "pelota.webp"), "WEBP",
                   quality=90, method=6, lossless=False)
    # los iconos son otra cosa: el logo de la app + «The Game» manuscrito
    from build_icono import construir as construir_icono
    construir_icono(out)
    build_og()
    print("brand: pelota.webp + iconos (build_icono.py) + og-image")

def build_og():
    """1200x630 — el wordmark sobre la cancha de noche, oscurecida."""
    W, H = 1200, 630
    base = Image.open(os.path.join(CAPS, "web_tv_08.png")).convert("RGB")
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
