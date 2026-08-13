# fulbito-game-website

Sitio de **Fulbito: The Game** — fútbol arcade 7v7, gratis.
En vivo: **https://game.fulbito.futbol**

Sitio estático, sin build step. Se sirve tal cual desde GitHub Pages (branch `main`, root).

```
index.html      la one-page entera
css/            variables.css (tokens) + site.css
js/             releases.js (descargas, contador y eventos GA) + main.js (motion)
                + pelota3d.js (la pelota) + roster.js (filtros del álbum, foil de los
                cromos y la ficha) + equipos.js (la pizarra del DT)
vendor/         three.js (sólo lo usa la pelota 3D, se carga diferido)
assets/ball/    teamgeist.glb
assets/img/     capturas del juego (WebP)
assets/roster/  retratos del plantel, 480x480 (WebP) + roster.json (la ficha)
assets/firmas/  los tres retratos grandes de las jugadas firma, 720x720
assets/brand/   mark de la pelota, favicons, og-image, fulbito.ico
assets/audio/   cuatro clips del relator
assets/video/   los tres clips de gameplay (ver abajo)
tools/          build_assets.py — regenera TODO lo binario de assets/
```

## Cómo publicar un build nuevo del juego

Las descargas de la web salen del **último release de este repo** (`releases/latest`),
leído en vivo por `js/releases.js`. Publicar un build nuevo = crear el release; la web
se actualiza sola, sin tocar HTML.

```powershell
# 1) empaquetar (en el repo del juego, game-unity)
pwsh tools/pack_release.ps1 -Version M79

# 2) publicar (los assets salen de game-unity/dist/)
gh release create M79 -R rodrigoestrellac/fulbito-game-website `
  --title "Fulbito M79" --notes-file notas.md `
  dist/FulbitoSetup-M79.exe dist/Fulbito-M79-windows.zip dist/Fulbito-M79-mac.zip dist/CHECKSUMS.txt
```

`releases.js` reconoce los assets por nombre: `*Setup*.exe` → Windows instalador,
`*windows*.zip` → Windows portable, `*mac*.zip` → macOS, `CHECKSUMS.txt` → checksums.
Si cambian esos patrones, actualizar `js/releases.js`.

**Fallback**: si la API de GitHub falla o llega al rate limit (60 req/h por IP), la web
usa los datos hardcodeados en `FALLBACK` dentro de `js/releases.js`. Conviene actualizar
ese bloque cuando se publica una versión nueva (es una constante, 4 líneas).

## ⚠️ El copy habla del JUEGO, nunca del estado del sitio

Regla dura, porque ya se coló tres veces: **nada de lo que se lee en la página puede ser
una nota de producción**. El visitante vino a ver un juego, no el avance de la obra.

Lo que hubo que sacar el 30-jul-2026:

- «Acá va el clip de una firma en acción» — un recordatorio para nosotros, publicado.
- «Ya están los veintiocho. El último en entrar fue Rober» — a nadie le importa el orden
  en que se hicieron los retratos.
- «28 retratados · álbum completo» — contaba **assets del sitio**, no jugadores. Ahora
  dice «26 de campo · 2 arqueros», que es un dato del juego.

El caso difícil es cuando el estado SÍ le sirve al visitante: «Beta — se empaquetó desde
Windows y no lo probó nadie en un Mac de verdad» se queda, porque es una advertencia que
cambia lo que la persona va a hacer. La diferencia no es el tema, es a quién le habla.

## Clips de gameplay

Los cuatro huecos declarados en el HTML (cada uno con un `data-video`) ya tienen clip. El
`<video>` se monta encima de la captura, en la misma caja y sin salto de layout; la
captura se queda debajo como respaldo.

| archivo | sección | qué muestra | dura | crop |
|---|---|---|---|---|
| `assets/video/hero.mp4` | hero | juego de mitad de cancha — es fondo detrás del wordmark | 4,7 s | `1500:844:400:280` |
| `assets/video/gol.mp4` | El gol | vaselina de Il Divino, palo, adentro y confeti | 4,2 s | `1728:972:288:138` |
| `assets/video/firma.mp4` | firmas | El Martillazo: el rayo y dos rivales aplastados | 2,7 s | `1400:788:452:250` |
| `assets/video/cajas.mp4` | cajas sorpresa | cuatro tramos: cae una caja, cancha inclinada, Pierluigi comprado y el colectivo | 14,7 s | `1728:972:288:138` |

El de cajas es el único **concatenado**: cuatro tramos de ~3,7 s de momentos distintos del
mismo partido, pegados con `-f concat -c copy`. Va con el crop ancho porque ahí el
**cartel del juego es el contenido**: sin «¡PIERLUIGI SE PUSO LA CAMISETA!» el tramo del
árbitro es un muñequito amarillo cualquiera. Ojo que el cartel muestra lo último que pasó,
no el efecto: en el tramo del colectivo dice «¡SUPER TIRO!» y cosas así. Es charla del
juego, no un error.

