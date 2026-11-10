/* LusterLux hero — "The Bay".
   A real Three.js detail garage: polished floor with a reflection, overhead
   LED bars, a key spotlight that sweeps on, and the car standing in it.

   On the car: this is THEIR McLaren, not a stock model. The plate is their own
   photograph and the geometry is a displaced mesh driven by a depth map of it
   (Depth Anything), so the camera genuinely moves around it with parallax, it
   catches the bay lighting, and it reflects in the floor. A generated CAD body
   was priced at 580 credits against a 242 balance, and a licensed McLaren mesh
   is not something to source casually, so photo-derived geometry is the honest
   way to put their actual car in 3D space.

   Scroll drives four beats:
     0.00  the bay is dark, the car sits dusty
     0.25  lights come up, foam goes on
     0.55  rinse, the spotlight sweeps, the floor lights up
     0.80  push in on the product

   Degrades to the rinsed photograph when WebGL is unavailable or the visitor
   prefers reduced motion. */
import * as THREE from './vendor/three.module.min.js';

const host = document.getElementById('bay');
if (host) boot(host);

function boot(host) {
  const cv = document.getElementById('bayCv');
  const reduced = matchMedia('(prefers-reduced-motion:reduce)').matches;
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, alpha: false });
  } catch (e) { host.classList.add('bay-static'); return; }
  if (reduced) { host.classList.add('bay-static'); return; }

  const BASE = (window.LL_BASE || '') + '/assets/';
  const V = host.getAttribute('data-v') || '';
  const small = innerWidth < 900;
  const tag = small ? 'm' : 'd';

  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, small ? 1.4 : 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.35;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x05070a);
  scene.fog = new THREE.Fog(0x080b10, 26, 72);

  const camera = new THREE.PerspectiveCamera(42, 2, 0.1, 200);

  /* ---------- the bay shell ---------- */
  function wallTexture() {
    const c = document.createElement('canvas');
    c.width = 256; c.height = 256;
    const g = c.getContext('2d');
    g.fillStyle = '#242a32'; g.fillRect(0, 0, 256, 256);
    g.strokeStyle = 'rgba(0,0,0,.34)'; g.lineWidth = 2;
    for (let y = 0; y <= 256; y += 32) { g.beginPath(); g.moveTo(0, y); g.lineTo(256, y); g.stroke(); }
    for (let r = 0; r < 8; r++) {
      const off = (r % 2) ? 32 : 0;
      for (let x = off; x <= 256; x += 64) {
        g.beginPath(); g.moveTo(x, r * 32); g.lineTo(x, r * 32 + 32); g.stroke();
      }
    }
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(10, 3);
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }
  const matWall = new THREE.MeshStandardMaterial({
    map: wallTexture(), color: 0xffffff, roughness: 0.88, metalness: 0.02
  });
  const back = new THREE.Mesh(new THREE.PlaneGeometry(60, 18), matWall);
  back.position.set(0, 5, -11.5); scene.add(back);

  const sideL = new THREE.Mesh(new THREE.PlaneGeometry(40, 18), matWall);
  sideL.rotation.y = Math.PI / 2; sideL.position.set(-13, 5, 2); scene.add(sideL);
  const sideR = sideL.clone(); sideR.rotation.y = -Math.PI / 2; sideR.position.x = 13; scene.add(sideR);

  /* polished concrete: dark, smooth enough to carry a reflection */
  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(80, 70),
    new THREE.MeshStandardMaterial({ color: 0x1b2026, roughness: 0.16, metalness: 0.72 })
  );
  floor.rotation.x = -Math.PI / 2; floor.position.y = -2.6; scene.add(floor);

  /* ---------- lighting rig ---------- */
  scene.add(new THREE.AmbientLight(0x4a5568, 0.95));
  const fill = new THREE.HemisphereLight(0x9fb4cc, 0x10151a, 0.55);
  scene.add(fill);

  const bars = [];
  for (let i = 0; i < 4; i++) {
    const bar = new THREE.Mesh(
      new THREE.BoxGeometry(15, 0.3, 0.62),
      new THREE.MeshBasicMaterial({ color: 0x0c1014 })
    );
    bar.position.set(0, 6.6, -8 + i * 4.4);
    scene.add(bar);
    const strip = new THREE.PointLight(0xdfe9ff, 0, 42, 2);
    strip.position.copy(bar.position); strip.position.y -= 0.4;
    scene.add(strip);
    bars.push({ bar, strip });
  }

  /* the key: a hard spotlight that comes on and sweeps the body */
  const key = new THREE.SpotLight(0xffffff, 0, 60, 0.46, 0.55, 1.4);
  key.position.set(-7, 11, 9);
  key.target.position.set(0, 0, 0);
  scene.add(key, key.target);

  /* a broad wash so the ROOM is lit, not only the car */
  const roomL = new THREE.DirectionalLight(0xc8d8ee, 0);
  roomL.position.set(-6, 10, 12);
  scene.add(roomL);
  const roomR = new THREE.DirectionalLight(0x9fb6d4, 0);
  roomR.position.set(8, 7, -6);
  scene.add(roomR);

  /* lime rim, the brand colour doing the back-edge */
  const rim = new THREE.PointLight(0xafcf0b, 0, 30, 2);
  rim.position.set(9, 2.6, -7);
  scene.add(rim);

  /* ---------- the car: their photo, displaced by its depth ---------- */
  const loader = new THREE.TextureLoader();
  const tex = (n) => {
    const t = loader.load(BASE + n + V);
    t.colorSpace = THREE.SRGBColorSpace;
    t.minFilter = THREE.LinearFilter;
    t.generateMipmaps = false;
    return t;
  };
  const mapClean = tex('wash/clean-' + tag + '.webp');
  const mapFoam  = tex('wash/foam-'  + tag + '.webp');
  const mapAlpha = loader.load(BASE + 'wash/alpha-' + tag + '.webp' + V);
  const mapDepth = loader.load(BASE + 'wash/depth-' + tag + '.webp' + V);
  /* The car's own matte. Depth alone cannot isolate it: monocular depth reads
     the near floor at 0.96, the same as the body. This matte comes from a
     background removal of their plate, so only the car enters the 3D set and
     the bay around it is ours. */
  const mapCar = loader.load(BASE + 'wash/car-' + tag + '.webp' + V);
  [mapAlpha, mapDepth, mapCar].forEach(t => { t.minFilter = THREE.LinearFilter; t.generateMipmaps = false; });

  const AR = 1920 / 1041;
  const CAR_W = 19;
  const carGeo = new THREE.PlaneGeometry(CAR_W, CAR_W / AR, small ? 150 : 300, small ? 85 : 170);

  const carMat = new THREE.ShaderMaterial({
    transparent: true,
    uniforms: {
      uClean: { value: mapClean }, uFoam: { value: mapFoam },
      uAlpha: { value: mapAlpha }, uDepth: { value: mapDepth }, uCar: { value: mapCar },
      uRinse: { value: 0 }, uDust: { value: 1 }, uRelief: { value: 2.9 },
      uKey: { value: new THREE.Vector3(-7, 11, 9) }, uLight: { value: 0 },
      uTime: { value: 0 }
    },
    vertexShader: `
      uniform sampler2D uDepth,uCar; uniform float uRelief;
      varying vec2 vUv; varying float vD; varying vec3 vPos;
      void main(){
        vUv = uv;
        float d = texture2D(uDepth, uv).r;   /* near is bright */
        float m = texture2D(uCar, uv).r;     /* only the body gets relief */
        vD = d;
        vec3 p = position;
        p.z += (d - 0.5) * uRelief * m;
        vPos = p;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
      }`,
    fragmentShader: `
      precision highp float;
      uniform sampler2D uClean,uFoam,uAlpha,uCar;
      uniform float uRinse,uDust,uLight,uTime;
      varying vec2 vUv; varying float vD; varying vec3 vPos;

      float h21(vec2 p){return fract(sin(dot(p,vec2(27.6,57.5)))*43758.5453);}
      float vn(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
        return mix(mix(h21(i),h21(i+vec2(1,0)),f.x),mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x),f.y);}
      float fbm(vec2 p){float s=0.,a=.5,m=0.;for(int i=0;i<4;i++){s+=a*vn(p);m+=a;a*=.5;p*=2.07;}return s/m;}

      void main(){
        /* only the car; the bay around it is the 3D set */
        float keep = texture2D(uCar, vUv).r;
        if (keep < 0.02) discard;

        vec3 clean = texture2D(uClean, vUv).rgb;
        vec3 foam  = texture2D(uFoam,  vUv).rgb;
        float fa   = texture2D(uAlpha, vUv).r;

        /* foam rinses off top-down with a ragged front, as in the real wash */
        float n = fbm(vUv*7.0)*0.55 + fbm(vUv*19.0)*0.45;
        float front = uRinse*1.55 - 0.28;
        float sheet = smoothstep(front-0.14, front+0.14, (1.0-vUv.y)*0.70 + n*0.46);
        vec3 col = mix(clean, foam, clamp(fa*sheet, 0.0, 1.0));

        /* road film before the wash: a dusty veil that lifts as foam goes on */
        float grime = fbm(vUv*vec2(9.0,5.0))*0.5 + 0.5;
        col = mix(col, mix(col, vec3(0.44,0.41,0.36), 0.30*grime), uDust);

        /* the bay's key light, so the body reacts to the rig coming on */
        col *= 0.42 + 0.58*uLight;
        float spec = pow(max(0.0, vD), 2.2) * uLight;
        col += vec3(0.30,0.34,0.40) * spec * 0.33;
        /* lime rim down the trailing edge */
        col += vec3(0.686,0.812,0.043) * smoothstep(0.55,1.0,vUv.x) * uLight * 0.11;

        gl_FragColor = vec4(col, keep);
      }`
  });
  const car = new THREE.Mesh(carGeo, carMat);
  car.position.set(0, 0.55, 0);
  scene.add(car);

  /* a cheap, convincing floor reflection: the same mesh mirrored and faded */
  const refl = new THREE.Mesh(carGeo, carMat.clone());
  refl.material.uniforms = carMat.uniforms;      /* share state */
  refl.material.opacity = 0.16;
  refl.scale.y = -1;
  refl.position.set(0, 0.55 - (CAR_W / AR) - 0.72, 0);
  scene.add(refl);

  /* ---------- scroll ---------- */
  const pin = host.querySelector('.bay-pin') || host;
  function progress() {
    const r = host.getBoundingClientRect();
    const span = host.offsetHeight - innerHeight;
    return span > 0 ? Math.min(1, Math.max(0, -r.top / span)) : 0;
  }
  function size() {
    const w = pin.clientWidth, h = pin.clientHeight;
    if (cv.width !== Math.round(w * renderer.getPixelRatio())) renderer.setSize(w, h, false);
    camera.aspect = w / h; camera.updateProjectionMatrix();
  }

  const ease = t => t * t * (3 - 2 * t);
  const lerp = (a, b, t) => a + (b - a) * t;
  const t0 = performance.now();
  let act = '1';

  function frame() {
    const p = progress();
    const time = (performance.now() - t0) / 1000;
    size();

    /* beats */
    const lights = 0.20 + 0.80 * ease(Math.min(1, Math.max(0, (p - 0.05) / 0.20)));
    const rinse  = Math.min(1, Math.max(0, (p - 0.24) / 0.34));
    const dust   = 1 - Math.min(1, Math.max(0, (p - 0.20) / 0.18));
    const push   = ease(Math.min(1, Math.max(0, (p - 0.58) / 0.42)));

    carMat.uniforms.uRinse.value = rinse;
    carMat.uniforms.uDust.value = dust;
    carMat.uniforms.uLight.value = lights;
    carMat.uniforms.uTime.value = time;

    bars.forEach((b, i) => {
      const on = Math.min(1, Math.max(0, (lights * 4) - i));
      b.strip.intensity = on * 38;
      b.bar.material.color.setRGB(0.05 + on * 0.75, 0.06 + on * 0.80, 0.07 + on * 0.86);
    });
    key.intensity = lights * 520;
    roomL.intensity = lights * 1.5;
    roomR.intensity = lights * 0.9;
    rim.intensity = lights * 34;
    /* the key sweeps across the body as the rinse finishes */
    const sweep = ease(Math.min(1, Math.max(0, (p - 0.30) / 0.36)));
    key.position.set(lerp(-9, 8, sweep), lerp(12, 8.4, sweep), lerp(10, 7, sweep));

    /* camera: a slow arc in, then a push toward the nose */
    const ang = lerp(-0.30, 0.16, ease(Math.min(1, p / 0.72)));
    const dist = lerp(19.5, 8.4, push);
    const hgt = lerp(3.4, 1.15, push);
    camera.position.set(Math.sin(ang) * dist, hgt, Math.cos(ang) * dist);
    camera.lookAt(lerp(0, 1.5, push), lerp(0.5, 0.2, push), 0);

    renderer.render(scene, camera);

    const want = p > 0.62 ? '2' : '1';
    if (want !== act) { act = want; host.setAttribute('data-act', act); }
    const r = document.getElementById('bayRail');
    if (r) r.style.width = (p * 100).toFixed(1) + '%';
  }

  let run = false;
  function tick() { if (!run) return; frame(); requestAnimationFrame(tick); }
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(es => {
      if (es[0].isIntersecting) { if (!run) { run = true; requestAnimationFrame(tick); } }
      else run = false;
    }, { rootMargin: '25% 0px' }).observe(host);
  } else { run = true; requestAnimationFrame(tick); }
  addEventListener('resize', () => { size(); frame(); }, { passive: true });

  let ready = 0;
  const done = () => { if (++ready >= 2) host.classList.add('bay-ready'); };
  mapClean.image ? done() : (mapClean.onUpdate = done);
  setTimeout(() => host.classList.add('bay-ready'), 1400);
  size(); frame();
  window.__bayProgress = progress;
}
