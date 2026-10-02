import { useEffect, useState, type FormEvent } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { Session } from '@supabase/supabase-js'

import { supabase } from '../../lib/supabase'

export default function OperatorAccess() {
  const queryClient = useQueryClient()
  const [session, setSession] = useState<Session | null>(null)
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session))
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, next) => {
      setSession(next)
      const protectedQueries = [['scenarios'], ['run'], ['timeseries'], ['compare']] as const
      if (event === 'SIGNED_IN') {
        for (const queryKey of protectedQueries) {
          void queryClient.invalidateQueries({ queryKey: [...queryKey] })
        }
      } else if (event === 'SIGNED_OUT') {
        for (const queryKey of protectedQueries) {
          queryClient.removeQueries({ queryKey: [...queryKey] })
        }
      }
    })
    return () => subscription.unsubscribe()
  }, [queryClient])

  async function sendSignInLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setMessage('')
    const { error } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: {
        shouldCreateUser: false,
        emailRedirectTo: window.location.origin,
      },
    })
    setBusy(false)
    setMessage(error ? error.message : 'If this is an invited operator account, check its inbox for a sign-in link.')
  }

  async function signOut() {
    setMessage('')
    const { error } = await supabase.auth.signOut()
    if (error) setMessage(error.message)
  }

  if (session?.user.email) {
    return (
      <div className="flex items-center justify-between gap-2 rounded-md border bg-muted/40 px-2 py-1.5 text-xs">
        <span className="min-w-0 truncate text-muted-foreground" title={session.user.email}>
          Signed in as {session.user.email}
        </span>
        <button className="shrink-0 font-medium text-primary hover:underline" onClick={signOut}>
          Sign out
        </button>
      </div>
    )
  }

  return (
    <form onSubmit={sendSignInLink} className="rounded-md border bg-card p-2.5">
      <p className="text-xs font-medium">Operator sign-in</p>
      <p className="mt-0.5 text-[11px] text-muted-foreground">
        Sign in with an invited email to view scenarios, save changes, and run the model.
      </p>
      <div className="mt-2 flex gap-1.5">
        <input
          aria-label="Operator email"
          autoComplete="email"
          className="min-w-0 flex-1 rounded border bg-background px-2 py-1 text-xs"
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="name@monash.edu"
        />
        <button
          className="rounded bg-primary px-2 py-1 text-xs font-medium text-primary-foreground disabled:opacity-50"
          type="submit"
          disabled={busy}
        >
          {busy ? 'Sending…' : 'Send link'}
        </button>
      </div>
      {message && <p role="status" className="mt-2 text-[11px] text-muted-foreground">{message}</p>}
    </form>
  )
}
