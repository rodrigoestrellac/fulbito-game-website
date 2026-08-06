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
   nueva que se agregue a SHOTS o al álbum hay que mirarla con zoom ANTES
   (escudos de clubes, logos de sponsors). Ver README § Chequeo de marcas.
   El caso testigo fue `rc3b`, que tenía el escudo del Real Madrid y el logo de
   adidas horneados en la textura y estuvo fuera del álbum hasta que se
   re-texturizó (30-jul-2026); hoy sí entra.
   El álbum ya NO se lista a mano: sale del juego, pero cada id tiene que estar
   en `APROBADOS` — esa lista ES el chequeo de marcas. Ver `auditar_album()`.
"""
import json
import os
import re
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
# ⚠️⚠️ EL ROSTER YA NO SE ESCRIBE A MANO (3-ago-2026). Era una lista fija y se
# DESINCRONIZO del juego sin que nadie lo notara: al revisarlo, el album tenia 28
# jugadores y el juego 50 — faltaban los DOCE de M92 (desde el 1-ago) y los DIEZ de
# M94. Es la misma clase de bug que `BluePoolIds` vs. los cuerpos de la escena
# (game-unity, M92g): dos listas que tienen que decir lo mismo y nada las compara.
# Y falla EN SILENCIO, que es lo peor: un album incompleto se ve igual de bien que
# uno completo.
#
# Ahora los candidatos SALEN DEL JUEGO (`MatchTuning.BluePoolIds` + `GkPoolIds`) y el
# slug se DERIVA de `NombreDe`. Sumar un jugador al juego lo pone en la lista solo.
#
# ⚠️ PERO NO SE PUBLICA SOLO, Y ESO ES A PROPOSITO. El README manda mirar cada
# retrato con zoom antes de publicarlo (escudos de clubes, logos de sponsors; el caso
# testigo es `rc3b`). Con un album 100% automatico, un modelo nuevo con el escudo del
# Real Madrid se publicaria sin que nadie lo haya visto: cambiariamos un bug
# silencioso (falta gente) por otro peor (se publica lo que no se reviso).
# Por eso son DOS piezas: la lista se deriva, pero cada id tiene que estar en
# `APROBADOS`, que es la firma de "yo mire este retrato". Un id sin aprobar hace que
# el script AVISE FUERTE y termine con error, en vez de faltar calladito.
APROBADOS = {
    # revisados hasta el 30-jul-2026
    "pulga", "haaland", "maldini", "dibu", "neuer", "zizou", "beckham", "neymar",
    "riquelme", "diegote", "dienton", "cuti", "licha", "toro", "iniesta", "puyol",
    "r9", "dutch", "bati", "bruja", "lucky", "arana", "dinho", "depaul", "samu",
    "zlatan", "pupi",
    # `rc3b` tenia el escudo del Real Madrid y el logo de adidas horneados en la
    # textura y estuvo fuera del album hasta que Rodrigo la re-texturizo (30-jul).
    "rc3",
    # 3-ago-2026 — los DOCE de M92 y los DIEZ de M94. Chequeo de marcas hecho sobre
    # los `_check_front.png` con zoom al torso: los 22 llevan el kit magenta liso de
    # Meshy, sin escudo ni sponsor. (El unico que asustaba era el Faraon por las
    # rayas azul/oro, pero es el NEMES —el tocado de faraon— y no una camiseta.)
    "ruud", "lea", "faraon", "nico", "carlitos", "cholo", "arjen", "pepito",
    "sergio", "kuni", "cr007", "tortuga",
    "ciudadano", "baby", "vini", "franco", "tommy", "lami", "pavelito", "fabio",
    "gigi", "checo",
    # 5-ago-2026 — los DOS de M111. Chequeo de marcas con zoom al torso sobre
    # `iceman_check_front.png` y `general_check_front.png`: kit magenta liso de
    # Meshy, pantalon blanco, sin escudo ni sponsor en ninguno de los dos.
    "iceman", "general",
    # 5-ago-2026 (tarde) — FIDEO (M117, LOS TALLARINES). Mismo chequeo sobre
    # `fideo_check_front.png`: kit magenta liso, pantalon blanco, limpio.
    "fideo",
}

# el archivo de captura cuando NO se llama como el id del juego
ALIAS_CAPTURA = {"bati": "batigol", "rc3": "rc3b", "neymar": "neymarfix"}

# ⚠️ SLUGS YA PUBLICADOS: son URLs vivas. El slug se deriva de `NombreDe`, asi que un
# cambio de apodo en el juego renombraria el archivo y romperia enlaces (y el SEO) sin
# que nadie lo pida. Estos quedan CONGELADOS: si la derivacion deja de coincidir, el
# script avisa — renombrar una URL publicada tiene que ser una decision, no un efecto
# secundario de tocar un nombre en el juego.
SLUGS_CONGELADOS = {
    "pulga": "la-pulga", "haaland": "el-vikingo", "maldini": "il-capitano",
    "dibu": "dibu", "neuer": "manuelito", "zizou": "zizou", "beckham": "david",
    "neymar": "ney", "riquelme": "el-torero", "diegote": "diegote",
    "dienton": "dienton", "cuti": "cuti", "licha": "the-butcher", "toro": "el-toro",
    "iniesta": "el-cerebro", "puyol": "tarzan", "r9": "fenomeno",
    "dutch": "el-holandes", "bati": "batigol", "bruja": "la-bruja", "lucky": "lucky",
    "arana": "la-arana", "dinho": "dinho", "depaul": "el-motorcito", "samu": "samu",
    "zlatan": "zlatan", "pupi": "el-pupi", "rc3": "rober",
}

MATCHTUNING = os.path.join(RAIZ, "game-unity", "FulbitoPenales", "Assets",
                           "Scripts", "MatchTuning.cs")
MATCHDIRECTOR = os.path.join(RAIZ, "game-unity", "FulbitoPenales", "Assets",
                             "Scripts", "MatchDirector.cs")


def _sin_acentos(s):
    return s.translate(str.maketrans("ÁÉÍÓÚÜÑáéíóúüñ", "AEIOUUNaeiouun"))


def slug_de(nombre):
    """`EL VIKINGO` -> `el-vikingo`. Reproduce EXACTO los 28 slugs ya publicados."""
    s = _sin_acentos(nombre).lower().strip()
    return "-".join(p for p in s.replace("/", " ").split(" ") if p)


def _lista_cs(txt, nombre):
    m = re.search(nombre + r"\s*=\s*\{(.*?)\};", txt, re.S)
    return re.findall(r'"([a-z0-9_]+)"', m.group(1)) if m else []


def roster_del_juego():
    """[(id, archivo_captura, slug, nombre)] del plantel APROBADO, en el orden
    del juego. Los arqueros van al final (el orden de `GkPoolIds`)."""
    txt = open(MATCHTUNING, encoding="utf-8").read()
    ids = _lista_cs(txt, "BluePoolIds")
    gks = [g for g in _lista_cs(txt, "GkPoolIds") if g not in ids]
    ids += gks
    bloque = re.search(r"NombreDe\(string id\).*?\n    \};", txt, re.S).group(0)
    nombres = dict(re.findall(r'"([a-z0-9_]+)"\s*=>\s*"([^"]+)"', bloque))
    out, sin_aprobar, choques = [], [], []
    for i in ids:
        if i not in APROBADOS:
            sin_aprobar.append(i)
            continue
        nombre = nombres.get(i, i.upper())
        slug = slug_de(nombre)
        congelado = SLUGS_CONGELADOS.get(i)
        if congelado and congelado != slug:
            choques.append((i, congelado, slug))
            slug = congelado          # manda la URL viva
        out.append((i, ALIAS_CAPTURA.get(i, i), slug, nombre))
    return out, sin_aprobar, choques, set(gks)


ROSTER_JUEGO, SIN_APROBAR, SLUG_CHOQUES, GK_IDS = roster_del_juego()
ROSTER = [(cap, slug) for _id, cap, slug, _n in ROSTER_JUEGO]


# ── roster.json: la ficha de cada jugador, derivada del juego ────────────────
# La web muestra STATS REALES (la ficha de la figurita) y esos numeros viven en
# los `P("id", pa, po, cu, co, st:, shp:, psp:, dr:, zur:)` de MatchTuning.cs.
# Se parsean de ahi por la misma razon por la que el album se deriva del juego:
# una copia a mano se desincroniza EN SILENCIO (ya paso: 28 vs 50 durante tres
# dias). Lo mismo con la jugada firma, que sale del switch del HUD en
# MatchDirector.cs (`"id" => "LA FIRMA (F)"`) — la unica lista del juego que
# nombra la firma de CADA id (la web decia que El Kuni tenia "El Fenomeno" y en
# el juego su firma es "EL KUNI": exactamente el bug que esto elimina).
STAT_KEYS = ("ritmo", "pegada", "comba", "control",
             "fuerza", "precision", "pase", "gambeta")


def stats_del_juego():
    """{id: {stat: multiplicador}} + {id: zurdo} desde los P(...) del juego."""
    txt = open(MATCHTUNING, encoding="utf-8").read()
    # la compresion del techo de velocidad (M65) se aplica en la fabrica P():
    # el multiplicador ESCRITO no es el que juega — hay que replicarla aca o
    # la web publicaria numeros que el juego ya no usa
    knee = float(re.search(r"PaceKnee = ([\d.]+)f", txt).group(1))
    topmul = float(re.search(r"PaceTopMul = ([\d.]+)f", txt).group(1))
    stats, zurdos = {}, {}
    for m in re.finditer(
            r'P\("([a-z0-9_]+)",\s*([\d.]+)f,\s*([\d.]+)f,\s*([\d.]+)f,'
            r'\s*([\d.]+)f([^)]*)\)', txt):
        i, pa, po, cu, co = m.group(1), *(float(m.group(k)) for k in (2, 3, 4, 5))
        extra = m.group(6)

        def kw(nombre, default=1.0):
            k = re.search(nombre + r":\s*([\d.]+)f", extra)
            return float(k.group(1)) if k else default

        if pa > knee:
            pa = knee + (pa - knee) * topmul
        stats[i] = dict(zip(STAT_KEYS, (pa, po, cu, co, kw("st"), kw("shp"),
                                        kw("psp"), kw("dr"))))
        zurdos[i] = "zur: true" in extra
    return stats, zurdos


def firmas_del_juego():
    """{id: 'LA FIRMA'} desde el switch del HUD (DrawHumanMeters)."""
    txt = open(MATCHDIRECTOR, encoding="utf-8").read()
    return dict(re.findall(r'"([a-z0-9_]+)"\s*=>\s*"([^"]+) \(F\)"', txt))


def build_roster_json():
    stats, zurdos = stats_del_juego()
    firmas = firmas_del_juego()
    ids = [i for i, _c, _s, _n in ROSTER_JUEGO]
    sin_datos = [i for i in ids if i not in stats]
    sin_firma = [i for i in ids if i not in firmas and i not in GK_IDS]
    if sin_datos or sin_firma:
        # mismo criterio que auditar_album: gritar, no faltar calladito
        print("!! roster.json INCOMPLETO — sin stats: %s / sin firma: %s"
              % (sin_datos or "-", sin_firma or "-"))
        sys.exit(1)
    # 0-99 con min-max POR ATRIBUTO sobre el plantel, piso 40: el peor del
    # juego en algo sigue siendo un jugador de Fulbito, no un tronco. El techo
    # 99 es del mejor REAL en ese atributo — no hay curva inventada.
    rango = {}
    for k in STAT_KEYS:
        vals = [stats[i][k] for i in ids]
        lo, hi = min(vals), max(vals)
        rango[k] = (lo, (hi - lo) or 1.0)
    jugadores = []
    for i, _cap, slug, nombre in ROSTER_JUEGO:
        jugadores.append({
            "id": i, "slug": slug, "nombre": nombre,
            "firma": firmas.get(i, "ARQUERO" if i in GK_IDS else "?"),
            "gk": i in GK_IDS, "zurdo": zurdos.get(i, False),
            "stats": {k: int(round(40 + 59 * (stats[i][k] - rango[k][0])
                                   / rango[k][1])) for k in STAT_KEYS},
        })
    with open(out("assets", "roster", "roster.json"), "w", encoding="utf-8") as f:
        json.dump(jugadores, f, ensure_ascii=False, separators=(",", ":"))
    print("roster.json: %d jugadores (%d arqueros, %d zurdos)"
          % (len(jugadores), sum(j["gk"] for j in jugadores),
             sum(j["zurdo"] for j in jugadores)))
    return jugadores
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
    # El hero: el MISMO plano que `assets/video/hero.mp4`, sacado del mismo
    # clip. Antes era `web_tv_08` (un plano mas abierto, con tribuna) y al
    # entrar el video se veia el salto de encuadre. Sale de
    #   ffmpeg -ss 17 -i <grabacion> -frames:v 1 \
    #          -vf "crop=1600:900:352:215" captures/web_hero_still.png
    # El crop saca el HUD del juego (marcador arriba, minimapa y barras
    # abajo, y la pildora del jugador que manejas): en un fondo detras del
    # wordmark, medio marcador cortado se lee como un error.
    ("web_hero_still", "cancha-noche"),
    # La banda de firmas: el MISMO plano que `assets/video/firma.mp4` y del
    # mismo clip, con el mismo crop. Antes era `web_tiro_07` (La Muralla),
    # y quedo mezclado: la foto y el epigrafe decian Muralla y el video que
    # se montaba encima era El Martillazo.
    #   ffmpeg -ss 82.93 -i <grabacion> -frames:v 1 \
    #          -vf "crop=1400:788:452:250,scale=1600:900" captures/web_firma_still.png
    # ⚠️ Este crop es MAS CERRADO que el de las otras dos: deja afuera todo el
    # HUD, incluido el cartel "¡EL MARTILLAZO!" y la pildora del jugador que
    # manejas, que pegada al borde de arriba se leia como cortada. El cartel no
    # se extrana porque el epigrafe de la banda ya nombra la jugada, y de paso el
    # golpe se ve el doble de grande.
    ("web_firma_still", "martillazo"),
    ("web_tiro_03", "gol"),
]
# ⚠️ Solo van las capturas que el sitio USA. Hasta el 30-jul-2026 esta lista
# generaba tambien `menu`, `atajada` y `partido`, que no estan referenciadas en
# ningun lado —ni en el HTML, ni en el CSS, ni en el JS—: sobraron de una version
# anterior del diseno. Ademas de pesar al pedo, tenian un problema peor: sus
# fuentes (`m15_menu_bg`, `m3_save_5`, `m7_match_mid`) las regenera cualquier sim
# del repo del juego, asi que un `build_assets.py` despues de re-correr SimMatch
# metia en el commit una captura distinta que nadie habia mirado. Antes de sumar
# una captura aca, tiene que existir el lugar donde se muestra.
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


def build_shots():
    for src, slug in SHOTS:
        p = os.path.join(CAPS, src + ".png")
        if not os.path.exists(p):
            print("  FALTA", p)
            continue
        im = Image.open(p).convert("RGB")
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


def auditar_album():
    """Compara TRES listas que tienen que decir lo mismo, y grita si no.

    ⚠️ Existe porque el album ya se desincronizo una vez EN SILENCIO (28 jugadores
    contra 50 del juego, durante tres dias). Las tres listas son:
        1. el plantel del juego (`BluePoolIds` + `GkPoolIds`)
        2. `APROBADOS`  — el chequeo de marcas, que es manual a proposito
        3. la grilla de `index.html` — donde el jugador realmente los ve
    Generar el .webp no alcanza: si no hay `<li>` en el HTML, la figurita no existe
    para nadie. Es la misma leccion de `BluePoolIds` vs. los cuerpos de la escena.
    """
    problemas = []
    if SIN_APROBAR:
        problemas.append(
            "SIN CHEQUEO DE MARCAS (%d): %s\n"
            "   -> abri game-unity/captures/<id>_check_front.png, HACE ZOOM A LA\n"
            "      CAMISETA (escudos de clubes, sponsors) y si esta limpia sumalo a\n"
            "      APROBADOS. Ver README seccion 'Chequeo de marcas'."
            % (len(SIN_APROBAR), ", ".join(SIN_APROBAR)))
    for i, congelado, derivado in SLUG_CHOQUES:
        problemas.append(
            "SLUG PUBLICADO QUE CAMBIARIA: '%s' esta publicado como '%s' y de\n"
            "   `NombreDe` ahora sale '%s'. Se publica el viejo para no romper la URL.\n"
            "   Si el cambio es a proposito, actualiza SLUGS_CONGELADOS Y el index.html."
            % (i, congelado, derivado))
    # ¿estan todos en la grilla del sitio?
    html = open(os.path.join(WEB, "index.html"), encoding="utf-8").read()
    faltan_html = [s for _i, _c, s, _n in ROSTER_JUEGO
                   if ("assets/roster/%s.webp" % s) not in html]
    if faltan_html:
        problemas.append(
            "SIN <li> EN index.html (%d): %s\n"
            "   -> el .webp se genera igual, pero en el sitio NO SE VE."
            % (len(faltan_html), ", ".join(faltan_html)))
    if problemas:
        print("\n" + "=" * 70)
        print("ALBUM INCOMPLETO")
        print("=" * 70)
        for p in problemas:
            print(" - " + p)
        print("=" * 70)
        return False
    print("album: %d jugadores, todos aprobados y en el index" % len(ROSTER_JUEGO))
    return True


if __name__ == "__main__":
    build_brand()
    build_roster()
    build_roster_json()
    build_shots()
    ok = auditar_album()
    print("listo")
    # ⚠️ sale con error DESPUES de generar todo: los assets quedan igual, pero el
    # que corrio esto se entera. Un album incompleto que termina en verde es
    # exactamente como se perdieron doce jugadores durante tres dias.
    sys.exit(0 if ok else 1)
