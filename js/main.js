/* main.js — el scroll es el reloj del partido.
   Todo lo de acá es progresivo: sin JS la página se ve entera igual (la clase
   .no-js del <html> deja los reveals visibles), y con prefers-reduced-motion no
   se anima nada — el reloj sigue andando porque es un dato, no una animación. */

document.documentElement.classList.remove('no-js');

const menosMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ── Reveals ─────────────────────────────────────────────────────────────── */
/* ⚠️ `threshold: 0` y NO 0.08: el 8 % de una grilla alta es más de lo que entra en
   la pantalla, y entonces el reveal no dispara nunca. Pasó de verdad — con `.rev`
   sobre la <ul> de LOS EQUIPOS (9.406 px en mobile) el 8 % pedía 752 px visibles y el
   root recortado (`rootMargin: -12%`) dejaba 743: nueve píxeles por los que la sección
   entera no existía en un teléfono. Ahora `.rev` va por tarjeta y no por grilla, pero
   el umbral queda en 0 igual: la regla no puede depender del alto del bloque. */
if ('IntersectionObserver' in window && !menosMovimiento) {
  const obs = new IntersectionObserver((entradas) => {
    entradas.forEach((e) => {
      if (!e.isIntersecting) return;
      e.target.classList.add('dentro');
      obs.unobserve(e.target);
    });
  }, { rootMargin: '0px 0px -12% 0px', threshold: 0 });
  document.querySelectorAll('.rev').forEach((el) => obs.observe(el));
} else {
  document.querySelectorAll('.rev').forEach((el) => el.classList.add('dentro'));
}

/* ── Carriles: poderes, equipos y sedes ──────────────────────────────────
   El deslizamiento es CSS (scroll-snap, ver site.css § CARRILES); esto sólo
   suma lo que el CSS no puede:
   - las flechas, para el mouse (la rueda no desliza de costado). El CSS las
     muestra sólo con `pointer: fine`, y se apagan en cada punta del carril.
   - el reveal de las tarjetas que arrancan fuera de la pantalla. El observer de
     arriba mira cada una contra la ventana, y una tarjeta tapada por el
     overflow del carril NO intersecta: aparecería recién al deslizar, a media
     opacidad debajo del dedo. Acá entran todas juntas cuando entra el carril.
   - foco de teclado y nombre para los carriles que no tienen nada enfocable
     adentro (sedes, poderes): sin eso el teclado no los puede deslizar. */
