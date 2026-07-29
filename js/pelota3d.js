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
  ACESFilmicToneMapping,
} from 'three';
import { GLTFLoader } from '../vendor/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from '../vendor/jsm/libs/meshopt_decoder.module.js';
import { RoomEnvironment } from '../vendor/jsm/environments/RoomEnvironment.js';

/* Encuadre. El lienzo es más alto que la pelota para que el rebote tenga aire:
   ALTO_REL es cuántas veces la caja de la pelota mide el lienzo. La cámara se
   calcula a partir de eso, no a ojo, así el tamaño en pantalla coincide con el
   de la imagen que reemplaza. */
const ALTO_REL = 2.6;
const ANCHO_REL = 1.34;
const FOV = 30;
const PERIODO = 1.25;      // segundos por rebote
const ALTURA = 1.45;       // unidades de mundo que sube (radio de la pelota = 1)
const GIRO = 0.42;         // radianes por segundo — "levemente"

export async function montarPelota3D(caja, imagen) {
  if (!caja.clientWidth) return;

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
  function medir() {
    const a = caja.clientWidth;
    if (!a) return;
    const W = Math.round(a * ANCHO_REL);
    const H = Math.round(a * ALTO_REL);
    renderer.setSize(W, H, false);
    lienzo.style.width = W + 'px';
    lienzo.style.height = H + 'px';
    lienzo.style.left = (a - W) / 2 + 'px';
    camara.aspect = W / H;
    camara.updateProjectionMatrix();
  }

  const escena = new Scene();
  /* Distancia derivada del encuadre: si la pelota (diámetro 2) tiene que ocupar
     1/ALTO_REL del alto visible, entonces alto visible = 2·ALTO_REL y
     d = ALTO_REL / tan(fov/2). Sin esto habría que ajustar la cámara a mano cada
     vez que cambia el tamaño del wordmark. */
  const camara = new PerspectiveCamera(FOV, 1, 0.1, 100);
  camara.position.z = ALTO_REL / Math.tan((FOV / 2) * Math.PI / 180);
  medir();
  new ResizeObserver(medir).observe(caja);

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
  // reposo: apoyada abajo del lienzo, donde estaba la imagen
  const yReposo = -ALTO_REL + 1;

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
  modelo.traverse((o) => {
    if (o.isMesh && o.material) {
      o.material.envMapIntensity = 1.15;
      if (o.material.map) o.material.map.anisotropy = 8;
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

    // parábola de rebote: sube y baja sin quedarse quieta arriba
    const f = (t % PERIODO) / PERIODO;
    pelota.position.y = yReposo + ALTURA * (1 - Math.pow(2 * f - 1, 2));
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
