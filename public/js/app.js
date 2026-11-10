import { $ } from "./dom.js";
import { renderFormats, setMode } from "./formats.js";
import { pasteFromClipboard } from "./clipboard.js";
import { onInput } from "./input.js";
import { startDownload } from "./download.js";

function bindEvents() {
  $("url-input").addEventListener("input", (e) => onInput(e.target.value));
  $("url-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") startDownload();
  });
  $("go-btn").addEventListener("click", startDownload);
  $("paste-btn")?.addEventListener("click", () => pasteFromClipboard(onInput));

  document.querySelectorAll("#mode-seg .seg-btn").forEach((b) =>
    b.addEventListener("click", () => setMode(b.dataset.mode))
  );
}

bindEvents();
renderFormats();
