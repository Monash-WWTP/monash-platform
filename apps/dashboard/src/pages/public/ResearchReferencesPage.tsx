import { Link } from "react-router-dom";
import { Download } from "lucide-react";
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
            <div className="reference-publication-heading">
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
                    Open full PDF
                  </a>
                  <a className="quiet-action" href={reference.pdfUrl} download>
                    Download PDF <Download size={17} aria-hidden="true" />
                  </a>
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>
      <Link to="/research">Back to research</Link>
    </main>
  );
}
