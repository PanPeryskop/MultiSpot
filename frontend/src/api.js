export async function api(path, { method = 'GET', body, signal } = {}) {
  let response
  try {
    response = await fetch(path, {
      method,
      credentials: 'include',
      signal,
      headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch (err) {
    if (err.name === 'AbortError') throw err
    throw new Error('Cannot reach the MultiSpot server', { cause: err })
  }
  let data
  try {
    data = await response.json()
  } catch {
    data = {}
  }
  if (!response.ok) {
    if (response.status === 401 && window._refreshAuth) window._refreshAuth()
    const detail = Array.isArray(data.detail)
      ? data.detail.map(d => d.msg || String(d)).join('; ')
      : data.detail
    throw new Error(detail || statusMessage(response.status))
  }
  return data
}

function statusMessage(status) {
  if (status === 401) return 'Session expired, log in again'
  if (status === 403) return 'Spotify refused this action'
  if (status === 404) return 'Nothing found. Is a Spotify device active?'
  if (status === 429) return 'Spotify is rate limiting us, try again in a moment'
  if (status >= 500) return 'Server error, try again'
  return `Request failed (${status})`
}

export function formatDuration(ms) {
  if (!ms && ms !== 0) return '?'
  const total = Math.round(ms / 1000)
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  if (h) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

export function compact(n) {
  if (n === null || n === undefined) return '?'
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)}B`
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`
  return String(n)
}

export function isSpotifyLink(value, kind) {
  const match = /(?:open\.spotify\.com\/(?:intl-[a-z-]+\/)?(?:embed\/)?|spotify:)(track|artist|album|playlist)[/:]([A-Za-z0-9]{22})/.exec(value || '')
  if (!match) return false
  return kind ? match[1] === kind : true
}