Además del archivo hay que agregar su nombre al array `CLIPS` de `js/main.js` (una línea).
Es a propósito: sondear con `HEAD` dejaba errores 404 en la consola.

### Cómo se graba

Game Bar (`Win+Alt+R`) o OBS, **1080p60 como mínimo**. Un tiempo de 15 minutos alcanza
para sacar los tres. Grabar **con audio** aunque los clips van muteados: sirve para ubicar
los momentos escuchando al relator.

⚠️ **La Game Bar viene de fábrica en 30 fps y encima pierde frames.** La primera grabación
salió con **27,6 fps reales** y espaciado de 15 a 50 ms — se veía a los saltos contra los
165 Hz del monitor. Se arregla en Configuración → Juegos → Capturas (ya no está en el
overlay `Win+G`): **Velocidad de fotogramas → 60 fps** y **Calidad → Alta**. Con eso la
misma máquina dio 53,9 fps y 59 Mbps. Conviene medirlo antes de cortar nada:

```bash
ffprobe -v error -select_streams v:0 \
        -show_entries stream=avg_frame_rate,nb_frames \
        -show_entries format=duration -of default=noprint_wrappers=1 crudo.mp4
```

`avg_frame_rate` es el dato: el `r_frame_rate` del contenedor **miente** (declaraba 120).
La captura del 12-ago-2026 dio **52,6 fps reales** con `r_frame_rate=120`. Los clips salen
igual a `-r 60` como el resto, para no tener dos cadencias distintas en la misma página.

### Capturas de pantalla de menús (`.pantalla`)

`assets/img/selector-equipos.webp` — la pantalla ELEGIR EQUIPOS, en LOS EQUIPOS. **No** va
recortada a 16:9 como las bandas: es un menú, y recortarlo se come justo la fila de arriba
y la de abajo. Clase `.pantalla`, con el ancho natural y un epígrafe en tiza.

Dos cosas que hubo que sacarle, y que van a volver a aparecer en cualquier captura de menú:

- **El sello de build** abajo a la derecha (decía `vM176`, y el sitio publica M174). Es una
  nota de producción publicada — mismo pecado que la sección de más arriba.
- **La barra de ayuda del menú principal**, que se filtra abajo de la del selector. Es del
  juego, pero se lee como un error de render.

Las dos se van con `crop=2304:1348:0:0`. Y conviene sacarla de la **grabación**, no de un
screenshot del reproductor: el JPG que llegó tenía la barra de controles encima.

### ⚠️ Lo que hay que mirar ANTES de cortar (capturas del 12-ago-2026)

Los cuatro clips salen de **dos** grabaciones distintas del 12-ago: `16-44-43` (7:10) da el
hero, el gol y las cajas; `18-29-07` (3:54) da la firma. Cuando llega un timestamp hay que
preguntar de cuál, porque los dos archivos empiezan en 00:00 y los rangos se parecen.

Y los timestamps que llegan «del 5:12 al 5:20» casi nunca son la toma. En esas capturas:

- **La cámara se mueve adentro del rango.** El colectivo estaba pedido de 5:12 a 5:20 y
  recién entra en cuadro a los **5:14,2**. Sacar una tira de contacto del rango (un frame
  por segundo) antes de cortar cuesta diez segundos y ahorra rehacer el clip.
- **Los primeros segundos son la placa de formaciones.** El «gameplay desde 00:07»
  arrancaba con el cartel FULBITO / PARTIDO AMISTOSO: el juego empieza a los **09 s**.
- **Hay frames oscuros.** A los 14,5 s la pantalla se oscurece porque alguien carga una
  firma. En un loop de fondo eso es un parpadeo.
- **La cámara se abre.** De los 18 s en adelante entra media tribuna, que es justo lo que
  no queremos en el hero.
- **El póster no siempre conviene sacarlo del clip.** Para el hero sí (es la regla). Para
  el gol no: el frame 0 del clip nuevo es un plano lejano con media tribuna, y la foto que
  ya estaba — desde atrás del arco, con el arquero — cuenta mejor la sección. Lo mismo con
  la foto de la caja sorpresa: en esta grabación la caja siempre queda chica y lejos.
- **La firma cortada trae OTRA firma de fondo.** En el clip del Martillazo se ve una torre
  blanca a la derecha: es «La Cerca», que alguien tiró un segundo antes. Es gameplay real
  y el epígrafe habla del martillo, así que queda — pero conviene saberlo antes de que
  alguien pregunte qué es esa escalera.

