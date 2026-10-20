import { Link } from "react-router-dom";
import { ArrowRight, Download } from "lucide-react";
import { documentationUrl } from "../../lib/documentation";
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
            Record local water observations with CitizenFlood. Explore
            wastewater monitoring, research methods and the evidence behind
            the platform.
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
        <figure className="app-preview home-preview">
          <img src="/assets/app/report-screen-latest.webp" alt="CitizenFlood report screen with rainfall, water level, temperature and wastewater observation categories" width="1080" height="2400" />
        </figure>
      </section>
      <section className="platform-paths" aria-label="Explore the platform">
        <article>
          <h2>Explore the research.</h2>
          <p>
            No approved articles are published yet. Read the current methods and
            limitations while this section is prepared.
          </p>
          <Link to="/research">
            Browse research <ArrowRight size={17} aria-hidden="true" />
          </Link>
        </article>
        <article>
          <h2>Methods and references.</h2>
          <p>Read the urban-water carbon-accounting guideline and see how references inform the platform.</p>
          <a href="/references/urban-water-carbon-accounting-guidelines.pdf">Open the guideline PDF <ArrowRight size={17} aria-hidden="true" /></a>
          <Link to="/research/references">View all references <ArrowRight size={17} aria-hidden="true" /></Link>
        </article>
      </section>
      <section className="evidence-note" aria-labelledby="documentation-heading">
        <h2 id="documentation-heading">Find your starting point.</h2>
        <div>
          <figure className="landscape-image">
            <img src="/assets/illustrations/river-landscape.webp" alt="A quiet river bordered by trees and a concrete embankment" width="1536" height="1024" loading="lazy" />
          </figure>
          <p>Read getting-started guides, reporting and monitoring workflows, model methods and release procedures. Start with a guide for your role, then follow the supporting sources and methods.</p>
          <nav className="home-guide-links" aria-label="Getting started guides">
            <a href={`${documentationUrl}/docs/get-started/citizens/`}>Report a water observation <ArrowRight size={17} aria-hidden="true" /></a>
            <a href={`${documentationUrl}/docs/guides/monitoring/`}>Understand monitoring records <ArrowRight size={17} aria-hidden="true" /></a>
            <a href={documentationUrl}>Browse the full manual <ArrowRight size={17} aria-hidden="true" /></a>
          </nav>
        </div>
      </section>
      <section className="evidence-note">
        <h2>Understand what you’re looking at.</h2>
        <p>
          Community observations describe what people report. Laboratory
          measurements describe sampled water quality. Model outputs are
          illustrative and unvalidated. Each is labelled with its own context.
        </p>
      </section>
    </main>
  );
}
