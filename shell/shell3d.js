/* StillPoint 3D shell — PHOTOREALISTIC
   Matched to the product photography (1a.png, 1b.png, 3.png):
   - Dark graphite body with matte clearcoat finish
   - Rich walnut lid with procedural wood grain
   - Warm oak desk with visible grain pattern
   - Soft contact shadows and ambient occlusion feel
   - Studio lighting: warm key, cool fill, subtle rim
   - Live CanvasTexture from firmware                              */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const canvas = document.getElementById('scene3d');
const epdCanvas = document.getElementById('epd');

/* ───────── Scene ───────── */
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1e1812);
scene.fog = new THREE.Fog(0x1e1812, 12, 22);

const camera = new THREE.PerspectiveCamera(28, 1, 0.1, 100);
camera.position.set(0, 1.5, 6.8);  // seated at desk, looking down — meditation gaze

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.25;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

/* ───────── Orbit Controls ───────── */
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.enablePan = false;
controls.minDistance = 3.5;
controls.maxDistance = 14;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.6;
controls.target.set(0, 0.0, 0);
controls.maxPolarAngle = Math.PI * 0.58;  // prevent going too far below
controls.minPolarAngle = Math.PI * 0.32;  // prevent going too high above

let idleTimer = null;
controls.addEventListener('start', () => {
  controls.autoRotate = false;
  clearTimeout(idleTimer);
});
controls.addEventListener('end', () => {
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => { controls.autoRotate = true; }, 8000);
});

/* ───────── Lighting (warm studio, matched to photos) ───────── */
// Hemisphere for natural ambient fill
scene.add(new THREE.HemisphereLight(0xffeedd, 0x443322, 0.6));

// Key light — warm from upper-right (like the desk lamp in 1a.png)
const keyLight = new THREE.DirectionalLight(0xffedcc, 2.8);
keyLight.position.set(4, 6, 5);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(2048, 2048);
keyLight.shadow.camera.near = 1;
keyLight.shadow.camera.far = 20;
keyLight.shadow.camera.left = -4;
keyLight.shadow.camera.right = 4;
keyLight.shadow.camera.top = 4;
keyLight.shadow.camera.bottom = -4;
keyLight.shadow.bias = -0.0005;
keyLight.shadow.normalBias = 0.02;
keyLight.shadow.radius = 6;
scene.add(keyLight);

// Fill light — cooler from the left for depth
const fillLight = new THREE.DirectionalLight(0xc8d8f0, 0.5);
fillLight.position.set(-5, 3, 3);
scene.add(fillLight);

// Rim light — subtle backlight to separate device from desk
const rimLight = new THREE.DirectionalLight(0xfff8f0, 0.35);
rimLight.position.set(0, 3, -6);
scene.add(rimLight);

// Warm under-bounce from the oak desk
const bounceLight = new THREE.DirectionalLight(0xffd4a0, 0.15);
bounceLight.position.set(0, -4, 2);
scene.add(bounceLight);

/* ───────── Environment map for realistic reflections ───────── */
const pmremGenerator = new THREE.PMREMGenerator(renderer);
const envScene = new THREE.Scene();
// Warm room-like environment
envScene.background = new THREE.Color(0x3d3020);
const envL1 = new THREE.DirectionalLight(0xfff0dd, 3.0);
envL1.position.set(3, 5, 5);
envScene.add(envL1);
const envL2 = new THREE.DirectionalLight(0xddd8d0, 1.5);
envL2.position.set(-4, 2, -3);
envScene.add(envL2);
// Warm ambient panel (simulates window reflection)
const panelGeo = new THREE.PlaneGeometry(8, 5);
const panelMat = new THREE.MeshBasicMaterial({ color: 0xfff4e8, side: THREE.DoubleSide });
const panel = new THREE.Mesh(panelGeo, panelMat);
panel.position.set(0, 4, -6);
envScene.add(panel);
const envMap = pmremGenerator.fromScene(envScene, 0.04).texture;
scene.environment = envMap;
pmremGenerator.dispose();

