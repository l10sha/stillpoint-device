/* StillPoint shell: renders firmware frames to an offscreen canvas,
   handles audio (chime + speech), HUD state, console, and input posting.
   The 3D module (shell3d.js) reads the canvas as a CanvasTexture. */
"use strict";

const EPD_W = 2072, EPD_H = 1072;
const PAPER = "#ebe8e0";
const GHOST_ALPHA = 0.055;

const epd = document.getElementById("epd");
const ctx = epd.getContext("2d", { willReadFrequently: true });

// frame = what the panel currently holds; ghost = accumulated partial-refresh residue
const frame = new OffscreenCanvas(EPD_W, EPD_H);
const fctx = frame.getContext("2d");
const ghost = new OffscreenCanvas(EPD_W, EPD_H);
const gctx = ghost.getContext("2d");

function resetWhite(c) { c.fillStyle = "#ffffff"; c.fillRect(0, 0, EPD_W, EPD_H); }
resetWhite(fctx);
resetWhite(gctx);

/* --- texture update hook (called by shell3d.js) --- */
let _onTextureUpdate = null;
window._shellSetTextureHook = function(fn) { _onTextureUpdate = fn; };

/* --- current device mode (used by shell3d.js for lid glow) --- */
window._shellMode = "boot";

function render() {
  ctx.globalCompositeOperation = "source-over";
  ctx.fillStyle = PAPER;
  ctx.fillRect(0, 0, EPD_W, EPD_H);
  ctx.globalCompositeOperation = "multiply";
  ctx.drawImage(ghost, 0, 0);
  ctx.drawImage(frame, 0, 0);
  ctx.globalCompositeOperation = "source-over";
  if (_onTextureUpdate) _onTextureUpdate();
}
render();

// --------------------------------------------------------- refresh sim ---
let busyTimer = null;
const busyDot = document.getElementById("busy");
function setBusy(ms) {
  busyDot.classList.add("on");
  clearTimeout(busyTimer);
  busyTimer = setTimeout(() => busyDot.classList.remove("on"), ms);
}

function fullRefresh(img, busyMs) {
  setBusy(busyMs);
  // Animate on the visible canvas for the 3D texture to pick up each step
  const steps = [
    () => { // inverted flash of incoming content
      ctx.filter = "invert(1)";
      ctx.drawImage(img, 0, 0);
      ctx.filter = "none";
      if (_onTextureUpdate) _onTextureUpdate();
    },
    () => {
      ctx.fillStyle = "#111";
      ctx.fillRect(0, 0, EPD_W, EPD_H);
      if (_onTextureUpdate) _onTextureUpdate();
    },
    () => {
      ctx.fillStyle = "#f4f2ec";
      ctx.fillRect(0, 0, EPD_W, EPD_H);
      if (_onTextureUpdate) _onTextureUpdate();
    },
    () => {
      ctx.filter = "invert(1)";
      ctx.drawImage(img, 0, 0);
      ctx.filter = "none";
      if (_onTextureUpdate) _onTextureUpdate();
    },
    () => {
      resetWhite(gctx);                     // full refresh clears ghosting
      fctx.drawImage(img, 0, 0);
      render();
    },
  ];
  steps.forEach((fn, i) => setTimeout(fn, i * 140));
}

function partialRefresh(img, region, busyMs) {
  setBusy(busyMs);
  const [x, y, w, h] = region;
  gctx.globalAlpha = GHOST_ALPHA;          // old pixels leave a faint residue
  gctx.drawImage(frame, x, y, w, h, x, y, w, h);
  gctx.globalAlpha = 1;
  fctx.clearRect(x, y, w, h);
  fctx.drawImage(img, x, y, w, h, x, y, w, h);
  render();
}

function applyScreen(ev) {
  const img = new Image();
  img.onload = () =>
    ev.refresh === "partial" && ev.region
      ? partialRefresh(img, ev.region, ev.busy_ms)
      : fullRefresh(img, ev.busy_ms || 1200);
  img.src = "data:image/png;base64," + ev.png;
}

