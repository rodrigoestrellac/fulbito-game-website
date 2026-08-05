/* releases.js — las descargas salen del ÚLTIMO release de este repo.
   No hay versiones hardcodeadas en el HTML: se publica un release y la web se
   entera sola. Si la API de GitHub no contesta (rate limit: 60 pedidos por hora
   por IP, o el usuario sin red) se usa FALLBACK, que hay que actualizar a mano
   cuando se publica una versión nueva. Ver README. */

const REPO = 'rodrigoestrellac/fulbito-game-website';

/* Espejo estático del release M88. Actualizar al publicar uno nuevo.
   Los bytes salen de `dist/` después de correr pack_release (stat, no redondeo):
   si no coinciden con el asset real, la web muestra un tamaño equivocado justo
   cuando la API falla — o sea, justo cuando nadie lo va a poder verificar. */
const FALLBACK = {
  tag: 'M88',
  archivos: {
    winSetup: { nombre: 'FulbitoSetup-M88.exe', bytes: 89623546 },
    winZip:   { nombre: 'Fulbito-M88-windows.zip', bytes: 113854998 },
    mac:      { nombre: 'Fulbito-M88-mac.zip', bytes: 122530416 },
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
    /* /releases en vez de /releases/latest: cuesta el mismo pedido y trae,
       además del último release, el download_count de TODOS los assets — de
       ahí sale el contador de descargas. */
    const r = await fetch(`https://api.github.com/repos/${REPO}/releases?per_page=100`, {
      headers: { Accept: 'application/vnd.github+json' },
    });
    if (!r.ok) throw new Error(`GitHub respondió ${r.status}`);
    const releases = await r.json();

    /* contador: los binarios de todas las versiones (CHECKSUMS.txt no es una
       descarga del juego). Sin dato de la API el elemento queda oculto — un
       número hardcodeado acá envejecería mintiendo. */
    const total = releases.flatMap((rel) => rel.assets || [])
      .filter((a) => /\.(exe|zip)$/i.test(a.name))
      .reduce((s, a) => s + (a.download_count || 0), 0);
    const cont = document.querySelector('[data-rel="descargas"]');
    if (cont && total > 0) {
      cont.textContent = `Ya se descargó ${total.toLocaleString('es-AR')} ${total === 1 ? 'vez' : 'veces'}.`;
      cont.hidden = false;
    }

    const data = releases.find((rel) => !rel.draft && !rel.prerelease);
    if (!data) return;
    const archivos = clasificar(data.assets || []);
    if (!archivos.winSetup && !archivos.winZip && !archivos.mac) return; // release sin binarios: queda el fallback
    pintar({ tag: data.tag_name, archivos });
  } catch (e) {
    console.info('[releases] queda el release estático:', e.message);
  }
}

cargar();
