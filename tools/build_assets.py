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
import numpy as np
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
    # 12-ago-2026 — los QUINCE que la web le debia al juego: TITAN (M164),
    # los cuatro de CA MILLONETAS (M164), los cuatro italianos de SPORTIVO
    # AZZURRI (M173), y los SEIS arqueros que entraron con M159/M173 (pato,
    # mono, casillero, dado, doblev, pinocho). Chequeo de marcas hecho sobre
    # los `_check_front.png` (contact sheet + zoom al torso): los quince
    # llevan el kit magenta liso de Meshy, pantalon blanco o magenta, sin
    # escudo ni sponsor; los arqueros con guantes lisos sin logo.
    "titan", "payasito", "valdanito", "muneco", "jefecito",
    "maestro", "pinturicchio", "divino", "reyromano",
    "pato", "mono", "casillero", "dado", "doblev", "pinocho",
    # 13-ago-2026 — TRENCINHO, que entra a EL SCRATCH en el lugar de PEPITO.
    # Chequeo de marcas con zoom al torso sobre `trencinho_check_front.png`:
    # camiseta bordo LISA (no es el magenta de Meshy, es un kit pintado), sin
    # escudo ni sponsor ni numero; pantalon blanco con vivo bordo.
    "trencinho",
    # 18-ago-2026 — los DIECISEIS que entraron con M194/M194b/M195/M195b-c: los
    # once de M194, los cuatro de THE RED BEATLES y los tres arqueros nuevos
    # (barbab, julito, chauve) mas aquaman. Chequeo de marcas hecho sobre los
    # `_check_front.png` recien rendereados (contact sheet + zoom al torso y a
    # los guantes): los dieciseis llevan el kit magenta liso de Meshy, short
    # blanco, sin escudo, sin sponsor y sin numero. Los cuatro arqueros usan el
    # guante rojo/negro de Meshy: el garabato claro del nudillo es ruido de la
    # textura, no una marca legible — y ademas cae FUERA del recorte del busto,
    # que corta arriba de los hombros.
    "mamut", "torre", "monstro", "patricio", "colorado", "relojero", "capitan",
    "nino", "titi", "dartagnan", "ashley", "lili",
    "barbab", "julito", "chauve", "aquaman",
    # 19-ago-2026 — los CINCO de M196. Mismo chequeo sobre los
    # `_check_front.png` recien rendereados (cuerpo entero + zoom al torso):
    # kit magenta liso de Meshy, short blanco, sin escudo, sin sponsor y sin
    # numero los cinco.
    "bombardero", "elefante", "hummus", "kaiser", "cruyff",
    # 25-ago-2026 — EL GUAJE, el unico que entro al pool despues de M196 (va en
    # LA FURIA). Mismo chequeo sobre `guaje_check_front.png` recien rendereado
    # (cuerpo entero + zoom al torso a 900 px): camiseta bordo LISA —kit
    # pintado, como el de trencinho, no el magenta de Meshy—, short blanco, sin
    # escudo, sin sponsor y sin numero.
    "guaje",
    # 16-sep-2026 — EL CISNE (M233), que entra a NARANJA MECANICA, IL DIAVOLO y
    # LA CANTERA. Zoom al torso sobre `cisne_check_front.png`: camiseta bordo
    # lisa con vivos oscuros, short blanco, sin escudo, sin sponsor y sin numero.
    "cisne",
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
    """`EL VIKINGO` -> `el-vikingo`. Reproduce EXACTO los 28 slugs ya publicados.

    ⚠️ Se sacan los apóstrofos (18-ago-2026, D'ARTAGNAN): el slug es a la vez
    NOMBRE DE ARCHIVO y fragmento de URL del deep-link `#cromo/<slug>`, y un
    `d'artagnan.webp` obliga a escapar la comilla en cada uno de los tres
    lugares (disco, href, comparación en JS). Ninguno de los 28 congelados
    tiene apóstrofo, así que esto no renombra nada publicado.
    """
    s = _sin_acentos(nombre).lower().strip().replace("'", "").replace("’", "")
    return "-".join(p for p in s.replace("/", " ").split(" ") if p)


def _sin_comentarios(txt):
    # los bloques de los .cs llevan comentarios con comillas y llaves adentro
    # ("DIA" no es "MIL", *"pedido de Rodrigo"*): parsear sin sacarlos primero
    # es garantía de leer basura.
    return re.sub(r"//[^\n]*", "", txt)


def _lista_cs(txt, nombre):
    # ⚠️ sin comentarios SIEMPRE. El 11-ago M173 metió un comentario entre el
    # `=` y la `{` de `GkPoolIds` y esta regex dejó de matchear: los DIEZ
    # arqueros desaparecieron del álbum EN SILENCIO (roster.json decía
    # "0 arqueros" y nada gritaba — la clase de bug que este script existe
    # para no tener).
    m = re.search(nombre + r"\s*=\s*\{(.*?)\};", _sin_comentarios(txt), re.S)
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
# ⚠️ M213 — NUEVE, NO OCHO. `marca` es el primer atributo defensivo del juego y
# entro porque Rodrigo pregunto *"¿por que un equipo de marca va a ser peor?"*: los
# ocho de antes eran de ataque o de fisico, asi que a un defensor se lo describia por
# RESTA. Ademas pesa en `DoTackle`, que hasta M213 calculaba el forcejeo solo con los
# atributos DE LA VICTIMA.
STAT_KEYS = ("ritmo", "pegada", "comba", "control",
             "fuerza", "precision", "pase", "gambeta", "marca")