### El crop del hero bajó a `1500:844:400:280`

El `1600:900:352:215` del hero viejo mete **público** arriba, y en un teléfono eso ocupa el
primer 15 % de la pantalla — `object-fit: cover` sobre un contenedor alto y angosto recorta
en HORIZONTAL, así que se ve el alto completo del cuadro y `object-position` en Y no
arregla nada. La ventana bajó hasta que arriba queda sólo la línea de carteles, que hace
de horizonte. El piso lo pone el **minimapa del HUD, que arranca en y≈1125**: 280+844=1124
pasa por un píxel. Si alguna vez se sube el alto del crop, mirar el borde de abajo.

### El cartel de la jugada y la píldora del jugador se pisan

El crop del gol (`y=155`) parte al medio la píldora del jugador que manejás, que en esta
captura cae en **y≈152-175**, justo abajo del marcador (que termina en y≈148) y encima del
cartel de la jugada (y≈165-190). No hay corte que deje el cartel y saque la píldora: se
pisan. Para el clip de cajas la ventana subió a **y=138**, que deja las dos enteras y el
marcador afuera.

### Cómo se cortan

```bash
ffmpeg -ss 00:02:16.8 -t 5.4 -i crudo.mp4 -an -c:v libx264 -preset slow -crf 26 \
       -pix_fmt yuv420p -vf "crop=1728:972:288:155,scale=1280:720" -r 60 \
       -movflags +faststart assets/video/gol.mp4
```

Dos cosas que no son obvias:

- **El `crop` saca el HUD.** El juego no tiene tecla para ocultarlo, y medio marcador
  cortado por el `object-fit: cover` se lee como un error de la página. `1728:972:288:155`
  deja afuera el marcador (termina en y=150), el minimapa y las barras de abajo, y
  **conserva los carteles** («¡¡GOLAAAZO!!», «¡EL MARTILLAZO!»), que empiezan justo
  debajo. El hero y la banda de firmas llevan recortes más cerrados —`1600:900:352:215` y
  `1400:788:452:250`— porque ahí no hay cartel que valga la pena preservar y sí está la
  píldora del jugador que manejás, que pegada al borde se lee como cortada. En la banda de
  firmas el epígrafe ya nombra la jugada, así que el cartel del juego sobraba.
- **El monitor es 16:10** (2560×1600), así que la grabación sale 16:10 y el `crop` la
  lleva a 16:9. No es que la captura esté mal encuadrada.

No hace falta generar un `.jpg` de póster: `montarVideos` usa como `poster` la `<img>` que
ya está en el HTML, que además ya está descargada. Un `.jpg` aparte sería una request de más.

⚠️ **El still del hero sale del mismo clip** (`captures/web_hero_still.png`, con el mismo
crop) para que no se vea el salto de encuadre cuando entra el video.

## ⚠️ Chequeo de marcas — OBLIGATORIO antes de publicar cualquier imagen o video

Nada donde se lea una marca registrada puede publicarse. El caso testigo fue `rc3b`
(Rober): tenía **el escudo del Real Madrid y el logo de adidas horneados en la textura**,
y por eso estuvo fuera del álbum hasta que se re-texturizó el 30-jul-2026. Que un modelo
ya se haya revisado una vez no sirve de nada — las texturas cambian.

Antes de commitear una imagen o un video nuevo:

1. Abrirlo y **hacer zoom a las camisetas**, una por una.
2. Si aparece un escudo o logo real → descartar la toma (o rearmar los equipos sin ese
   modelo antes de capturar).
3. **Nunca** publicar `captures/kitroster.png` ni derivados.
4. En el copy, alt-texts y **nombres de archivo**: sólo los apodos in-game
   (EL VIKINGO, IL CAPITANO, EL MOTORCITO…), nunca los apellidos reales.

La textura de `rc3b` se limpió el 30-jul-2026 y Rober entró al álbum. Se verificó con
zoom sobre el render, no sobre la palabra de nadie: la limpieza de una textura no exime
del chequeo.

## Deploy

Push a `main` → GitHub Pages deploya solo. Custom domain `game.fulbito.futbol` (CNAME en
el repo) + Enforce HTTPS. DNS: `CNAME game → rodrigoestrellac.github.io` en `fulbito.futbol`.

## De dónde salen las capturas — y por qué las primeras estaban mal

Las tres capturas que estuvieron publicadas hasta el 30-jul-2026 (el fondo del hero,
"El gol" y la banda de jugadas firma) salían de `PocSetup.SimPostFxAB`, que es el
**A/B de post-proceso**: abre la escena en modo editor y renderiza. En modo editor no
corre el loop de Unity — ningún `Animator` tickea, el director no avanza y la física
está quieta. O sea que esas capturas mostraban la escena **congelada en su pose de
bind**, y por eso:

