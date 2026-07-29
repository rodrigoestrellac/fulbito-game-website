#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arma el ícono del sitio y del instalador: el MISMO logo de la app Fulbito
(baldosa verde + anillo dorado + Teamgeist blanca) con un «The Game» manuscrito
abajo, en la misma letra que la firma del footer (Caveat).

    python tools/build_icono.py

Sale a assets/brand/: favicon.svg, favicon-32.png, apple-touch-180.png y
fulbito.ico. Lo llama build_assets.py, no hace falta correrlo aparte.

⚠️ ARTE DISTINTA POR TAMAÑO. A 16 y 32 px un texto manuscrito es una mancha:
   no se lee, y encima le roba lugar a la pelota, que es lo único que a ese
   tamaño identifica algo. Entonces:
       16 / 32 / 48 px  -> el logo de la app SOLO (sin texto)
       180 / 256 px     -> el logo + «The Game»
   Por eso el .ico se escribe a mano (PIL sólo sabe reescalar UNA imagen a
   todos los tamaños, no meter arte distinta en cada uno).
"""
import os
import struct
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(HERE)
RAIZ = os.path.abspath(os.path.join(WEB, ".."))

LOGO_APP = os.path.join(RAIZ, "fulbito", "src", "assets", "icons", "icon-512.webp")
FONT_CAVEAT = os.path.join(HERE, "Caveat-Bold.ttf")

NOCHE = (13, 27, 15, 255)
ORO = (201, 169, 78, 255)
CAL = (240, 237, 228, 255)


def contenido_del_logo():
    """Recorta el interior del ícono de la app (anillo dorado + pelota), sin su
    propia baldosa ni su borde: la baldosa la vuelve a dibujar este script, y si
    no se sacara quedarían dos bordes redondeados uno adentro del otro."""
    im = Image.open(LOGO_APP).convert("RGBA")
    # el anillo dorado es lo más saturado hacia el dorado: busco su extensión
    px = im.load()
    W, H = im.size
    x0, y0, x1, y1 = W, H, 0, 0
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            r, g, b, a = px[x, y]
            if a < 40:
                continue
            # SÓLO el dorado del anillo. Ojo: no sumar "casi blanco" para pescar
            # la pelota — el borde crema de la baldosa de la app también es casi
            # blanco, y entonces el recorte se lo lleva y quedan dos bordes
            # redondeados, uno adentro del otro. El anillo ya encierra la pelota.
            if r > 150 and g > 110 and b < 130 and (r - b) > 55:
                if x < x0: x0 = x
                if y < y0: y0 = y
                if x > x1: x1 = x
                if y > y1: y1 = y
    if x0 >= x1:
        return im
    disco = im.crop((x0, y0, x1 + 1, y1 + 1))

    # Enmascarado CIRCULAR: el recorte es un cuadrado de fondo verde alrededor de
    # un anillo redondo, y ese verde no es exactamente el mismo de la baldosa que
    # dibuja este script -> se veia un parche cuadrado. El anillo es un circulo,
    # asi que la mascara es exacta, no una aproximacion. Se dibuja a 4x y se baja
    # para que el borde quede suave.
    L = max(disco.size)
    disco = disco.resize((L, L), Image.LANCZOS)
    m = Image.new('L', (L * 4, L * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, L * 4 - 1, L * 4 - 1], fill=255)
    m = m.resize((L, L), Image.LANCZOS)
    salida = Image.new('RGBA', (L, L), (0, 0, 0, 0))
    salida.paste(disco, (0, 0), m)
    return salida


def baldosa(S, radio=0.22):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = int(S * radio)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=r, fill=NOCHE)
    # hairline crema, como la del ícono de la app
    b = max(1, int(S * .018))
    d.rounded_rectangle([b, b, S - 1 - b, S - 1 - b], radius=int(r * .9),
                        outline=CAL, width=max(1, int(S * .012)))
    return im


def icono(size, con_texto, radio=0.22, ss=3):
    """`con_texto` decide si entra el «The Game» — ver la nota de arriba."""
    S = size * ss
    im = baldosa(S, radio)
    logo = contenido_del_logo()

    if con_texto:
        # la pelota ocupa la parte de arriba y el texto la banda de abajo
        caja = int(S * 0.60)
        arriba = int(S * 0.115)
        texto_y = int(S * 0.735)
    else:
        caja = int(S * 0.74)
        arriba = (S - caja) // 2
        texto_y = None

    l = logo.copy()
    l.thumbnail((caja, caja), Image.LANCZOS)
    im.alpha_composite(l, ((S - l.width) // 2, arriba))

    if texto_y is not None:
        d = ImageDraw.Draw(im)
        f = ImageFont.truetype(FONT_CAVEAT, int(S * 0.20))
        try:
            f.set_variation_by_name("Bold")
        except Exception:
            pass
        t = "The Game"
        ancho = d.textlength(t, font=f)
        # si no entra, lo achico hasta que entre (el ancho de Caveat varía con
        # el peso de la variable font, no lo doy por sentado)
        limite = S * 0.80
        if ancho > limite:
            f = ImageFont.truetype(FONT_CAVEAT, int(S * 0.20 * limite / ancho))
            try:
                f.set_variation_by_name("Bold")
            except Exception:
                pass
            ancho = d.textlength(t, font=f)
        d.text(((S - ancho) / 2, texto_y), t, font=f, fill=ORO)

    return im.resize((size, size), Image.LANCZOS)


def escribir_ico(destino, piezas):
    """ICO a mano: PIL sólo reescala una imagen a todos los tamaños, y acá cada
    tamaño lleva arte distinta. Formato: cabecera de 6 bytes + una entrada de 16
    por imagen + los PNG concatenados."""
    blobs = []
    for im in piezas:
        b = BytesIO()
        im.save(b, "PNG", optimize=True)
        blobs.append(b.getvalue())

    cab = struct.pack("<HHH", 0, 1, len(piezas))
    offset = 6 + 16 * len(piezas)
    entradas = b""
    for im, blob in zip(piezas, blobs):
        w = 0 if im.width >= 256 else im.width
        h = 0 if im.height >= 256 else im.height
        entradas += struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(blob), offset)
        offset += len(blob)

    with open(destino, "wb") as f:
        f.write(cab + entradas + b"".join(blobs))


def svg_favicon(im32):
    import base64
    b = BytesIO()
    im32.save(b, "PNG", optimize=True)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">\n'
            '  <image width="64" height="64" image-rendering="auto" '
            'href="data:image/png;base64,%s"/>\n</svg>\n'
            % base64.b64encode(b.getvalue()).decode())


def construir(out):
    chico = icono(128, con_texto=False)          # base nítida p/ los chicos
    grande = icono(256, con_texto=True)

    icono(32, con_texto=False).save(out("assets", "brand", "favicon-32.png"))
    icono(180, con_texto=True, radio=0.0).save(out("assets", "brand", "apple-touch-180.png"))
    open(out("assets", "brand", "favicon.svg"), "w", encoding="utf-8").write(
        svg_favicon(chico))

    escribir_ico(out("assets", "brand", "fulbito.ico"), [
        icono(16, con_texto=False),
        icono(32, con_texto=False),
        icono(48, con_texto=False),
        grande,
    ])
    return grande


if __name__ == "__main__":
    def out(*p):
        d = os.path.join(WEB, *p)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        return d
    g = construir(out)
    g.save(os.path.join(HERE, "_preview_icono.png"))
    print("ícono listo — preview en tools/_preview_icono.png")
