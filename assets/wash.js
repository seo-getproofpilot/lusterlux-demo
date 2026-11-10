/* LusterLux hero — "Two Scales".
   Act I  THE RINSE : their own McLaren, foamed, rinsed off by scroll. Real
                      photography; the foam alpha is the measured difference
                      between their two registered frames, dissolved away with
                      noise so the edge is ragged like real rinsing.
   Act II THE DIVE  : the camera pushes into the clear coat. Grit sits on the
                      paint, NanoFusion capsules close around each particle and
                      float it clear, then the hydrophobic layer forms and
                      water beads. Procedural, so it costs nothing to ship.

   One canvas, one shader, driven by one scroll progress. A rAF loop runs only
   while the hero is on screen. Without WebGL the markup already shows the
   rinsed plate, so the section degrades to a still. */
(function () {
  'use strict';
  var host = document.getElementById('wash');
  if (!host) return;
  var cv = document.getElementById('washCv');
  var reduced = matchMedia('(prefers-reduced-motion:reduce)').matches;
  var gl = null;
  try {
    gl = cv.getContext('webgl', { alpha: false, antialias: false, powerPreference: 'high-performance' });
  } catch (e) { gl = null; }
  if (!gl || reduced) { host.classList.add('wash-static'); return; }

  var VERT =
    'attribute vec2 p;varying vec2 v;void main(){v=p*0.5+0.5;gl_Position=vec4(p,0.,1.);}';

  var FRAG = [
    'precision highp float;',
    'varying vec2 v;',
    'uniform sampler2D uFoam,uClean,uAlpha;',
    'uniform vec2 uRes,uImg;',
    'uniform float uP,uT;',

    'float h21(vec2 p){return fract(sin(dot(p,vec2(27.619,57.583)))*43758.5453);}',
    'vec2 h22(vec2 p){return fract(sin(vec2(dot(p,vec2(127.1,311.7)),dot(p,vec2(269.5,183.3))))*43758.5453);}',
    'float vnoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);',
    ' float a=h21(i),b=h21(i+vec2(1,0)),c=h21(i+vec2(0,1)),d=h21(i+vec2(1,1));',
    ' return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);}',
    'float fbm(vec2 p){float s=0.,m=0.,a=.5;for(int i=0;i<5;i++){s+=a*vnoise(p);m+=a;a*=.5;p*=2.03;}return s/m;}',
    /* the wash bay is in shade; open the shadows and warm it slightly */
    'vec3 lift(vec3 c){c=pow(c,vec3(0.82));c=(c-0.5)*1.06+0.54;',
    ' c*=vec3(1.035,1.015,0.985);return clamp(c,0.,1.);}',

    /* cover-fit the plate into the viewport, with a slow push-in */
    'vec2 coverUV(vec2 uv,float zoom,vec2 focus){',
    ' float ar=uRes.x/uRes.y, ir=uImg.x/uImg.y;',
    ' vec2 s=ar>ir?vec2(1.,ir/ar):vec2(ar/ir,1.);',
    ' uv=(uv-.5)*s/zoom+focus;return uv;}',

    /* ---------- Act II: the clear coat, at grit scale ----------
       A macro view of lit clear coat, not a void. The first pass rendered
       near-black (mean luma 34) which is exactly the slab look to avoid, so
       the base carries real luminance, orange-peel texture and a broad key. */
    'vec3 micro(vec2 uv,float m){',
    ' float ar=uRes.x/uRes.y; vec2 q=vec2((uv.x-.5)*ar,uv.y-.5);',
    ' float a=smoothstep(0.00,0.26,m), b=smoothstep(0.22,0.74,m), c=smoothstep(0.46,1.0,m);',
    /* lit panel: graphite blue, brighter toward the key, with orange peel */
    ' float peel=fbm(q*13.0)*0.6+fbm(q*34.0)*0.4;',
    ' vec3 col=mix(vec3(.105,.125,.150),vec3(.300,.340,.385),smoothstep(-.55,.55,uv.y*1.1-.1));',
    ' col+=vec3(.055,.062,.070)*(peel-0.5)*1.6;',
    /* broad key light sweeping the panel + a tight specular bar */
    ' float kx=-1.05+2.4*fract(uT*.035);',
    ' col+=vec3(.42,.47,.52)*exp(-pow((q.x-kx)*1.15,2.))*.55;',
    ' col+=vec3(.95,1.,1.)*exp(-pow((q.x-kx)*6.5,2.))*.22;',
    ' col+=vec3(.10,.12,.14)*pow(max(0.,1.-length(q*vec2(.8,1.5))),2.0);',
    /* Grit, and the polymer shell that closes around it and carries it off.
       The shell must stay with the particle while it lifts — the point of the
       sequence is that the dirt leaves INSIDE the capsule. Phases overlap so
       there is never a frame of lifted dark grit on an empty panel. */
    ' vec2 g=q*3.6; vec2 cell=floor(g);',
    ' vec3 lime=vec3(.686,.812,.043);',
    ' for(int dy=-1;dy<=1;dy++){for(int dx=-1;dx<=1;dx++){',
    '   vec2 id=cell+vec2(float(dx),float(dy));',
    '   vec2 rnd=h22(id); float seed=h21(id+7.1);',
    '   if(seed<.34) continue;',
    '   vec2 pc=id+.18+rnd*.64;',
    '   float lift=b*(.70+seed*1.05);',
    '   pc.y+=lift; pc.x+=sin(seed*31.4+uT*.5)*lift*.26;',
    '   float d=length(g-pc);',
    '   float gr=.050+seed*.040;',
    '   float cr=gr+a*(.062+seed*.028);',
    /* the capsule only fades once it has travelled, not on a global clock */
    '   float gone=smoothstep(.55,1.15,lift);',
    '   float vis=a*(1.-gone);',
    /* dirt rides inside the shell and leaves with it */
    '   float dirt=smoothstep(gr,gr*.45,d)*(1.-gone);',
    '   col=mix(col,vec3(.115,.095,.075),dirt*.92);',
    '   float shell=smoothstep(cr,cr*.90,d)-smoothstep(cr*.90,cr*.60,d);',
    '   col+=lime*shell*2.1*vis;',
    '   float inner=smoothstep(cr*.92,0.,d);',
    '   col=mix(col,mix(col,lime,.22),inner*vis*.9);',
    '   col+=lime*exp(-pow(d/max(cr,1e-4),2.0)*1.5)*.20*vis;',
    ' }}',
    /* the hydrophobic layer that stays behind, and water beading on it */
    ' if(c>.001){',
    '  col=mix(col,col*1.07+vec3(.012,.016,.014),c*.6);',
    '  vec2 bg=q*5.0; vec2 bc=floor(bg);',
    '  for(int dy=-1;dy<=1;dy++){for(int dx=-1;dx<=1;dx++){',
    '    vec2 id=bc+vec2(float(dx),float(dy));',
    '    vec2 rnd=h22(id+3.3); float seed=h21(id+11.7);',
    '    if(seed<.40) continue;',
    '    vec2 pc=id+.2+rnd*.6;',
    '    float r=(.090+seed*.090)*smoothstep(0.,.55,c);',
    '    if(r<1e-3) continue;',
    '    float d=length(bg-pc);',
    '    float bead=smoothstep(r,r*.88,d);',
    '    vec2 n=(bg-pc)/r;',
    '    float spec=pow(max(0.,1.-length(n-vec2(-.34,.40))),7.)*1.9;',
    '    float rim=smoothstep(r,r*.95,d)-smoothstep(r*.95,r*.74,d);',
    '    col=mix(col,col*1.34+vec3(.04,.05,.055),bead*.92);',
    '    col+=vec3(1.,1.,.98)*spec*bead;',
    '    col+=vec3(.72,.86,.56)*rim*.38;',
    '  }}',
    ' }',
    ' return col;}',

    'void main(){',
    ' vec2 uv=v;',
    /* --- Act I --- */
    ' float rinse=smoothstep(0.02,0.56,uP);',
    ' float push=1.0+0.22*smoothstep(0.0,0.62,uP);',
    ' vec2 focus=mix(vec2(.56,.52),vec2(.64,.46),smoothstep(.2,.78,uP));',
    ' vec2 iuv=coverUV(uv,push,focus);',
    ' vec3 col;',
    ' if(iuv.x<0.||iuv.x>1.||iuv.y<0.||iuv.y>1.){col=vec3(.045,.05,.058);}',
    ' else{',
    '  vec3 clean=lift(texture2D(uClean,vec2(iuv.x,1.-iuv.y)).rgb);',
    '  vec3 foam =lift(texture2D(uFoam ,vec2(iuv.x,1.-iuv.y)).rgb);',
    '  float fa  =texture2D(uAlpha,vec2(iuv.x,1.-iuv.y)).r;',
    /* dissolve front sweeps down, ragged with fbm, so foam sheets off */
    '  float n=fbm(iuv*7.0)*0.55+fbm(iuv*19.0)*0.45;',
    '  float front=rinse*1.55-0.28;',
    '  float keep=smoothstep(front-0.14,front+0.14,(1.0-iuv.y)*0.70+n*0.46);',
    '  float a=fa*keep;',
    '  col=mix(clean,foam,clamp(a,0.,1.));',
    /* a wet sheet of light riding the rinse front */
    '  float band=exp(-pow(((1.0-iuv.y)*0.70+n*0.46-front)*7.5,2.0));',
    '  col+=vec3(.42,.52,.46)*band*fa*0.55*(1.0-smoothstep(.5,.62,uP));',
    '  col*=1.0-0.28*smoothstep(0.42,0.60,uP);',   /* dim into the dive */
    ' }',
    /* --- Act II --- */
    ' float m=smoothstep(0.52,1.0,uP);',
    ' if(m>0.001) col=mix(col,micro(uv,m),smoothstep(0.52,0.66,uP));',
    /* grade: a touch of contrast and a vignette */
    ' col=(col-.5)*1.045+.5;',
    ' float vg=1.0-0.20*pow(length((uv-.5)*vec2(1.08,1.0)),2.2);',
    ' gl_FragColor=vec4(max(col,vec3(0.))*vg,1.0);}'
  ].join('\n');

  function sh(type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      console.warn('wash shader:', gl.getShaderInfoLog(s)); return null;
    }
    return s;
  }
  var vs = sh(gl.VERTEX_SHADER, VERT), fs = sh(gl.FRAGMENT_SHADER, FRAG);
  if (!vs || !fs) { host.classList.add('wash-static'); return; }
  var pr = gl.createProgram();
  gl.attachShader(pr, vs); gl.attachShader(pr, fs); gl.linkProgram(pr);
  if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) { host.classList.add('wash-static'); return; }
  gl.useProgram(pr);

  var buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 3,-1, -1,3]), gl.STATIC_DRAW);
  var loc = gl.getAttribLocation(pr, 'p');
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

  var U = {};
  ['uFoam','uClean','uAlpha','uRes','uImg','uP','uT'].forEach(function (n) {
    U[n] = gl.getUniformLocation(pr, n);
  });

  var tag = innerWidth < 900 ? 'm' : 'd';
  var base = (window.LL_BASE || '') + '/assets/wash/';
  var V = host.getAttribute('data-v') || '';
  var ready = 0, imgW = 1, imgH = 1;

  function texture(unit, url, uni) {
    var t = gl.createTexture();
    gl.activeTexture(gl.TEXTURE0 + unit);
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, 1, 1, 0, gl.RGB, gl.UNSIGNED_BYTE, new Uint8Array([10,12,14]));
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.uniform1i(U[uni], unit);
    var im = new Image();
    im.crossOrigin = 'anonymous';
    im.onload = function () {
      imgW = im.naturalWidth; imgH = im.naturalHeight;
      gl.activeTexture(gl.TEXTURE0 + unit);
      gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, im);
      ready++;
      if (ready >= 3) host.classList.add('wash-ready');
      draw();
    };
    im.src = url;
  }
  texture(0, base + 'foam-'  + tag + '.webp' + V, 'uFoam');
  texture(1, base + 'clean-' + tag + '.webp' + V, 'uClean');
  texture(2, base + 'alpha-' + tag + '.webp' + V, 'uAlpha');

  var dpr = Math.min(devicePixelRatio || 1, 1.75);
  // Size to the PINNED box, not the tall scroll track: host is 360vh and would
  // give a canvas several thousand pixels tall for a one-viewport view.
  var pin = host.querySelector('.wash-pin') || host;
  function size() {
    var w = Math.round(pin.clientWidth * dpr), h = Math.round(pin.clientHeight * dpr);
    if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
    gl.viewport(0, 0, cv.width, cv.height);
  }
  var t0 = performance.now();
  function progress() {
    var r = host.getBoundingClientRect();
    var span = host.offsetHeight - innerHeight;
    return span > 0 ? Math.min(1, Math.max(0, -r.top / span)) : 0;
  }
  var rail = document.getElementById('washRail');
  var act = '1';
  function draw() {
    size();
    var p = progress();
    gl.uniform2f(U.uRes, cv.width, cv.height);
    gl.uniform2f(U.uImg, imgW, imgH);
    gl.uniform1f(U.uP, p);
    gl.uniform1f(U.uT, (performance.now() - t0) / 1000);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    // the copy swaps once the dive has actually started, not at the midpoint,
    // so the rinse headline stays up while the car is still being rinsed
    var want = p > 0.58 ? '2' : '1';
    if (want !== act) { act = want; host.setAttribute('data-act', act); }
    if (rail) rail.style.width = (p * 100).toFixed(1) + '%';
  }

  var run = false;
  function tick() { if (!run) return; draw(); requestAnimationFrame(tick); }
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (es) {
      if (es[0].isIntersecting) { if (!run) { run = true; requestAnimationFrame(tick); } }
      else { run = false; }
    }, { rootMargin: '20% 0px' }).observe(host);
  } else { run = true; requestAnimationFrame(tick); }
  addEventListener('resize', function () { dpr = Math.min(devicePixelRatio || 1, 1.75); draw(); }, { passive: true });
  window.__washProgress = progress;
})();
