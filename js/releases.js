/* releases.js — adónde llevan los botones de descarga.
   9-nov-2026 (M299): LAS DESCARGAS SON DE ITCH.IO. Antes salían del último release de GitHub de este repo, y
   ese release se quedó en M293 mientras el juego seguía (itch tenía M299): quien bajaba desde la web se
   llevaba una versión que ya no encontraba servidor online. Rodrigo eligió un solo lugar de descarga.
   · Windows y Mac → la página de itch (butler sube los canales `windows` y `mac`; itch ofrece el de tu sistema).
   · Android → la prueba de Google Play (probar/).
   · Navegador → jugar.fulbito.futbol.
   ⚠️ `VERSION` se actualiza A MANO al publicar en itch (es sólo el número que muestra la página; los
   botones no dependen de él). La API de itch que dice la versión de un canal pide clave.
   El contador de descargas sigue saliendo de los releases VIEJOS de GitHub (el histórico real). */

const VERSION = 'M302';
const ITCH = 'https://rodrigoestrellac.itch.io/fulbito';
const JUGAR = 'https://jugar.fulbito.futbol/';
const REPO = 'rodrigoestrellac/fulbito-game-website';   // sólo para el contador histórico

function detectarSO() {
  const ua = navigator.userAgent;
  const plat = navigator.userAgentData?.platform || navigator.platform || '';
  /* ⚠️ Android se pregunta PRIMERO: su user-agent dice «Linux» y además «Android»,
     y varios navegadores de celular mienten con el resto. */
  if (/Android/i.test(ua)) return 'android';
  if (/iPhone|iPad|iPod/i.test(plat + ua) || (/Mac/i.test(plat + ua) && navigator.maxTouchPoints > 1)) return 'ios';
  if (/Mac/i.test(plat + ua)) return 'mac';
  if (/Win/i.test(plat + ua)) return 'win';
  return 'otro';
}

function pintar() {
  const so = detectarSO();
  document.querySelectorAll('[data-rel="version"]').forEach((el) => { el.textContent = VERSION; });

  /* ── CTA principal: lo que le sirve a quien está mirando ── */
  const cta = so === 'android' ? { href: 'probar/', largo: 'Probalo en Android', corto: 'Probar', peso: 'Google Play' }
            : so === 'ios'     ? { href: JUGAR, largo: 'Jugar en el iPad', corto: 'Jugar', peso: 'en el navegador' }
            : so === 'mac'     ? { href: ITCH, largo: 'Descargar para macOS', corto: 'Descargar', peso: 'itch.io' }
            :                    { href: ITCH, largo: 'Descargar para Windows', corto: 'Descargar', peso: 'itch.io' };
  document.querySelectorAll('[data-rel="cta"]').forEach((el) => {
    el.href = cta.href;
    el.removeAttribute('aria-disabled');
    const etiqueta = el.querySelector('[data-rel="cta-texto"]');
    if (etiqueta) etiqueta.textContent = el.dataset.corto ? cta.corto : cta.largo;
    const peso = el.querySelector('[data-rel="cta-peso"]');
    if (peso) peso.textContent = cta.peso;
  });
  // en el iPad el botón grande ya es «jugar»: el de al lado sobra
  if (so === 'ios') document.querySelectorAll('[data-rel="jugar"]').forEach((el) => { el.hidden = true; });

  /* ── Lista completa ── */
  const lista = document.querySelector('[data-rel="lista"]');
  if (lista) {
    const filas = [
      { so: 'Navegador', que: 'Sin instalar nada: abrilo en la PC, la Mac, el iPad o el celular y jugá. Bajado se juega mejor, sobre todo en Windows.', href: JUGAR, boton: 'Jugar ahora' },
      { so: 'Windows', que: 'En itch.io: bajás el zip, lo descomprimís y abrís <em>Fulbito.exe</em>. Con la app de itch se actualiza solo.', href: ITCH, boton: 'Descargar' },
      { so: 'macOS', que: '<em>Beta</em>, en itch.io. La primera vez macOS lo bloquea y hay que habilitarlo una sola vez: <a href="#paso-mac">mirá cómo</a>.', href: ITCH, boton: 'Descargar' },
      { so: 'Android', que: 'En prueba en Google Play: sumate como tester en dos pasos y te llegan las actualizaciones solas. Se juega con los dedos o con un joystick Bluetooth.', href: 'probar/', boton: 'Probarlo' },
    ];
    /* la fila del sistema de quien mira va justo después del navegador */
    const deSO = { win: 'Windows', mac: 'macOS', android: 'Android' }[so];
    const resto = filas.slice(1).sort((a, b) => (b.so === deSO) - (a.so === deSO));
    lista.innerHTML = [filas[0], ...resto].map((f) => `<div class="bajada-item">
        <span class="bajada-item__so">${f.so}</span>
        <span class="bajada-item__meta">${f.que}</span>
        <a class="btn btn--chico" href="${f.href}">${f.boton}</a>
      </div>`).join('');
  }
}

