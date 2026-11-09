export async function fetchQueueStatus() {
    const res = await fetch('/api/queue');
    return await res.json();
}
