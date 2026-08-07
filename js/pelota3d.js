/* pelota3d.js — la pelota Teamgeist en 3D al lado de FULBITO, rebotando y
   girando despacio. Es el mismo modelo y el mismo gesto que el hero de
   fulbito.futbol; acá va más contenido porque comparte renglón con el wordmark.

   Esto es una MEJORA, no la base: el hero se ve completo con el PNG del render
   (assets/brand/pelota.webp), y este módulo sólo se importa si vale la pena
   (ver main.js). Si algo falla, la imagen se queda y no se nota.

   Modelo: «Adidas Teamgeist Ball (Germany 2006)» de Armellino Raffaele
   (Sketchfab), CC-BY-4.0. Texturas editadas. Atribución en el footer. */

import {
  WebGLRenderer, PerspectiveCamera, Scene, Group,
  DirectionalLight, AmbientLight, PMREMGenerator, Box3, Vector3,
  ACESFilmicToneMapping, NoToneMapping, Color,
} from 'three';
import { GLTFLoader } from '../vendor/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from '../vendor/jsm/libs/meshopt_decoder.module.js';
import { RoomEnvironment } from '../vendor/jsm/environments/RoomEnvironment.js';

/* El rebote va ENTRE EL BASELINE Y EL ALTO DE LAS LETRAS de FULBITO: apoya en el
   baseline y en el punto más alto su tope llega a la altura de las mayúsculas,
   sin pasarse. Nada de esto se estima: la altura de mayúscula se MIDE de la
   tipografía ya cargada (`actualBoundingBoxAscent` de una F), porque depende del
   font-size —que es fluido, con clamp— y de que Oswald haya llegado. Con la
   tipografía de respaldo la métrica es otra y el rebote saldría mal.

   El recorrido es corto a propósito: la pelota mide ~80 % del alto de las letras,
   así que entre las dos líneas quedan ~30 px en desktop y ~10 en mobile. Si se
   quisiera un pique más grande, la palanca es el `width` de `.wordmark__caja`:
   una pelota más chica deja más recorrido. */
const FOV = 30;
const PERIODO = 1.25;      // segundos por pique
const GIRO = 0.42;         // radianes por segundo — "levemente"
const RECORRIDO_MIN = 0.10;  // fracción del diámetro: piso, para que siempre se note algo

/* ⚠️ AIRE — por qué el lienzo NO puede medir justo lo que mide el recorrido.
   La primera versión calculaba el alto como `diámetro + recorrido` exacto, con
   la idea de que en el pico la pelota tocara el borde de arriba y nada más. En
   la práctica se CORTABA: la silueta de una esfera en perspectiva es más grande
   que su radio geométrico proyectado —el contorno visible abarca un ángulo
   asin(r/d) y no atan(r/d)—, y encima la pelota lleva una `drop-shadow` que
   también ocupa. Los dos sobrantes son chicos, pero pasan justo en el pico, que
   es donde se mira. Con aire alrededor no hay nada que ajustar al píxel. */
const AIRE = 0.07;         // fracción del diámetro, de aire alrededor de la pelota
/* La pelota apoya un poco POR DEBAJO del baseline. Con el punto de apoyo
   exactamente sobre la línea, el pique arranca pareciendo que flota: el ojo lee
   el contacto en el ecuador de la sombra, no en la tangente de la esfera. */
const BAJADA = 0.07;       // fracción del diámetro que baja el punto de apoyo

/** Altura de mayúscula en px de la tipografía REAL del elemento. */
function altoDeMayuscula(el) {
  const cs = getComputedStyle(el);
  const ctx = document.createElement('canvas').getContext('2d');
  ctx.font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
  return ctx.measureText('F').actualBoundingBoxAscent || parseFloat(cs.fontSize) * 0.72;
}

