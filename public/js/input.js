import { $ } from "./dom.js";
import { state } from "./state.js";
import { inspectApi } from "./api.js";
import { renderInspect, clearInspect } from "./inspect.js";

export function onInput(val) {
  clearTimeout(state.inspectTimer);
  const url = val.trim();
  if (!/^https?:\/\//.test(url)) {
    clearInspect();
    return;
  }
  state.setInspectTimer(setTimeout(() => inspect(url), 400));
}

async function inspect(url) {
  try {
    const data = await inspectApi(url);
    if (data) renderInspect(data);
  } catch {
    /* ignore */
  }
}
