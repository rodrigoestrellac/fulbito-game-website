/* roster.js — el álbum de figuritas se vuelve interactivo.
   Todo es progresivo: sin JS queda la grilla estática completa del HTML (los 52
   cromos se ven igual), y esto sólo AGREGA — filtros, el brillo de figurita
   dorada, y la ficha que se abre al tocar un cromo. Los datos salen de
   assets/roster/roster.json, que build_assets.py deriva del juego: acá no hay
   ningún número escrito a mano, porque las listas a mano se desincronizan en
   silencio (la lección del álbum 28 vs 50). */

/* Las descripciones de las jugadas firma SÍ son editoriales (el juego no las
   tiene escritas en ningún lado). Los números que citan son los de
   MatchTuning.cs — si una firma cambia de duración o radio, esto hay que
   tocarlo a mano; por eso cada línea nombra el dato y no "un rato" o "cerca". */
const FIRMAS_DESC = {
  'EL MARTILLAZO': 'Saca un martillo de la nada, lo levanta, lo baja — y todo el que esté a tres metros y medio queda dos segundos aplastado, hecho panqueque.',
  'LA EMBESTIDA': 'Arranca al doble de velocidad durante tres segundos y medio y hace panqueque a todo el que se le cruza.',
  'LA MURALLA': 'Levanta una pared de cinco metros y la deja seis segundos. No te da la pelota: te da tiempo.',
  'EL GIGANTE': 'Se agranda una vez y media durante tres segundos y medio, y con rozarte te voltea.',
  'LA PAUSA': 'Cuatro segundos de pausa: los rivales pasan a cámara lenta y un compañero pica catorce metros al arco.',
  'EL CAÑONAZO': 'Saca un cañón pirata y dispara la pelota en llamas. Adentro de los dieciséis metros, no hay arquero.',
  'EL MISIL': 'Se carga un lanzamisiles al hombro y la pelota sale con ojiva. Cerca del arco no hay forma de atajarla.',
  'EL TRACTOR': 'Tres segundos lento pero imparable: baja un cambio y va volteando gente a su paso.',
  'LA TELARAÑA': 'Teje una red de cuatro metros que atrapa dos segundos y medio a todo rival que agarra adentro.',
  'EL HECHIZO': 'Deja quietos a los rivales en cinco metros a la redonda durante dos segundos, con estrellitas.',
  'EL MAREO': 'La pedalada: al que la mira de cerca —cinco metros— le quedan dos segundos de estrellitas.',
  'LA PULGUITA': 'Se achica a la mitad y acelera una vez y media. Andá a agarrarlo.',
  'LA ROULETTE': 'Gira sobre la pelota como en Francia 98 y marea a los de alrededor. Suena La Marsellesa.',
  'LOS FLASHES': 'Sesión de fotos en plena jugada: encandila dos segundos y medio a los rivales en cuatro metros y medio.',
  'EL FENÓMENO': 'El arranque del 9 de verdad: acelera de golpe y ya le quedaste atrás.',
  'VELOCIDAD': 'El pique corto del Diez: unos segundos en los que nadie lo alcanza.',
  'EL KUNI': 'Acelera y define: el punto que entra frío y la manda a guardar.',
  'LA LIANA': 'Sale disparado quince metros colgado de una liana, ida y vuelta, llevándose puesto lo que toque.',
  'EL PITBULL': 'Cinco segundos de cacería: corre más que todos y al que tiene la pelota lo caza.',
  'LA MORDIDA': 'Un mordisco a tres metros: el mordido queda cuatro segundos tirado, sobándose.',
  'EL HACHA': 'Revolea el hacha y viaja treinta y cinco metros tumbando todo lo que encuentra.',
  'LA BOMBA': 'Suelta una bomba que rueda sola y explota en cuatro metros. Correr no siempre alcanza.',
  'EL KILLER': 'El disparo rasante del área: sale a la velocidad del cañonazo y atropella defensas en el camino.',
  'EL PISOTÓN': 'Se agranda, levanta el pie y pisa: aplastón de tres metros que deja panqueques a todos.',
  'LA BARRIDA': 'La súper barrida: abre un surco en el pasto donde los rivales tropiezan.',
  'LA MOMIA': 'Momifica a los rivales en cinco metros: cuatro segundos y medio caminando como zombies.',
  'LA MINA': 'Entierra una mina a su espalda y ahí queda, esperando. El que la pisa, vuela tres metros.',
  'EL PISCINAZO': 'Se tira a la pileta. Siete de cada diez veces, la compran y es tiro libre.',
  'EL TURBO': 'Un estallido en línea recta a casi el doble de lo que corre cualquiera, llevándose por delante al que se le cruce. Dura un suspiro.',
  'LA MIRA': 'Cámara lenta y una mirilla desde mitad de cancha: el pase cae exactamente donde la pusiste.',
  'LA PISTOLA': 'Desenfunda y tira una ráfaga: cada tiro que entra aturde al que lo come.',
  'LA CERCA': 'Planta un alambrado de seis metros que dura doce segundos. El que lo toca queda pegado.',
  'EN LLAMAS': 'Se prende fuego: chamusca a los rivales en cuatro metros y los deja quietos.',
  'EL HIELO': 'Congela en estatua dos segundos y medio a todo rival en cuatro metros y medio.',
  'LOS TALLARINES': 'Enrolla a los rivales en spaghetti a cuatro metros a la redonda y los tira al piso: dos segundos y medio comiendo pasto.',
  'EL GRITO': 'Un grito de guerra que viaja treinta metros en onda expansiva y voltea todo lo que agarra el frente.',
  'LA CAJA': 'Convierte a los rivales a cuatro metros en cajas sorpresa: dos segundos y medio encajonados hasta que el resorte escupe al payaso.',
  'EL ARAÑAZO': 'Tres garras que tajean DOS veces: la primera tanda voltea, y al que se corrió lo espera la segunda medio segundo después.',
  'LA PINTURA': 'Vuelca un balde de pintura unos metros adelante y la mancha queda ocho segundos en el pasto: el que la pisa, patina.',
  'IL MIRACOLO': 'La única firma que no le hace nada a nadie: levanta a los compañeros caídos en seis metros y les deja un envión. Divino.',
  'EL EXPRESO': 'Se sube a una locomotora y sale tres segundos y medio a un tercio más de lo que corre: voltea todo lo que tenga adelante, pero no dobla — el que se corre al costado se salva.',
  'LA ATALAYA': 'Planta una torre que se queda ocho segundos tirando una flecha por segundo al rival de pie más cercano en cinco metros y medio. Cada flechazo deja tirado casi dos segundos.',
  'EL SUSTO': 'Levanta los brazos y ruge: los rivales a cinco metros salen en desbandada dos segundos y pico, pálidos y corriendo más rápido que nunca. El que llevaba la pelota, la suelta.',
  'LOS FANTASMAS': 'Salen tres señuelos idénticos y él se mezcla entre ellos: casi dos segundos y medio en los que el rival no sabe a cuál seguir.',
  'EL INTOCABLE': 'Cuatro segundos y medio en los que no le pueden hacer una falta: le entran y sigue como si nada. No voltea a nadie — a una liana o un hacha se cae igual que cualquiera.',
  'LA REMONTADA': 'La única que sólo se puede tirar si vas perdiendo: seis segundos de envión para TODO el equipo, un rayo rojo a cada compañero, un veintidós por ciento más de velocidad y un veinte por ciento más de pegada.',
  'EN GARDE': 'Saca el florete: la estocada se lleva puesto al rival más cercano en tres metros, y quedan dos segundos y pico de guardia en los que el que le tira una entrada termina en el piso — y tampoco le pueden robar.',
  'LA ASPIRADORA': 'Tres segundos de imán: la pelota suelta que le pase a tres metros y medio se curva sola hacia él. No corre a buscarla — se para en el carril del pase y espera.',
  'EL CORTOCIRCUITO': 'Un chispazo que llega a doce metros y APAGA las firmas rivales que estén prendidas — gigante, turbo, pitbull, guardia, lo que sea. Y de paso le vacía media barra al medidor del otro equipo.',
  'LA CRUYFF': 'El giro de 1974: frena, la esconde y sale para el otro lado a un tercio más de velocidad. El que lo marcaba sigue de largo casi un segundo, mirando dónde quedó.',
  'ARQUERO': 'Ataja. Que no es poco: en Fulbito los arqueros vuelan de verdad.',
};

