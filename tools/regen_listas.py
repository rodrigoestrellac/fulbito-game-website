#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reescribe las TRES grillas de `index.html` desde los JSON derivados del juego.

    python tools/build_assets.py      # 1) los JSON, desde game-unity
    python tools/regen_listas.py      # 2) los <li>, desde los JSON
    python tools/build_assets.py      # 3) tiene que dar VERDE

Por que existe
--------------
El ALBUM, el CATALOGO de equipos y las SEDES son HTML estatico a proposito: sin JS la
pagina se ve entera. Pero eso las convierte en TRES LISTAS QUE TIENEN QUE DECIR LO MISMO
QUE EL JUEGO, y a mano se desincronizan en silencio — la web publico durante semanas
cuatro formaciones viejas, un equipo con el nombre viejo, EL CEREBRO con la firma que
tenia antes de M194, y cuatro conceptos de los que el juego ya se habia despegado
JUSTAMENTE para sacar un nombre real.

Y hay un modo de falla peor, que es el que obliga a regenerar TODO y no solo lo que
cambio: **las barras VEL/FUE/PRE son z-scores contra el pool de campo**. Un jugador
nuevo en el juego mueve las 37 tarjetas, incluidas las de equipos que nadie toco.

`_tarjeta_desfasada` (en build_assets.py) es el detector; esto es la cura.