export async function montarPelota3D(caja, imagen, titulo) {
  if (!caja.clientWidth) return;
  // sin esto se mide la tipografía de respaldo y el rebote queda con otra altura
  if (document.fonts && document.fonts.ready) await document.fonts.ready;

  const renderer = new WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.toneMapping = ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.18;

  const lienzo = renderer.domElement;
  lienzo.setAttribute('aria-hidden', 'true');
  Object.assign(lienzo.style, {
    position: 'absolute', left: '0', bottom: '0', top: 'auto',
    opacity: '0', transition: 'opacity .45s ease', pointerEvents: 'none',
  });
  caja.appendChild(lienzo);

  /* El wordmark es fluido (clamp + vw): la caja cambia de tamaño al girar el
     teléfono o al arrastrar la ventana. Sin esto el lienzo se queda con la
     medida que tenía cuando cargó — que es tarde, después del load, y puede no
     ser la definitiva. */
  let yReposo = 0, recorrido = 0;   // en unidades de mundo (radio de la pelota = 1)

  function medir() {
    const d = caja.clientWidth;                       // diámetro de la pelota, en px
    if (!d) return;
    const mayuscula = titulo ? altoDeMayuscula(titulo) : d * 1.25;
    const aire = d * AIRE;
    const bajada = d * BAJADA;
    /* Recorrido: la pelota apoya `bajada` px DEBAJO del baseline y en el pico su
       tope tiene que llegar justo al alto de las mayúsculas. O sea que sube todo
       lo que va del tope de la pelota en reposo (d − bajada) al de las letras. */
    const subePx = Math.max(mayuscula - d + bajada, d * RECORRIDO_MIN);

    const W = Math.ceil(d + 2 * aire);
    const H = Math.ceil(d + subePx + aire);
    renderer.setSize(W, H, false);
    lienzo.style.width = W + 'px';
    lienzo.style.height = H + 'px';
    lienzo.style.left = (d - W) / 2 + 'px';
    // el piso del lienzo baja con la pelota; como está en position:absolute,
    // asomarse por abajo de la caja no mueve nada del layout
    lienzo.style.bottom = -bajada + 'px';

    /* Un radio de pelota = d/2 px, así que el alto visible en unidades de mundo
       es 2H/d y la cámara va a (H/d)/tan(fov/2). El borde de abajo del lienzo cae
       en y = -H/d, y ahí apoya la pelota: su centro queda a un radio de eso. */
    camara.aspect = W / H;
    camara.position.z = (H / d) / Math.tan((FOV / 2) * Math.PI / 180);
    camara.updateProjectionMatrix();

    yReposo = -H / d + 1;
    recorrido = 2 * subePx / d;
    pelota.position.y = yReposo;
  }

  const escena = new Scene();
  // el encuadre lo fija medir(), que es el que conoce el diámetro real
  const camara = new PerspectiveCamera(FOV, 1, 0.1, 100);

  const pmrem = new PMREMGenerator(renderer);
  escena.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

  // mismas luces que el render estático: clave dorada arriba-izquierda
  const clave = new DirectionalLight(0xF2DFA6, 2.6);
  clave.position.set(-2.4, 3.0, 2.2);
  escena.add(clave);
  const relleno = new DirectionalLight(0x8FA98C, 0.55);
  relleno.position.set(2.6, -1.2, 1.4);
  escena.add(relleno);
  escena.add(new AmbientLight(0xF0EDE4, 0.35));

  const pelota = new Group();
  escena.add(pelota);
  medir();
  // el wordmark es fluido: al cambiar de tamaño hay que volver a medir todo
  new ResizeObserver(medir).observe(caja);

  const gltf = await new Promise((ok, mal) => {
    const cargador = new GLTFLoader();
    cargador.setMeshoptDecoder(MeshoptDecoder);
    cargador.load('assets/ball/teamgeist.glb', ok, undefined, mal);
  });

  const modelo = gltf.scene;
  const bb = new Box3().setFromObject(modelo);
  const radio = bb.getSize(new Vector3()).length() / (2 * Math.sqrt(3));
  modelo.position.sub(bb.getCenter(new Vector3()));
  modelo.scale.setScalar(1 / radio);
  /* PRUEBA (no publicar sin OK de Rodrigo): la pelota dorada de la final de la
     Copa (M106), con los tintes de Pelota.Oro / Pelota.Verde del juego. El
     mecanismo es el mismo de Unity (el tinte MULTIPLICA la textura), pero la
     luz de este hero está calibrada para la pelota BLANCA y lavaba el color:
     acá el tinte va pre-saturado y con menos reflejo de entorno, y la clave
     dorada baja un punto — sólo mientras la pelota va tintada. */
  /* La pelota de la final, con los COLORES MEDIDOS del juego: los hex salen de
     samplear una captura in-game (cuerpo 172,135,17 · paneles 39,113,61), no
     de los tintes — el color final en Unity es tinte × textura × luz toon y
     acá esa cadena no existe. Material UNLIT (MeshBasicMaterial): ni ACES, ni
     especular, ni sombreado — plano y opaco como lo pinta el juego. El hex se
     pasa por Color() para que three lo tome como sRGB y no lo aclare. */
  renderer.toneMapping = NoToneMapping;
  const PLANOS = { Ball_Triangles: 0xac8811, Ball_Ovals: 0x27713d };
  /* luz suave: la ambiente sostiene el color medido tal cual y la direccional
     agrega el poquito de volumen y brillo que pidio Rodrigo ("muy plana") —
     en el tono medio sigue estando el color sampleado del juego */
  clave.intensity = 0.7;
  relleno.intensity = 0.2;
  escena.children.forEach((l) => { if (l.isAmbientLight) l.intensity = 0.78; });
  modelo.traverse((o) => {
    if (o.isMesh && o.material) {
      const hex = PLANOS[o.material.name];
      if (hex !== undefined) {
        if (o.material.map) o.material.map.anisotropy = 8;
        o.material.color = new Color(hex);
        o.material.roughness = 0.72;
        o.material.metalness = 0;
        o.material.envMapIntensity = 0.18;
        // el GLB trae BARNIZ (clearcoat): su lustre no lo baja `roughness`
        if ('clearcoat' in o.material) o.material.clearcoat = 0;
      }
    }
  });
  pelota.add(modelo);
  pelota.rotation.set(0.34, -0.62, 0.06);
  pelota.position.y = yReposo;

  renderer.render(escena, camara);
  renderer.render(escena, camara);   // el envmap entra en la segunda pasada
  lienzo.style.opacity = '1';
  if (imagen) imagen.style.visibility = 'hidden';   // sigue ocupando su lugar

  /* Se dibuja SÓLO si el hero está a la vista y la pestaña está al frente: una
     pelota girando en una pestaña de fondo es ventilador gratis. */
  let visible = true, activa = true, raf = 0, t0 = 0;

  function frame(ahora) {
    if (!visible || !activa) { raf = 0; return; }
    raf = requestAnimationFrame(frame);
    if (!t0) t0 = ahora;
    const t = (ahora - t0) / 1000;

    // parábola de pique: sube y baja sin quedarse quieta arriba
    const f = (t % PERIODO) / PERIODO;
    pelota.position.y = yReposo + recorrido * (1 - Math.pow(2 * f - 1, 2));
    pelota.rotation.y = -0.62 + t * GIRO;
    pelota.rotation.x = 0.34 + Math.sin(t * 0.8) * 0.06;

    renderer.render(escena, camara);
  }
  function arrancar() { if (!raf && visible && activa) { t0 = 0; raf = requestAnimationFrame(frame); } }

  new IntersectionObserver((es) => {
    visible = es[0].isIntersecting;
    visible ? arrancar() : null;
  }, { threshold: 0 }).observe(caja);

  document.addEventListener('visibilitychange', () => {
    activa = !document.hidden;
    activa ? arrancar() : null;
  });

  arrancar();
}