function montarCarriles() {
  const sel = '.poderes, .equipos, .sedes, .firmas';
  document.querySelectorAll(sel).forEach((tira) => {
    const envoltura = document.createElement('div');
    envoltura.className = 'carril';
    tira.parentNode.insertBefore(envoltura, tira);
    envoltura.appendChild(tira);

    // las tarjetas de equipo se vuelven botones en equipos.js (que corre después):
    // el foco ya entra por ellas y el navegador desliza el carril solo
    const sinFoco = !tira.matches('.equipos') && !tira.querySelector('a, button');
    const titulo = tira.closest('section')?.querySelector('h2')?.textContent.trim() || '';

    const flecha = (dir, texto, etiqueta) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = `carril__flecha carril__flecha--${dir}`;
      b.textContent = texto;
      b.setAttribute('aria-label', etiqueta);
      b.tabIndex = -1;   // con teclado se desliza el carril mismo; la flecha es para el mouse
      b.addEventListener('click', () => {
        const paso = Math.max(tira.clientWidth * 0.85, 200) * (dir === 'next' ? 1 : -1);
        tira.scrollBy({ left: paso, behavior: menosMovimiento ? 'auto' : 'smooth' });
      });
      envoltura.appendChild(b);
    };
    flecha('prev', '‹', 'Anteriores');
    flecha('next', '›', 'Siguientes');

    const puntas = () => {
      const max = tira.scrollWidth - tira.clientWidth;
      envoltura.toggleAttribute('data-inicio', tira.scrollLeft <= 4);
      envoltura.toggleAttribute('data-final', tira.scrollLeft >= max - 4);
      // .firmas es carril sólo en angosto: en desktop no tiene que ser una
      // parada de tabulación de más
      if (sinFoco && max > 4 && !tira.hasAttribute('tabindex')) {
        tira.tabIndex = 0;
        tira.setAttribute('role', 'region');
        tira.setAttribute('aria-label', titulo + ' (se desliza de costado)');
      } else if (sinFoco && max <= 4 && tira.hasAttribute('tabindex')) {
        tira.removeAttribute('tabindex');
        tira.removeAttribute('role');
        tira.removeAttribute('aria-label');
      }
    };
    tira.addEventListener('scroll', puntas, { passive: true });
    window.addEventListener('resize', puntas);
    puntas();

    if ('IntersectionObserver' in window && !menosMovimiento) {
      const obs = new IntersectionObserver(([e]) => {
        if (!e.isIntersecting) return;
        tira.querySelectorAll('.rev').forEach((el) => el.classList.add('dentro'));
        obs.disconnect();
      }, { rootMargin: '0px 0px -12% 0px', threshold: 0 });
      obs.observe(tira);
    }
  });
}
montarCarriles();

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
/* 27-oct-2026: regrabados desde el build (game-unity, FULBITO_VIDEO en MatchDirectorRafaga272.cs):
   el inicio y el gol de un partido CPU contra CPU sin tocar la cámara (FULBITO_RAFAGA_LIMPIO), la
   firma con el Martillazo de cerca. Las cajas siguen con la foto: en la grabación la cámara salta
   entre tomas y no quedó un tramo limpio. Para sumarlo: el MP4, su nombre acá y el `data-video`
   de su hueco en index.html. */
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

/* ── Las cajas sorpresa: el tablero de las dieciséis ─────────────────────────
   Un tablist de verdad (flechas, Inicio/Fin, aria-selected) sobre las dieciséis
   fichas, que están TODAS en el HTML. Sin JS se ven en lista; con JS, una por vez
   (`.cajas--vivo`, ver site.css).
   La rotación sola es para el que scrollea sin tocar: avanza cada CAJAS_T, se
   PAUSA con el mouse o el foco adentro, corre sólo con la sección a la vista, y se
   APAGA para siempre en cuanto alguien elige una — que una ficha se le cambie a
   quien la está leyendo es lo peor que puede hacer un carrusel. Con
   prefers-reduced-motion no rota nunca. */
const CAJAS_T = 4500;