/* Los pasos de instalación son <details> (index.html § descargar): se abre el del sistema de quien mira. */
function abrirSegunSO() {
  const so = detectarSO() === 'ios' ? 'mac' : detectarSO();
  if (so === 'otro') return;
  document.querySelectorAll('details[data-so]').forEach((d) => {
    d.open = d.dataset.so.split(' ').includes(so);
  });
}

/* El «mirá cómo» de la fila de Mac salta a #paso-mac: si ese paso está plegado, se abre antes de saltar. */
function abrirAlSaltar() {
  const abrir = (id) => {
    const destino = id && document.getElementById(id);
    const d = destino && (destino.matches('details') ? destino : destino.querySelector('details'));
    if (d) d.open = true;
  };
  document.addEventListener('click', (ev) => {
    const a = ev.target.closest?.('a[href^="#"]');
    if (a) abrir(a.getAttribute('href').slice(1));
  });
  abrir(location.hash.slice(1));
}

/* El contador: las descargas históricas de los releases de GitHub (hasta M293). Sin dato, queda oculto. */
async function contar() {
  try {
    const r = await fetch(`https://api.github.com/repos/${REPO}/releases?per_page=100`, {
      headers: { Accept: 'application/vnd.github+json' },
    });
    if (!r.ok) throw new Error(`GitHub respondió ${r.status}`);
    const releases = await r.json();
    const total = releases.flatMap((rel) => rel.assets || [])
      .filter((a) => /\.(exe|zip|apk)$/i.test(a.name))
      .reduce((s, a) => s + (a.download_count || 0), 0);
    /* Redondeado PARA ABAJO y con «+» (Rodrigo, 30-oct): 131 → «+130». Abajo de 10, el exacto. */
    const redondo = (n) => {
      if (n < 10) return n.toLocaleString('es-AR');
      const paso = n < 1000 ? 10 : n < 10000 ? 100 : 1000;
      return `+${(Math.floor(n / paso) * paso).toLocaleString('es-AR')}`;
    };
    const cont = document.querySelector('[data-rel="descargas"]');
    if (cont && total > 0) {
      cont.textContent = total < 10
        ? `Ya se descargó ${total} ${total === 1 ? 'vez' : 'veces'}.`
        : `Ya van ${redondo(total)} descargas.`;
      cont.hidden = false;
    }
    const UMBRAL_HERO = 100;   // en el hero el número es prueba social: abajo del umbral prueba lo contrario
    const zoc = document.querySelector('[data-rel="descargas-zoc"]');
    const zocN = document.querySelector('[data-rel="descargas-n"]');
    if (zoc && zocN && total >= UMBRAL_HERO) {
      zocN.textContent = redondo(total);
      zoc.hidden = false;
    }
  } catch (e) {
    console.info('[releases] sin contador:', e.message);
  }
}

/* GA: un solo listener en captura, porque la lista se reescribe entera. */
function medirDescargas() {
  document.addEventListener('click', (ev) => {
    if (typeof gtag !== 'function') return;
    const salto = ev.target.closest?.('a[href="#descargar"]');
    if (salto) {
      const seccion = salto.closest('section')?.querySelector('h2')?.textContent.trim();
      gtag('event', 'cta_inline', { desde: seccion || (salto.closest('.pie') ? 'pie' : 'otro') });
      return;
    }
    if (ev.target.closest?.('a[href*="youtu.be"], a[href*="youtube.com"]')) {
      gtag('event', 'ver_gameplay', { desde: 'gol' });
      return;
    }
    const a = ev.target.closest?.('a[href*="itch.io"], a[href*="jugar.fulbito.futbol"], a[href^="probar/"]');
    if (!a) return;
    const donde = a.closest('.marcador') ? 'marcador'
                : a.closest('.hero') ? 'hero'
                : a.closest('[data-rel="lista"]') ? 'lista'
                : 'otro';
    gtag('event', 'descarga', {
      tipo: a.href.includes('jugar.fulbito.futbol') ? 'web' : a.href.includes('itch.io') ? 'itch' : 'android',
      desde: donde,
      so: detectarSO(),
    });
  }, true);
}

medirDescargas();
abrirSegunSO();
abrirAlSaltar();
pintar();
contar();
