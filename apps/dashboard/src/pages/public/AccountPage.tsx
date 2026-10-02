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
      <p className="reading-intro">Shared accounts are not available yet.</p>
      <p>
        We are connecting CitizenFlood and the dashboard to one account service.{" "}
        {registration
          ? "Verified citizen registration will open when that integration is ready."
          : "New platform login will become available after the shared account integration is ready."}
      </p>
      <section>
        <h2>One account, separate permissions</h2>
        <p>
          Citizen registration will provide access to reporting features.
          Operator workspace access requires an invitation and multi-factor
          authentication. Creating a citizen account does not grant operator
          permissions.
        </p>
      </section>
      <p>
        Existing invited operators can use the current dashboard sign-in during
        migration.
      </p>
      <Link to="/dashboard">Open the current dashboard</Link>
    </main>
  );
}
