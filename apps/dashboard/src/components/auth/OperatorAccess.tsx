import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAccount } from '../../api/accounts'
import { fetchApi } from '../../api/transport'

export default function OperatorAccess() {
  const queryClient = useQueryClient()
  const { data: account } = useAccount()
  const [error, setError] = useState('')
  async function signOut() {
    try { await fetchApi('/api/v1/auth/logout', { method: 'POST' }); queryClient.clear() }
    catch (e) { setError(e instanceof Error ? e.message : 'Sign out failed') }
  }
  return <section className="rounded-md border bg-card p-2.5 text-xs" aria-label="Account access">
    {account ? <>
      <p>Signed in as {account.email}</p>
      {!account.capabilities.includes('scenario:operate') && <p>Scenario access requires an operator invitation.</p>}
      {account.capabilities.includes('report:review') && <a className="mr-3 underline" href="/dashboard/moderation">Review reports</a>}
      <a className="mr-3 underline" href="/api/v1/auth/login?operator=true">Verify MFA</a>
      <button className="mt-2 text-primary underline" onClick={signOut}>Sign out</button>
    </> : <>
      <p className="font-medium">Operator sign-in</p>
      <p className="mt-1">Use your shared account. Operator access requires an invitation and MFA.</p>
      <a className="mt-2 inline-block text-primary underline" href="/api/v1/auth/login?operator=true">Sign in</a>
    </>}
    {error && <p role="alert">{error}</p>}
  </section>
}
