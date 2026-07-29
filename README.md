# fulbito-game-website

Sitio de **Fulbito: The Game** — fútbol arcade 7v7, gratis, hecho a mano.
En vivo: **https://game.fulbito.futbol**

Sitio estático, sin build step. Se sirve tal cual desde GitHub Pages (branch `main`, root).

```
index.html      la one-page entera
css/            variables.css (tokens) + site.css
js/             releases.js (descargas dinámicas) + main.js (motion)
assets/img/     capturas del juego (WebP)
assets/roster/  retratos del plantel, 480x480 (WebP)
assets/firmas/  los tres retratos grandes de las jugadas firma, 720x720
assets/brand/   mark de la pelota, favicons, og-image, fulbito.ico
assets/audio/   cuatro clips del relator
assets/video/   clips de gameplay (opcional, ver abajo)
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

## Clips de gameplay (opcional)

El hero y las secciones de features funcionan **con capturas solas**. Si en algún momento
hay clips grabados (Game Bar / OBS, 1080p60), se activan solos al dejarlos acá:

| archivo | dónde entra |
|---|---|
| `assets/video/hero.mp4` | fondo del hero (reemplaza la imagen) |
| `assets/video/gol.mp4` | feature "el momento del gol" |
| `assets/video/firma.mp4` | feature "jugadas firma" |
| `assets/video/penal.mp4` | feature "penales" |

Además del archivo, hay que agregar su nombre al array `CLIPS` de `js/main.js`
(una línea). Es a propósito: sondear con `HEAD` dejaba errores 404 en la consola.
Formato: H.264, **sin audio** (`-an`), `-crf 26`, ancho 1280, y un `poster` `.jpg` al lado
con el mismo nombre. Presupuesto total de video de la página: **≤ 15 MB**.

```bash
ffmpeg -i crudo.mp4 -an -c:v libx264 -crf 26 -vf scale=1280:-2 -movflags +faststart assets/video/gol.mp4
ffmpeg -i assets/video/gol.mp4 -vframes 1 -q:v 4 assets/video/gol.jpg
```

## ⚠️ Chequeo de marcas — OBLIGATORIO antes de publicar cualquier imagen o video

El modelo `rc3b` del juego tiene **el escudo del Real Madrid y el logo de adidas horneados
en la textura**. Nada donde se lea una marca registrada puede publicarse.

Antes de commitear una imagen o un video nuevo:

1. Abrirlo y **hacer zoom a las camisetas**, una por una.
2. Si aparece un escudo o logo real → descartar la toma (o rearmar los equipos sin ese
   modelo antes de capturar).
3. **Nunca** publicar `captures/kitroster.png` ni derivados.
4. En el copy, alt-texts y **nombres de archivo**: sólo los apodos in-game
   (EL VIKINGO, IL CAPITANO, EL MOTORCITO…), nunca los apellidos reales.

Pendiente del lado del juego (no bloquea la web): limpiar la textura de `rc3b`.

## Deploy

Push a `main` → GitHub Pages deploya solo. Custom domain `game.fulbito.futbol` (CNAME en
el repo) + Enforce HTTPS. DNS: `CNAME game → rodrigoestrellac.github.io` en `fulbito.futbol`.

## El ícono del instalador

`assets/brand/fulbito.ico` lo genera el mismo script y es el que usa el instalador
del juego (`game-unity/installer/fulbito.iss`, `SetupIconFile`). Si se cambia el mark,
hay que volver a copiarlo: `cp assets/brand/fulbito.ico ../game-unity/installer/`.

## Por qué las capturas se veían pixeladas

`PocSetup.ShotWithCam` (repo del juego) renderizaba a **1280x720 sin antialias**. En una
pantalla de 1440 CSS px con devicePixelRatio 2 eso se estira al doble, y el outline de 1 px
del shader toon queda escalonado. El 29-jul-2026 se subió a **2560x1440 con MSAA 8**, pero
las capturas que ya estaban en `captures/` siguen en 720p: para regenerar las de una escena
hay que volver a correr su sim en Unity (`PocSetup.SimPostFxAB` para las `postfx_*`,
`PocSetup.SimFirmas` para las `m24n_*`).

Mientras tanto, el sitio evita el problema: ninguna captura se muestra a más ancho del que
tiene, las tarjetas de jugadas firma usan los **retratos** (renders limpios) en vez de la
jugada en acción, y el hero le aplica un desenfoque graduado a la tribuna — que es una
textura de sprites de baja resolución — para que lea como profundidad de campo.

## El mark de la pelota

`assets/brand/pelota.webp` sale de `tools/pelota-fuente.png`, que lo generó **Gemini**
(`gemini-3-pro-image`) con `tools/gen_logo.py` — variante `1-pelota-arcade`. El modelo
lo devuelve sobre un fondo magenta plano y `build_assets.py` lo recorta por croma,
erosionando un pixel el alfa para matar el fleco del antialias.

Para probar otras variantes: `python tools/gen_logo.py` (usa `GOOGLE_AI_API_KEY` del
`.env` de la app; **cuesta ~USD 0.15 por imagen** con el modelo pro, ~0.04 con
`--flash`). Los candidatos van a `tools/logo_candidatos/`, que está en `.gitignore`.
Cuando se elige uno, se copia a `tools/pelota-fuente.png` y se corre `build_assets.py`.

⚠️ Los prompts describen el patrón de paneles **sin nombrar ninguna marca**, y la
variante de escudo se descartó justamente porque parecía un badge de club. Mismo
criterio que el resto del sitio (ver § Chequeo de marcas).

Alternativa disponible: el mark de línea que usa la app
(`fulbito/src/assets/teamgeist.png`, ícono de Javier Flowers / Noun Project). Para
volver a él, apuntar `MARK_SRC` ahí y poner `MARK_CHROMA = False` en `build_assets.py`
— y reponer el crédito en el footer.

## Legal

Proyecto personal, sin fines comerciales. No está afiliado ni autorizado por ningún club,
jugador, marca ni liga.
