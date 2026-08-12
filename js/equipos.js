/* equipos.js — el catálogo se vuelve pizarra de DT.
   Mismo contrato progresivo que roster.js: sin JS queda la grilla estática
   completa del HTML (los 27 con escudo, concepto, formación y barras), y esto
   sólo AGREGA la ficha que se abre al tocar una tarjeta. Los datos salen de
   assets/equipos/equipos.json, que build_assets.py deriva del juego —
   incluidos los SLOTS de cada formación, que es lo que permite parar a los
   siete en la mini-cancha donde juegan de verdad y no en un dibujito. */

const menosMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* «SCALONETA 22» → «Scaloneta 22» — para los nombres de jugador y el aria.
   El NOMBRE del equipo se muestra como grita el juego (mayúsculas): es el
   marcador, no un párrafo. */
const componer = (s) => s.toLowerCase().replace(/\S+/g, (w) =>
  /\d/.test(w) ? w.toUpperCase() : w.charAt(0).toUpperCase() + w.slice(1));

async function montarEquipos() {
  const grilla = document.querySelector('.equipos');
  if (!grilla || !window.fetch || typeof HTMLDialogElement === 'undefined') return;

  let data, roster;
  try {
    [data, roster] = await Promise.all([
      fetch('assets/equipos/equipos.json').then((r) => r.json()),
      fetch('assets/roster/roster.json').then((r) => r.json()),
    ]);
  } catch {
    return; // sin datos queda la grilla estática, que ya cuenta todo
  }

  const jug = new Map(roster.map((j) => [j.id, j]));
  const porSlug = new Map(data.equipos.map((e, n) => [e.slug, { ...e, n: n + 1 }]));
  const tarjetas = new Map(); // slug -> <li>

  grilla.querySelectorAll('.equipo').forEach((li) => {
    const src = li.querySelector('img')?.getAttribute('src') || '';
    const slug = (src.match(/equipos\/([a-z0-9-]+)\.webp$/) || [])[1];
    const e = porSlug.get(slug);
    if (!e) return;
    tarjetas.set(slug, li);

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'equipo__abrir';
    btn.setAttribute('aria-label', `Pizarra de ${componer(e.nombre)}`);
    while (li.firstChild) btn.appendChild(li.firstChild);
    li.appendChild(btn);
    btn.addEventListener('click', () => abrirPizarra(slug));
  });

  /* ── la ficha: la pizarra táctica del equipo ──────────────────────────── */
  const ficha = document.createElement('dialog');
  ficha.className = 'ficha ficha--equipo';
  ficha.setAttribute('aria-label', 'Pizarra del equipo');
  document.body.appendChild(ficha);

  ficha.addEventListener('click', (e) => { if (e.target === ficha) ficha.close(); });
  ficha.addEventListener('close', () => {
    slugAbierto = null;
    history.replaceState(null, '', location.pathname + location.search);
  });
  ficha.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') { e.preventDefault(); pasar(1); }
    if (e.key === 'ArrowLeft') { e.preventDefault(); pasar(-1); }
  });
  // el mismo gesto que el álbum: deslizar pasa de equipo (ver roster.js)
  let toqueX = 0, toqueY = 0;
  ficha.addEventListener('touchstart', (e) => {
    toqueX = e.changedTouches[0].clientX;
    toqueY = e.changedTouches[0].clientY;
  }, { passive: true });
  ficha.addEventListener('touchend', (e) => {
    const dx = e.changedTouches[0].clientX - toqueX;
    const dy = e.changedTouches[0].clientY - toqueY;
    if (Math.abs(dx) > 48 && Math.abs(dx) > 1.6 * Math.abs(dy)) pasar(dx < 0 ? 1 : -1);
  }, { passive: true });

  let slugAbierto = null;

  function pasar(paso) {
    const lista = data.equipos;
    const i = lista.findIndex((e) => e.slug === slugAbierto);
    abrirPizarra(lista[(i + paso + lista.length) % lista.length].slug, paso);
  }

  /* un slot (z, x) del juego → posición en la media cancha vertical.
     z va del arco propio (1.5, el arquero) a la mitad (44); x, de -10 a 10.
     Los factores dejan aire para el retrato y su nombre en los bordes. */
  function jugadorHTML(id, slot, esGk) {
    const j = jug.get(id);
    if (!j) return '';
    const x = (50 + slot[1] * 3.6).toFixed(1);
    const y = (6 + slot[0] * 1.75).toFixed(1);
    return `<figure class="pizarra__jug${esGk ? ' pizarra__jug--gk' : ''}" style="--x:${x}%;--y:${y}%">
        <img src="assets/roster/${j.slug}.webp" alt="" width="120" height="120" loading="lazy">
        <figcaption>${componer(j.nombre)}</figcaption>
      </figure>`;
  }

  function abrirPizarra(slug, rumbo) {
    const e = porSlug.get(slug);
    if (!e) return;
    slugAbierto = slug;

    const f = data.formaciones[e.form];
    const gk = jug.get(e.gk);
    const parados = [jugadorHTML(e.gk, f.slots[0], true)]
      .concat(e.ids.map((id, k) => jugadorHTML(id, f.slots[k + 1], false)))
      .join('');
    const barras = [['Velocidad', e.vel], ['Fuerza', e.fue], ['Precisión', e.pre]]
      .map(([rotulo, v]) => `
        <div class="ficha__stat">
          <dt>${rotulo}</dt>
          <dd><span class="ficha__barra"><i style="--v:${v}"></i></span><b>${v}</b></dd>
        </div>`).join('');

    ficha.innerHTML = `
      <article class="ficha__panel ficha__panel--equipo">
        <header class="ficha__cabeza">
          <span class="ficha__num" aria-hidden="true">${String(e.n).padStart(2, '0')}<i>/${data.equipos.length}</i></span>
          <button class="ficha__cerrar" type="button" aria-label="Cerrar la pizarra">×</button>
        </header>
        <div class="ficha__cuerpo ficha__cuerpo--equipo">
          <figure class="pizarra">
            <div class="pizarra__cancha">${parados}</div>
            <figcaption class="pizarra__form">${f.name} — ${f.def} atrás, ${f.mid} al medio, ${f.fwd} arriba</figcaption>
          </figure>
          <div class="ficha__datos">
            <img class="fichaeq__escudo" src="assets/equipos/${e.slug}.webp" alt="" width="128" height="128">
            <h3 class="ficha__nombre">${e.nombre}</h3>
            <p class="fichaeq__concepto">${e.concepto}</p>
            <dl class="ficha__stats ficha__stats--equipo">${barras}</dl>
            <p class="fichaeq__arco">Al arco: <b>${componer(gk ? gk.nombre : e.gk)}</b></p>
          </div>
        </div>
        <footer class="ficha__pasar">
          <button class="ficha__flecha" type="button" data-paso="-1" aria-label="Equipo anterior">←</button>
          <button class="ficha__flecha" type="button" data-paso="1" aria-label="Equipo siguiente">→</button>
        </footer>
      </article>`;

    ficha.querySelector('.ficha__cerrar').addEventListener('click', () => ficha.close());
    ficha.querySelectorAll('[data-paso]').forEach((b) =>
      b.addEventListener('click', () => pasar(Number(b.dataset.paso))));

    if (!ficha.open) {
      ficha.showModal();
    } else {
      // mismo detalle que el álbum: innerHTML se llevó el foco y sin él las
      // flechas del teclado dejan de escucharse
      const flecha = ficha.querySelector(`[data-paso="${rumbo < 0 ? -1 : 1}"]`);
      (flecha || ficha.querySelector('.ficha__cerrar')).focus({ preventScroll: true });
    }
    history.replaceState(null, '', '#equipo/' + slug);

    if (rumbo && !menosMovimiento) {
      ficha.querySelector('.ficha__panel').style.animation =
        `ficha-pasa-${rumbo > 0 ? 'sig' : 'ant'} .3s var(--ease)`;
    }
    // las barras crecen al abrir, como en el cromo (ver roster.js)
    if (!menosMovimiento) {
      const bs = ficha.querySelectorAll('.ficha__barra i');
      bs.forEach((b) => { b.dataset.v = b.style.getPropertyValue('--v'); b.style.setProperty('--v', 0); });
      requestAnimationFrame(() => requestAnimationFrame(() =>
        bs.forEach((b) => b.style.setProperty('--v', b.dataset.v))));
    }
  }

  // #equipo/<slug> compartido: la pizarra se abre sola sobre el catálogo
  const pedido = (location.hash.match(/^#equipo\/([a-z0-9-]+)$/) || [])[1];
  if (pedido && porSlug.has(pedido)) {
    tarjetas.get(pedido)?.scrollIntoView({ block: 'center' });
    abrirPizarra(pedido);
  }
}

montarEquipos();
