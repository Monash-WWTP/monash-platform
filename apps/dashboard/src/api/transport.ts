/** Versioned API transport. Identity is held by the backend session cookie. */
export async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (init?.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (!['GET', 'HEAD'].includes(init?.method ?? 'GET') && typeof document !== 'undefined') {
    const csrf = document.cookie.split('; ').find(v => v.startsWith('monash_csrf='))?.slice('monash_csrf='.length)
    if (csrf) headers.set('X-CSRF-Token', decodeURIComponent(csrf))
  }
  const base = import.meta.env?.VITE_API_BASE ?? ''
  const response = await fetch(`${base}${path}`, { ...init, headers, credentials: 'include' })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.error?.message ?? `Request failed (${response.status})`)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

export interface Page<T> { items: T[]; total: number; offset: number; limit: number }
export async function allPages<T>(path: string): Promise<T[]> {
  const values: T[] = []
  for (let offset = 0; ; offset += 500) {
    const page = await fetchApi<Page<T>>(`${path}${path.includes('?') ? '&' : '?'}offset=${offset}&limit=500`)
    values.push(...page.items)
    if (values.length >= page.total || page.items.length === 0) return values
  }
}