/* ───────── Helper: smooth rounded-rect 2D shape ───────── */
function rrect(w, h, r) {
    const s = new THREE.Shape();
    s.moveTo(-w/2 + r, -h/2);
    s.lineTo( w/2 - r, -h/2);
    s.quadraticCurveTo( w/2, -h/2,  w/2, -h/2 + r);
    s.lineTo( w/2,  h/2 - r);
    s.quadraticCurveTo( w/2,  h/2,  w/2 - r,  h/2);
    s.lineTo(-w/2 + r,  h/2);
    s.quadraticCurveTo(-w/2,  h/2, -w/2,  h/2 - r);
    s.lineTo(-w/2, -h/2 + r);
    s.quadraticCurveTo(-w/2, -h/2, -w/2 + r, -h/2);
    return s;
}

function smoothstep(edge0, edge1, x) {
    const t = Math.max(0, Math.min(1, (x - edge0) / (edge1 - edge0)));
    return t * t * (3 - 2 * t);
}

/* ═══════════════════════════════════════════
 *  STILLPOINT DEVICE
 *  Real: 200mm wide × 120mm tall × 150mm deep
 *  3D units: 3.3W × 1.8H × 2.4D
 * ═══════════════════════════════════════════ */

const TILT_DEG = 18;
const TILT_RAD = TILT_DEG * Math.PI / 180;

const BW = 2.8;
const BH = 1.8;
const BD = 2.1;
const BR = 0.75;   // large radius — smooth pebble shape

// Reclined flat facet sculpted into the front of the body — the screen mounts
// flush on this plane, so the display is built into the stone, not floating.
const FACET_HW = 1.05;   // facet half-extents
const FACET_HH = 0.68;
const FACET_Z0 = 0.88;   // facet depth

const TY =  BH / 2;
const BY = -BH / 2;
const FZ =  BD / 2;
const BZ = -BD / 2;

const device = new THREE.Group();

/* ── 1. Main body — dark graphite with matte clearcoat ── */
const bodyGeom = new RoundedBoxGeometry(BW, BH, BD, 48, BR);
const pos = bodyGeom.attributes.position;

for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    let y = pos.getY(i);
    let z = pos.getZ(i);

    // Flat bottom
    if (y < BY + 0.15) {
        const squish = smoothstep(BY + 0.15, BY, y);
        y = y + squish * 0.06;
    }

    // Front lean — the whole face reclines slightly
    if (z > 0) {
        const t = (y - BY) / (TY - BY);
        z += -t * Math.tan(TILT_RAD) * BH * 0.55;
    }

    // Remove top-front overhang — the rounded corner must not
    // protrude past the screen plane, or it shadows the display
    if (y > FACET_HH * 0.25 && z > 0) {
        const aboveScreen = smoothstep(FACET_HH * 0.25, TY, y);
        const screenPlaneZ = FACET_Z0 - Math.tan(TILT_RAD) * y + 0.03;
        if (z > screenPlaneZ) {
            z = z + (screenPlaneZ - z) * aboveScreen;
        }
    }

    // Front facet — flatten the forward surface onto the reclined screen plane.
    // Superellipse falloff keeps a soft chamfer where facet meets the stone.
    if (z > FZ * 0.55) {
        const f = Math.pow(
            Math.pow(Math.abs(x) / FACET_HW, 4) + Math.pow(Math.abs(y) / FACET_HH, 4),
            0.25
        );
        const w = smoothstep(1.02, 0.92, f);
        if (w > 0) {
            const zf = FACET_Z0 - Math.tan(TILT_RAD) * y;
            z = z * (1 - w) + zf * w;
        }
    }

    // Lid recess — carve a flat shelf into the top of the body where the
    // walnut lid sits, so it can be flush instead of floating on a dome.
    // Lid footprint: 1.8 wide × 0.85 deep, centered at z = -0.20
    const lidHW = 1.8 / 2 + 0.06;   // half-width + margin
    const lidHD = 0.85 / 2 + 0.06;  // half-depth + margin
    const lidCenterZ = -0.20;
    const lidRecessY = TY - 0.03;    // shelf height — just below body peak
    if (y > lidRecessY - 0.15) {
        // Superellipse membership for the pill-shaped recess
        const rz = z - lidCenterZ;
        const fLid = Math.pow(
            Math.pow(Math.abs(x) / lidHW, 6) + Math.pow(Math.abs(rz) / lidHD, 6),
            1 / 6
        );
        const wLid = smoothstep(1.05, 0.85, fLid);
        if (wLid > 0 && y > lidRecessY) {
            y = y * (1 - wLid) + lidRecessY * wLid;
        }
    }

    pos.setX(i, x);
    pos.setY(i, y);
    pos.setZ(i, z);
}
pos.needsUpdate = true;
bodyGeom.computeVertexNormals();

