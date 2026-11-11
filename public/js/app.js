// ---------- config ----------
const FORMATS = {
  audio: ["mp3", "wav", "flac", "m4a"],
  video: ["mp4_best", "mp4_1080", "mp4_720"],
  file: ["raw"],
};

const FORMAT_LABELS = {
  mp3: "MP3",
  wav: "WAV",
  flac: "FLAC",
  m4a: "M4A",
  mp4_best: "Best",
  mp4_1080: "1080p",
  mp4_720: "720p",
  raw: "Original",
};

const GO_ICON_SVG =
  '<svg id="go-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="4" x2="12" y2="15"/><polyline points="7 10 12 15 17 10"/><line x1="5" y1="20" x2="19" y2="20"/></svg>';

// ---------- state ----------
let mode = "audio";
let format = "mp3";
let inspected = null;
let inspectTimer = null;

const state = {
  get mode() { return mode; },
  get format() { return format; },
  get inspected() { return inspected; },
  get inspectTimer() { return inspectTimer; },
  setMode(m) { mode = m; },
  setFormat(f) { format = f; },
  setInspected(data) { inspected = data; },
  setInspectTimer(t) { inspectTimer = t; },
};

// ---------- dom ----------
const $ = (id) => document.getElementById(id);

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (m) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m])
  );
}

