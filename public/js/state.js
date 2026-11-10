let mode = "audio";
let format = "mp3";
let inspected = null;
let inspectTimer = null;

export const state = {
  get mode() { return mode; },
  get format() { return format; },
  get inspected() { return inspected; },
  get inspectTimer() { return inspectTimer; },
  setMode(m) { mode = m; },
  setFormat(f) { format = f; },
  setInspected(data) { inspected = data; },
  setInspectTimer(t) { inspectTimer = t; },
};