def stats_del_juego():
    """{id: {stat: multiplicador}} + {id: zurdo} desde los P(...) del juego."""
    txt = open(MATCHTUNING, encoding="utf-8").read()
    # ⚠️ LA TABLA QUE SE LEE NO ES LA QUE JUEGA, y ahora por DOS motivos: la fabrica
    # `P()` transforma los numeros escritos antes de guardarlos, asi que replicar eso
    # aca no es prolijidad — sin esto la web publica numeros que el juego no usa.
    #   1. M65, `PaceTopMul`: lo que esta por encima de `PaceKnee` se comprime hacia la
    #      rodilla. Es monotona, o sea que no crea empates ni invierte el orden.
    #   2. M213, `ArcadeMul`: los OTROS OCHO se comprimen hacia 1.0 con
    #      `v' = 1 + (v-1)·mul`. `pace` NO pasa por aca — tiene su propia compresion y
    #      aplicarle las dos lo comprimiria dos veces.
    # Los dos diales se LEEN del juego. Hardcodear 0.35 o 0.60 aca es la forma exacta
    # en que esta replica queda vieja en silencio: el juego cambia el dial, la web sigue
    # publicando la escala anterior y nada grita.
    knee = float(re.search(r"PaceKnee = ([\d.]+)f", txt).group(1))
    topmul = float(re.search(r"PaceTopMul = ([\d.]+)f", txt).group(1))
    arcmul = float(re.search(r"ArcadeMul = ([\d.]+)f", txt).group(1))

    arcmul = np.float32(arcmul)
    knee, topmul = np.float32(knee), np.float32(topmul)

    def arc(v):
        return np.float32(1.0) + (np.float32(v) - np.float32(1.0)) * arcmul
    stats, zurdos = {}, {}
    for m in re.finditer(
            r'P\("([a-z0-9_]+)",\s*([\d.]+)f,\s*([\d.]+)f,\s*([\d.]+)f,'
            r'\s*([\d.]+)f([^)]*)\)', txt):
        i, pa, po, cu, co = m.group(1), *(float(m.group(k)) for k in (2, 3, 4, 5))
        extra = m.group(6)

        def kw(nombre, default=1.0):
            k = re.search(nombre + r":\s*([\d.]+)f", extra)
            return float(k.group(1)) if k else default

        pa = np.float32(pa)
        if pa > knee:
            pa = knee + (pa - knee) * topmul
        stats[i] = dict(zip(STAT_KEYS,
                            (pa,) + tuple(arc(v) for v in
                                          (po, cu, co, kw("st"), kw("shp"),
                                           kw("psp"), kw("dr"), kw("mk")))))
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
# ── equipos.json: el catálogo de equipos, derivado del juego (M153…M173) ─────
# Desde M153 el juego no se arma jugador por jugador: se ELIGE un equipo del
# catálogo (`Equipos.cs`), con formación, arquero, escudo y barras VEL/FUE/PRE/DEF.
# La web lo deriva de ahí por la misma razón que el álbum: una copia a mano se
# desincroniza en silencio. Se parsean CUATRO cosas del juego:
#   1. `Equipos.Catalogo`  — nombre, concepto, formación, gk y los 6 de campo
#   2. `Equipos.EscudoId`  — el slug del escudo (mismo orden que el catálogo)
#   3. `Equipos.AbrevId`   — las tres letras del marcador (ídem)
#   4. `MatchTuning.Formations` — los esquemas con sus SLOTS reales (z, x),
#      que es lo que permite dibujar la mini-cancha de la ficha con las
#      posiciones de verdad y no un dibujito inventado.
#
# ⚠️ LAS BARRAS SE RECALCULAN ACÁ con la MISMA cuenta que `Equipos.Barra()`:
# z contra la media y el desvío del pool DE CAMPO (58), desvío dividido √6
# porque se compara una media de seis, escala 15, clamp 10..95. Cualquier
# desvío de esa réplica publica números que el juego no muestra — por eso
# `tools/verificar_barras.py` (una vez) se comparó contra la salida real de
# `PocEquipos.SimEquipos` (27/27 exactos, 12-ago-2026). Si un perfil de
# `MatchTuning` cambia, las barras de acá se mueven SOLAS igual que en el juego.
EQUIPOS_CS = os.path.join(RAIZ, "game-unity", "FulbitoPenales", "Assets",
                          "Scripts", "Equipos.cs")
ESCUDOS_SRC = os.path.join(RAIZ, "game-unity", "FulbitoPenales", "Assets",
                           "Resources", "Escudos")
ESTADIOS_CS = os.path.join(RAIZ, "game-unity", "FulbitoPenales", "Assets",
                           "Scripts", "Estadios.cs")

# El chequeo de marcas de las CAPTURAS DE SEDE, misma mecánica que los escudos.
# Acá el riesgo es distinto y peor: tres de los ocho estadios llegaron con el
# NOMBRE DE UN ESTADIO REAL pintado en la fachada, en los palcos, en murales y
# en la pantalla, y se despersonalizaron a mano en el repo del juego
# (`assets-src/bodegon_fbx.py`, `monumento_fbx.py`). O sea que acá no alcanza
# con mirar las camisetas: hay que LEER EL ESTADIO — fachada, cartel del
# acceso, pantalla y carteles perimetrales — antes de publicar la foto.
SEDES_APROBADAS = {
    # 25-ago-2026 — las OCHO, miradas a 1280x720 y con zoom a cada superficie
    # que lleva texto. Re-miradas el mismo día al cambiar la vista de `_aerea` a
    # `_web`: los dos encuadres que más cambiaron son el del Bodegón (ahora entra
    # por la boca de la herradura y se ve la cancha y los contenedores) y el de
    # Old Road (ahora se ve la cancha por encima de la tribuna baja); en los dos
    # lo único legible sigue siendo props nuestros. Lo que se lee en las fotos es todo del juego:
    # `FULBITO STADIUM` en la fachada de LA CATEDRAL, `STADIO DELLE CURVE` en la
    # marquesina del italiano, `BODEGÓN XENEIZE` sobre los palcos, `EL MONUMENTO`
    # y `PUERTA LA HINCHADA` en el anillo de M188; los carteles perimetrales y
    # los trapos de la hinchada dicen FULBITO / LA BANDA / AGUANTE / VAMOS, que
    # son props nuestros. Ningún nombre de estadio real, ningún sponsor.
    # ⚠️ La pantalla del italiano muestra `CASA 2-1 OSPITI`, que es el marcador
    # clavado del modelo: no es una marca, pero conviene saber que está ahí
    # antes de que alguien pregunte por qué el resultado no cambia.
    "catedral", "coliseo", "municipal", "stadioitaliano", "oldroad",
    "bodegonxeneize", "elmonumento", "maracuya",
    # 16-sep-2026 — COLISEO GALÁCTICO (M230), sobre `_aerea` (ver SEDE_VISTA_DE).
    # Zoom a la fachada y al anillo de video: dicen `COLISEO GALÁCTICO` y `COPA
    # FULBITO` (los pinta `assets-src/galactico_letreros.py`; el nombre es
    # inventado, no de un estadio real). Carteles perimetrales: LA BANDA /
    # FULBITO / AGUANTE / VAMOS. Sin sponsors.
    "coliseogalactico",
}
# de qué toma cada sede su foto.
# ⚠️ `_web` Y NO `_aerea` (25-ago-2026). Las `_tv` y `_aerea_cruce` están
# encuadradas sobre la cancha —que es igual en las ocho— y ahí las sedes se
# vuelven indistinguibles. Pero la `_aerea` tampoco servía: es el ARRANQUE DEL
# VUELO DE LA CEREMONIA, o sea el MISMO acimut para las ocho, y con un ángulo
# fijo el Bodegón (que es una herradura) se veía por la espalda y Old Road (que
# tiene UNA tribuna alta con techo) salía sin cancha. Rodrigo, mirando las ocho:
# *"la visual del Bodegón Xeneize debería ser desde el otro lado"*, *"en Old Road
# no se ve la cancha"*.
# La `_web` la agregó `PocEstadios.CapturarSedes` en M211 y elige el lado y la
# altura MIDIENDO: entra por el sector más bajo del estadio y se eleva lo que
# haga falta para pasar por encima de ese borde. Se regenera con
#   Unity.exe -batchmode -quit -projectPath <proj> #             -executeMethod PocEstadios.CapturarSedes
SEDE_VISTA = "_web"
# ⚠️ LA EXCEPCIÓN, y por qué es una sola. En COLISEO GALÁCTICO la `_web` entra por
# el lado donde `abrir_techo()` estaciona el techo retráctil: `AcimutBajo` mide la
# ALTURA MÁXIMA del sector, y ese lado es el más bajo, pero la losa del techo
# estacionado queda entre la cámara y la cancha y tapa dos tercios del cuadro
# (captura del 8-sep). La `_aerea` de la misma corrida muestra la piel de LED, las
# bandejas y la cancha. Lo correcto a la larga es que `AcimutBajo` pese lo que
# TAPA y no lo que mide de alto; mientras tanto, la foto se elige acá — mirándola.
SEDE_VISTA_DE = {"coliseogalactico": "_aerea"}
SEDE_MAX_W = 1280

