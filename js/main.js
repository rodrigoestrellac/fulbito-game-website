/* main.js — el scroll es el reloj del partido.
   Todo lo de acá es progresivo: sin JS la página se ve entera igual (la clase
   .no-js del <html> deja los reveals visibles), y con prefers-reduced-motion no
   se anima nada — el reloj sigue andando porque es un dato, no una animación. */

document.documentElement.classList.remove('no-js');

const menosMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ── Reveals ─────────────────────────────────────────────────────────────── */
if ('IntersectionObserver' in window && !menosMovimiento) {
  const obs = new IntersectionObserver((entradas) => {
    entradas.forEach((e) => {
      if (!e.isIntersecting) return;
      e.target.classList.add('dentro');
      obs.unobserve(e.target);
    });
  }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });
  document.querySelectorAll('.rev').forEach((el) => obs.observe(el));
} else {
  document.querySelectorAll('.rev').forEach((el) => el.classList.add('dentro'));
}

/* los cromos entran en cascada: cada uno sabe su lugar en la fila. El delay
   lo aplica el CSS (cromo-entra) y solo si hay motion. */
document.querySelectorAll('.album .figu').forEach((el, i) => el.style.setProperty('--i', i));

/* ── Marcador fijo + reloj ───────────────────────────────────────────────── */
const marcador = document.querySelector('.marcador');
const reloj = document.querySelector('[data-reloj]');
const hero = document.querySelector('.hero');

let pendiente = false;
function alScrollear() {
  const y = window.scrollY;

  if (marcador && hero) {
    marcador.classList.toggle('visible', y > hero.offsetHeight * 0.72);
  }

  if (reloj) {
    const recorrible = document.documentElement.scrollHeight - window.innerHeight;
    const avance = recorrible > 0 ? Math.min(1, Math.max(0, y / recorrible)) : 0;
    const min = Math.round(avance * 90);
    const nuevo = avance >= 0.995 ? "90+'" : `${min}'`;
    if (nuevo !== reloj.textContent) {
      reloj.textContent = nuevo;
      // el latido de minuto nuevo: sacar la clase y forzar reflow para que la
      // animación pueda volver a arrancar (el dato cambia igual sin motion)
      if (!menosMovimiento) {
        reloj.classList.remove('tic');
        void reloj.offsetWidth;
        reloj.classList.add('tic');
      }
    }
  }
  pendiente = false;
}
function pedirScroll() {
  if (pendiente) return;
  pendiente = true;
  requestAnimationFrame(alScrollear);
}
window.addEventListener('scroll', pedirScroll, { passive: true });
window.addEventListener('resize', pedirScroll);
alScrollear();

/* ── El relator: audio SÓLO con clic, uno por vez ────────────────────────── */
let sonando = null;
document.querySelectorAll('[data-voz]').forEach((boton) => {
  boton.addEventListener('click', () => {
    const src = boton.dataset.voz;

    if (sonando && sonando.audio.dataset.src === src && !sonando.audio.paused) {
      sonando.audio.pause();
      sonando.boton.setAttribute('aria-pressed', 'false');
      sonando = null;
      return;
    }
    if (sonando) {
      sonando.audio.pause();
      sonando.boton.setAttribute('aria-pressed', 'false');
    }

    const audio = new Audio(src);
    audio.dataset.src = src;
    audio.play().catch((e) => console.info('[relator] no arrancó:', e.message));
    boton.setAttribute('aria-pressed', 'true');
    sonando = { audio, boton };
    audio.addEventListener('ended', () => {
      boton.setAttribute('aria-pressed', 'false');
      if (sonando && sonando.audio === audio) sonando = null;
    });
  });
});

/* ── Clips de gameplay ────────────────────────────────────────────────────
   Todavía no hay clips grabados. Cuando los haya: se dejan los MP4 en
   assets/video/ y se agrega el nombre del archivo a CLIPS. El <video> reemplaza
   solo a la captura, sin tocar el HTML.

   ⚠️ Antes esto sondeaba con un HEAD a cada archivo, pero un 404 queda igual
   anotado en la consola aunque el JS lo maneje — dos errores rojos en una
   página que no tiene ninguno. Una lista explícita es más barata y más clara.
   Ver README § Clips de gameplay. */
const CLIPS = ['hero.mp4', 'gol.mp4', 'firma.mp4'];

function montarVideos() {
  if (menosMovimiento || !CLIPS.length) return;
  document.querySelectorAll('[data-video]').forEach((hueco) => {
    const src = hueco.dataset.video;
    if (!CLIPS.some((f) => src.endsWith(f))) return;

    const poster = hueco.querySelector('img');
    const v = document.createElement('video');
    v.src = src;
    v.muted = true; v.loop = true; v.autoplay = true;
    v.playsInline = true; v.preload = 'none';
    if (poster) v.poster = poster.currentSrc || poster.src;
    /* ⚠️ La <img> SE QUEDA. Antes esto la borraba en `canplay`, y el bug estuvo
       latente hasta el primer clip de verdad: en las bandas la altura de la caja
       la da la <img> (`.banda__img { aspect-ratio: 16/9 }`), porque el <video>
       es `position: absolute; inset: 0` y no ocupa lugar en el layout. Borrarla
       colapsaba la seccion a ALTURA CERO — y de paso Chrome pausa un video que
       no esta visible, asi que ni siquiera se reproducia.
       Dejarla ademas es gratis: el <video> la tapa (los dos son `object-fit:
       cover` sobre la misma caja) y si el clip falla a mitad de camino, la
       captura sigue ahi debajo. */
    hueco.appendChild(v);
  });
}
montarVideos();

/* ── La pelota 3D del hero ────────────────────────────────────────────────
   three.js + el modelo son ~1,4 MB: eso NO puede pesar en el primer paint. Se
   importa despues del load y en idle, y solo si conviene:
     - sin prefers-reduced-motion (con eso queda la imagen, quieta)
     - con WebGL de verdad (el chequeo se hace aca, no al evaluar el script: en
       un arranque en frio la GPU puede no estar lista todavia)
     - sin ahorro de datos ni conexion lenta
   Si algo de esto falla, queda el PNG del render y el hero se ve igual. */
function pelota3DConviene() {
  if (menosMovimiento) return false;
  const con = navigator.connection;
  if (con && (con.saveData || /(^|-)2g$/.test(con.effectiveType || ''))) return false;
  try {
    const c = document.createElement('canvas');
    return !!(c.getContext('webgl2') || c.getContext('webgl'));
  } catch { return false; }
}

function cargarPelota3D() {
  const caja = document.getElementById('pelota3d');
  if (!caja || !pelota3DConviene()) return;
  // v2 = la pelota dorada de la final (los colores medidos del juego). El
  // parámetro es sólo versionado de caché: al cambiar la pelota, subirlo.
  import('./pelota3d.js?v=2')
    .then((m) => m.montarPelota3D(caja, caja.querySelector('img'),
                                  document.querySelector('.wordmark__texto')))
    .catch((e) => console.info('[pelota3d] queda la imagen:', e.message));
}

const enCuantoSePueda = window.requestIdleCallback || ((fn) => setTimeout(fn, 300));
if (document.readyState === 'complete') enCuantoSePueda(cargarPelota3D);
else window.addEventListener('load', () => enCuantoSePueda(cargarPelota3D), { once: true });
