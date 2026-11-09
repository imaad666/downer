export async function readClipboardText() {
    try {
        return await navigator.clipboard.readText();
    } catch {
        return "";
    }
}
