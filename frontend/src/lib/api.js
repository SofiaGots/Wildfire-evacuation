// Everything the page says to the backend goes through here.
// In development Vite forwards /api/... to the FastAPI server (see vite.config.js).

export async function getHealth() {
  const res = await fetch("/api/health")
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function estimateEvacuation(payload) {
  const res = await fetch("/api/evacuation/estimate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const body = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = body?.detail?.[0]?.msg ?? `HTTP ${res.status}`
    throw new Error(detail)
  }
  return body
}