// MeshPhysicalMaterial for clearcoat — matches the matte-with-sheen in the photos
const bodyMat = new THREE.MeshPhysicalMaterial({
    color: 0x4a4a4d,          // darker graphite, matching 1a.png
    metalness: 0.15,
    roughness: 0.62,
    clearcoat: 0.3,           // subtle clearcoat sheen
    clearcoatRoughness: 0.4,
    envMapIntensity: 0.5,
    sheen: 0.1,
    sheenRoughness: 0.6,
    sheenColor: new THREE.Color(0x888888),
});
const bodyMesh = new THREE.Mesh(bodyGeom, bodyMat);
bodyMesh.castShadow = true;
bodyMesh.receiveShadow = true;
device.add(bodyMesh);

/* ── 2. Walnut haptic lid — true pill/oval, INSET into the body (6a-kasina.png) ── */
const walnutW = 1.8;
const walnutD = 0.85;
const walnutThick = 0.05;

// Stadium/pill outline with true semicircle ends
function pillShape(w, d) {
    const s = new THREE.Shape();
    const hr = d / 2;           // semicircle radius = half depth
    const straight = w / 2 - hr; // straight section half-length
    s.moveTo(-straight, -hr);
    s.lineTo(straight, -hr);
    s.absarc(straight, 0, hr, -Math.PI / 2, Math.PI / 2, false);
    s.lineTo(-straight, hr);
    s.absarc(-straight, 0, hr, Math.PI / 2, Math.PI * 3 / 2, false);
    return s;
}

const walnutGeom = new THREE.ExtrudeGeometry(pillShape(walnutW, walnutD), {
    depth: walnutThick,
    bevelEnabled: true,
    bevelThickness: 0.012,
    bevelSize: 0.012,
    bevelSegments: 4,
    curveSegments: 32
});
// Rotate so extrusion goes along +y (upward), pill lies in xz plane
walnutGeom.rotateX(-Math.PI / 2);

const wpos = walnutGeom.attributes.position;
for (let i = 0; i < wpos.count; i++) {
    const z = wpos.getZ(i);
    if (z > 0) {
        wpos.setZ(i, z - Math.tan(TILT_RAD) * BH * 0.55 * 0.30);
    }
}
wpos.needsUpdate = true;
walnutGeom.computeVertexNormals();

// Procedural walnut grain texture
const walGrainCanvas = document.createElement('canvas');
walGrainCanvas.width = 512;
walGrainCanvas.height = 256;
const wCtx = walGrainCanvas.getContext('2d');
// Rich walnut base
const walGrad = wCtx.createLinearGradient(0, 0, 512, 0);
walGrad.addColorStop(0, '#6b4226');
walGrad.addColorStop(0.3, '#7d5234');
walGrad.addColorStop(0.5, '#6b4226');
walGrad.addColorStop(0.7, '#85593a');
walGrad.addColorStop(1, '#6b4226');
wCtx.fillStyle = walGrad;
wCtx.fillRect(0, 0, 512, 256);
// Grain lines — fine horizontal stripes
wCtx.globalAlpha = 0.12;
for (let i = 0; i < 300; i++) {
    const y = Math.random() * 256;
    const w = 0.3 + Math.random() * 1.5;
    const shade = Math.random();
    wCtx.fillStyle = shade > 0.6 ? '#3a2210' : shade > 0.3 ? '#8c6640' : '#4d3018';
    wCtx.fillRect(0, y, 512, w);
}
// Wider annual ring bands
wCtx.globalAlpha = 0.06;
for (let i = 0; i < 20; i++) {
    const y = Math.random() * 256;
    wCtx.fillStyle = Math.random() > 0.5 ? '#2c1808' : '#a07848';
    wCtx.fillRect(0, y, 512, 2 + Math.random() * 4);
}
wCtx.globalAlpha = 1;

const walGrainTex = new THREE.CanvasTexture(walGrainCanvas);
walGrainTex.wrapS = walGrainTex.wrapT = THREE.RepeatWrapping;
walGrainTex.repeat.set(1, 1);

