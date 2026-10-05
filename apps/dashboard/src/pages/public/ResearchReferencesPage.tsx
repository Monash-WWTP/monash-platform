import { Link } from "react-router-dom";
import { researchReferences } from "../../research/references";

export default function ResearchReferencesPage() {
  return (
    <main id="public-main" className="public-reading">
      <h1>References</h1>
      <p className="reading-intro">
        Publications and technical resources that inform the platform’s
        research and future methods.
      </p>
      <ol className="research-list reference-list">
        {researchReferences.map((reference) => (
          <li key={reference.slug}>
            <h2>{reference.title}</h2>
            <p>
              {reference.organization}. Edited and translated by{" "}
              {reference.editorsTranslators.join(" and ")} ({reference.publishedAt}).
              {" "}
              {reference.publisher}.
            </p>
            <p>{reference.relevance}</p>
            <p>
              License stated in the supplied edition: {reference.license}.
              Third-party material may have separate rights.
            </p>
            <p>
              DOI: <a href={reference.publisherUrl}>{reference.doi}</a>
            </p>
            <a href={reference.pdfUrl}>Open the hosted PDF</a>
          </li>
        ))}
      </ol>
      <Link to="/research">Back to research</Link>
    </main>
  );
}