- todos los jugadores en T-pose,
- el arquero parado en vez de volando,
- nadie pateando,
- y la pelota en el punto del medio: la sección "El gol" no tenía ni un gol.

Encima eran de 720p (el resto ya estaba en 2560x1440), así que además se veían blandas
en pantalla retina. Las dos cosas se leían juntas como "está pixelado", pero eran dos
problemas distintos y el grave era el primero.

Ahora salen de **`PocSetup.SimWeb`**, que corre el partido de verdad — el mismo loop
que `SimMatch`: tickea el director, simula la física a mano y llama `Animator.Update`
uno por uno — y dispara **atado a lo que pasa** en vez de a un frame fijo:

```
Unity.exe -batchmode -quit -projectPath <FulbitoPenales> -executeMethod PocSetup.SimWeb
```

Deja unas 40 capturas en `captures/web_*` a 2560x1440 con MSAA 8; sirven tres. Los
grupos son `web_tiro_*` (remate en vuelo: el único instante donde el arquero está
estirado de verdad), `web_golazo_*` (la ráfaga alrededor del gol), `web_tv_*` (el plano
de transmisión, para el hero) y `web_cerca_*` (contrapicado).

⚠️ **`SimWeb` no es reproducible frame a frame.** Usa un seed fijo, pero la física
y la evaluación de animaciones no son deterministas entre corridas: dos ejecuciones
del mismo código dan el mismo partido a grandes rasgos y fotos distintas. O sea que
`web_tv_08.png` **no es un identificador estable** — el PNG elegido es la fuente de
verdad, no su nombre. Si hace falta rehacer el sitio tal cual está, no alcanza con
volver a correr el sim.

⚠️ **Al elegir, descartar los frames de saque.** Con el juego detenido el blend tree
queda en `Speed = 0` y los jugadores aparecen con los brazos en cruz. Hay que quedarse
con frames de **pelota en movimiento** — se chequea con zoom, igual que las marcas.

Las que se eligieron están en `SHOTS`, en `tools/build_assets.py`. Las `m15_menu_bg`,
`m3_save_5` y `m7_match_mid` vienen de otros sims que ya corrían el juego y están bien.

## Los retratos del álbum

Salen de `captures/<tag>_check_front.png`, que hasta julio de 2026 se hacían **a mano**
en Blender durante el riggeo de cada modelo. Los cinco modelos que se integraron después
(Dinho, El Motorcito, Samu, Zlatan, El Pupi) nunca tuvieron el suyo, y en la web eso se
veía como huecos en el álbum. Ahora los genera un script:

```
blender -b --factory-startup -P assets-src/render_check_front.py        # los que faltan
blender -b --factory-startup -P assets-src/render_check_front.py -- zizou   # uno puntual
```

El recorte del busto **se mide** sobre cada render (`ventana_del_busto`) en vez de usar
una ventana fija en píxeles, así conviven los renders viejos y los nuevos en la misma
grilla sin descuadrarse.

Rober fue el último de los 28 originales: su modelo (`chibi_rc3b`) era el único con el
escudo y el logo horneados, y entró cuando se re-texturizó.

### ⚠️ El álbum se DERIVA del juego (3-ago-2026) — antes era una lista a mano

**El álbum se había quedado en 28 jugadores mientras el juego tenía 50, y nadie lo
notó.** Faltaban los DOCE de M92 (desde el 1-ago) y los DIEZ de M94. La causa era que
`ROSTER` en `tools/build_assets.py` se escribía a mano: una lista que tiene que decir lo
mismo que otra y que nada comparaba. Es el mismo bug que en el repo del juego costó a La
Tortuga (`BluePoolIds` vs. los cuerpos de la escena, M92g), y falla igual de mal — **en
silencio**, porque un álbum incompleto se ve tan bien como uno completo.

Ahora los candidatos **salen del juego** (`MatchTuning.BluePoolIds` + `GkPoolIds`) y el
slug se **deriva de `NombreDe`**. Sumar un jugador al juego lo mete en la lista solo.

**Pero no se publica solo, y eso es deliberado.** El chequeo de marcas de más arriba es
manual a propósito: si el álbum fuera 100% automático, un modelo nuevo con el escudo de
un club se publicaría sin que nadie lo haya mirado — cambiaríamos un bug silencioso
(falta gente) por uno peor (se publica lo que no se revisó). Por eso son **dos piezas**:

1. la lista se deriva del juego;
2. cada id tiene que estar en **`APROBADOS`**, que es la firma de *"yo miré este retrato
   con zoom"*.