// ---------- api ----------
async function postJSON(path, body) {
  return fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function inspectApi(url) {
  const res = await postJSON("/api/inspect", { url });
  if (!res.ok) return null;
  return res.json();
}

// ---------- toast ----------
function toast(msg, type = "") {
  const t = document.createElement("div");
  t.className = "toast " + type;
  t.textContent = msg;
  $("toasts").appendChild(t);
  setTimeout(() => {
    t.style.opacity = "0";
    t.style.transition = "opacity .3s";
    setTimeout(() => t.remove(), 320);
  }, 3200);
}

// ---------- formats ----------
function renderFormats() {
  $("format-row").innerHTML = FORMATS[state.mode].map(
    (f) =>
      `<button class="fmt-btn ${f === state.format ? "active" : ""}" data-fmt="${esc(f)}">${esc(FORMAT_LABELS[f])}</button>`
  ).join("");

  document.querySelectorAll("#format-row .fmt-btn").forEach((b) =>
    b.addEventListener("click", () => {
      state.setFormat(b.dataset.fmt);
      renderFormats();
    })
  );
}

function setMode(m) {
  state.setMode(m);
  state.setFormat(FORMATS[m][0]);
  document.querySelectorAll("#mode-seg .seg-btn").forEach((b) =>
    b.classList.toggle("active", b.dataset.mode === m)
  );
  renderFormats();
}

// ---------- clipboard ----------
async function pasteFromClipboard(onPasted) {
  try {
    const text = await navigator.clipboard.readText();
    if (text && text.trim().startsWith("http")) {
      $("url-input").value = text.trim();
      onPasted(text.trim());
      toast("Link pasted", "ok");
    } else {
      toast("Clipboard has no link", "err");
    }
  } catch {
    toast("Press Ctrl+V to paste", "err");
  }
}

// ---------- inspect ----------
function fallbackThumb(platform) {
  const letter = (platform || "?")[0].toUpperCase();
  const svg =
    `<svg xmlns='http://www.w3.org/2000/svg' width='56' height='56'>` +
    `<rect width='56' height='56' fill='%23eceef2'/>` +
    `<text x='50%' y='54%' dominant-baseline='middle' text-anchor='middle' ` +
    `font-family='sans-serif' font-size='26' font-weight='700' fill='%235d6472'>${letter}</text></svg>`;
  return "data:image/svg+xml;utf8," + encodeURIComponent(svg);
}

function renderInspect(data) {
  state.setInspected(data);
  const thumb = data.thumbnail || fallbackThumb(data.platform);
  $("inspect-slot").innerHTML = `
    <div class="inspect" id="inspect-card">
      <img class="inspect-thumb" src="${thumb}" alt="" loading="lazy" onerror="this.style.opacity=.25" />
      <div style="min-width:0;flex:1" class="inspect-content">
        <div class="inspect-title">${esc(data.title)}</div>
        <div class="inspect-meta">
          <span class="platform-pill">${esc(data.platform || "Web")}</span>
          ${data.uploader ? `<span>${esc(data.uploader)}</span>` : ""}
          ${data.duration_formatted ? `<span>· ${esc(data.duration_formatted)}</span>` : ""}
        </div>
      </div>
    </div>`;
}

function clearInspect() {
  $("inspect-slot").innerHTML = "";
  state.setInspected(null);
}

function setInspectProgress(status, icon, cls) {
  const card = document.getElementById("inspect-card");
  if (!card) return;
  card.className = `inspect ${cls}`;
  const content = card.querySelector(".inspect-content");
  content.innerHTML = `
    <div class="inspect-progress">
      <div class="status">${status}</div>
      <div class="bar"><div></div></div>
    </div>
  `;
  const thumb = card.querySelector(".inspect-thumb");
  thumb.style.opacity = cls ? "0.5" : "1";
  const iconDiv = document.createElement("div");
  iconDiv.className = "status-icon";
  iconDiv.innerHTML = icon;
  card.insertBefore(iconDiv, content);
}

// ---------- input ----------
function renderSkeleton() {
  $("inspect-slot").innerHTML = `
    <div class="skeleton">
      <div class="sk-thumb"></div>
      <div class="sk-lines">
        <div class="sk-line"></div>
        <div class="sk-line-sm"></div>
      </div>
    </div>`;
}

function onInput(val) {
  clearTimeout(state.inspectTimer);
  const url = val.trim();
  if (!/^https?:\/\//.test(url)) {
    clearInspect();
    return;
  }
  renderSkeleton();
  state.setInspectTimer(setTimeout(() => inspect(url), 400));
}

async function inspect(url) {
  try {
    const data = await inspectApi(url);
    if (data) renderInspect(data);
  } catch {
    clearInspect();
  }
}

// ---------- progress ----------
const ICONS = {
  working:
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.2-8.56"/></svg>',
  ok: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
  err: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
};

let timer = null;

function progressStart(title) {
  clearTimeout(timer);
  setInspectProgress("Downloading…", ICONS.working, "active");
  const subs = [
    "Resolving link…",
    "Fetching media info…",
    "Downloading file…",
    "Converting audio…",
    "Almost there…",
  ];
  let i = 0;
  timer = setInterval(() => {
    i = (i + 1) % subs.length;
    const el = document.querySelector(".status");
    if (el) el.textContent = subs[i];
  }, 2600);
}

function progressDone(ok, title, sub) {
  clearTimeout(timer);
  timer = null;
  setInspectProgress(ok ? "Saved" : "Failed", ok ? ICONS.ok : ICONS.err, ok ? "ok" : "err");
  setTimeout(() => {
    const el = document.querySelector(".inspect");
    if (el) el.remove();
  }, ok ? 5000 : 8000);
}

// ---------- download ----------
function setBusy(busy) {
  $("go-btn").disabled = busy;
  $("go-icon").outerHTML = busy ? '<div class="spinner" id="go-icon"></div>' : GO_ICON_SVG;
}

function saveBlob(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name || "download";
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
}

function clickDownload(url, filename) {
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || "";
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function filenameFromDisposition(dispo) {
  const match = dispo.match(/filename="?([^";]+)"?/);
  if (match) return match[1];
  const title = state.inspected && state.inspected.title;
  return `${title || "download"}.${state.format === "raw" ? "" : state.format.split("_")[0]}`;
}

function shortTitle() {
  const t = state.inspected && state.inspected.title;
  return t ? t.slice(0, 42) + (t.length > 42 ? "…" : "") : "Download";
}

async function startDownload() {
  const url = $("url-input").value.trim();
  if (!url) {
    toast("Paste a link first", "err");
    return;
  }

  setBusy(true);
  progressStart(shortTitle());

  try {
    const res = await postJSON("/api/download", {
      url,
      mode: state.mode,
      format: state.format,
      title: state.inspected ? state.inspected.title : null,
    });

    const ctype = res.headers.get("content-type") || "";

    if (res.ok && ctype.includes("application/json")) {
      const data = await res.json();
      if (data.download_url) {
        clickDownload(data.download_url, data.filename);
        progressDone(true, "Download started", data.filename || "File sent to your browser");
      }
    } else if (res.ok) {
      const blob = await res.blob();
      const name = filenameFromDisposition(res.headers.get("content-disposition") || "");
      saveBlob(blob, name);
      progressDone(true, "Saved", name);
      toast("Saved to your downloads", "ok");
    } else {
      let msg = "Download failed";
      try {
        msg = (await res.json()).detail || msg;
      } catch {}
      msg = String(msg).slice(0, 140);
      progressDone(false, "Download failed", msg);
      toast(msg, "err");
    }
  } catch {
    progressDone(false, "Network error", "Could not reach the server — try again");
    toast("Network error — try again", "err");
  } finally {
    setBusy(false);
  }
}

// ---------- app ----------
function init() {
  renderFormats();

  $("url-input").addEventListener("input", (e) => onInput(e.target.value));
  $("url-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") startDownload();
  });

  $("paste-btn").addEventListener("click", () => pasteFromClipboard(onInput));
  $("go-btn").addEventListener("click", startDownload);

  document.querySelectorAll("#mode-seg .seg-btn").forEach((b) =>
    b.addEventListener("click", () => setMode(b.dataset.mode))
  );
}

init();