# El chequeo de marcas de los ESCUDOS, misma mecánica que APROBADOS: el slug
# tiene que estar acá o el script termina con error. Son las parodias de
# `game-unity/tools/gen_escudos.py` — la regla de la casa es que el escudo
# dibuja el CONCEPTO, nunca la marca del club real.
ESCUDOS_APROBADOS = {
    # revisados el 12-ago-2026 (contact sheet + zoom, los 27): ninguno
    # reproduce un escudo registrado. Los tres guiños más fuertes usan
    # símbolos de ciudad o heráldica genérica, no la marca: boke = azul/oro
    # con ancla y estrellas (no el escudo de CABJ), millonetas = banda roja
    # sin monograma, culebra = el biscione visconteo (heráldica de Milán).
    "fulbitofc", "scaloneta22", "scaloneta26", "albiceleste", "boke",
    "scratch", "piernacambiada", "capitanes", "pulmones", "polvora", "magos",
    "galacticos", "jogobonito", "rompehuesos", "vikingos", "ultimotango",
    "potrero", "indomables", "millonetas", "tikitaka", "culebra", "diavolo",
    "viejasenora", "teatro", "parisiens", "cantera", "azzurri",
    # 18-ago-2026 — los CUATRO de M195b/c. Mirados con zoom: ninguno reproduce
    # un escudo registrado ni lleva texto. beatles = cuatro siluetas mop-top
    # alrededor de una pelota (dibuja la BANDA, no el escudo del club de la
    # ciudad); leones = tres cabezas de leon doradas sobre azul, heraldica
    # inglesa generica (mismo criterio que `culebra` con el biscione); bleus =
    # el gallo galo sobre azul con la banda tricolor, emblema nacional, sin
    # hexagono ni siglas; artilleros = DOS canones cruzados con balas de canon,
    # heraldica de artilleria — el escudo real de los Gunners es UN canon solo
    # y lleva el nombre escrito.
    "beatles", "leones", "artilleros", "bleus",
    # 19-ago-2026 — los CUATRO de M196. Los cuatro dibujan HERALDICA
    # NACIONAL O REGIONAL, que es dominio publico, y ninguno lleva texto ni la
    # marca de la federacion: mannschaft = el aguila federal con la banda
    # negro/rojo/oro (no el aguila del DFB, que va con siglas); naranja = el
    # leon rampante naranja sobre azul (armas de los Paises Bajos, no el
    # escudo de la KNVB); bavaros = la corona sobre los rombos blanquiazules
    # (la BANDERA DE BAVIERA, mismo criterio que `culebra` con el biscione).
    # ⚠️ El mas al limite es `aristocratas`: cetro + rosa blanca sobre azul y
    # oro toma el VOCABULARIO heraldico del club de Londres, pero no su leon
    # rampante ni el disco, y va sin nombre. Se aprueba con el mismo criterio
    # que `boke` (azul/oro con ancla y estrellas) y `millonetas` (banda roja
    # sin monograma) — si alguna vez se afina la regla, empezar por este.
    "mannschaft", "naranja", "aristocratas", "bavaros",
    # 25-ago-2026 — los DOS de M206/M210. Mirados con zoom, ninguno lleva texto
    # ni reproduce un escudo registrado: `furia` = un toro dorado embistiendo
    # sobre rojo con banda roja y oro (el toro es iconografia nacional espanola,
    # no el escudo de la RFEF, que va con corona y siglas); `colchoneros` =
    # rayas rojas y blancas con banda azul y un CANDADO al medio — o sea el
    # colchon y el candado, que son los dos apodos, y no el oso con el madrono
    # del club real. Mismo criterio que `boke` y `millonetas`: colores de la
    # camiseta si, marca no.
    "furia", "colchoneros",
    # 31-ago-2026 — `loba` (M229). Mirado con zoom: un LOBO dorado de perfil,
    # parado y aullando, sobre escudo porpora con borde y banda de oro. Sin
    # texto, sin numeros y sin monograma.
    # ⚠️ LO QUE HAY QUE MIRAR ACA NO ES EL ANIMAL, SON LOS GEMELOS. La loba sola
    # es iconografia de la ciudad de Roma —heraldica publica desde hace veinticinco
    # siglos, igual que el toro de `furia` o el aguila de `mannschaft`—; la que ES
    # el escudo del club es la ESCENA de la loba amamantando a los dos bebes. Este
    # no la tiene: el lobo esta parado y solo, y el prompt de `gen_escudos.py` niega
    # los gemelos con todas las letras. Mismo criterio que `colchoneros`, donde el
    # oso quedo AFUERA por ser el emblema literal del club.
    "loba",
}

ESCUDO_OUT = 256    # los PNG fuente son 256×256; se convierten sin escalar


def formaciones_del_juego():
    """Los 7 esquemas con sus slots (z, x) reales — GK primero."""
    txt = _sin_comentarios(open(MATCHTUNING, encoding="utf-8").read())
    bloque = re.search(r"Formations\s*=\s*\{(.*?)\n    \};", txt, re.S).group(1)
    formas = []
    for m in re.finditer(
            r'new Formacion\s*\{\s*name = "([^"]+)",\s*def = (\d+),\s*'
            r'mid = (\d+),\s*fwd = (\d+),\s*slots = new\[\]\s*\{(.*?)\}\s*\}',
            bloque, re.S):
        slots = [[float(z), float(x)] for z, x in
                 re.findall(r"new Vector2\(\s*([-\d.]+)f?,\s*([-\d.]+)f?\s*\)",
                            m.group(5))]
        formas.append({"name": m.group(1), "def": int(m.group(2)),
                       "mid": int(m.group(3)), "fwd": int(m.group(4)),
                       "slots": slots})
    return formas


