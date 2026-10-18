import { Link } from "react-router-dom";
export default function AccountPage() {
  return (
    <main id="public-main" className="public-reading">
      <h1>Account availability</h1>
      <p className="reading-intro">
        One account for the dashboard and the API-connected CitizenFlood app in
        local staging.
      </p>
      <p>
        The downloadable public APK 1.0.0 still uses the existing CitizenFlood
        account service. Shared accounts are being verified before the next
        release.
      </p>
      <div className="account-service-status" role="status">
        <strong>Account service is in local staging</strong>
        <p>
          The new API and Authentik sign-in service are not online here yet.
          When deployed, this page will open Authentik for sign-in or verified
          registration.
        </p>
      </div>
      <p className="account-public-access">
        No account is needed to download CitizenFlood or read approved research.
      </p>
      <section>
        <h2>One account, separate permissions</h2>
        <p>
          Citizen registration allows reporting. Operator and moderator access
          require an invitation and multi-factor authentication.
        </p>
        <p>
          The public APK version 1.0.0 still uses the legacy reporting service.
          The API-connected app is being verified locally before release.
        </p>
      </section>
      <Link className="quiet-action" to="/download">Get CitizenFlood for Android</Link>
    </main>
  );
}
