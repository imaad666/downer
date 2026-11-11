import { $ } from "./dom.js";
import { GO_ICON_SVG } from "./config.js";
import { state } from "./state.js";
import { postJSON } from "./api.js";
import { toast } from "./toast.js";
import { progressStart, progressDone } from "./progress.js";

export function setBusy(busy) {
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

export async function startDownload() {
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
