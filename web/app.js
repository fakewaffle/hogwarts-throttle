const MAX_SPEED = 31;
const MAX_VOLUME = 7;
const SEND_INTERVAL_MS = 120;

const $ = (id) => document.getElementById(id);
let state = { connected: false, speed: 0, forward: true, bell: false, lights: true, smoke: false, volume: 5 };
let dragging = false;

async function send(action, value) {
  try {
    const response = await fetch(`/api/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value }),
    });
    if (response.ok) render(await response.json());
  } catch (error) {
    render({ ...state, connected: false });
  }
}

async function poll() {
  try {
    const response = await fetch("/api/state");
    if (response.ok) render(await response.json());
  } catch (error) {
    render({ ...state, connected: false });
  }
}

function render(next) {
  state = next;
  document.body.classList.toggle("offline", !state.connected);
  $("status").className = `status ${state.connected ? "on" : "off"}`;
  $("status-text").textContent = state.connected ? "Train connected" : "Looking for the train…";
  if (!dragging) drawSpeed(state.speed);
  $("forward").classList.toggle("on", state.forward);
  $("reverse").classList.toggle("on", !state.forward);
  $("bell").classList.toggle("on", state.bell);
  $("lights").classList.toggle("on", state.lights);
  $("smoke").classList.toggle("on", state.smoke);
  drawVolume(state.volume);
  document.querySelectorAll("button").forEach((button) => (button.disabled = !state.connected));
}

function drawSpeed(speed) {
  const track = $("track");
  const thumb = $("thumb");
  const travel = track.clientHeight - thumb.offsetHeight;
  const offset = (speed / MAX_SPEED) * travel;
  thumb.style.bottom = `${offset}px`;
  $("fill").style.height = `${offset + thumb.offsetHeight / 2}px`;
  $("speed").textContent = `${Math.round((speed / MAX_SPEED) * 100)}%`;
  $("needle").style.transform = `rotate(${dialAngle(speed / MAX_SPEED)}deg)`;
}

function drawVolume(volume) {
  $("volume").querySelectorAll("i").forEach((pip, index) => pip.classList.toggle("lit", index < volume));
}

const DIAL_SWEEP = 240;
const dialAngle = (ratio) => ratio * DIAL_SWEEP - DIAL_SWEEP / 2;

function dialPoint(ratio, radius) {
  const radians = (dialAngle(ratio) * Math.PI) / 180;
  return [100 + radius * Math.sin(radians), 100 - radius * Math.cos(radians)];
}

function buildDial() {
  const ns = "http://www.w3.org/2000/svg";
  for (let step = 0; step <= MAX_SPEED; step++) {
    const major = step % 5 === 0 || step === MAX_SPEED;
    const [x1, y1] = dialPoint(step / MAX_SPEED, major ? 64 : 70);
    const [x2, y2] = dialPoint(step / MAX_SPEED, 78);
    const tick = document.createElementNS(ns, "line");
    tick.setAttribute("class", major ? "g-tick major" : "g-tick");
    Object.entries({ x1, y1, x2, y2 }).forEach(([key, value]) => tick.setAttribute(key, value.toFixed(1)));
    $("ticks").appendChild(tick);
  }
  const [rx1, ry1] = dialPoint(0.8, 58);
  const [rx2, ry2] = dialPoint(1, 58);
  $("redline").setAttribute("d", `M${rx1.toFixed(1)} ${ry1.toFixed(1)} A58 58 0 0 1 ${rx2.toFixed(1)} ${ry2.toFixed(1)}`);
  for (let level = 1; level <= MAX_VOLUME; level++) {
    const pip = document.createElement("i");
    pip.style.height = `${8 + level * 2.6}px`;
    $("volume").appendChild(pip);
  }
}

function speedAt(clientY) {
  const rect = $("track").getBoundingClientRect();
  const thumbHalf = $("thumb").offsetHeight / 2;
  const ratio = (rect.bottom - thumbHalf - clientY) / (rect.height - thumbHalf * 2);
  return Math.round(Math.min(1, Math.max(0, ratio)) * MAX_SPEED);
}

function setUpThrottle() {
  const track = $("track");
  let pending = null;
  let lastSent = 0;
  let timer = null;

  const flush = () => {
    timer = null;
    if (pending === null) return;
    lastSent = performance.now();
    send("speed", pending);
    pending = null;
  };

  const move = (event) => {
    if (!dragging || !state.connected) return;
    const speed = speedAt(event.clientY);
    drawSpeed(speed);
    pending = speed;
    const wait = SEND_INTERVAL_MS - (performance.now() - lastSent);
    if (wait <= 0) flush();
    else if (!timer) timer = setTimeout(flush, wait);
  };

  track.addEventListener("pointerdown", (event) => {
    if (!state.connected) return;
    dragging = true;
    document.body.classList.add("dragging");
    track.setPointerCapture(event.pointerId);
    move(event);
  });
  track.addEventListener("pointermove", move);
  const release = () => {
    dragging = false;
    document.body.classList.remove("dragging");
    clearTimeout(timer);
    flush();
  };
  track.addEventListener("pointerup", release);
  track.addEventListener("pointercancel", release);
}

function hold(button, action) {
  const start = (event) => {
    event.preventDefault();
    button.setPointerCapture(event.pointerId);
    button.classList.add("pressed");
    send(action, true);
  };
  const end = () => {
    if (!button.classList.contains("pressed")) return;
    button.classList.remove("pressed");
    send(action, false);
  };
  button.addEventListener("pointerdown", start);
  button.addEventListener("pointerup", end);
  button.addEventListener("pointercancel", end);
}

$("stop").addEventListener("click", () => send("stop"));
$("forward").addEventListener("click", () => send("direction", true));
$("reverse").addEventListener("click", () => send("direction", false));
$("bell").addEventListener("click", () => send("bell", !state.bell));
$("lights").addEventListener("click", () => send("lights", !state.lights));
$("smoke").addEventListener("click", () => send("smoke", !state.smoke));
$("dialog").addEventListener("click", () => send("dialog"));
$("volume-down").addEventListener("click", () => send("volume", Math.max(0, state.volume - 1)));
$("volume-up").addEventListener("click", () => send("volume", Math.min(MAX_VOLUME, state.volume + 1)));
hold($("horn"), "horn");
document.addEventListener("contextmenu", (event) => event.preventDefault());
window.addEventListener("resize", () => drawSpeed(state.speed));

buildDial();
setUpThrottle();
render(state);
poll();
setInterval(poll, 1000);
