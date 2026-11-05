import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAccount } from '../../api/accounts'
import { fetchApi } from '../../api/transport'

export default function OperatorAccess({ simulation = false }: { simulation?: boolean }) {
  const queryClient = useQueryClient()
  const { data: account } = useAccount()
  const [error, setError] = useState('')
  async function signOut() {
    try { await fetchApi('/api/v1/auth/logout', { method: 'POST' }); queryClient.clear() }
    catch (e) { setError(e instanceof Error ? e.message : 'Sign out failed') }
  }
  return <section className="rounded-lg border border-border bg-card p-3 text-sm [overflow-wrap:anywhere]" aria-label="Account access">
    {account ? <>
      <p>Signed in as {account.display_name || account.email}</p>
      <a className="mr-3 underline" href="/account">Account settings</a>
      {account.capabilities.includes('platform:admin') && <a className="mr-3 underline" href="/dashboard/admin">Administration</a>}
      {account.capabilities.includes('report:respond') && <a className="mr-3 underline" href="/dashboard/operations">Operations reports</a>}
      {account.capabilities.includes('report:review') && <a className="mr-3 underline" href="/dashboard/moderation">Review reports</a>}
      {!simulation && <a className="mr-3 underline" href="/api/v1/auth/login?operator=true">Verify MFA</a>}
      <button className="mt-2 text-primary underline" onClick={signOut}>Sign out</button>
    </> : <>
      <p className="font-medium">{simulation ? 'Sign in to use Simulation lab' : 'Operator sign-in'}</p>
      {!simulation && <p className="mt-1">Use your shared account. Operator access requires an invitation and MFA.</p>}
      <a className="mt-2 inline-block text-primary underline" href={simulation ? '/api/v1/auth/login' : '/api/v1/auth/login?operator=true'}>Sign in</a>
    </>}
    {error && <p role="alert">{error}</p>}
  </section>
}