const walnutMat = new THREE.MeshPhysicalMaterial({
    map: walGrainTex,
    color: 0xccaa88,
    roughness: 0.58,
    metalness: 0.0,
    clearcoat: 0.15,
    clearcoatRoughness: 0.5,
    envMapIntensity: 0.2,
    emissive: 0x7d5234,
    emissiveIntensity: 0.0,    // will pulse during sessions
});
const walnutMesh = new THREE.Mesh(walnutGeom, walnutMat);
// Flush: lid sits on the carved recess shelf in the body
const lidTotalH = walnutThick + 2 * 0.012;  // extrude depth + 2× bevel
walnutMesh.position.set(0, TY - 0.03 - 0.025, -0.20);
walnutMesh.castShadow = true;
walnutMesh.receiveShadow = true;
walnutMesh.userData.isLid = true;
device.add(walnutMesh);

// Dark recess channel — matching pill outline, slightly larger
const recessGeo = new THREE.ShapeGeometry(pillShape(walnutW + 0.10, walnutD + 0.10), 48);
const recessMat = new THREE.MeshStandardMaterial({
    color: 0x0a0a0a, roughness: 0.95, metalness: 0.0, transparent: true, opacity: 0.6
});
const recessMesh = new THREE.Mesh(recessGeo, recessMat);
recessMesh.rotation.x = -Math.PI / 2;
recessMesh.position.set(0, TY - lidTotalH + 0.008, -0.20);
device.add(recessMesh);

/* ── 3. Screen assembly — LIVE FIRMWARE TEXTURE ── */
const screenGroup = new THREE.Group();
screenGroup.rotation.x = -TILT_RAD;

// Sit flush on the sculpted facet
screenGroup.position.set(0, 0.0, FACET_Z0 + 0.012);

// Black bezel — thin frame with rounded corners (matched to 6a-kasina.png)
const bezelW = 2.04;
const bezelH = 1.22;
const bezelR = 0.38;
const bezelGeo = new THREE.ShapeGeometry(rrect(bezelW, bezelH, bezelR), 64);
const bezelMat = new THREE.MeshPhysicalMaterial({
    color: 0x050505,
    roughness: 0.95,
    metalness: 0.0,
    clearcoat: 0.0,
});
screenGroup.add(new THREE.Mesh(bezelGeo, bezelMat));

// Live e-ink texture
const screenTex = new THREE.CanvasTexture(epdCanvas);
screenTex.minFilter = THREE.LinearFilter;
screenTex.magFilter = THREE.LinearFilter;
screenTex.colorSpace = THREE.SRGBColorSpace;

const displayW = 1.90;
const displayH = 1.10;
const displayR = 0.30;
const displayGeo = new THREE.ShapeGeometry(rrect(displayW, displayH, displayR), 48);

// ShapeGeometry emits UVs in raw shape units (±displayW/2, ±displayH/2), not 0–1.
// Remap so the framebuffer fills the display height at its native aspect ratio,
// centered horizontally; the plane is wider than the panel, and the clamped
// overflow samples the framebuffer's paper-white edge columns, so it blends in.
{
    const texAspect = epdCanvas.width / epdCanvas.height;
    const texW = displayH * texAspect;   // texture width in shape units when fit to height
    const uv = displayGeo.attributes.uv;
    for (let i = 0; i < uv.count; i++) {
        uv.setXY(i, uv.getX(i) / texW + 0.5, uv.getY(i) / displayH + 0.5);
    }
    uv.needsUpdate = true;
}

// E-ink display — slightly warm paper tone, very matte
const displayMat = new THREE.MeshPhysicalMaterial({
    map: screenTex,
    roughness: 0.92,
    metalness: 0.0,
    clearcoat: 0.08,           // very subtle glass layer over e-ink
    clearcoatRoughness: 0.3,
    envMapIntensity: 0.04,
});
const displayMesh = new THREE.Mesh(displayGeo, displayMat);
displayMesh.position.z = 0.004;
screenGroup.add(displayMesh);

// Glass reflection overlay — very subtle specular highlight that makes it look real
const glassGeo = new THREE.ShapeGeometry(rrect(displayW, displayH, displayR), 48);
const glassMat = new THREE.MeshPhysicalMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 0.03,
    roughness: 0.15,
    metalness: 0.0,
    clearcoat: 1.0,
    clearcoatRoughness: 0.08,
    envMapIntensity: 0.4,
});
const glassMesh = new THREE.Mesh(glassGeo, glassMat);
glassMesh.position.z = 0.006;
screenGroup.add(glassMesh);

