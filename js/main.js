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
    reloj.textContent = avance >= 0.995 ? "90+'" : `${min}'`;
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
const CLIPS = [];   // p.ej.: ['hero.mp4', 'gol.mp4']

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
    v.addEventListener('canplay', () => { if (poster) poster.remove(); }, { once: true });
    hueco.appendChild(v);
  });
}
montarVideos();