def equipos_del_juego():
    """El catálogo entero, en su orden (que es el de EscudoId y AbrevId)."""
    txt = _sin_comentarios(open(EQUIPOS_CS, encoding="utf-8").read())
    bloque = re.search(r"Catalogo\s*=[^{]*\{(.*?)\n    \};", txt, re.S).group(1)
    equipos = []
    # el lazy corta en la PRIMERA `}`, que es la del arreglo de ids — como los
    # ids son el último campo del struct, el chunk trae todos los campos
    for m in re.finditer(r"new Equipo\s*\{(.*?)\}", bloque, re.S):
        chunk = m.group(1)
        equipos.append({
            "nombre": re.search(r'nombre = "([^"]+)"', chunk).group(1),
            "form": int(re.search(r"form = (\d+)", chunk).group(1)),
            "gk": re.search(r'gk = "([a-z0-9_]+)"', chunk).group(1),
            "concepto": re.search(r'concepto = "([^"]+)"', chunk).group(1),
            # M177 — la cancha del equipo, como CONSTANTE (`sede = Estadios.Coliseo`).
            # Se resuelve contra `Estadios.cs` mas abajo; se guarda el nombre crudo
            # para que un `sede` que no exista se vea como lo que es.
            "sede_const": re.search(r"sede\s*=\s*Estadios\.(\w+)",
                                    chunk).group(1),
            "ids": re.findall(r'"([a-z0-9_]+)"',
                              chunk.split("ids = new[]")[1]),
        })
    # M197 — LAS LIGAS. Un arreglo paralelo más, como `EscudoId`: `Validar()` en el
    # juego le chequea el largo contra el catálogo, y acá se chequea igual (abajo).
    # ⚠️ EL ORDEN DE `LigaNombre` NO ES ALFABÉTICO NI POR TAMAÑO: es el orden en que
    # el selector del juego cicla las ligas, y por eso es el orden de la web.
    ligas = re.findall(r'"([^"]+)"',
                       re.search(r"LigaNombre\s*=\s*[^{]*\{(.*?)\};", txt,
                                 re.S).group(1))
    liga_de = re.findall(r"Liga(Clubes|Selecciones|Combinados)",
                         re.search(r"LigaDe\s*=\s*\{(.*?)\};", txt, re.S).group(1))
    orden = {"Clubes": 0, "Selecciones": 1, "Combinados": 2}
    escudos = re.findall(r'"([a-z0-9_]+)"',
                         re.search(r"EscudoId\s*=\s*\{(.*?)\};", txt,
                                   re.S).group(1))
    abrevs = re.findall(r'"([A-Z0-9]{2,3})"',
                        re.search(r"AbrevId\s*=\s*\{(.*?)\};", txt,
                                  re.S).group(1))
    if not (len(equipos) == len(escudos) == len(abrevs) == len(liga_de)):
        print("!! equipos.json ROTO — catálogo %d / escudos %d / abrevs %d / ligas %d"
              % (len(equipos), len(escudos), len(abrevs), len(liga_de)))
        sys.exit(1)
    for eq, esc, ab, lg in zip(equipos, escudos, abrevs, liga_de):
        eq["slug"], eq["abrev"], eq["liga"] = esc, ab, orden[lg]
    return equipos, ligas


# ============================================================================
# LAS CUATRO BARRAS — replica de `Equipos.Eje` + `Equipos.Barra` (M213)
# ============================================================================
# ⚠️ ERAN TRES Y AHORA SON CUATRO. Entro DEFENSA, y no es una barra mas: las tres
# viejas eran VELOCIDAD / FUERZA / PRECISION, o sea tres formas de medir ATACAR, asi
# que un plantel de marca no tenia donde sumar y salia ultimo. Una web que siga
# iterando `for e in range(3)` no muestra una barra de menos: muestra el catalogo
# ordenado por una idea que el juego ya no tiene.
#
# ⚠️ Los cuatro ejes reparten los NUEVE atributos sin dejar ninguno afuera y SIN USAR
# NINGUNO DOS VECES. Por eso DEFENSA es `marca` PURA: mezclarle `fuerza` la haria
# contar en dos barras y un equipo fuerte se veria defensivo sin serlo.
EJES = ("vel", "fue", "pre", "def")

# ⚠️⚠️ TODA ESTA CUENTA VA EN float32, Y NO ES PEDANTERIA. El juego es C# con `float`
# de 32 bits de punta a punta —los literales `0.60f`, los campos de `Prof`, la suma de
# los seis, la division y la escala— y esta replica en `double` daba 35/37: EL SCRATCH
# y LA CANTERA caian del otro lado del `.5` al redondear. O sea que la diferencia no se
# ve como un error, se ve como **un punto de barra**, que es exactamente el tipo de
# mentira que `verificar_barras.py` existe para cazar. Con f32 dan 37/37 exactos.
#
# ⚠️ `np.float32(x)` en cada constante NO es decorativo: numpy promueve a float64 en
# cuanto se mezcla con un float de Python, y ahi vuelve el problema sin avisar.
f32 = np.float32


def _eje(s, e):
    """Los mismos pesos que `Equipos.Eje` (claves en castellano porque
    `stats_del_juego` ya traduce pace→ritmo, etc.), en float32."""
    if e == 0:                                    # VELOCIDAD
        return f32(0.60) * s["ritmo"] + f32(0.40) * s["gambeta"]
    if e == 1:                                    # FUERZA
        return f32(0.50) * s["pegada"] + f32(0.50) * s["fuerza"]
    if e == 3:                                    # DEFENSA — `marca` pura
        return s["marca"]
    return (f32(0.30) * s["precision"] + f32(0.25) * s["pase"]      # PRECISIÓN
            + f32(0.25) * s["control"] + f32(0.20) * s["comba"])


def barras_del_catalogo(equipos, stats):
    """Replica de `Equipos.Barra`: ESCALA ABSOLUTA contra las anclas del juego.

    ⚠️⚠️ M213 — SE FUE EL z-SCORE, y para esta web es la mejor noticia del hito. El
    z-score era suma cero: se media contra la media del pool, asi que **agregar un
    jugador movia las barras de los 37 equipos** y la pagina quedaba vieja por un
    cambio que no la tocaba. Ahora cada eje se mapea contra un rango fijo, o sea que
    una tarjeta solo cambia si cambio ESE equipo. La nota de `regen_listas.py` sobre
    "un jugador nuevo mueve las 37" describe el mundo anterior a esto.

    ⚠️ Las anclas se LEEN de `Equipos.cs`, no se copian. Son el unico numero de esta
    replica que el juego puede mover sin que nada mas cambie de forma — y si se
    copiaran, la web publicaria la escala vieja sin un solo error. Lo mismo el piso y
    el techo del clamp.
    """
    txt = _sin_comentarios(open(EQUIPOS_CS, encoding="utf-8").read())

    def anclas(nombre):
        b = re.search(nombre + r"\s*=\s*\{([^}]*)\}", txt).group(1)
        return [float(v) for v in re.findall(r"([\d.]+)f", b)]

    lo, hi = anclas("AnclaLo"), anclas("AnclaHi")
    piso, techo = (int(v) for v in
                   re.search(r"Piso = (\d+), Techo = (\d+)", txt).groups())
    if not (len(lo) == len(hi) == len(EJES)):
        print("!! las anclas de Equipos.cs son %d/%d y los ejes son %d — la replica "
              "quedo vieja" % (len(lo), len(hi), len(EJES)))
        sys.exit(1)
    lo = [f32(v) for v in lo]
    hi = [f32(v) for v in hi]
    for eq in equipos:
        for e, k in enumerate(EJES):
            # se acumula de a uno y recien despues se divide, como `Equipos.Barra`:
            # sumar en otro orden en float32 puede dar otro ultimo bit
            t = f32(0.0)
            for i in eq["ids"]:
                t = t + _eje(stats[i], e)
            t = t / f32(len(eq["ids"]))
            u = (t - lo[e]) / (hi[e] - lo[e])
            eq[k] = max(piso, min(techo, round(float(u * f32(100.0)))))
            # el mismo aviso que la assertion de PocEquipos: si un equipo toca el
            # piso o el techo, la escala del juego se quedo corta — y la web estaria
            # dibujando una barra llena que en realidad es "no sabemos cuanto mas".
            if eq[k] <= piso or eq[k] >= techo:
                print("  OJO: %s CLAMPEA en %s=%d — las anclas de Equipos.Barra se "
                      "quedaron cortas" % (eq["nombre"], k.upper(), eq[k]))
    return equipos


