import { $, esc } from "./dom.js";
import { state } from "./state.js";

function fallbackThumb(platform) {
  const letter = (platform || "?")[0].toUpperCase();
  const svg =
    `<svg xmlns='http://www.w3.org/2000/svg' width='56' height='56'>` +
    `<rect width='56' height='56' fill='%23eceef2'/>` +
    `<text x='50%' y='54%' dominant-baseline='middle' text-anchor='middle' ` +
    `font-family='sans-serif' font-size='26' font-weight='700' fill='%235d6472'>${letter}</text></svg>`;
  return "data:image/svg+xml;utf8," + encodeURIComponent(svg);
}

export function renderInspect(data) {
  state.setInspected(data);
  const thumb = data.thumbnail || fallbackThumb(data.platform);
  $("inspect-slot").innerHTML = `
    <div class="inspect">
      <img class="inspect-thumb" src="${thumb}" alt="" loading="lazy" onerror="this.style.opacity=.25" />
      <div style="min-width:0;flex:1">
        <div class="inspect-title">${esc(data.title)}</div>
        <div class="inspect-meta">
          <span class="platform-pill">${esc(data.platform || "Web")}</span>
          ${data.uploader ? `<span>${esc(data.uploader)}</span>` : ""}
          ${data.duration_formatted ? `<span>· ${esc(data.duration_formatted)}</span>` : ""}
        </div>
      </div>
    </div>`;
}

export function clearInspect() {
  $("inspect-slot").innerHTML = "";
  state.setInspected(null);
}
