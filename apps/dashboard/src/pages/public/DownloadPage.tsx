import { useState } from "react";
import { Link } from "react-router-dom";
import { Download } from "lucide-react";
import { currentRelease } from "../../releases/release";
export default function DownloadPage() {
  const release = currentRelease;
  const [copyStatus, setCopyStatus] = useState("");
  async function copyLink() {
    try {
      await navigator.clipboard.writeText(
        new URL("/download", window.location.origin).href,
      );
      setCopyStatus("Link copied.");
    } catch {
      setCopyStatus(
        "Copy unavailable. Copy this page’s address from your browser.",
      );
    }
  }
  return (
    <main id="public-main" className="public-reading">
      <h1>CitizenFlood for Android</h1>
      <p className="reading-intro">
        Report what you observe in your local area using the existing live
        CitizenFlood service. Shared accounts with the dashboard are not
        available yet.
      </p>
      <section className="release-details" aria-labelledby="release-title">
        <h2 id="release-title">
          {release
            ? "Download the current release"
            : "Android release coming soon"}
        </h2>
        {release ? (
          <>
            <a className="apk-button" href={release.artifactUrl}>
              <Download size={20} />
              Download Android APK
            </a>
            <dl>
              <dt>Version</dt>
              <dd>{release.versionName}</dd>
              <dt>Released</dt>
              <dd>{release.publishedAt}</dd>
              <dt>File size</dt>
              <dd>{(release.byteSize / 1048576).toFixed(1)} MB</dd>
              <dt>Minimum Android</dt>
              <dd>{release.minAndroid}</dd>
              <dt>SHA-256</dt>
              <dd className="checksum">{release.sha256}</dd>
            </dl>
            <h3>Release notes</h3>
            <ul>
              {release.notes.map((note, i) => (
                <li key={i}>{note}</li>
              ))}
            </ul>
          </>
        ) : (
          <>
            <p>
              A signed public APK has not been released yet. The development
              build is not distributed here.
            </p>
            <button className="apk-button" disabled>
              <Download size={20} />
              Download Android APK
            </button>
          </>
        )}
      </section>
      <section>
        <h2>Installation guide</h2>
        <ol>
          <li>
            On an Android device, download the published APK from this page.
          </li>
          <li>
            Open the downloaded file. Android may ask you to allow installation
            from the browser or file manager you used.
          </li>
          <li>
            Review the Android installation prompt and confirm installation.
            Your browser cannot install the app silently.
          </li>
          <li>
            Open CitizenFlood. The current app starts an anonymous session;
            email sign-in is available within the app.
          </li>
        </ol>
        <p>
          Device policies and Android security settings can restrict
          installation. Follow the device’s instructions; contact your device
          administrator if installation is managed.
        </p>
      </section>
      <section>
        <h2>Updates and other devices</h2>
        <p>
          Future releases will appear on this page with version details and a
          checksum. Updates must use the same authorized signing identity. APK
          files are for Android; they cannot be installed on an iPhone.
        </p>
        <p>
          On a desktop or iPhone, open this website on your Android device.
        </p>
      </section>
      <button className="copy-link" onClick={copyLink}>
        Copy download page link
      </button>
      <p role="status">{copyStatus}</p>
      <Link to="/">Back to the platform</Link>
    </main>
  );
}
