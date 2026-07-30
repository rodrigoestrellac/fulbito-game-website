# fulbito-game-website

Sitio de **Fulbito: The Game** — fútbol arcade 7v7, gratis.
En vivo: **https://game.fulbito.futbol**

Sitio estático, sin build step. Se sirve tal cual desde GitHub Pages (branch `main`, root).

```
index.html      la one-page entera
css/            variables.css (tokens) + site.css
js/             releases.js (descargas) + main.js (motion) + pelota3d.js (la pelota)
vendor/         three.js (sólo lo usa la pelota 3D, se carga diferido)
assets/ball/    teamgeist.glb
assets/img/     capturas del juego (WebP)
assets/roster/  retratos del plantel, 480x480 (WebP)
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

Los tres huecos declarados en el HTML (cada uno con un `data-video`) ya tienen clip. El
`<video>` se monta encima de la captura, en la misma caja y sin salto de layout; la
captura se queda debajo como respaldo.

| archivo | sección | qué muestra | dura |
|---|---|---|---|
| `assets/video/hero.mp4` | hero | juego tranquilo de mitad de cancha — es fondo detrás del wordmark | 6,6 s |
| `assets/video/gol.mp4` | 09', "El gol" | remate, gol, «¡¡GOLAAAZO!!» y confeti | 5,4 s |
| `assets/video/firma.mp4` | 23', firmas | El Martillazo | 3,0 s |

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
  debajo. Para el hero el recorte es más agresivo —`1600:900:352:215`— porque ahí no hay
  cartel que preservar y sí está la píldora del jugador que manejás.
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

El álbum está **completo, los 28**. Rober fue el último: su modelo (`chibi_rc3b`) era el
único con el escudo y el logo horneados, y entró cuando se re-texturizó.

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

## Legal

Proyecto personal, sin fines comerciales. No está afiliado ni autorizado por ningún club,
jugador, marca ni liga.
