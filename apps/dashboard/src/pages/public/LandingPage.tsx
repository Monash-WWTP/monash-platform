import { Link } from "react-router-dom";
import { ArrowRight, Download } from "lucide-react";
import { currentRelease } from "../../releases/release";
export default function LandingPage() {
  return (
    <main id="public-main" className="platform-home">
      <section className="home-intro">
        <div>
          <h1>
            Water observations.
            <br />A clearer shared picture.
          </h1>
          <p className="home-lead">
            A place for community reports, wastewater monitoring and research.
          </p>
          <p className="home-description">
            Record observations with CitizenFlood. Explore the laboratory record
            in the dashboard. Read research as approved articles become
            available.
          </p>
          <div className="home-actions">
            <Link className="apk-button" to="/download">
              <Download size={20} aria-hidden="true" />
              Get CitizenFlood
            </Link>
            <Link className="quiet-action" to="/dashboard">
              Open dashboard <ArrowRight size={18} aria-hidden="true" />
            </Link>
          </div>
          <p className="home-release">
            Android{currentRelease ? ` ${currentRelease.versionName}` : ""} ·
            direct APK download
          </p>
        </div>
        <Link className="home-app" to="/download">
          <img
            src="/assets/app/citizenflood-icon.png"
            alt=""
            width="76"
            height="76"
          />
          <span>
            <strong>CitizenFlood</strong>
            <span>Your observations, recorded in the field.</span>
            <span className="home-app-link">
              View the Android app <ArrowRight size={16} aria-hidden="true" />
            </span>
          </span>
        </Link>
      </section>
      <section className="platform-paths" aria-label="Explore the platform">
        <article>
          <h2>Record an observation.</h2>
          <p>
            Rainfall, water level, temperature or wastewater. Capture what you
            see with the Android app.
          </p>
          <Link to="/download">
            Download CitizenFlood <ArrowRight size={17} aria-hidden="true" />
          </Link>
        </article>
        <article>
          <h2>Explore the water record.</h2>
          <p>
            View laboratory measurements and their source context. Invited
            operators can access scenario tools.
          </p>
          <Link to="/dashboard">
            Open the dashboard <ArrowRight size={17} aria-hidden="true" />
          </Link>
        </article>
        <article>
          <h2>Read the work behind it.</h2>
          <p>
            Approved research articles and publication links will appear here
            when they are ready to share.
          </p>
          <Link to="/research">
            Browse research <ArrowRight size={17} aria-hidden="true" />
          </Link>
        </article>
      </section>
      <section className="evidence-note">
        <h2>Understand what you’re looking at.</h2>
        <p>
          Community observations describe what people report. Laboratory
          measurements describe sampled water quality. Model outputs are
          illustrative and unvalidated. Each is labelled with its own context.
        </p>
      </section>
      <section className="shared-account-band">
        <div>
          <h2>One platform account.</h2>
          <p>
            Shared accounts are available in local staging for the dashboard and
            API-connected app. The public APK 1.0.0 uses the existing
            CitizenFlood account service.
          </p>
        </div>
        <Link className="quiet-action" to="/register">
          Create an account <ArrowRight size={18} aria-hidden="true" />
        </Link>
      </section>
    </main>
  );
}
