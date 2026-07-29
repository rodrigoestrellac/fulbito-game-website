# fulbito-game-website

Sitio de **Fulbito: The Game** — fútbol arcade 7v7, gratis, hecho a mano.
En vivo: **https://game.fulbito.futbol**

Sitio estático, sin build step. Se sirve tal cual desde GitHub Pages (branch `main`, root).

```
index.html      la one-page entera
css/            variables.css (tokens) + site.css
js/             releases.js (descargas dinámicas) + main.js (motion)
assets/img/     capturas del juego (WebP)
assets/roster/  retratos de los jugadores (WebP)
assets/brand/   wordmark, favicons, og-image
assets/video/   clips de gameplay (opcional, ver abajo)
tools/          scripts de generación de assets
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

`js/main.js` chequea con un `HEAD` si el archivo existe y recién ahí monta el `<video>`.
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

## Legal

Proyecto personal, sin fines comerciales. No está afiliado ni autorizado por ningún club,
jugador, marca ni liga. Pelota Teamgeist: modelo CC-BY (atribución en el footer).