function montarCajas() {
  const caja = document.querySelector('.cajas');
  const tiles = caja ? [...caja.querySelectorAll('.caja-tile')] : [];
  if (!tiles.length) return;
  const fichas = tiles.map((t) => document.getElementById(t.getAttribute('aria-controls')));
  caja.classList.add('cajas--vivo');
  caja.style.setProperty('--cajas-t', CAJAS_T + 'ms');
  let actual = 0, timer = null, visible = false, encima = false, tocada = false;

  /* 27-oct-2026 — LA FOTO ES LA DE LA CAJA ELEGIDA. Rodrigo: «una captura del efecto de cada
     caja, que cambie al tocar cada una. Tiene que estar bien optimizado para desktop y mobile».
     Cada caja tiene su foto del juego en dos anchos (assets/img/cajas-efecto/<id>-960.webp y
     -1600.webp, ver tools/build_assets.py) y el navegador elige con `srcset`/`sizes`.
     ⚠️ No se baja ninguna hasta que la sección está a la vista, y después sólo la elegida y la
     siguiente (la que va a mostrar la rotación). La nueva se decodifica ANTES de ponerla
     (`decode()`), así el cambio no parpadea en blanco; si el usuario ya eligió otra mientras
     cargaba, la vieja se descarta. */
  const foto = caja.querySelector('.cajas__foto');
  const idDe = (k) => tiles[k].id.replace('caja-t-', '');
  const SIZES = '(max-width: 760px) 100vw, 56vw';
  const srcset = (id) => `assets/img/cajas-efecto/${id}-960.webp 960w, assets/img/cajas-efecto/${id}-1600.webp 1600w`;
  const precargada = new Set();
  const precargar = (k) => {
    const id = idDe((k + tiles.length) % tiles.length);
    if (precargada.has(id)) return;
    precargada.add(id);
    const im = new Image(); im.sizes = SIZES; im.srcset = srcset(id);
  };
  let pedida = '';
  const mostrarFoto = (k) => {
    if (!foto || !visible) return;
    const id = idDe(k);
    if (pedida === id) return;
    pedida = id;
    const im = new Image(); im.sizes = SIZES; im.srcset = srcset(id);
    const poner = () => {
      if (pedida !== id) return;
      foto.sizes = SIZES; foto.srcset = srcset(id);
      foto.alt = 'En el juego: ' + tiles[k].querySelector('.visually-hidden').textContent;
    };
    (im.decode ? im.decode() : Promise.resolve()).then(poner, poner);
    precargar(k + 1);
  };

  const elegir = (i, foco) => {
    actual = (i + tiles.length) % tiles.length;
    tiles.forEach((t, k) => {
      const si = k === actual;
      t.setAttribute('aria-selected', si ? 'true' : 'false');
      t.tabIndex = si ? 0 : -1;
      fichas[k].classList.toggle('es-actual', si);
      fichas[k].hidden = false;   // la visibilidad la maneja la clase (transición)
      fichas[k].setAttribute('aria-hidden', si ? 'false' : 'true');
    });
    if (foco) tiles[actual].focus();
    mostrarFoto(actual);
  };

  const rotar = () => {
    clearInterval(timer); timer = null;
    const corre = !menosMovimiento && !tocada && visible && !encima;
    caja.classList.toggle('cajas--rotando', !menosMovimiento && !tocada);
    caja.classList.toggle('cajas--pausa', !corre);
    if (corre) {
      // reinicia la rayita para que arranque junto con el intervalo
      const i = caja.querySelector('.cajas__reloj i');
      if (i) { i.style.animation = 'none'; void i.offsetWidth; i.style.animation = ''; }
      timer = setInterval(() => elegir(actual + 1, false), CAJAS_T);
    }
  };

  const parar = () => { tocada = true; rotar(); };
  tiles.forEach((t, k) => t.addEventListener('click', () => { parar(); elegir(k, false); }));
  caja.querySelector('.cajas__grilla').addEventListener('keydown', (e) => {
    const paso = { ArrowRight: 1, ArrowDown: 4, ArrowLeft: -1, ArrowUp: -4 }[e.key];   // el tablero es de 4 columnas (era 5)
    if (paso !== undefined) { e.preventDefault(); parar(); elegir(actual + paso, true); }
    else if (e.key === 'Home') { e.preventDefault(); parar(); elegir(0, true); }
    else if (e.key === 'End') { e.preventDefault(); parar(); elegir(tiles.length - 1, true); }
  });
  const panel = caja.querySelector('.cajas__panel');
  panel.addEventListener('pointerenter', () => { encima = true; rotar(); });
  panel.addEventListener('pointerleave', () => { encima = false; rotar(); });
  panel.addEventListener('focusin', () => { encima = true; rotar(); });
  panel.addEventListener('focusout', () => { encima = false; rotar(); });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible) mostrarFoto(actual); rotar(); },
                             { threshold: 0.35 }).observe(caja);
  } else { visible = true; }

  elegir(0, false);
  rotar();
}
montarCajas();

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
  // v3 = la pelota dorada con un punto más de brillo. El parámetro es sólo
  // versionado de caché: al cambiar la pelota, subirlo.
  import('./pelota3d.js?v=3')
    .then((m) => m.montarPelota3D(caja, caja.querySelector('img'),
                                  document.querySelector('.wordmark__texto')))
    .catch((e) => console.info('[pelota3d] queda la imagen:', e.message));
}

const enCuantoSePueda = window.requestIdleCallback || ((fn) => setTimeout(fn, 300));
if (document.readyState === 'complete') enCuantoSePueda(cargarPelota3D);
else window.addEventListener('load', () => enCuantoSePueda(cargarPelota3D), { once: true });