Un id sin aprobar **no se publica** y el script **avisa fuerte y termina con error**, en
vez de faltar calladito. Lo mismo si a alguien le falta el `<li>` en `index.html`:
generar el `.webp` no alcanza — sin la figurita en el HTML, en el sitio no se ve.
`auditar_album()` compara **las tres listas** (plantel del juego · `APROBADOS` · grilla
del `index.html`) al final de cada corrida.

⚠️ **`SLUGS_CONGELADOS`**: los slugs ya publicados son URLs vivas. Como el slug ahora
sale de `NombreDe`, cambiarle el apodo a un jugador en el juego renombraría su archivo y
rompería enlaces y SEO sin que nadie lo pida. Los 28 publicados quedan congelados: si la
derivación deja de coincidir, el script lo dice y sigue publicando el viejo. Renombrar
una URL tiene que ser una decisión, no un efecto secundario.

**Estado: los 52** (48 de campo + 4 arqueros). Los 22 que entraron el 3-ago pasaron el
chequeo de marcas con zoom al torso: todos con el kit magenta liso de Meshy, sin escudo
ni sponsor. El único que asustaba era **El Faraón** por las rayas azul/oro — pero es el
**nemes**, el tocado de faraón, no una camiseta. Iceman y El General (M111, 5-ago)
pasaron el mismo chequeo: kit magenta liso los dos.

### La grilla va EN EL ORDEN DEL JUEGO (5-ago-2026)

Cada cromo muestra su número (`figu__num`, lo pone roster.js) y el número es el índice
en `BluePoolIds` + `GkPoolIds` — el orden del juego, con los arqueros al final. La
grilla del HTML está en ESE orden: con números visibles, un álbum desordenado se lee
como un error. Si se agrega un jugador, su `<li>` va donde el juego lo ponga (o sea:
regenerá la grilla, no la agregues al final "para que quede cerca").

### roster.json — la ficha con los stats del juego (5-ago-2026)

Al tocar un cromo se abre una **ficha** (dialog nativo, roster.js) con la jugada firma,
una descripción y los ocho stats del jugador. Nada de eso está escrito a mano:

- **stats**: `build_assets.py` parsea los `P("id", …)` de `MatchTuning.cs` — con la
  compresión del techo de velocidad de M65 replicada, porque el multiplicador escrito no
  es el que juega — y los normaliza a 40–99 con min-max por atributo sobre el plantel.
- **firma por jugador**: sale del switch del HUD en `MatchDirector.cs`
  (`"id" => "LA FIRMA (F)"`), la única lista del juego que las nombra todas. (La web
  decía que El Kuni tenía "El Fenómeno"; su firma es "EL KUNI". Ese bug ya no puede
  volver.)
- Todo va a `assets/roster/roster.json`, que se regenera en cada corrida.

Lo único editorial son las **descripciones de las 39 firmas** (`FIRMAS_DESC` en
`js/roster.js`): el juego no las tiene escritas. Citan números de `MatchTuning.cs` —
si una firma cambia de duración o radio, esa línea se toca a mano.

⚠️ `roster.js` se carga con `type="module"` a propósito: aísla el scope (main.js ya
declara `menosMovimiento` y un segundo `const` global rompería TODO el JS de la página
con un SyntaxError).

Para agregar un jugador nuevo al álbum:

```
# 1) el retrato, en el repo del juego
blender -b --factory-startup -P assets-src/render_check_front.py -- <id>
# 2) MIRARLO CON ZOOM (escudos, sponsors) y recién ahí sumarlo a APROBADOS
# 3) el <li> en index.html   ·   4) correr build_assets.py: tiene que dar VERDE
python tools/build_assets.py
```

## Los equipos — el catálogo, la pizarra y los escudos (12-ago-2026)

Desde M153 el juego se juega POR EQUIPOS: un catálogo de 27 con nombre, concepto,
formación, arquero y barras VEL/FUE/PRE. La sección LOS EQUIPOS del sitio se deriva
entera del juego, con el mismo contrato que el álbum:

- **`assets/equipos/equipos.json`**: `build_assets.py` parsea `Equipos.Catalogo`,
  `EscudoId`, `AbrevId` y `MatchTuning.Formations` (con los SLOTS reales de cada
  esquema — de ahí sale la mini-cancha de la ficha, no de un dibujito).
- **Las barras se RECALCULAN** con la réplica exacta de `Equipos.Barra()` (z contra el
  pool de campo, σ/√6, escala 15, clamp 10–95). Verificada contra la salida real de
  `PocEquipos.SimEquipos`: 27/27 exactos. Si dudás, corré `tools/verificar_barras.py`
  con un log fresco de SimEquipos — un DIFF ahí significa que la réplica quedó vieja.