⚠️ Reescribe SOLO lo que hay adentro de los tres contenedores. Lo demas del index.html
(bajadas, contadores, secciones) NO lo toca: ese copy es editorial y se corrige a mano
— lo audita `auditar_contadores` en build_assets.py.
"""
import io
import json
import os
import re
import sys

WEB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(WEB, "index.html")

NL = "\n"


def titulo(s):
    """`D'ARTAGNAN` -> `D'Artagnan`, `EN GARDE` -> `En Garde`.

    ⚠️ No alcanza con `.title()` de Python: la regla que se quiere es *sube la primera
    letra de cada palabra Y la que sigue a un apostrofo*, que es la misma que aplica
    `componer()` en roster.js. Se escribe una sola vez para que las dos coincidan.
    """
    out = []
    for palabra in s.split(" "):
        p = palabra[:1].upper() + palabra[1:].lower()
        p = re.sub(r"(’|')(\w)", lambda m: m.group(1) + m.group(2).upper(), p)
        out.append(p)
    return " ".join(out)


def esc(s):
    """El apostrofo va como entidad porque asi quedo publicado (18-ago) y un
    diff de entidades no es un cambio de contenido."""
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace("'", "&#x27;"))


def miles(n):
    return "{:,}".format(n).replace(",", ".")


# ============================================================================
# EL CATALOGO — agrupado por liga (M197 en el juego, 25-ago-2026 en la web)
# ============================================================================
# El criterio de cada liga, en una linea. Es EDITORIAL —el juego lo tiene solo como
# comentario en `Equipos.cs`— pero no es inventado: sale de ahi, del bloque "EL CRITERIO
# ES DE ORIGEN, NO DE CALIDAD NI DE ESTILO". Si manana entra una liga nueva, `li_equipos`
# TERMINA CON ERROR en vez de publicar el titulo pelado.
LIGA_QUE = {
    "EQUIPOS": "los clubes: el nombre es inventado, el plantel es el de verdad",
    "SELECCIONES": "los países, armados con los que de verdad juegan ahí",
    "COMBINADOS FULBITO": "los inventados: se arman por una idea, no por un escudo",
}


def tarjeta_equipo(eq, formas, nombres):
    gk = titulo(nombres.get(eq["gk"], eq["gk"]))
    barras = "".join(
        '<div><dt><abbr title="%s">%s</abbr></dt>'
        '<dd><i style="--v:%d"></i><b>%d</b></dd></div>' % (largo, corto, v, v)
        for largo, corto, v in (("Velocidad", "VEL", eq["vel"]),
                                ("Fuerza", "FUE", eq["fue"]),
                                ("Precisión", "PRE", eq["pre"])))
    return (
        '            <li class="equipo rev">' + NL +
        '              <img class="equipo__escudo" src="assets/equipos/%s.webp"'
        ' alt="Escudo de %s" width="128" height="128" loading="lazy">' + NL +
        '              <h3 class="equipo__nombre">%s</h3>' + NL +
        '              <p class="equipo__concepto">%s</p>' + NL +
        '              <p class="equipo__meta"><b>%s</b>'
        ' <span aria-hidden="true">·</span> %s al arco</p>' + NL +
        '              <dl class="equipo__barras">%s</dl>' + NL +
        '            </li>'
    ) % (eq["slug"], esc(titulo(eq["nombre"])), esc(eq["nombre"]),
         esc(eq["concepto"]), formas[eq["form"]]["name"], esc(gk), barras)


def bloques_ligas(datos):
    """Las 37 tarjetas AGRUPADAS POR LIGA, en el orden en que el selector del juego
    cicla las ligas (`Equipos.LigaNombre` = EQUIPOS · SELECCIONES · COMBINADOS
    FULBITO). Ese orden no es alfabetico ni por tamano: es el del juego, y la web lo
    copia por la misma razon que copia todo lo demas.

    ⚠️ ADENTRO DE CADA LIGA SE RESPETA EL ORDEN DEL CATALOGO, y no es un detalle: el
    numero que muestra la pizarra es el indice en `Equipos.Catalogo` y `copa.json`
    guarda ESOS indices. Agrupar es una decision de RENDER; el dato no se reordena
    (por eso `equipos.json` sigue en orden de catalogo).
    """
    formas = datos["formaciones"]
    nombres = {j["id"]: j["nombre"] for j in roster()}
    bloques = []
    for i, liga in enumerate(datos["ligas"]):
        delaliga = [e for e in datos["equipos"] if e["liga"] == i]
        if not delaliga:
            sys.exit("!! la liga %r no tiene ni un equipo — en el juego eso rompe el "
                     "selector en silencio, ver Equipos.Validar()" % liga)
        que = LIGA_QUE.get(liga)
        if not que:
            sys.exit("!! falta la linea de la liga %r en LIGA_QUE "
                     "(tools/regen_listas.py)" % liga)
        tarjetas = NL.join(tarjeta_equipo(e, formas, nombres) for e in delaliga)
        bloques.append(
            '        <section class="liga">' + NL +
            '          <h3 class="liga__titulo rev">%s'
            ' <span class="liga__n">%d</span></h3>' % (esc(liga), len(delaliga)) + NL +
            '          <p class="liga__que rev">%s</p>' % esc(que) + NL +
            '          <ul class="equipos">' + NL + tarjetas + NL +
            '          </ul>' + NL +
            '        </section>')
    return NL.join(bloques)


# ============================================================================
# LAS SEDES
# ============================================================================
def li_sedes(sedes):
    """Las ocho tarjetas, ORDENADAS POR AFORO de mayor a menor.

    ⚠️ El orden ES el contenido y por eso no es el del arreglo `Todos`: la regla del
    juego es que la final se juega en la sede jugable con MAS gente
    (`Estadios.MasGrande`) y el potrero en la de menos (`MasChica`). Puestas de mayor a
    menor, la primera y la ultima tarjeta explican las dos reglas sin que haya que
    escribirlas. Si manana entra una sede mas grande, se muda la final Y se muda la
    tarjeta.

    La reglita (`--v`) es el aforo contra el de la sede mas grande, con la misma
    tecnica que las barras de los equipos. Sirve para lo que el numero solo no dice: EL
    MUNICIPAL entra nueve veces adentro de MARACUYA.
    """
    vivas = [s for s in sedes if s["lista"]]
    vivas.sort(key=lambda s: -s["aforo"])
    tope = vivas[0]["aforo"]
    filas = []
    for sd in vivas:
        marca = ""
        if sd["final"]:
            marca = "Acá se juega la final"
        elif sd["potrero"]:
            marca = "Acá se juega el potrero"
        marca_html = ((NL + '          <p class="sede__marca">%s</p>' % esc(marca))
                      if marca else "")
        alt = "Vista aérea de %s, lleno: %s" % (sd["nombre"], sd["concepto"])
        filas.append(
            ('        <li class="sede rev">' + NL +
             '          <img class="sede__foto" src="assets/sedes/%s.webp"'
             ' alt="%s" width="1280" height="720" loading="lazy">%s' + NL +
             '          <h3 class="sede__nombre">%s</h3>' + NL +
             '          <p class="sede__concepto">%s</p>' + NL +
             '          <p class="sede__aforo"><b>%s</b> hinchas'
             '<i style="--v:%d" aria-hidden="true"></i></p>' + NL +
             '          <p class="sede__locales">'
             '<span class="sede__locales-tit">De local</span> %s</p>' + NL +
             '        </li>')
            % (sd["slug"], esc(alt), marca_html, esc(sd["nombre"]),
               esc(sd["concepto"]), miles(sd["aforo"]),
               round(100 * sd["aforo"] / tope),
               esc(" · ".join(sd["equipos"]))))
    return NL.join(filas)


# ============================================================================
# EL ALBUM
# ============================================================================
def li_album(jugadores):
    filas = []
    for j in jugadores:
        nombre = esc(titulo(j["nombre"]))
        if j["gk"]:
            pos = ('<span class="figu__pos" data-pos="ARQ" aria-hidden="true">'
                   'ARQ</span>')
            alt, firma = "Retrato de %s, arquero" % nombre, "Arquero"
        else:
            pos, alt, firma = "", "Retrato de %s" % nombre, esc(titulo(j["firma"]))
        filas.append(
            '        <li class="figu">%s<img src="assets/roster/%s.webp"'
            ' alt="%s" width="360" height="360" loading="lazy">'
            '<div class="figu__pie"><span class="figu__nombre">%s</span>'
            '<span class="figu__firma">%s</span></div></li>'
            % (pos, j["slug"], alt, nombre, firma))
    return NL.join(filas)


_ROSTER = None


def roster():
    global _ROSTER
    if _ROSTER is None:
        with io.open(os.path.join(WEB, "assets", "roster", "roster.json"),
                     encoding="utf-8") as f:
            _ROSTER = json.load(f)
    return _ROSTER


def reemplazar(html, apertura, cierre, cuerpo):
    """Cambia lo de adentro del contenedor que abre con `apertura`. Falla fuerte si no
    lo encuentra: un reemplazo que no matchea y sigue de largo deja el HTML viejo
    publicado y el script diciendo 'listo'."""
    i = html.find(apertura)
    if i < 0:
        sys.exit("!! no encontre %r en index.html" % apertura)
    ini = i + len(apertura)
    fin = html.find(cierre, ini)
    if fin < 0:
        sys.exit("!! no encontre el cierre %r de %r" % (cierre, apertura))
    return html[:ini] + NL + cuerpo + NL + html[fin:]


def main():
    with io.open(os.path.join(WEB, "assets", "equipos", "equipos.json"),
                 encoding="utf-8") as f:
        equipos = json.load(f)
    with io.open(os.path.join(WEB, "assets", "sedes", "sedes.json"),
                 encoding="utf-8") as f:
        sedes = json.load(f)
    with io.open(INDEX, encoding="utf-8") as f:
        html = f.read()
    antes = html
    html = reemplazar(html, '<div class="ligas">', "      </div>",
                      bloques_ligas(equipos))
    html = reemplazar(html, '<ul class="sedes">', "      </ul>", li_sedes(sedes))
    html = reemplazar(html, '<ul class="album rev">', "      </ul>",
                      li_album(roster()))
    if html == antes:
        print("index.html ya estaba al dia (%d equipos, %d cromos)"
              % (len(equipos["equipos"]), len(roster())))
        return
    with io.open(INDEX, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    campo = sum(1 for j in roster() if not j["gk"])
    print("index.html reescrito: %d equipos en %d ligas, %d sedes, %d cromos "
          "(%d de campo, %d arqueros)"
          % (len(equipos["equipos"]), len(equipos["ligas"]),
             sum(1 for s in sedes if s["lista"]),
             len(roster()), campo, len(roster()) - campo))


if __name__ == "__main__":
    main()
