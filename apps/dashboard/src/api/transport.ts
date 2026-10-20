export class ApiRequestError extends Error {
  status: number
  code?: string
  details?: unknown
  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message); this.name = 'ApiRequestError'; this.status = status; this.code = code; this.details = details
  }
}

/** Versioned API transport. Identity is held by the backend session cookie. */
export async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (init?.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (!['GET', 'HEAD'].includes(init?.method ?? 'GET') && typeof document !== 'undefined') {
    const csrf = document.cookie.split('; ').find(v => v.startsWith('monash_csrf='))?.slice('monash_csrf='.length)
    if (csrf) headers.set('X-CSRF-Token', decodeURIComponent(csrf))
  }
  const base = import.meta.env?.VITE_API_BASE ?? ''
  const readOnly = ['GET', 'HEAD'].includes(init?.method ?? 'GET')
  const controller = new AbortController()
  const cancel = () => controller.abort(init?.signal?.reason)
  if (init?.signal?.aborted) cancel()
  else init?.signal?.addEventListener('abort', cancel, { once: true })
  const timeout = setTimeout(() => controller.abort(new DOMException('Request deadline exceeded', 'TimeoutError')), readOnly ? 15_000 : 120_000)
  try {
    const response = await fetch(`${base}${path}`, { ...init, headers, credentials: 'include', signal: controller.signal })
    if (!response.ok) {
      const body = await response.json().catch(() => null)
      throw new ApiRequestError(body?.error?.message ?? (response.status === 404
        ? 'The requested service is unavailable. Please retry later; if this continues, contact the platform maintainer.'
        : `Request failed (${response.status}). Please try again.`), response.status, body?.error?.code, body?.error?.details)
    }
    if (response.status === 204) return undefined as T
    return await response.json()
  } catch (error) {
    if (controller.signal.reason?.name === 'TimeoutError') {
      throw new Error(readOnly
        ? 'The service timed out. Please retry; your selection has been kept.'
        : 'The service timed out. The action may have completed. Refresh and check its status before trying again.', { cause: error })
    }
    throw error
  } finally {
    clearTimeout(timeout)
    init?.signal?.removeEventListener('abort', cancel)
  }
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