def build_equipos_json():
    stats, _zurdos = stats_del_juego()
    catalogo, ligas = equipos_del_juego()
    equipos = barras_del_catalogo(catalogo, stats)
    # ⚠️ `equipos` SIGUE EN EL ORDEN DEL CATÁLOGO y eso no se toca: `copa.json` guarda
    # los ÍNDICES de los 16 sorteados, y el número de la pizarra es el del catálogo.
    # Agrupar por liga es cosa del RENDER (regen_listas.py), no del dato.
    data = {"formaciones": formaciones_del_juego(),
            "ligas": ligas,
            "equipos": [{k: eq[k] for k in
                         ("slug", "nombre", "abrev", "concepto", "form",
                          "gk", "ids", "vel", "fue", "pre", "def", "liga")}
                        for eq in equipos]}
    with open(out("assets", "equipos", "equipos.json"), "w",
              encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print("equipos.json: %d equipos en %d ligas (%s), %d formaciones"
          % (len(equipos), len(ligas),
             " ".join("%s %d" % (n, sum(1 for e in equipos if e["liga"] == i))
                      for i, n in enumerate(ligas)),
             len(data["formaciones"])))
    return equipos


def build_escudos(equipos):
    for eq in equipos:
        p = os.path.join(ESCUDOS_SRC, eq["slug"] + ".png")
        if not os.path.exists(p):
            print("  FALTA", p)
            continue
        Image.open(p).convert("RGBA").save(
            out("assets", "equipos", eq["slug"] + ".webp"),
            "WEBP", quality=90, method=6)
    print("escudos: %d" % len(equipos))


# ============================================================================
# LAS SEDES (M177/M207) — los ocho estadios, derivados igual que el catálogo
# ============================================================================
# Mismo contrato que los equipos y el álbum: la lista SALE DEL JUEGO y las
# tarjetas se regeneran desde el JSON (`tools/regen_listas.py`). Acá hay tres
# números que a mano envejecen sin que nada grite, y los tres ya cambiaron una
# vez cada uno:
#
#   · el AFORO no es capacidad de folleto, es la gente que el sembrador pone de
#     verdad y que `AuditarSedes` cuenta colgando de la sede (4 vértices = 1
#     persona). EL MONUMENTO pasó de 30 163 a 34 483 sin tocar el modelo.
#   · quién juega DE LOCAL en cada una sale de `Equipo.sede`, y un equipo nuevo
#     se reparte solo (LOS COLCHONEROS entró al Coliseo en M206).
#   · dónde se juega LA FINAL no está escrito en ningún lado: es `MasGrande`,
#     o sea la sede jugable con más aforo. Se mudó dos veces —Catedral →
#     delle Curve (M176) → MARACUYÁ (M207)— y las dos veces por un número, no
#     por una decisión escrita. Publicar "la final se juega en X" a mano es
#     exactamente la trampa que `DeRonda` tenía en el juego y que se borró.
def sedes_del_juego(equipos):
    txt = _sin_comentarios(open(ESTADIOS_CS, encoding="utf-8").read())
    # `public const int Catedral = 0, Coliseo = 1, ...` — el nombre de la
    # constante NO es el `id` (Italiano vs StadioItaliano), así que hace falta
    # el mapa para resolver el `sede = Estadios.X` de cada equipo.
    consts = {}
    m = re.search(r"public const int (Catedral\s*=.*?);", txt, re.S)
    for nom, val in re.findall(r"(\w+)\s*=\s*(\d+)", m.group(1)):
        consts[nom] = int(val)
    bloque = re.search(r"Sede\[\]\s+Todos\s*=\s*\{(.*?)\n    \};",
                       txt, re.S).group(1)
    sedes = []
    for s in re.finditer(r"new Sede\s*\{(.*?)\}", bloque, re.S):
        c = s.group(1)
        sedes.append({
            "nombre": re.search(r'nombre = "([^"]+)"', c).group(1),
            "id": re.search(r'id = "(\w+)"', c).group(1),
            "concepto": re.search(r'concepto = "([^"]+)"', c).group(1),
            "aforo": int(re.search(r"aforo = (\d+)", c).group(1)),
            "lista": re.search(r"lista = (true|false)", c).group(1) == "true",
        })
    for sd in sedes:
        sd["slug"] = sd["id"].lower()
        sd["equipos"] = []
    for eq in equipos:
        i = consts.get(eq["sede_const"])
        if i is None or i >= len(sedes):
            print("!! %s tiene sede %r y no existe en Estadios.cs"
                  % (eq["nombre"], eq["sede_const"]))
            sys.exit(1)
        eq["sede"] = i
        sedes[i]["equipos"].append(eq["nombre"])
    # `MasGrande` / `MasChica`: la final y el potrero. Replicados tal cual —
    # recorren en orden y se quedan con el PRIMERO que supera, así que un
    # empate de aforo lo gana el de índice más bajo, igual que el juego.
    jugables = [i for i, s in enumerate(sedes) if s["lista"]]
    final = max(jugables, key=lambda i: (sedes[i]["aforo"], -i))
    potrero = min(jugables, key=lambda i: (sedes[i]["aforo"], i))
    for i, sd in enumerate(sedes):
        sd["final"] = (i == final)
        sd["potrero"] = (i == potrero)
    return sedes


def build_sedes(equipos):
    """El JSON + las ocho fotos. Devuelve las sedes (jugables y apagadas)."""
    sedes = sedes_del_juego(equipos)
    for sd in sedes:
        p = os.path.join(CAPS, "sede_%s%s.png"
                         % (sd["slug"], SEDE_VISTA_DE.get(sd["slug"], SEDE_VISTA)))
        if not os.path.exists(p):
            print("  FALTA", p)
            continue
        im = Image.open(p).convert("RGB")
        if im.width > SEDE_MAX_W:
            im = im.resize((SEDE_MAX_W,
                            round(im.height * SEDE_MAX_W / im.width)),
                           Image.LANCZOS)
        im.save(out("assets", "sedes", sd["slug"] + ".webp"),
                "WEBP", quality=82, method=6)
    with open(out("assets", "sedes", "sedes.json"), "w", encoding="utf-8") as f:
        json.dump([{k: sd[k] for k in ("slug", "nombre", "concepto", "aforo",
                                       "lista", "equipos", "final", "potrero")}
                   for sd in sedes], f, ensure_ascii=False,
                  separators=(",", ":"))
    print("sedes.json: %d sedes (%d jugables), final en %s"
          % (len(sedes), sum(1 for s in sedes if s["lista"]),
             next(s["nombre"] for s in sedes if s["final"])))
    return sedes


def auditar_sedes(sedes):
    """Mismo contrato que `auditar_equipos`: la tarjeta tiene que existir y
    tiene que decir lo que dice el juego."""
    html = open(os.path.join(WEB, "index.html"), encoding="utf-8").read()
    problemas = []
    # ⚠️ CERO SEDES NO ES "todo bien": es que el parseo de Estadios.cs se quedo sin
    # matchear (le cambiaron el nombre al arreglo, o la forma del struct). Sin esto,
    # el for de abajo no itera, no hay problemas, y la funcion firma un catalogo que
    # nunca leyo. Es el mismo patron del regex sin anclar de verificar_barras.
    if not sedes:
        problemas.append(
            "NO PARSEE NI UNA SEDE de Estadios.cs" + SALTO
            + "   -> NO es que esten todas bien: es que el chequeo quedo ciego.")
    # ⚠️ Y al reves: una tarjeta publicada que el juego ya no tiene. El for de abajo
    # recorre el JUEGO, asi que una sede que se saca del catalogo se queda para
    # siempre en la pagina sin que nadie la nombre.
    en_html = set(re.findall(r"assets/sedes/([a-z0-9]+)\.webp", html))
    huerfanas = en_html - {s["slug"] for s in sedes if s["lista"]}
    if huerfanas:
        problemas.append("TARJETAS DE SEDE SIN SEDE EN EL JUEGO: %s"
                         % ", ".join(sorted(huerfanas)))
    sin_aprobar = [s["slug"] for s in sedes if s["slug"] not in SEDES_APROBADAS]
    if sin_aprobar:
        problemas.append(
            "CAPTURAS DE SEDE SIN CHEQUEO DE MARCAS (%d): %s\n"
            "   -> abri game-unity/captures/sede_<slug>%s.png y LEE EL ESTADIO\n"
            "      (fachada, accesos, pantalla, carteles): ningun nombre de\n"
            "      estadio real ni sponsor. Recien ahi sumalo a SEDES_APROBADAS."
            % (len(sin_aprobar), ", ".join(sin_aprobar), SEDE_VISTA))
    for sd in sedes:
        if not sd["lista"]:
            # una sede apagada no se publica, y eso no es un error: es contenido
            # que el jugador no puede elegir.
            if "assets/sedes/%s.webp" % sd["slug"] in html:
                problemas.append("SEDE APAGADA PUBLICADA: %s (lista = false)"
                                 % sd["nombre"])
            continue
        i = html.find("assets/sedes/%s.webp" % sd["slug"])
        if i < 0:
            problemas.append("SIN TARJETA EN index.html: %s (%s)"
                             % (sd["slug"], sd["nombre"]))
            continue
        li = html[html.rfind('<li class="sede', 0, i):html.find("</li>", i)]
        for que, espera in (("nombre", ">%s</h3>" % sd["nombre"]),
                            ("concepto", ">%s</p>" % sd["concepto"]),
                            ("aforo", "<b>%s</b>" % _miles(sd["aforo"]))):
            if espera not in li:
                problemas.append(
                    ("TARJETA DE SEDE DESFASADA (%s) en %s: falta %r"
                     % (que, sd["nombre"], espera)) + SALTO
                    + "   -> el juego manda; corre tools/regen_listas.py.")
        if not sd["equipos"]:
            problemas.append(
                "SEDE SIN DUENO: %s no es la cancha de ningun equipo\n"
                "   -> en el juego eso es contenido muerto (nunca sale en un\n"
                "      amistoso) y lo avisa PocEquipos.SimEquipos." % sd["nombre"])
    if problemas:
        print("\n" + "=" * 70)
        print("SEDES INCOMPLETAS")
        print("=" * 70)
        for p in problemas:
            print(" - " + p)
        print("=" * 70)
        return False
    print("sedes: %d publicadas, todas aprobadas y en el index"
          % sum(1 for s in sedes if s["lista"]))
    return True


def _miles(n):
    """42427 -> '42.427'. El punto es el separador de miles en es-AR."""
    return "{:,}".format(n).replace(",", ".")


# ============================================================================
# LOS CONTADORES DEL COPY — la última lista a mano que nadie comparaba
# ============================================================================
# Las grillas tienen auditoría desde hace semanas, pero los NÚMEROS SUELTOS del
# copy no tenían ninguna, y el 25-ago-2026 se encontró el zócalo del hero
# diciendo "90 jugadores en 35 equipos" con el juego en 91 y 37 — publicado, en
# la PRIMERA pantalla, y sobrevivió a tres pasadas de las otras auditorías.
#
# ⚠️ LA MITAD ESTÁN ESCRITOS EN LETRAS ("Treinta y siete equipos", "¿Los otros
# cuarenta y siete?"), que es justamente por qué se desfasan: un `35` se ve raro
# al lado de una grilla de 37, y "treinta y cinco" no se ve raro nunca. Por eso
# el chequeo también sabe deletrear.
_UNI = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
        "nueve", "diez", "once", "doce", "trece", "catorce", "quince",
        "dieciséis", "diecisiete", "dieciocho", "diecinueve", "veinte",
        "veintiuno", "veintidós", "veintitrés", "veinticuatro", "veinticinco",
        "veintiséis", "veintisiete", "veintiocho", "veintinueve"]