- **Escudos**: `Resources/Escudos/*.png` → `assets/equipos/*.webp`. Mismo mecanismo de
  chequeo de marcas que el álbum: cada slug tiene que estar en `ESCUDOS_APROBADOS` o el
  build termina en error. Son las parodias de `gen_escudos.py`; la regla es que el
  escudo dibuja el CONCEPTO, nunca la marca de un club real.
- **La grilla es estática** (barras incluidas, con `--v` inline): sin JS se ve todo.
  `js/equipos.js` (module, como roster.js) sólo AGREGA la pizarra: el dialog con la
  formación real y los retratos del álbum parados en sus slots.
- `auditar_equipos()` grita si un equipo no tiene tarjeta en el HTML, si un id del
  catálogo no tiene retrato aprobado, o si hay escudos huérfanos.

Para un equipo nuevo en el juego: correr `build_assets.py`, mirar el escudo nuevo con
zoom, sumarlo a `ESCUDOS_APROBADOS`, y agregar su tarjeta en `index.html` (el build
dice exactamente qué falta).

## La pelota y el ícono

Son dos cosas distintas y salen de fuentes distintas.

### La pelota del hero — 3D, viva

Al lado de FULBITO **rebota y gira despacio la pelota Teamgeist en 3D**: el mismo
modelo (`assets/ball/teamgeist.glb`) y el mismo gesto que el hero de `fulbito.futbol`.
Lo monta `js/pelota3d.js` con three.js.

Es una **mejora progresiva**, no la base. `js/main.js` la importa recién después del
`load` y en idle, y sólo si conviene: sin `prefers-reduced-motion`, con WebGL de verdad
(chequeado en ese momento, no al evaluar el script — en un arranque en frío la GPU puede
no estar lista) y sin ahorro de datos ni conexión 2G. Si cualquiera de esas falla, queda
`assets/brand/pelota.webp` — un render estático del mismo modelo — y el hero se ve igual.
three.js + el modelo son ~1,4 MB: **eso no puede pesar en el primer paint**, y por eso no
está en el HTML.

**El pique va entre el baseline de FULBITO y el alto de las letras**: apoya en el baseline y
en el punto más alto su tope llega a la altura de las mayúsculas, sin pasarse. Eso no está
estimado —

- el piso: `.wordmark__caja` no lleva `align-self` ni `margin-bottom`, así que el contenedor
  la alinea por baseline y, siendo un bloque sin texto adentro, su borde inferior **es** el
  baseline del título;
- el techo: la altura de mayúscula se **mide** con `actualBoundingBoxAscent` de una «F» en la
  tipografía real, después de `document.fonts.ready`. Hace falta medirla porque el
  `font-size` es fluido (clamp) y porque con la tipografía de respaldo la métrica es otra.

De ahí sale todo el encuadre, en vez de constantes a ojo: la cámara se ubica en
`(H/d) / tan(fov/2)` y la pelota reposa a un radio del borde de abajo del lienzo. Un
`ResizeObserver` lo recalcula cuando cambia el tamaño, y la animación se detiene cuando
el hero sale de pantalla o la pestaña pasa a segundo plano.

Dos números que no son geometría sino ojo, y que hacen falta:

- **`AIRE` (7 % del diámetro)**. El lienzo NO puede medir `diámetro + recorrido` exacto.
  La primera versión lo hacía y la pelota **se cortaba en el pico**: la silueta de una
  esfera en perspectiva es más grande que su radio geométrico proyectado —el contorno
  visible abarca `asin(r/d)`, no `atan(r/d)`—. Son pocos píxeles, pero pasan justo donde
  se mira.
- **`BAJADA` (7 % del diámetro)**. El punto de apoyo va un poco por debajo del baseline:
  apoyada exactamente sobre la línea parece que flota, porque el ojo lee el contacto en
  la sombra y no en la tangente de la esfera. El mismo 7 % está en CSS sobre la `<img>`
  de respaldo, para que el fallback estático quede a la misma altura.

⚠️ El recorrido es **corto**: la pelota mide ~80 % del alto de las letras, así que entre las
dos líneas quedan unos **36 px en desktop y 14 en mobile**. Si se quisiera un pique más
grande, la palanca es el `width` de `.wordmark__caja` — una pelota más chica deja más
recorrido.

Para regenerar el PNG estático: servir el repo, abrir `http://localhost:8899/tools/render3d/`
y guardar `window.PELOTA_PNG` como `tools/pelota-fuente.png`; después `build_assets.py` lo
recorta al alfa y lo escala.

**Licencia**: el modelo es «Adidas Teamgeist Ball (Germany 2006)» de Armellino Raffaele
(Sketchfab), **CC BY 4.0** → atribución obligatoria, está en el footer. Las texturas ya
venían editadas: **verificado que los PNG del GLB traen sólo las formas de los paneles,
sin logos ni estrellas.**