device.add(screenGroup);

// Hook: tell shell.js to flag texture updates
window._shellSetTextureHook(() => { screenTex.needsUpdate = true; });

/* ── 4. Speaker grille (back face) ── */
const dotGeo = new THREE.CircleGeometry(0.016, 8);
const dotMat = new THREE.MeshStandardMaterial({
    color: 0x2a2a2e, roughness: 0.9, metalness: 0.05,
});

const grilleCenterY = 0.12;
const grilleRows = 5, grilleCols = 7;
for (let r = -grilleRows; r <= grilleRows; r++) {
    for (let c = -grilleCols; c <= grilleCols; c++) {
        const nx = c / (grilleCols + 0.5);
        const ny = r / (grilleRows + 0.5);
        if (nx * nx + ny * ny <= 1.0) {
            const dot = new THREE.Mesh(dotGeo, dotMat);
            dot.position.set(c * 0.042, r * 0.042 + grilleCenterY, BZ - 0.003);
            dot.rotation.y = Math.PI;
            device.add(dot);
        }
    }
}

/* ── 5. I/O port strip (back face) ── */
const portMat = new THREE.MeshStandardMaterial({
    color: 0x1a1a1e, metalness: 0.5, roughness: 0.3,
});
const trayGeo = new THREE.ShapeGeometry(rrect(0.80, 0.14, 0.05), 16);
const trayMat = new THREE.MeshStandardMaterial({
    color: 0x2a2a2e, roughness: 0.7, metalness: 0.25,
});
const tray = new THREE.Mesh(trayGeo, trayMat);
tray.position.set(0, -0.46, BZ - 0.002);
tray.rotation.y = Math.PI;
device.add(tray);

const usbGeo = new RoundedBoxGeometry(0.20, 0.07, 0.04, 2, 0.018);
const usb = new THREE.Mesh(usbGeo, portMat);
usb.position.set(-0.17, -0.46, BZ - 0.008);
device.add(usb);

const sdGeo = new RoundedBoxGeometry(0.15, 0.065, 0.04, 2, 0.01);
const sd = new THREE.Mesh(sdGeo, portMat);
sd.position.set(0.06, -0.46, BZ - 0.008);
device.add(sd);

const muteCyl = new THREE.CylinderGeometry(0.035, 0.035, 0.03, 16);
const mute = new THREE.Mesh(muteCyl, portMat);
mute.rotation.x = Math.PI / 2;
mute.position.set(0.26, -0.46, BZ - 0.008);
device.add(mute);

scene.add(device);

/* ── 6. Warm oak desk surface — photorealistic wood ── */
const grainCanvas = document.createElement('canvas');
grainCanvas.width = 1024;
grainCanvas.height = 1024;
const gCtx = grainCanvas.getContext('2d');

// Rich warm oak base gradient
const deskGrad = gCtx.createLinearGradient(0, 0, 1024, 0);
deskGrad.addColorStop(0, '#9c7e56');
deskGrad.addColorStop(0.25, '#a8885e');
deskGrad.addColorStop(0.5, '#96784e');
deskGrad.addColorStop(0.75, '#a48860');
deskGrad.addColorStop(1, '#9a7c54');
gCtx.fillStyle = deskGrad;
gCtx.fillRect(0, 0, 1024, 1024);

// Fine grain lines
gCtx.globalAlpha = 0.08;
for (let i = 0; i < 500; i++) {
    const y = Math.random() * 1024;
    const w = 0.3 + Math.random() * 1.2;
    gCtx.fillStyle = Math.random() > 0.5 ? '#5a3c1e' : '#c8a878';
    gCtx.fillRect(0, y, 1024, w);
}

// Wider annual ring patterns
gCtx.globalAlpha = 0.04;
for (let i = 0; i < 30; i++) {
    const y = Math.random() * 1024;
    gCtx.fillStyle = Math.random() > 0.5 ? '#3c2810' : '#b89868';
    gCtx.fillRect(0, y, 1024, 3 + Math.random() * 6);
}

