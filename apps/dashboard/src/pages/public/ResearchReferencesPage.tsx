import { Link } from "react-router-dom";
import { ArrowRight, Download } from "lucide-react";
import { researchReferences } from "../../research/references";

export default function ResearchReferencesPage() {
  return (
    <main id="public-main" className="public-reading">
      <h1>References</h1>
      <p className="reading-intro">
        Publications and technical resources that inform the platform’s
        research and future methods.
      </p>
      <div className="reference-collection">
        {researchReferences.map((reference) => (
          <article
            className="reference-publication"
            id={reference.slug}
            key={reference.slug}
          >
            <header className="reference-publication-heading">
              <figure className="reference-cover">
                <img src={reference.coverUrl} alt={`Cover of ${reference.title}`} />
                <figcaption>Cover of the supplied edition</figcaption>
              </figure>
              <div className="reference-metadata">
                <p className="section-label">Technical resource · {reference.publishedAt}</p>
                <h2>{reference.title}</h2>
                <p>
                  {reference.organization}. Edited and translated by{" "}
                  {reference.editorsTranslators.join(" and ")}. {reference.publisher}.
                </p>
                <p>{reference.relevance}</p>
                <p className="reference-rights">
                  License stated in the supplied edition: {reference.license}.
                  Third-party material may have separate rights.
                </p>
                <p className="reference-doi">
                  DOI: <a href={reference.publisherUrl}>{reference.doi}</a>
                </p>
                <div className="reference-actions">
                  <a
                    className="apk-button"
                    href={reference.pdfUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open full PDF <ArrowRight size={17} aria-hidden="true" />
                  </a>
                  <a className="quiet-action" href={reference.pdfUrl} download>
                    Download PDF <Download size={17} aria-hidden="true" />
                  </a>
                </div>
              </div>
            </header>
            <section
              className="reference-reader"
              id={`${reference.slug}-document-viewer`}
              aria-labelledby={`${reference.slug}-reader-title`}
            >
              <div className="reference-reader-heading">
                <div>
                  <p className="section-label">Read online</p>
                  <h3 id={`${reference.slug}-reader-title`}>Publication preview</h3>
                </div>
                <a href={reference.pdfUrl} target="_blank" rel="noopener noreferrer">
                  Open in a new tab
                </a>
              </div>
              <iframe
                className="reference-pdf-viewer"
                src={`${reference.pdfUrl}#view=FitH`}
                title={`PDF viewer: ${reference.title}`}
                loading="lazy"
              />
              <p className="reference-reader-fallback">
                If the document does not appear in your browser, use the open or
                download links above.
              </p>
            </section>
          </article>
        ))}
      </div>
      <Link to="/research">Back to research</Link>
    </main>
  );
}