// --------------------------------------------------------------- audio ---
let audioCtx = null;
let soundOn = false;

function ensureAudio() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (audioCtx.state === "suspended") audioCtx.resume();
}

function chime() {
  if (!soundOn) return;
  ensureAudio();
  const t = audioCtx.currentTime;
  const f0 = 523.25; // struck-bowl partials
  [[f0, 0.16, 5.0], [f0 * 2.756, 0.05, 3.2], [f0 * 5.404, 0.018, 1.8]].forEach(([f, amp, dur]) => {
    const o = audioCtx.createOscillator();
    const g = audioCtx.createGain();
    o.type = "sine";
    o.frequency.value = f;
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(amp, t + 0.015);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(audioCtx.destination);
    o.start(t);
    o.stop(t + dur);
  });
}

let voice = null;
function pickVoice() {
  const voices = speechSynthesis.getVoices();
  const prefs = ["Samantha", "Karen", "Moira", "Daniel"];
  voice = prefs.map(n => voices.find(v => v.name.startsWith(n))).find(Boolean)
       || voices.find(v => v.lang.startsWith("en")) || null;
}
if ("speechSynthesis" in window) {
  pickVoice();
  speechSynthesis.onvoiceschanged = pickVoice;
}

function speak(text) {
  if (!soundOn || !("speechSynthesis" in window)) return;
  const u = new SpeechSynthesisUtterance(text);
  if (voice) u.voice = voice;
  u.rate = 0.82;   // unhurried, meditation pace
  u.pitch = 0.92;
  u.volume = 0.95;
  speechSynthesis.speak(u);
}

// ------------------------------------------------------------- console ---
const consoleEl = document.getElementById("console");
function logLine(svc, msg) {
  const now = document.getElementById("simtime").textContent;
  const div = document.createElement("div");
  div.innerHTML = `<span class="t">${now}</span> <span class="svc">[${svc}]</span> ${msg
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")}`;
  consoleEl.appendChild(div);
  while (consoleEl.childElementCount > 140) consoleEl.firstChild.remove();
  consoleEl.scrollTop = consoleEl.scrollHeight;
}

// ---------------------------------------------------------------- state ---
function onState(ev) {
  document.getElementById("simtime").textContent = ev.simtime;
  document.getElementById("phase").textContent = ev.phase;
  document.getElementById("mode").textContent = ev.mode;
  window._shellMode = ev.mode;
  document.querySelectorAll(".speed").forEach(b =>
    b.classList.toggle("on", Number(b.dataset.speed) === ev.speed));
}

// ----------------------------------------------------------------- SSE ---
const es = new EventSource("/events");
es.onmessage = (m) => {
  const ev = JSON.parse(m.data);
  if (ev.type === "screen") applyScreen(ev);
  else if (ev.type === "state") onState(ev);
  else if (ev.type === "log") logLine(ev.svc, ev.msg);
  else if (ev.type === "speak") { logLine("tts", "▶ speaking"); speak(ev.text); }
  else if (ev.type === "chime") chime();
};
es.onerror = () => logLine("shell", "event stream reconnecting…");

// -------------------------------------------------------------- inputs ---
function post(action, arg) {
  fetch("/input", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, arg }),
  }).catch(() => logLine("shell", "input failed — is the firmware running?"));
}
// Expose for shell3d.js raycast clicks
window._shellPost = post;

document.querySelectorAll("[data-act]").forEach(b =>
  b.addEventListener("click", () => post(b.dataset.act, b.dataset.arg || null)));

document.querySelectorAll("[data-warp]").forEach(b =>
  b.addEventListener("click", () => post("warp", b.dataset.warp.split(",").map(Number))));

document.querySelectorAll("[data-speed]").forEach(b =>
  b.addEventListener("click", () => post("speed", Number(b.dataset.speed))));

const soundBtn = document.getElementById("soundBtn");
soundBtn.addEventListener("click", () => {
  soundOn = !soundOn;
  if (soundOn) { ensureAudio(); chime(); }
  else speechSynthesis.cancel();
  soundBtn.textContent = soundOn ? "sound on" : "enable sound";
});
