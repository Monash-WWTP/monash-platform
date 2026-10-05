import { useQuery } from '@tanstack/react-query'
import { fetchApi } from './transport'
export interface Account { id: string; email: string; capabilities: string[] }
export function useAccount() {
  return useQuery({ queryKey: ['account'], queryFn: () => fetchApi<Account>('/api/v1/auth/me'), retry: false })
}
