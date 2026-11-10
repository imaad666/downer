export async function postJSON(path, body) {
  return fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function inspectApi(url) {
  const res = await postJSON("/api/inspect", { url });
  if (!res.ok) return null;
  return res.json();
}
