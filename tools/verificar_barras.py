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
la web publica barras que el selector no muestra y nada grita.

⚠️ Y la réplica es más grande de lo que parece: no son sólo los pesos de los ejes.
Están la compresión del techo de velocidad (`PaceTopMul`), el dial arcade que
comprime los otros ocho atributos (`ArcadeMul`, M213) y las anclas de la escala
absoluta (`AnclaLo`/`AnclaHi`, que reemplazaron al z-score). Cualquiera de esos
cuatro se puede mover en el juego sin que la web se entere.

Última corrida en verde: 37/37 exactos en las CUATRO barras (26-ago-2026, M213).
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
    # M213 - LA CUARTA COLUMNA. El log ahora trae DEF y este regex NO la pedia:
    # como `re.match` no ancla el final, matcheaba igual y la verificacion habria
    # dado 37/37 sin comparar la barra nueva ni una vez. Un chequeo que ignora una
    # columna es peor que no tenerlo, porque firma lo que no miro.
    m = re.match(r"\[EQUIPO\] (.+?)\s+(\S+)\s+GK (.+?)\s+VEL\s+(\d+)"
                 r"\s+FUE\s+(\d+)\s+PRE\s+(\d+)\s+DEF\s+(\d+)", linea)
    if m:
        ref[m.group(1).strip()] = (m.group(2), int(m.group(4)), int(m.group(5)),
                                   int(m.group(6)), int(m.group(7)))
if not ref:
    print("!! el log no trae lineas [EQUIPO] — ¿corriste PocEquipos.SimEquipos?")
    sys.exit(2)

diffs = 0
for eq in data["equipos"]:
    juego = ref.pop(eq["nombre"], None)
    web = (data["formaciones"][eq["form"]]["name"],
           eq["vel"], eq["fue"], eq["pre"], eq["def"])
    if juego != web:
        print("DIFF %-25s juego: %s  web: %s" % (eq["nombre"], juego, web))
        diffs += 1
for sobra in ref:
    print("EN EL JUEGO Y NO EN LA WEB:", sobra)
    diffs += 1
print("%d equipos comparados — %d diferencias" % (len(data["equipos"]), diffs))
sys.exit(1 if diffs else 0)