### El favicon y el `.ico` del instalador — el logo de la app + «The Game»

`tools/build_icono.py` toma el **ícono de la app** (`fulbito/src/assets/icons/icon-512.webp`:
baldosa verde, anillo dorado, Teamgeist blanca), le recorta el interior con máscara circular
—si no, se arrastra un parche cuadrado del verde y queda un borde adentro de otro— y le
agrega **«The Game» manuscrito** en Caveat, la misma letra de la firma del footer.

⚠️ **Arte distinta por tamaño**: a 16 y 32 px un texto manuscrito es una mancha y encima le
roba lugar a la pelota, que es lo único que identifica algo a ese tamaño.

| tamaño | qué lleva |
|---|---|
| 16 / 32 / 48 px | el logo solo, sin texto |
| 180 / 256 px | el logo + «The Game» |

Por eso el `.ico` **se escribe a mano** (cabecera + directorio + PNG concatenados): PIL sólo
sabe reescalar *una* imagen a todos los tamaños, no meter arte distinta en cada uno.

Al cambiar el ícono hay que copiarlo al repo del juego:
`cp assets/brand/fulbito.ico ../game-unity/installer/`

<details>
<summary>Camino descartado: generar la pelota con Gemini</summary>

`tools/gen_logo.py` genera variantes de logo con `gemini-3-pro-image` (usa
`GOOGLE_AI_API_KEY` del `.env` de la app; **~USD 0.15 por imagen**, ~0.04 con
`--flash`). Salen a `tools/logo_candidatos/`, que está en `.gitignore`.

Se probaron siete. La mejor (`1-pelota-arcade`) estuvo un rato en el sitio y se cayó
por dos motivos: **no era la Teamgeist** y, con esos paneles curvos anchos, **leía como
pelota de vóley**. También se descartaron un lockup con el texto (el wordmark en CSS es
texto real: escala, se indexa y lo lee un lector de pantalla) y un escudo, que parecía
badge de club — justo lo que el sitio evita. El script queda por si sirve para otra cosa.
</details>

## Tipografías — self-hosteadas (5-ago-2026)

Oswald 500/700, DM Sans 400/500 y Caveat 600 se sirven desde `assets/fonts/` (woff2,
subset latin) vía `css/fonts.css`. Antes venían de fonts.googleapis.com: dos preconnect,
una request de terceros en el camino crítico y la IP de cada visitante contada a Google.
Para regenerar (p.ej. si se suma un peso): pedir
`https://fonts.googleapis.com/css2?family=…&display=swap` con un User-Agent de Chrome,
bajar los woff2 del bloque `/* latin */` de cada cara y reescribir `css/fonts.css` con
los mismos `unicode-range`.

## El contador de descargas

`releases.js` pide `/releases?per_page=100` (mismo costo de rate limit que
`/releases/latest`) y suma el `download_count` de todos los `.exe`/`.zip` de todas las
versiones — CHECKSUMS.txt no cuenta. Se muestra en dos lugares:

| hueco | dónde | condición |
|---|---|---|
| `[data-rel="descargas"]` | sección de descarga, frase completa | `total > 0` |
| `[data-rel="descargas-zoc"]` + `[data-rel="descargas-n"]` | zócalo del hero, sólo el número | `total >= UMBRAL_HERO` (100) |

**Sin dato de la API los dos quedan ocultos**: no hay número hardcodeado porque
envejecería mintiendo. El **umbral del hero** es aparte y es a propósito: ahí arriba el
número es prueba social, y «10 descargas» en la primera pantalla prueba lo contrario.
Abajo del umbral el dato igual se lee completo en la sección de descarga, donde es
información y no argumento.

## Eventos de descarga (GA)

GA estaba cargado desde el primer día pero **ningún click disparaba evento**: no había
forma de saber qué porcentaje baja el juego ni desde qué botón. `releases.js` engancha
**un solo listener en `document`, en fase de captura** — tiene que ser así porque el
propio `releases.js` reescribe la lista de descargas entera y los botones que había al
cargar dejan de existir.

| evento | cuándo | parámetros |
|---|---|---|
| `descarga` | click en cualquier `a[href*="/releases/"]` | `tipo` (`win-setup`/`win-zip`/`mac`/`checksums`/`generico`), `desde` (`hero`/`marcador`/`lista`/`otro`), `archivo` |
| `cta_inline` | click en cualquier `a[href="#descargar"]` | `desde` = el `<h2>` de la sección donde está el botón, o `pie` |

`cta_inline` es lo que dice **cuál de los dos tramos convence**: hay un botón al final de
LOS EQUIPOS y otro al final de MODOS.

