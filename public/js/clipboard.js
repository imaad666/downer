import { $ } from "./dom.js";
import { toast } from "./toast.js";

export async function pasteFromClipboard(onPasted) {
  try {
    const text = await navigator.clipboard.readText();
    if (text && text.trim().startsWith("http")) {
      $("url-input").value = text.trim();
      onPasted(text.trim());
      toast("Link pasted", "ok");
    } else {
      toast("Clipboard has no link", "err");
    }
  } catch {
    toast("Press Ctrl+V to paste", "err");
  }
}