_DEC = {30: "treinta", 40: "cuarenta", 50: "cincuenta", 60: "sesenta",
        70: "setenta", 80: "ochenta", 90: "noventa"}


def en_letras(n, apocope=False):
    """`apocope` para cuando va delante del sustantivo: «cincuenta y UN poderes»,
    no «cincuenta y uno poderes» (el auditor exigia la forma incorrecta)."""
    if apocope and n % 10 == 1 and n != 11:
        return en_letras(n - 1) + " y un" if n > 30 else ("un" if n == 1 else "veintiún")
    if n < 30:
        return _UNI[n]
    if n == 100:
        return "cien"
    d, u = n // 10 * 10, n % 10
    return _DEC[d] if u == 0 else "%s y %s" % (_DEC[d], _UNI[u])


def auditar_contadores(equipos, sedes, jugadores, ligas):
    html = open(os.path.join(WEB, "index.html"), encoding="utf-8").read()
    nj = len(jugadores)
    ne = len(equipos)
    ns = sum(1 for s in sedes if s["lista"])
    campo = sum(1 for j in jugadores if not j["gk"])
    poderes = len({j["firma"] for j in jugadores if not j["gk"]})
    # (qué es, el texto que TIENE que estar, dónde vive)
    esperados = [
        ("zócalo del hero", "<b>%d</b> jugadores en <b>%d</b> equipos" % (nj, ne)),
        ("contador del álbum",
         "<b>%d</b> de campo <span aria-hidden=\"true\">·</span> <b>%d</b> arqueros"
         % (campo, nj - campo)),
        ("título del álbum", ">%s</h2>" % en_letras(nj).capitalize()),
        ("volanta de equipos", ">%s equipos</p>" % en_letras(ne, True).capitalize()),
        ("volanta de poderes", ">%s poderes</p>" % en_letras(poderes, True).capitalize()),
        ("volanta de sedes", ">%s canchas</p>" % en_letras(ns, True).capitalize()),
        # los tres poderes con tarjeta grande son a mano; el resto es el resto
        ("los poderes que faltan", "¿Los otros %s?" % en_letras(poderes - 3)),
        ("meta description", "%d jugadores, %d equipos, %d canchas, %d poderes"
                             % (nj, ne, ns, poderes)),
    ]
    # el título de cada liga lleva SU cuenta al lado, y ése es el contador que más
    # fácil se desfasa: un equipo nuevo entra a UNA liga y las otras dos no cambian
    for i, liga in enumerate(ligas):
        n = sum(1 for e in equipos if e["liga"] == i)
        esperados.append(("título de la liga %s" % liga,
                          '>%s <span class="liga__n">%d</span></h3>' % (liga, n)))
    # ⚠️ mismo criterio: si no hay nada que comparar, el que fallo es el chequeo
    if not esperados or not html:
        print("!! auditar_contadores no tenia nada que comparar — quedo ciego")
        return False
    faltan = [(q, t) for q, t in esperados if t not in html]
    if faltan:
        print("\n" + "=" * 70)
        print("CONTADORES DESFASADOS EN EL COPY")
        print("=" * 70)
        for q, t in faltan:
            print(" - %s: falta %r" % (q, t))
        print("   -> son a mano (copy editorial); el juego manda.")
        print("=" * 70)
        return False
    print("contadores: %d jugadores · %d equipos en %d ligas · %d canchas · %d poderes,"
          " todos al dia" % (nj, ne, len(ligas), ns, poderes))
    return True


