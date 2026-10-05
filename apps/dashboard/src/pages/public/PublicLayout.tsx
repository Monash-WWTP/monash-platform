import { Link, Outlet } from "react-router-dom";
import "./public.css";
export default function PublicLayout() {
  return (
    <div className="public-portal">
      <a className="skip-link" href="#public-main">
        Skip to content
      </a>
      <header className="public-header">
        <Link className="public-brand" to="/">
          Monash Water
        </Link>
        <nav aria-label="Main navigation">
          <Link to="/download">Download app</Link>
          <Link to="/research">Research</Link>
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/login">Log in</Link>
          <Link className="account-link" to="/register">
            Create account
          </Link>
        </nav>
      </header>
      <Outlet />
      <footer className="public-footer">
        <span>Monash Water Platform · community, monitoring and research</span>
        <Link to="/download">CitizenFlood for Android</Link>
      </footer>
    </div>
  );
}
