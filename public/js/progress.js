import { $ } from "./dom.js";

const ICONS = {
  working:
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.2-8.56"/></svg>',
  ok: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
  err: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
};

let timer = null;

function card(title, sub, icon, cls) {
  $("progress-slot").innerHTML = `
    <div class="progress-card ${cls}">
      <div class="progress-top">
        <div class="progress-icon">${icon}</div>
        <div class="progress-title">${title}</div>
      </div>
      <div class="progress-sub">${sub}</div>
      <div class="progress-bar"><div></div></div>
    </div>`;
}

export function progressStart(title) {
  clearTimeout(timer);
  card(title, "Resolving link…", ICONS.working, "");
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
    const sub = document.querySelector(".progress-sub");
    if (sub) sub.textContent = subs[i];
  }, 2600);
}

export function progressDone(ok, title, sub) {
  clearTimeout(timer);
  timer = null;
  card(
    title,
    sub,
    ok ? ICONS.ok : ICONS.err,
    ok ? "ok" : "err"
  );
  setTimeout(() => {
    const el = document.querySelector(".progress-card");
    if (el) el.remove();
  }, ok ? 5000 : 8000);
}