SALTO = chr(10)

# ⚠️ LA TARJETA DE CADA EQUIPO ES A MANO Y SE DESFASA EN SILENCIO. El 13-ago-2026
# la web mostraba CUATRO formaciones viejas, un nombre viejo (BOKE JRS, que en el
# juego ya era ATLETICO XENEIZE) y LA CANTERA con "Manuelito al arco" cuando su
# arquero es PINOCHO desde siempre. Nada de eso rompe nada: la pagina se ve
# perfecta, sólo miente. Por eso se compara contra `equipos.json`, que sí sale
# del juego.
def _tarjeta_desfasada(html, eq):
    with open(os.path.join(WEB, "assets", "equipos", "equipos.json"),
              encoding="utf-8") as f:
        datos = json.load(f)
    forma = datos["formaciones"][eq["form"]]["name"]
    nombres = {i: n for i, _c, _s, n in ROSTER_JUEGO}
    gk = " ".join(w[:1].upper() + w[1:].lower()
                  for w in nombres.get(eq["gk"], eq["gk"]).split(" "))
    # ⚠️ SI NO ENCUENTRA LA TARJETA, ESO ES UNA FALLA — no un chequeo que se saltea.
    # Con `find` devolviendo -1, `html[ini:-1]` es casi el documento entero y TODOS los
    # `espera` aparecen (los pone otra tarjeta), asi que la funcion devolvia "sin
    # fallas" justo cuando no habia mirado nada. Hoy el llamador ya filtra ese caso,
    # pero el que se apoya en su llamador es el chequeo que un dia se apaga solo.
    fallas = []
    i = html.find("assets/equipos/%s.webp" % eq["slug"])
    ini = html.rfind('<li class="equipo', 0, i) if i >= 0 else -1
    fin = html.find("</li>", i) if i >= 0 else -1
    if i < 0 or ini < 0 or fin < 0:
        return [("TARJETA ILEGIBLE en %s: no encontre su <li> completo en index.html"
                 % eq["nombre"]) + SALTO
                + "   -> NO es que la tarjeta este bien; es que el chequeo no pudo mirarla."]
    li = html[ini:fin]
    for que, espera in (("nombre", ">%s</h3>" % eq["nombre"]),
                        ("concepto", ">%s</p>" % eq["concepto"]),
                        ("formacion", "<b>%s</b>" % forma),
                        ("arquero", "%s al arco" % gk),
                        # ⚠️ se chequean VEL y DEF, no una sola: DEF entro en M213 y
                        # una tarjeta con las tres viejas correctas y sin la cuarta
                        # pasaba el chequeo entera.
                        ("barras", "<b>%d</b>" % eq["vel"]),
                        ("barra DEF", 'title="Defensa">DEF</abbr></dt>'
                                      '<dd><i style="--v:%d">' % eq["def"])):
        if espera not in li:
            fallas.append(
                ("TARJETA DESFASADA (%s) en %s: falta %r"
                 % (que, eq["nombre"], espera))
                + SALTO + "   -> el juego manda; corregi el <li> en index.html.")
    return fallas


def auditar_equipos(equipos):
    """Mismo contrato que `auditar_album`: las listas que tienen que decir lo
    mismo, comparadas — y si no, se grita. Devuelve False si hay problemas."""
    # ⚠️ sin comentarios: `GkPoolIds` tiene uno entre el `=` y la `{` que a
    # `_lista_cs` le devuelve lista vacía — y entonces TODO arquero es "de afuera"
    txt = _sin_comentarios(open(MATCHTUNING, encoding="utf-8").read())
    pool = set(_lista_cs(txt, "BluePoolIds"))
    gks = set(_lista_cs(txt, "GkPoolIds"))
    html = open(os.path.join(WEB, "index.html"), encoding="utf-8").read()
    problemas = []
    sin_aprobar = [eq["slug"] for eq in equipos
                   if eq["slug"] not in ESCUDOS_APROBADOS]
    if sin_aprobar:
        problemas.append(
            "ESCUDOS SIN CHEQUEO DE MARCAS (%d): %s\n"
            "   -> abri Resources/Escudos/<slug>.png, verifica que sea la\n"
            "      parodia y no un escudo real, y sumalo a ESCUDOS_APROBADOS."
            % (len(sin_aprobar), ", ".join(sin_aprobar)))
    for eq in equipos:
        if len(eq["ids"]) != 6 or len(set(eq["ids"])) != 6:
            problemas.append("PLANTEL ROTO en %s: %s"
                             % (eq["nombre"], eq["ids"]))
        afuera = [i for i in eq["ids"] if i not in pool]
        if afuera or eq["gk"] not in gks:
            problemas.append("ID FUERA DEL POOL en %s: %s"
                             % (eq["nombre"], afuera or eq["gk"]))
        # la ficha dibuja los retratos: un jugador sin aprobar en la web se
        # veria como figurita vacia en la mini-cancha
        sin_retrato = [i for i in eq["ids"] + [eq["gk"]]
                       if i not in APROBADOS]
        if sin_retrato:
            problemas.append("SIN RETRATO EN LA WEB, %s: %s"
                             % (eq["nombre"], ", ".join(sin_retrato)))
        if ("assets/equipos/%s.webp" % eq["slug"]) not in html:
            problemas.append("SIN TARJETA EN index.html: %s (%s)"
                             % (eq["slug"], eq["nombre"]))
        else:
            problemas += _tarjeta_desfasada(html, eq)
    # ¿algun escudo huerfano en el juego que el catalogo no usa?
    import glob as _glob
    en_disco = {os.path.basename(p)[:-4]
                for p in _glob.glob(os.path.join(ESCUDOS_SRC, "*.png"))}
    huerfanos = en_disco - {eq["slug"] for eq in equipos}
    if huerfanos:
        problemas.append("ESCUDOS SIN EQUIPO en Resources/Escudos: %s"
                         % ", ".join(sorted(huerfanos)))
    if problemas:
        print("\n" + "=" * 70)
        print("CATALOGO DE EQUIPOS INCOMPLETO")
        print("=" * 70)
        for p in problemas:
            print(" - " + p)
        print("=" * 70)
        return False
    print("equipos: %d, todos aprobados y en el index" % len(equipos))
    return True


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
    # M172 — la caja sorpresa en el círculo central, los dos equipos alrededor.
    # Sale de `PocSimCajas.FotoCajas` (foto ESCENIFICADA de los props, no un
    # frame de sim): los jugadores están en poses de idle, no en T-pose, así
    # que no le cabe la advertencia de arriba. Es 700px y se muestra a mitad
    # de columna, donde alcanza y sobra.
    ("m172_caja_tv", "caja-sorpresa"),
    # La pantalla ELEGIR EQUIPOS (25-ago-2026). NO va recortada a 16:9 como las
    # otras: es un menu y recortarlo se come la fila de arriba y la de abajo.
    # Entra por SHOTS —y no como .webp suelto en assets/img, que es como estuvo
    # hasta hoy— por la misma razon que el still del hero: un binario que el
    # build no regenera es un binario que nadie puede rehacer sin adivinar de
    # donde salio.
    # ⚠️ Sale de un screenshot del juego y hay que RECORTARLE DOS COSAS antes de
    # dejarlo en captures/, las dos del 12-ago y las dos volvieron a aparecer:
    #   · el sello de build de abajo a la derecha (es una nota de produccion);
    #   · la barra de ayuda del MENU PRINCIPAL, que se filtra abajo de la del
    #     selector y se lee como un error de render.
    # En la captura de M210 (2478x1534) las dos se van con crop 2478x1476 desde
    # 0,0: la barra dorada del selector termina en y=1474 exacto.
    ("web_selector_still", "selector-equipos"),
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