// Subtle color variation patches (natural wood tone shifts)
gCtx.globalAlpha = 0.03;
for (let i = 0; i < 15; i++) {
    const x = Math.random() * 1024;
    const y = Math.random() * 1024;
    const r = 40 + Math.random() * 120;
    gCtx.fillStyle = Math.random() > 0.5 ? '#8a6a40' : '#b09060';
    gCtx.beginPath();
    gCtx.ellipse(x, y, r, r * 0.3, 0, 0, Math.PI * 2);
    gCtx.fill();
}

// Fine noise for texture
gCtx.globalAlpha = 0.012;
for (let i = 0; i < 12000; i++) {
    gCtx.fillStyle = Math.random() > 0.5 ? '#000' : '#fff';
    gCtx.fillRect(Math.random() * 1024, Math.random() * 1024, 1, 1);
}
gCtx.globalAlpha = 1;

const grainTex = new THREE.CanvasTexture(grainCanvas);
grainTex.wrapS = grainTex.wrapT = THREE.RepeatWrapping;
grainTex.repeat.set(4, 3);

// Bump map from the same grain (gives depth to the wood)
const bumpTex = grainTex.clone();
bumpTex.wrapS = bumpTex.wrapT = THREE.RepeatWrapping;
bumpTex.repeat.set(4, 3);

const deskGeo = new THREE.PlaneGeometry(20, 14);
const deskMat = new THREE.MeshPhysicalMaterial({
    map: grainTex,
    bumpMap: bumpTex,
    bumpScale: 0.003,
    color: 0xddccaa,
    roughness: 0.75,
    metalness: 0.0,
    clearcoat: 0.12,           // subtle desk varnish
    clearcoatRoughness: 0.6,
    envMapIntensity: 0.06,
});
const deskPlane = new THREE.Mesh(deskGeo, deskMat);
deskPlane.rotation.x = -Math.PI / 2;
deskPlane.position.y = -0.86;
deskPlane.receiveShadow = true;
scene.add(deskPlane);

// Soft radial shadow directly under the device (contact shadow)
const shadowCanvas = document.createElement('canvas');
shadowCanvas.width = 256;
shadowCanvas.height = 256;
const sCtx = shadowCanvas.getContext('2d');
const shadowGrad = sCtx.createRadialGradient(128, 128, 0, 128, 128, 128);
shadowGrad.addColorStop(0, 'rgba(0,0,0,0.22)');
shadowGrad.addColorStop(0.5, 'rgba(0,0,0,0.12)');
shadowGrad.addColorStop(1, 'rgba(0,0,0,0)');
sCtx.fillStyle = shadowGrad;
sCtx.fillRect(0, 0, 256, 256);

const shadowTex = new THREE.CanvasTexture(shadowCanvas);
const contactShadowGeo = new THREE.PlaneGeometry(5.5, 3.8);
const contactShadowMat = new THREE.MeshBasicMaterial({
    map: shadowTex,
    transparent: true,
    opacity: 0.8,
    depthWrite: false,
});
const contactShadow = new THREE.Mesh(contactShadowGeo, contactShadowMat);
contactShadow.rotation.x = -Math.PI / 2;
contactShadow.position.y = -0.858;
scene.add(contactShadow);

/* ───────── Raycasting — click the walnut lid ───────── */
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

canvas.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObject(walnutMesh, false);
    if (hits.length > 0 && window._shellPost) {
        window._shellPost("tap");
        walnutMesh.position.y -= 0.015;
        setTimeout(() => { walnutMesh.position.y += 0.015; }, 120);
    }
});

canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObject(walnutMesh, false);
    canvas.style.cursor = hits.length > 0 ? 'pointer' : 'grab';
});

/* ───────── Animation loop ───────── */
function animate() {
    const t = performance.now();

    // Device sits firmly on the desk — no floating

    // Walnut lid breathing glow during practice / session modes
    const mode = window._shellMode || "ambient";
    if (mode === "practice" || mode === "session") {
        const pulse = (Math.sin(t * 0.002) * 0.5 + 0.5) * 0.02;
        walnutMat.emissiveIntensity = pulse;
    } else {
        walnutMat.emissiveIntensity *= 0.92;
    }

    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
}
animate();

/* ───────── Responsive resize ───────── */
function onResize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    const w = rect.width;
    const h = rect.height;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
}
onResize();
addEventListener('resize', onResize);
