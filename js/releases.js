/* releases.js — las descargas salen del ÚLTIMO release de este repo.
   No hay versiones hardcodeadas en el HTML: se publica un release y la web se
   entera sola. Si la API de GitHub no contesta (rate limit: 60 pedidos por hora
   por IP, o el usuario sin red) se usa FALLBACK, que hay que actualizar a mano
   cuando se publica una versión nueva. Ver README. */

const REPO = 'rodrigoestrellac/fulbito-game-website';

/* Espejo estático del release M78. Actualizar al publicar uno nuevo. */
const FALLBACK = {
  tag: 'M78',
  archivos: {
    winSetup: { nombre: 'FulbitoSetup-M78.exe', bytes: 87969180 },
    winZip:   { nombre: 'Fulbito-M78-windows.zip', bytes: 112354036 },
    mac:      { nombre: 'Fulbito-M78-mac.zip', bytes: 121029486 },
    checksums:{ nombre: 'CHECKSUMS.txt', bytes: 311 },
  },
};

const urlDescarga = (tag, nombre) =>
  `https://github.com/${REPO}/releases/download/${encodeURIComponent(tag)}/${encodeURIComponent(nombre)}`;

const mb = (bytes) => bytes >= 1024 * 1024
  ? `${Math.round(bytes / 1048576)} MB`
  : `${Math.max(1, Math.round(bytes / 1024))} KB`;

/* Clasifica los assets del release por nombre. Si cambian los nombres que
   genera pack_release.ps1, hay que tocar estos patrones. */
function clasificar(assets) {
  const buscar = (re) => {
    const a = assets.find((x) => re.test(x.name));
    return a ? { nombre: a.name, bytes: a.size } : null;
  };
  return {
    winSetup: buscar(/setup.*\.exe$/i),
    winZip: buscar(/windows.*\.zip$/i),
    mac: buscar(/mac.*\.zip$/i),
    checksums: buscar(/^checksums.*\.txt$/i),
  };
}

function detectarSO() {
  const ua = navigator.userAgent;
  const plat = navigator.userAgentData?.platform || navigator.platform || '';
  if (/Mac|iPhone|iPad|iPod/i.test(plat + ua)) return 'mac';
  if (/Win/i.test(plat + ua)) return 'win';
  return 'otro';
}

function pintar(release) {
  const { tag, archivos } = release;
  const so = detectarSO();

  document.querySelectorAll('[data-rel="version"]').forEach((el) => { el.textContent = tag; });

  /* ── CTA principal: el archivo que le sirve a quien está mirando ── */
  const principal = so === 'mac'
    ? { a: archivos.mac, txt: 'Descargar para macOS' }
    : { a: archivos.winSetup || archivos.winZip, txt: 'Descargar para Windows' };

  document.querySelectorAll('[data-rel="cta"]').forEach((el) => {
    if (!principal.a) return;
    el.href = urlDescarga(tag, principal.a.nombre);
    el.removeAttribute('aria-disabled');
    const etiqueta = el.querySelector('[data-rel="cta-texto"]');
    // el botón del marcador es angosto: ahí va sólo "Descargar"
    if (etiqueta) etiqueta.textContent = el.dataset.corto ? 'Descargar' : principal.txt;
    const peso = el.querySelector('[data-rel="cta-peso"]');
    if (peso) peso.textContent = mb(principal.a.bytes);
  });

  const nota = document.querySelector('[data-rel="cta-nota"]');
  if (nota) {
    if (so === 'mac' && archivos.winSetup) {
      nota.innerHTML = `¿Estás en Windows? <a href="${urlDescarga(tag, archivos.winSetup.nombre)}">Bajá el instalador</a>.`;
    } else if (archivos.mac) {
      nota.innerHTML = `¿Mac? <a href="${urlDescarga(tag, archivos.mac.nombre)}">Bajá el zip</a> — va como beta.`;
    }
  }

  const pesoHero = document.querySelector('[data-rel="peso"]');
  if (pesoHero && principal.a) pesoHero.textContent = mb(principal.a.bytes);

  /* ── Lista completa de descargas ── */
  const lista = document.querySelector('[data-rel="lista"]');
  if (lista) {
    const filas = [
      { k: 'winSetup', so: 'Windows', que: 'Instalador. Se instala solo, sin permisos de administrador.' },
      { k: 'winZip', so: 'Windows', que: 'Portable. Lo descomprimís y ejecutás <em>Fulbito.exe</em>. Sirve si la PC no te deja instalar nada.' },
      { k: 'mac', so: 'macOS', que: '<em>Beta</em> — se empaquetó desde Windows y no lo probó nadie en un Mac de verdad. Si no te abre, contame.' },
    ];
    lista.innerHTML = filas.filter((f) => archivos[f.k]).map((f) => {
      const a = archivos[f.k];
      return `<div class="bajada-item">
        <span class="bajada-item__so">${f.so}</span>
        <span class="bajada-item__meta">${f.que}</span>
        <a class="btn btn--chico" href="${urlDescarga(tag, a.nombre)}">
          Descargar <span aria-hidden="true">·</span> ${mb(a.bytes)}
        </a>
      </div>`;
    }).join('');
  }

  const chk = document.querySelector('[data-rel="checksums"]');
  if (chk && archivos.checksums) {
    chk.href = urlDescarga(tag, archivos.checksums.nombre);
    chk.hidden = false;
  }
}

async function cargar() {
  pintar(FALLBACK); // se pinta ya, sin esperar a la red
  try {
    const r = await fetch(`https://api.github.com/repos/${REPO}/releases/latest`, {
      headers: { Accept: 'application/vnd.github+json' },
    });
    if (!r.ok) throw new Error(`GitHub respondió ${r.status}`);
    const data = await r.json();
    const archivos = clasificar(data.assets || []);
    if (!archivos.winSetup && !archivos.winZip && !archivos.mac) return; // release sin binarios: queda el fallback
    pintar({ tag: data.tag_name, archivos });
  } catch (e) {
    console.info('[releases] queda el release estático:', e.message);
  }
}

cargar();
