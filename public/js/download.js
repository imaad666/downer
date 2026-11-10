import { $ } from "./dom.js";
import { GO_ICON_SVG } from "./config.js";
import { state } from "./state.js";
import { postJSON } from "./api.js";
import { toast } from "./toast.js";

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

export async function startDownload() {
  const url = $("url-input").value.trim();
  if (!url) {
    toast("Paste a link first", "err");
    return;
  }

  setBusy(true);
  toast(state.mode === "audio" ? "Converting audio…" : "Preparing download…", "ok");

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
        toast("Download started", "ok");
      }
    } else if (res.ok) {
      const blob = await res.blob();
      saveBlob(blob, filenameFromDisposition(res.headers.get("content-disposition") || ""));
      toast("Saved to your downloads", "ok");
    } else {
      let msg = "Download failed";
      try {
        msg = (await res.json()).detail || msg;
      } catch {}
      toast(String(msg).slice(0, 140), "err");
    }
  } catch {
    toast("Network error — try again", "err");
  } finally {
    setBusy(false);
  }
}
