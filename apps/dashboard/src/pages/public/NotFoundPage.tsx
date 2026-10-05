import { Link } from "react-router-dom";
export default function NotFoundPage() {
  return (
    <main id="public-main" className="public-reading">
      <h1>Page not found</h1>
      <p>The address does not match a page on this platform.</p>
      <Link to="/">Go to the landing page</Link>
    </main>
  );
}
