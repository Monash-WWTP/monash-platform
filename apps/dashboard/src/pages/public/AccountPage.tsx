import { Link, useLocation } from 'react-router-dom'
export default function AccountPage() {
  const registration = useLocation().pathname === '/register'
  return <main id="public-main" className="public-reading">
    <h1>{registration ? 'Create a platform account' : 'Log in to your platform account'}</h1>
    <p className="reading-intro">One account for the dashboard and the API-connected CitizenFlood app.</p>
    <p>{registration ? 'Verify your email to create a citizen account.' : 'Continue to the shared account service to sign in.'}</p>
    <a className="apk-button" href={registration ? '/api/v1/auth/register' : '/api/v1/auth/login'}>
      {registration ? 'Create account' : 'Continue to sign in'}
    </a>
    <section><h2>One account, separate permissions</h2>
      <p>Citizen registration allows reporting. Operator and moderator access require an invitation and multi-factor authentication.</p>
      <p>The public APK version 1.0.0 still uses the legacy reporting service. The API-connected app is being verified locally before release.</p>
    </section>
    <Link to="/dashboard">Open the dashboard</Link>
  </main>
}
