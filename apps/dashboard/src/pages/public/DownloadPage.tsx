import { useState } from "react";
import { Link } from "react-router-dom";
import { Download, ArrowRight, Copy, Smartphone } from "lucide-react";
import { currentRelease } from "../../releases/release";
export default function DownloadPage() {
  const release = currentRelease;
  const [copyStatus, setCopyStatus] = useState("");
  async function copyLink() {
    try {
      await navigator.clipboard.writeText(
        new URL("/download", window.location.origin).href,
      );
      setCopyStatus("Download page link copied.");
    } catch {
      setCopyStatus("Copy this page’s address from your browser to share it.");
    }
  }
  return (
    <main id="public-main" className="download-page">
      <div className="download-topline">
        <Link to="/">Monash Water</Link>
        <span>Android app</span>
      </div>
      <section className="download-hero" aria-labelledby="app-title">
        <div className="download-copy">
          <div className="app-identity">
            <img
              src="/assets/app/citizenflood-icon.png"
              alt=""
              width="88"
              height="88"
            />
            <div>
              <h1 id="app-title">CitizenFlood</h1>
            </div>
          </div>
          <p className="app-summary">
            Record what you see.
            <br />
            Keep your local water observations together.
          </p>
          <p className="app-description">
            Report rainfall, water levels, temperature and wastewater
            observations from your Android phone.
          </p>
          <div className="download-action">
            {release ? (
              <a className="apk-button" href={release.artifactUrl}>
                <Download size={20} aria-hidden="true" />
                Download APK
              </a>
            ) : (
              <button className="apk-button" disabled>
                <Download size={20} aria-hidden="true" />
                Release coming soon
              </button>
            )}
            <span>Direct download · no Play Store required</span>
          </div>
          {release && (
            <dl className="release-facts">
              <div>
                <dt>Version</dt>
                <dd>{release.versionName}</dd>
              </div>
              <div>
                <dt>Download size</dt>
                <dd>{(release.byteSize / 1048576).toFixed(1)} MB</dd>
              </div>
              <div>
                <dt>Requires</dt>
                <dd>Android {release.minAndroid}+</dd>
              </div>
            </dl>
          )}
          <p className="device-note">
            <Smartphone size={17} aria-hidden="true" />
            Android only. Using an iPhone or computer? Open this page on your
            Android phone.
          </p>
          <button className="text-button" onClick={copyLink}>
            <Copy size={16} aria-hidden="true" />
            Copy download link
          </button>
          <p className="copy-status" role="status">
            {copyStatus}
          </p>
        </div>
        <figure className="app-preview">
          <img
            src="/assets/app/report-screen.png"
            alt="CitizenFlood report screen with rainfall, water level, temperature and wastewater observation categories"
            width="922"
            height="2048"
          />
          <figcaption>
            Actual app screen · published Android version 1.0.0
          </figcaption>
        </figure>
      </section>
      <section className="installation" aria-labelledby="install-title">
        <div className="section-heading">
          <h2 id="install-title">Install in three steps.</h2>
          <p>Download the app directly from this page.</p>
        </div>
        <ol className="install-steps">
          <li>
            <span>1</span>
            <div>
              <h3>Download the APK</h3>
              <p>
                Tap “Download APK” on your Android phone. Open the file when the
                download finishes.
              </p>
            </div>
          </li>
          <li>
            <span>2</span>
            <div>
              <h3>Allow this installation</h3>
              <p>
                If Android asks, allow your browser to install this app, then
                return to the installation prompt.
              </p>
            </div>
          </li>
          <li>
            <span>3</span>
            <div>
              <h3>Open CitizenFlood</h3>
              <p>
                Confirm “Install”, then open the app and choose the observation
                you want to record.
              </p>
            </div>
          </li>
        </ol>
        <p className="install-note">
          You can turn off the browser’s installation permission afterward. If
          your device is managed, your administrator may need to allow
          installation.
        </p>
      </section>
      <section
        className="download-support"
        aria-label="Release and account information"
      >
        <div>
          <h2>Your platform account</h2>
          <p>
            The new platform uses one verified account across the dashboard and
            the API-connected CitizenFlood app. Operator access requires an
            invitation and MFA.
          </p>
          <p>
            Shared accounts are being verified in local staging. The public APK
            above still uses the existing CitizenFlood account service.
          </p>
          <Link to="/login">
            Platform sign-in <ArrowRight size={16} aria-hidden="true" />
          </Link>
        </div>
        <div className="release-disclosures">
          <details>
            <summary>Version and release notes</summary>
            {release ? (
              <>
                <p>
                  Version {release.versionName} · released {release.publishedAt}
                </p>
                <ul>
                  {release.notes.map((note, i) => (
                    <li key={i}>{note}</li>
                  ))}
                </ul>
              </>
            ) : (
              <p>A signed public release will appear here when ready.</p>
            )}
          </details>
          <details>
            <summary>Verify your download</summary>
            <p>The SHA-256 checksum identifies the exact published APK file.</p>
            {release && <code className="checksum">{release.sha256}</code>}
          </details>
          <details>
            <summary>How app updates work</summary>
            <p>
              Download the next published APK here and install it over the
              existing app. Updates use the same release signing identity. APK
              files cannot be installed on an iPhone.
            </p>
          </details>
        </div>
      </section>
    </main>
  );
}
