import { Link } from "react-router-dom";
export default function AccountPage() {
  return (
    <main id="public-main" className="public-reading">
      <h1>Account availability</h1>
      <p className="reading-intro">
        Open CitizenFlood on your Android phone to manage your app account.
      </p>
      <p>
        No account is needed to download CitizenFlood or read the research and
        documentation.
      </p>
      <section>
        <h2>Operator and moderator access</h2>
        <p>
          Contact your platform administrator for access. These permissions
          require an invitation and multi-factor authentication.
        </p>
      </section>
      <Link className="quiet-action" to="/download">Get CitizenFlood for Android</Link>
    </main>
  );
}
