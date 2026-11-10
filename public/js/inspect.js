import { $, esc } from "./dom.js";
import { state } from "./state.js";

const FALLBACK_THUMB =
  "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='56' height='56'%3E%3Crect width='56' height='56' fill='%23eceef2'/%3E%3C/svg%3E";

export function renderInspect(data) {
  state.setInspected(data);
  const thumb = data.thumbnail || FALLBACK_THUMB;
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
