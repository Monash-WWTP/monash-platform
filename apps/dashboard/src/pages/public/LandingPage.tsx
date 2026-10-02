import { currentRelease } from "../../releases/release";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  Download,
  Users,
  FlaskConical,
  ChartNoAxesColumnIncreasing,
  Plus,
  Minus,
  Layers,
} from "lucide-react";

const purposes = [
  {
    name: "CitizenFlood",
    description: "Community observations from the public.",
    to: "/download",
    color: "citizen",
  },
  {
    name: "Operator workspace",
    description: "Wastewater operations and monitoring.",
    to: "/dashboard",
    color: "laboratory",
  },
  {
    name: "Research",
    description: "Illustrative model outputs and research.",
    to: "/research",
    color: "model",
  },
];
export default function LandingPage() {
  const [zoom, setZoom] = useState(1);
  const [legend, setLegend] = useState(
    () => window.matchMedia("(min-width: 701px)").matches,
  );
  useEffect(() => {
    const query = window.matchMedia("(min-width: 701px)");
    const update = () => setLegend(query.matches);
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  return (
    <main id="public-main">
      <section className="public-atlas" aria-label="Platform introduction">
        <div className="atlas-artwork" aria-hidden="true">
          <img
            src="/assets/plates/atlas.png"
            alt=""
            style={{ transform: `scale(${zoom})` }}
          />
        </div>
        <div className="atlas-opening">
          <h1>
            Understand water.
            <br />
            Report what you see.
          </h1>
          <p className="atlas-intro">
            Citizen observations, wastewater monitoring and research —
            <br className="desktop-break" /> with their evidence kept distinct.
          </p>
          <div className="atlas-release">
            {currentRelease ? (
              <a className="apk-button" href={currentRelease.artifactUrl}>
                <Download size={20} aria-hidden="true" />
                Download Android APK
              </a>
            ) : (
              <button className="apk-button" disabled>
                <Download size={20} aria-hidden="true" />
                Download Android APK
              </button>
            )}
            <div>
              <p>
                {currentRelease
                  ? `Android ${currentRelease.versionName}`
                  : "Android release coming soon"}
              </p>
              <Link to="/download">
                Installation guide <ArrowRight size={14} aria-hidden="true" />
              </Link>
            </div>
          </div>
          <div className="purpose-index">
            <h2>Explore the map by purpose</h2>
            {purposes.map((p) => (
              <Link className="purpose-row" key={p.name} to={p.to}>
                <span className={`purpose-dot ${p.color}`} aria-hidden="true" />
                <strong>{p.name}</strong>
                <span>{p.description}</span>
                <ArrowRight size={16} aria-hidden="true" />
              </Link>
            ))}
          </div>
        </div>
        <div className="atlas-tools" aria-label="Illustration controls">
          <button
            aria-label="Zoom illustration in"
            disabled={zoom >= 1.6}
            onClick={() => setZoom((v) => Math.min(1.6, v + 0.2))}
          >
            <Plus size={18} />
          </button>
          <button
            aria-label="Zoom illustration out"
            disabled={zoom <= 1}
            onClick={() => setZoom((v) => Math.max(1, v - 0.2))}
          >
            <Minus size={18} />
          </button>
          <button
            aria-label={
              legend ? "Hide illustration legend" : "Show illustration legend"
            }
            aria-pressed={legend}
            onClick={() => setLegend((v) => !v)}
          >
            <Layers size={18} />
          </button>
        </div>
        <div className="atlas-caption">
          <span className="north-mark" aria-hidden="true">
            N<span />
          </span>
          <span className="scale-mark" aria-hidden="true" />
          <span>Illustrative geography — not live monitoring.</span>
        </div>
        {legend && (
          <aside className="atlas-legend" aria-label="Illustration legend">
            <div>
              <span className="river-swatch" />
              Rivers and waterways
            </div>
            <div>
              <span className="catchment-swatch" />
              Catchment area
            </div>
            <div>
              <span className="park-swatch" />
              Parks and public land
            </div>
            <div>
              <span className="water-swatch" />
              Coastline / water body
            </div>
          </aside>
        )}
      </section>
      <section className="public-evidence" aria-labelledby="evidence-title">
        <div className="evidence-introduction">
          <h2 id="evidence-title">Three kinds of evidence</h2>
          <p>
            Different types of information help us see a fuller picture of water
            in our environment.
            <br className="desktop-break" /> Each has a distinct purpose, and we
            keep their evidence separate.
          </p>
        </div>
        <div className="evidence-columns">
          <article>
            <span className="evidence-icon citizen">
              <Users size={48} aria-hidden="true" />
            </span>
            <div>
              <h3>Community observations</h3>
              <p>
                Reports from people in the community, such as photos and notes
                about water in their local area.
              </p>
              <Link to="/download">
                Go to CitizenFlood <ArrowRight size={14} aria-hidden="true" />
              </Link>
            </div>
          </article>
          <article>
            <span className="evidence-icon laboratory">
              <FlaskConical size={48} aria-hidden="true" />
            </span>
            <div>
              <h3>Laboratory measurements</h3>
              <p>
                Wastewater and water quality measurements from operational
                monitoring.
              </p>
              <Link to="/dashboard">
                Go to operator workspace{" "}
                <ArrowRight size={14} aria-hidden="true" />
              </Link>
            </div>
          </article>
          <article>
            <span className="evidence-icon model">
              <ChartNoAxesColumnIncreasing size={48} aria-hidden="true" />
            </span>
            <div>
              <h3>Illustrative model outputs</h3>
              <p>
                Model outputs used for research and exploration, not real-time
                monitoring.
              </p>
              <Link to="/research">
                Go to research <ArrowRight size={14} aria-hidden="true" />
              </Link>
            </div>
          </article>
        </div>
        <div className="research-strip">
          <h2>Research</h2>
          <span className="research-rule" aria-hidden="true" />
          <p>Approved publications will appear here.</p>
          <Link to="/research">
            View all research <ArrowRight size={14} aria-hidden="true" />
          </Link>
        </div>
      </section>
    </main>
  );
}
