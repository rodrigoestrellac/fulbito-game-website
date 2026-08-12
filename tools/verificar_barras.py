#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compara las barras de `assets/equipos/equipos.json` contra la salida REAL
del juego, que es la única verdad sobre lo que el jugador ve en el selector.

    1. genera el log con el juego:
       Unity.exe -batchmode -quit -projectPath <FulbitoPenales> \
                 -executeMethod PocEquipos.SimEquipos -logFile sim.log
    2. python tools/build_assets.py
    3. python tools/verificar_barras.py sim.log

La réplica de `Equipos.Barra()` vive en `build_assets.py` (`_eje` +
`barras_del_catalogo`) y este script existe porque esa réplica puede quedar
vieja EN SILENCIO: si mañana el juego cambia los pesos de un eje o la escala,
la web publica barras que el selector no muestra y nada grita. Última corrida
en verde: 27/27 exactos (12-ago-2026).
"""
import io
import json
import os
import re
import sys

WEB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if len(sys.argv) != 2:
    print(__doc__)
    sys.exit(2)

data = json.load(open(os.path.join(WEB, "assets", "equipos", "equipos.json"),
                      encoding="utf-8"))
ref = {}
for linea in io.open(sys.argv[1], encoding="utf-8", errors="replace"):
    m = re.match(r"\[EQUIPO\] (.+?)\s+(\S+)\s+GK (.+?)\s+VEL\s+(\d+)"
                 r"\s+FUE\s+(\d+)\s+PRE\s+(\d+)", linea)
    if m:
        ref[m.group(1).strip()] = (m.group(2), int(m.group(4)),
                                   int(m.group(5)), int(m.group(6)))
if not ref:
    print("!! el log no trae lineas [EQUIPO] — ¿corriste PocEquipos.SimEquipos?")
    sys.exit(2)

diffs = 0
for eq in data["equipos"]:
    juego = ref.pop(eq["nombre"], None)
    web = (data["formaciones"][eq["form"]]["name"],
           eq["vel"], eq["fue"], eq["pre"])
    if juego != web:
        print("DIFF %-25s juego: %s  web: %s" % (eq["nombre"], juego, web))
        diffs += 1
for sobra in ref:
    print("EN EL JUEGO Y NO EN LA WEB:", sobra)
    diffs += 1
print("%d equipos comparados — %d diferencias" % (len(data["equipos"]), diffs))
sys.exit(1 if diffs else 0)
