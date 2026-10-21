import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAccount, useAccountSettings, trustedAccountActions } from '../../api/accounts'
import { ApiRequestError } from '../../api/transport'

export default function AccountPage() {
  const client = useQueryClient()
  const account = useAccount()
  const settings = useAccountSettings(Boolean(account.data))
  useEffect(() => {
    if (sessionStorage.getItem('monash-settings-return')) {
      sessionStorage.removeItem('monash-settings-return')
      client.clear()
      window.location.assign('/api/v1/auth/login?account_settings=true')
    }
  }, [client])
  useEffect(() => {
    if (account.error instanceof ApiRequestError && account.error.status === 401) {
      client.removeQueries({ predicate: query => query.queryKey[0] !== 'account' })
    }
  }, [account.error, client])
  const actions = trustedAccountActions(settings.data)
  const labels: [string, string][] = [['profile', 'Profile'], ['email', 'Change email'], ['password', 'Change password'], ['security', 'MFA & account sessions'], ['signout_all', 'Sign out all devices']]
  return <main id="public-main" className="public-reading">
    <h1>Your account</h1>
    {account.data ? <>
      {account.data.display_name && <p className="reading-intro">{account.data.display_name}</p>}
      <p>{account.data.email}</p>
      <p>Account settings open secure sign-in.</p>
      <nav aria-label="Account settings">
        {labels.map(([action, label]) => actions[action] && <p key={action}><a className="quiet-action" href={actions[action]} onClick={() => {
          sessionStorage.setItem('monash-settings-return', '1')
          client.clear()
        }}>{label}</a></p>)}
      </nav>
      {settings.isPending ? <p>Loading settings…</p> : Object.keys(actions).length === 0 && <p>Account settings are unavailable.</p>}
      {settings.isError && <p role="alert">Could not reach account settings.</p>}
      <button className="quiet-action" onClick={() => { void settings.refetch() }}>Retry settings</button>
    </> : account.isPending ? <p>Loading account…</p> : <>
      {account.error instanceof ApiRequestError && account.error.status !== 401 && <p role="alert">Account service unavailable. Please try again.</p>}
      <p><a className="quiet-action" href="/api/v1/auth/login?account_settings=true">Sign in</a></p>
      <p><a className="quiet-action" href="/api/v1/auth/register">Create account</a></p>
    </>}
  </main>
}