# ── retratos para la pizarra: el gris del estudio se vuelve sólido ───────────
# Los retratos del álbum viven sobre tarjetas oscuras y el gris del render no
# molesta; sobre el VERDE de la mini-cancha ese mismo gris se lee como un
# círculo SEMITRANSPARENTE (bug report de Rodrigo, 12-ago: "están con
# opacidad"). No hay opacidad ninguna — es el fondo del retrato. Acá se
# reemplaza por el sólido oscuro del panel (#1C231C, el mismo `background` que
# el CSS le pone al círculo) y la ficha queda sólida de verdad.
#
# ⚠️ FLOOD-FILL DESDE LOS BORDES, no umbral global: el gris del fondo (~#3a)
# cae en el rango de las barbas y el pelo oscuro, y un umbral por valor le
# haría agujeros a la cara. Lo que se pinta es lo CONECTADO al borde, que es
# la definición de "fondo". Sembrado cada 40 px por los cuatro lados porque
# los brazos en T parten el fondo en regiones que un solo corner no alcanza.
PIZARRA_OUT = 240
PIZARRA_FONDO = (28, 35, 28)    # #1C231C


def build_pizarra():
    for src, slug in ROSTER:
        p = os.path.join(CAPS, src + "_check_front.png")
        if not os.path.exists(p):
            print("  FALTA", p)
            continue
        im = Image.open(p).convert("RGB")
        im = im.crop(ventana_del_busto(im))
        fondo = im.getpixel((2, 2))
        seeds = ([(x, y) for x in range(1, im.width, 40)
                  for y in (1, im.height - 2)]
                 + [(x, y) for y in range(1, im.height, 40)
                    for x in (1, im.width - 2)])
        for xy in seeds:
            px = im.getpixel(xy)
            if all(abs(a - b) <= 26 for a, b in zip(px, fondo)):
                ImageDraw.floodfill(im, xy, PIZARRA_FONDO, thresh=26)
        im = im.resize((PIZARRA_OUT, PIZARRA_OUT), Image.LANCZOS)
        im.save(out("assets", "pizarra", slug + ".webp"),
                "WEBP", quality=84, method=6)
    print("pizarra: %d retratos con fondo solido" % len(ROSTER))


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
    problemas, notas = [], []
    if SIN_APROBAR:
        problemas.append(
            "SIN CHEQUEO DE MARCAS (%d): %s\n"
            "   -> abri game-unity/captures/<id>_check_front.png, HACE ZOOM A LA\n"
            "      CAMISETA (escudos de clubes, sponsors) y si esta limpia sumalo a\n"
            "      APROBADOS. Ver README seccion 'Chequeo de marcas'."
            % (len(SIN_APROBAR), ", ".join(SIN_APROBAR)))
    # LOS CHOQUES DE SLUG NO SON UNA FALLA: SON UNA NOTA. Estuvieron en `problemas`
    # hasta el 26-ago-2026 y eso dejaba el build ROJO PARA SIEMPRE — `SLUGS_CONGELADOS`
    # existe justamente para que la derivacion NO coincida, asi que cada congelado
    # garantiza un choque en cada corrida. Un build que siempre termina en rojo deja de
    # ser una senal: el que lo mira aprende a ignorar la salida, y el dia que hay un
    # problema de verdad queda enterrado entre seis avisos que ya sabe que no importan.
    # Se siguen imprimiendo —la informacion sirve— pero ya no tumban la corrida.
    for i, congelado, derivado in SLUG_CHOQUES:
        notas.append(
            "SLUG CONGELADO: '%s' se publica como '%s' y de `NombreDe` ahora sale "
            "'%s'." % (i, congelado, derivado)
            + SALTO + "   Se publica el viejo A PROPOSITO, para no romper la URL. Si"
            + SALTO + "   querés que la URL siga al nombre: sacalo de SLUGS_CONGELADOS"
            + SALTO + "   y meté el viejo en ALIAS_SLUG (js/roster.js), que sostiene"
            + SALTO + "   los links que ya andan dando vueltas.")
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
    for n in notas:
        print(" · " + n)
    print("album: %d jugadores, todos aprobados y en el index (%d slug congelado)"
          % (len(ROSTER_JUEGO), len(notas)))
    return True


if __name__ == "__main__":
    build_brand()
    build_roster()
    build_pizarra()
    build_roster_json()
    equipos = build_equipos_json()
    build_escudos(equipos)
    sedes = build_sedes(equipos)
    build_shots()
    ok = auditar_album()
    ok = auditar_equipos(equipos) and ok
    ok = auditar_sedes(sedes) and ok
    with open(out("assets", "roster", "roster.json"), encoding="utf-8") as f:
        ok = auditar_contadores(equipos, sedes, json.load(f),
                                json.load(open(out("assets", "equipos",
                                                   "equipos.json"),
                                               encoding="utf-8"))["ligas"]) and ok
    print("listo")
    # ⚠️ sale con error DESPUES de generar todo: los assets quedan igual, pero el
    # que corrio esto se entera. Un album incompleto que termina en verde es
    # exactamente como se perdieron doce jugadores durante tres dias.
    sys.exit(0 if ok else 1)
