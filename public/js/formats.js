import { $, esc } from "./dom.js";
import { FORMATS, FORMAT_LABELS } from "./config.js";
import { state } from "./state.js";

export function renderFormats() {
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

export function setMode(m) {
  state.setMode(m);
  state.setFormat(FORMATS[m][0]);
  document.querySelectorAll("#mode-seg .seg-btn").forEach((b) =>
    b.classList.toggle("active", b.dataset.mode === m)
  );
  renderFormats();
}