## ⚠️ Las tipografías están SUBSETEADAS: ojo con los signos raros

`css/fonts.css` declara `unicode-range: … U+2000-206F …` pero el .woff2 **no trae todo
ese rango**. Y como el rango está declarado, el navegador no cae al fallback del sistema:
dibuja tofu (▯). Pasó el 12-ago-2026 con la comilla curva `“` (U+201C) de las citas.

Lo que SÍ anda y ya está usado en la página: `« »` (U+00AB/BB), `—` (U+2014), `·`, `→`.
Antes de meter un signo nuevo, mirá el render — no alcanza con que exista en Unicode.

## ⚠️ El reveal: `.rev` va en los HIJOS de una grilla, nunca en la grilla

`main.js` observa los `.rev` con un `IntersectionObserver`. El **12-ago-2026** se
descubrió que LOS EQUIPOS **no se veía nunca en un teléfono**: la clase estaba sobre la
`<ul class="equipos">` entera, que en mobile medía 9.406 px. Con `threshold: 0.08` el
observer pedía 752 px visibles y el root recortado (`rootMargin: -12%`) dejaba como
máximo 743. **Nueve píxeles** — y en un iPhone SE moría también el álbum. Medido:
38 pantallas de scroll con una sección entera en negro.

Dos reglas, las dos:

1. `.rev` va en **cada tarjeta**, no en el contenedor de la grilla (así lo hacía el
   álbum desde siempre con su cascada `--i`).
2. `threshold: 0`, porque cualquier fracción de un bloque alto puede no entrar en la
   pantalla. La regla no puede depender del alto del bloque.

Cuidado al mover `.rev` a un elemento que ya declara su propio `transition` **más abajo
en site.css**: le gana al de `.rev` y la tarjeta aparece de golpe, sin opacidad. `.equipo`
lo resuelve con `.equipo.rev` / `.equipo.rev.dentro` (especificidad doble).

## Deep-link de la ficha

Cada cromo tiene URL: `#cromo/<slug>` (p.ej. `#cromo/el-vikingo`). Se escribe con
`replaceState` — no con `location.hash` — para que el historial no se llene con cada
flecha: volver atrás sale de la página, no repasa 52 cromos. Al cerrar la ficha el hash
se limpia. Llegar con el hash puesto abre la ficha sola sobre el álbum.

## El orden de las secciones no está numerado (y por eso se puede mover)

Hasta el 12-ago-2026 cada sección tenía un **chip de minuto** (`data-min="27'"`, pintado
por `.minuto[data-min]::before`). Se fueron todos menos el `90+` del pie, por dos razones:

- **Nunca coincidían con el reloj vivo del header.** Parado sobre CAJAS SORPRESA el header
  marcaba 16' y el sello 27'. Dos relojes en pantalla que se desmienten se leen como
  error, no como metáfora — y como los sellos eran estáticos no había forma de
  sincronizarlos.
- **Clavaban el orden**: mover una sección obligaba a renumerar todas.

El `90+` del pie se queda porque es el único que siempre acierta: el scroll efectivamente
llegó al final. El chip sólo se pinta si hay `data-min`, así que para sacar otro alcanza
con borrar el atributo.

Al mover una sección hay que **recalcular el `seccion--suave`**: los fondos alternan una
sí y una no, y dos gradientes pegados se ven como un error de render.

## ⚠️ La sección de modos TAMBIÉN es una lista que se desincroniza

El menú real vive en `MenuDirector.cs` (game-unity, el array de tuplas al principio).
El 5-ago-2026 la web decía "Seis modos" y el juego tenía SIETE — faltaba la COPA
FULBITO, que existe desde M85. Al tocar el menú del juego, actualizar la sección MODOS
**y** la meta description. (Es la misma clase de bug que el
álbum 28 vs 50; esta lista sigue siendo a mano porque son siete renglones con copy
propio, pero el chequeo es: contar los ítems del array y contar los `<li>` del menú.)

**Y no alcanza con contar los renglones: el TEXTO de cada uno también envejece.** El
13-ago-2026 la web decía *"Copa Fulbito · 8 equipos — cuartos, semifinal y final"* y hacía
rato que la COPA v2 son **16**, con fase de grupos antes del cuadro (`Copa.cs`:
`NEq = 16, NGrupos = 4, PorGrupo = 4, Fechas = 3`). Además se juega de a dos
(`MenuCopa.cs`, fila JUGADORES), y la web decía "1 mando o teclado". Cuando dudes de un
número del copy, el número está en una constante del juego — buscalo ahí, no en el
plan ni en el commit viejo que lo escribió.

## Legal

Proyecto personal, sin fines comerciales. No está afiliado ni autorizado por ningún club,
jugador, marca ni liga.
