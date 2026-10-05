import { Link, useLocation } from "react-router-dom";
export default function AccountPage() {
  const registration = useLocation().pathname === "/register";
  return (
    <main id="public-main" className="public-reading">
      <h1>
        {registration
          ? "Create a platform account"
          : "Log in to your platform account"}
      </h1>
      <p className="reading-intro">
        One account for the dashboard and the API-connected CitizenFlood app in
        local staging.
      </p>
      <p>
        The downloadable public APK 1.0.0 still uses the existing CitizenFlood
        account service. Shared accounts are being verified before the next
        release.
      </p>
      <p>
        {registration
          ? "Citizen registration will verify your email and create an account shared with CitizenFlood and the dashboard."
          : "Your shared account will work with CitizenFlood and the dashboard."}
      </p>
      <div className="account-service-status" role="status">
        <strong>Account service is in local staging</strong>
        <p>
          The new API and Authentik sign-in service are not online here yet.
          When deployed, this page will open Authentik for sign-in or verified
          registration.
        </p>
      </div>
      <button className="apk-button" type="button" disabled>
        {registration
          ? "Registration opens with service launch"
          : "Sign-in opens with service launch"}
      </button>
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
      <Link to="/dashboard">Open the dashboard</Link>
    </main>
  );
}