const STATS_ROTULOS = [
  ['ritmo', 'Ritmo'], ['pegada', 'Pegada'], ['comba', 'Comba'],
  ['control', 'Control'], ['fuerza', 'Fuerza'], ['precision', 'Precisión'],
  ['pase', 'Pase'], ['gambeta', 'Gambeta'],
];

/* los dos recién llegados (M111) llevan el moño de NUEVO. Editorial: cuando
   dejen de ser noticia, se vacía la lista y listo. */
const NUEVOS = [
  'titan', 'payasito', 'valdanito', 'muneco', 'jefecito',        // M164
  'maestro', 'pinturicchio', 'divino', 'reyromano',              // M173
  'pato', 'mono', 'casillero', 'dado', 'doblev', 'pinocho',      // arqueros M159/M173
];

const menosMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const punteroFino = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

/* «EL VIKINGO» → «El Vikingo» — el JSON trae los nombres como los grita el HUD
   del juego (mayúsculas); acá se componen como en el resto de la página.
   Una palabra con dígitos queda toda en mayúsculas: CR007, no Cr007.
   Y la letra que sigue a un apóstrofo también sube: D'Artagnan, no D'artagnan. */
const componer = (s) => s.toLowerCase().replace(/\S+/g, (w) =>
  /\d/.test(w) ? w.toUpperCase()
                : w.replace(/(^|['’])(\S)/g, (_, a, c) => a + c.toUpperCase()));

async function montarAlbum() {
  const album = document.querySelector('.album');
  if (!album || !window.fetch || typeof HTMLDialogElement === 'undefined') return;

  let data;
  try {
    data = await (await fetch('assets/roster/roster.json')).json();
  } catch {
    return; // sin datos queda la grilla estática, que ya se ve completa
  }

  const porSlug = new Map(data.map((j, n) => [j.slug, { ...j, n: n + 1 }]));
  const tarjetas = new Map(); // slug -> <li>

  /* ── cada cromo se vuelve un botón que abre la ficha ──────────────────── */
  album.querySelectorAll('.figu').forEach((li) => {
    const src = li.querySelector('img')?.getAttribute('src') || '';
    const slug = (src.match(/roster\/([a-z0-9-]+)\.webp$/) || [])[1];
    const j = porSlug.get(slug);
    if (!j) return;
    tarjetas.set(slug, li);
    li.dataset.slug = slug;

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'figu__abrir';
    btn.setAttribute('aria-label', `Ficha de ${componer(j.nombre)}`);
    while (li.firstChild) btn.appendChild(li.firstChild);
    li.appendChild(btn);

    // el número de cromo: el orden es el del juego, no un adorno
    const num = document.createElement('span');
    num.className = 'figu__num';
    num.setAttribute('aria-hidden', 'true');
    num.textContent = String(j.n).padStart(2, '0');
    btn.appendChild(num);

    if (NUEVOS.includes(j.id)) {
      const chip = document.createElement('span');
      chip.className = 'figu__nuevo';
      chip.textContent = 'Nuevo';
      btn.appendChild(chip);
    }

    btn.addEventListener('click', () => abrirFicha(slug));
  });

  /* ── el brillo de figurita dorada + el tilt ───────────────────────────────
     El foil sigue al puntero con dos custom properties por tarjeta; el tilt es
     de a poquito (±5°). Sólo con puntero fino y sin reduced-motion: en un
     táctil no hay hover que valga y el gesto sería ruido. */
  if (punteroFino && !menosMovimiento) {
    album.classList.add('album--foil');
    album.addEventListener('pointermove', (e) => {
      const li = e.target.closest('.figu');
      if (!li) return;
      const r = li.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width;   // 0..1
      const y = (e.clientY - r.top) / r.height;
      li.style.setProperty('--mx', `${(x * 100).toFixed(1)}%`);
      li.style.setProperty('--my', `${(y * 100).toFixed(1)}%`);
      li.style.setProperty('--rx', `${((0.5 - y) * 8).toFixed(2)}deg`);
      li.style.setProperty('--ry', `${((x - 0.5) * 10).toFixed(2)}deg`);
    });
    album.addEventListener('pointerout', (e) => {
      const li = e.target.closest('.figu');
      // ⚠️ sólo las variables del tilt: en style también vive el --i de la
      // cascada de entrada (lo pone main.js) y un removeAttribute lo pisaría
      if (li && !li.contains(e.relatedTarget)) {
        ['--mx', '--my', '--rx', '--ry'].forEach((p) => li.style.removeProperty(p));
      }
    });
  }

  /* ── filtros ──────────────────────────────────────────────────────────── */
  const deCampo = data.filter((j) => !j.gk);
  const filtros = [
    { rotulo: 'Todos', n: data.length, pasa: () => true },
    { rotulo: 'De campo', n: deCampo.length, pasa: (j) => !j.gk },
    { rotulo: 'Arqueros', n: data.length - deCampo.length, pasa: (j) => j.gk },
    { rotulo: 'Zurdos', n: data.filter((j) => j.zurdo).length, pasa: (j) => j.zurdo },
  ];
  const firmas = [...new Set(deCampo.map((j) => j.firma))];

  const barra = document.createElement('div');
  barra.className = 'album__filtros';
  barra.setAttribute('role', 'group');
  barra.setAttribute('aria-label', 'Filtrar el plantel');

  let filtroActivo = filtros[0];
  const botones = filtros.map((f) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'album__filtro';
    b.setAttribute('aria-pressed', f === filtroActivo ? 'true' : 'false');
    b.innerHTML = `${f.rotulo} <b>${f.n}</b>`;
    b.addEventListener('click', () => { selectFirma.value = ''; aplicar(f, b); });
    barra.appendChild(b);
    return b;
  });

  // las 35 firmas van en un <select>: como chips serían otra sábana
  const selectFirma = document.createElement('select');
  selectFirma.id = 'filtro-firma';
  selectFirma.className = 'album__firma-select';
  selectFirma.setAttribute('aria-label', 'Filtrar por jugada firma');
  selectFirma.innerHTML = '<option value="">Por firma…</option>' + firmas.map((f) => {
    const n = deCampo.filter((j) => j.firma === f).length;
    return `<option value="${f}">${componer(f)} (${n})</option>`;
  }).join('');
  selectFirma.addEventListener('change', () => {
    const f = selectFirma.value;
    if (!f) return aplicar(filtros[0], botones[0]);
    aplicar({ rotulo: f, pasa: (j) => j.firma === f }, null);
  });
  barra.appendChild(selectFirma);
  album.before(barra);

  function aplicar(filtro, boton) {
    filtroActivo = filtro;
    botones.forEach((b) => b.setAttribute('aria-pressed', b === boton ? 'true' : 'false'));
    tarjetas.forEach((li, slug) => {
      li.hidden = !filtro.pasa(porSlug.get(slug));
    });
  }

  /* ── la ficha: el dorso de la figurita ────────────────────────────────── */
  const ficha = document.createElement('dialog');
  ficha.className = 'ficha';
  ficha.setAttribute('aria-label', 'Ficha del jugador');
  document.body.appendChild(ficha);

  // clic en el fondo = cerrar (el panel adentro se traga sus propios clics)
  ficha.addEventListener('click', (e) => { if (e.target === ficha) ficha.close(); });
  /* cada cromo tiene URL: #cromo/el-vikingo. replaceState y no location.hash
     para no ensuciar el historial con cada flecha (volver atrás debe salir de
     la página, no repasar 52 cromos). */
  ficha.addEventListener('close', () => {
    slugAbierto = null;
    history.replaceState(null, '', location.pathname + location.search);
  });
  ficha.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') { e.preventDefault(); pasarFicha(1); }
    if (e.key === 'ArrowLeft') { e.preventDefault(); pasarFicha(-1); }
  });
  /* en un táctil la ficha se pasa DESLIZANDO, como las hojas del álbum. Se
     decide recién al soltar y sin preventDefault: el scroll vertical (que en
     mobile lo hace la ficha misma) sigue siendo del navegador. Horizontal
     manda sólo si dx supera el umbral Y le gana claro al dy — un scroll en
     diagonal no tiene que cambiar de cromo. */
  let toqueX = 0, toqueY = 0;
  ficha.addEventListener('touchstart', (e) => {
    toqueX = e.changedTouches[0].clientX;
    toqueY = e.changedTouches[0].clientY;
  }, { passive: true });
  ficha.addEventListener('touchend', (e) => {
    const dx = e.changedTouches[0].clientX - toqueX;
    const dy = e.changedTouches[0].clientY - toqueY;
    if (Math.abs(dx) > 48 && Math.abs(dx) > 1.6 * Math.abs(dy)) {
      pasarFicha(dx < 0 ? 1 : -1);   // deslizar a la izquierda = cromo siguiente
    }
  }, { passive: true });

  let slugAbierto = null;

  function visibles() {
    return data.filter((j) => filtroActivo.pasa(j) && tarjetas.has(j.slug));
  }

  function pasarFicha(paso) {
    const lista = visibles();
    if (!lista.length) return;
    const i = lista.findIndex((j) => j.slug === slugAbierto);
    abrirFicha(lista[(i + paso + lista.length) % lista.length].slug, paso);
  }

  function abrirFicha(slug, rumbo) {
    const j = porSlug.get(slug);
    if (!j) return;
    slugAbierto = slug;

    const comparten = data.filter((x) => x.firma === j.firma && x.slug !== slug);
    const desc = FIRMAS_DESC[j.firma] || '';
    const sellos = [
      j.gk ? '<span class="ficha__sello ficha__sello--arq">Arquero</span>' : '',
      j.zurdo ? '<span class="ficha__sello">Zurdo</span>' : '',
      NUEVOS.includes(j.id) ? '<span class="ficha__sello ficha__sello--nuevo">Nuevo</span>' : '',
    ].join('');

    ficha.innerHTML = `
      <article class="ficha__panel">
        <header class="ficha__cabeza">
          <span class="ficha__num" aria-hidden="true">${String(j.n).padStart(2, '0')}<i>/${data.length}</i></span>
          <button class="ficha__cerrar" type="button" aria-label="Cerrar la ficha">×</button>
        </header>
        <div class="ficha__cuerpo">
          <figure class="ficha__retrato">
            <img src="assets/roster/${j.slug}.webp" alt="Retrato de ${componer(j.nombre)}" width="480" height="480">
          </figure>
          <div class="ficha__datos">
            <h3 class="ficha__nombre">${componer(j.nombre)}</h3>
            <p class="ficha__firma">${j.gk ? 'Arquero' : componer(j.firma)}${sellos}</p>
            ${desc ? `<p class="ficha__desc">${desc}</p>` : ''}
            <dl class="ficha__stats">
              ${STATS_ROTULOS.map(([k, rotulo]) => `
                <div class="ficha__stat">
                  <dt>${rotulo}</dt>
                  <dd><span class="ficha__barra"><i style="--v:${j.stats[k]}"></i></span><b>${j.stats[k]}</b></dd>
                </div>`).join('')}
            </dl>
            ${comparten.length ? `
              <p class="ficha__comparten">${j.gk ? 'Los otros arqueros:' : 'También la tiene:'}
                ${comparten.map((x) => `<button type="button" data-slug="${x.slug}">${componer(x.nombre)}</button>`).join(' ')}
              </p>` : ''}
          </div>
        </div>
        <footer class="ficha__pasar">
          <button class="ficha__flecha" type="button" data-paso="-1" aria-label="Cromo anterior">←</button>
          <button class="ficha__flecha" type="button" data-paso="1" aria-label="Cromo siguiente">→</button>
        </footer>
      </article>`;

    ficha.querySelector('.ficha__cerrar').addEventListener('click', () => ficha.close());
    ficha.querySelectorAll('[data-paso]').forEach((b) =>
      b.addEventListener('click', () => pasarFicha(Number(b.dataset.paso))));
    ficha.querySelectorAll('[data-slug]').forEach((b) =>
      b.addEventListener('click', () => abrirFicha(b.dataset.slug, 1)));

    if (!ficha.open) {
      ficha.showModal();
    } else {
      /* el innerHTML de recién se llevó puesto al botón que tenía el foco, y
         con el foco en el body el keydown del dialog no escucha más: las
         flechas del teclado morían al primer cambio de cromo. Se devuelve el
         foco a la flecha del rumbo, así Enter también sigue pasando cromos. */
      const flecha = ficha.querySelector(`[data-paso="${rumbo < 0 ? -1 : 1}"]`);
      (flecha || ficha.querySelector('.ficha__cerrar')).focus({ preventScroll: true });
    }
    history.replaceState(null, '', '#cromo/' + slug);

    // al PASAR de cromo (flechas, swipe, «también la tiene»), el panel entra
    // deslizándose desde el lado del gesto — la hoja del álbum que se da vuelta
    if (rumbo && !menosMovimiento) {
      ficha.querySelector('.ficha__panel').style.animation =
        `ficha-pasa-${rumbo > 0 ? 'sig' : 'ant'} .3s var(--ease)`;
    }

    /* las barras crecen desde cero al abrir; sin motion, aparecen llenas.
       El doble rAF es para que el estilo inicial (--v:0) llegue a pintarse. */
    if (!menosMovimiento) {
      const barras = ficha.querySelectorAll('.ficha__barra i');
      barras.forEach((b) => { b.dataset.v = b.style.getPropertyValue('--v'); b.style.setProperty('--v', 0); });
      requestAnimationFrame(() => requestAnimationFrame(() =>
        barras.forEach((b) => b.style.setProperty('--v', b.dataset.v))));
    }
  }

  // si alguien llega con #cromo/<slug> (le compartieron una figurita), la
  // ficha se abre sola sobre el álbum
  const pedido = (location.hash.match(/^#cromo\/([a-z0-9-]+)$/) || [])[1];
  if (pedido && porSlug.has(pedido)) {
    tarjetas.get(pedido)?.scrollIntoView({ block: 'center' });
    abrirFicha(pedido);
  }
}

montarAlbum();
