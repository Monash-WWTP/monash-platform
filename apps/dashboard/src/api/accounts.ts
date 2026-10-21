import { useQuery } from '@tanstack/react-query'
import { fetchApi } from './transport'
export interface Account { id: string; email: string; display_name?: string | null; capabilities: string[] }
export function useAccount() {
  const query = useQuery({ queryKey: ['account'], queryFn: () => fetchApi<Account>('/api/v1/auth/me'), retry: false })
  return { ...query, data: query.isError ? undefined : query.data }
}

export interface AccountSettings { available: boolean; origin: string | null; actions: Record<string, string> }
const settingPaths: Record<string, string> = {
  profile: 'monash-account-profile', email: 'monash-account-email', password: 'monash-account-password',
  security: 'monash-account-security', sessions: 'monash-account-security', signout_all: 'monash-account-signout-all',
}
export function trustedAccountActions(settings?: AccountSettings): Record<string, string> {
  if (!settings?.available || !settings.origin) return {}
  try {
    const origin = new URL(settings.origin)
    if (origin.username || origin.password || origin.search || origin.hash || origin.pathname !== '/' ||
      (origin.protocol !== 'https:' && !(origin.protocol === 'http:' && ['localhost', '127.0.0.1', '[::1]'].includes(origin.hostname)))) return {}
    return Object.fromEntries(Object.entries(settingPaths).filter(([key, slug]) => settings.actions[key] === `${origin.origin}/if/flow/${slug}/`).map(([key]) => [key, settings.actions[key]]))
  } catch { return {} }
}
export function useAccountSettings(enabled: boolean) {
  return useQuery({ queryKey: ['account-settings'], queryFn: () => fetchApi<AccountSettings>('/api/v1/auth/account-settings'), enabled, retry: false })
}
