import { $ } from "./dom.js";
import { state } from "./state.js";
import { inspectApi } from "./api.js";
import { renderInspect, clearInspect } from "./inspect.js";

export function renderSkeleton() {
  $("inspect-slot").innerHTML = `
    <div class="skeleton">
      <div class="sk-thumb"></div>
      <div class="sk-lines">
        <div class="sk-line"></div>
        <div class="sk-line-sm"></div>
      </div>
    </div>`;
}

export function onInput(val) {
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
