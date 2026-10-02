import { Link } from "react-router-dom";
import { publishedArticles } from "../../research/articles";
export default function ResearchPage() {
  return (
    <main id="public-main" className="public-reading">
      <h1>Research</h1>
      <p className="reading-intro">
        Methods, publications and project notes with clear sources and
        publication status.
      </p>
      {publishedArticles.length === 0 ? (
        <section className="research-empty">
          <h2>Approved publications will appear here.</h2>
          <p>
            We are preparing this section. Articles will be published only after
            review and approval.
          </p>
        </section>
      ) : (
        <ul className="research-list">
          {publishedArticles.map((a) => (
            <li key={a.slug}>
              <p>
                {a.type} · {a.publishedAt}
              </p>
              <h2>
                <Link to={`/research/${a.slug}`}>{a.title}</Link>
              </h2>
              <p>{a.authors.join(", ")}</p>
            </li>
          ))}
        </ul>
      )}
      <section>
        <h2>Reading the evidence</h2>
        <p>
          Community observations, laboratory measurements and model outputs are
          different kinds of evidence. The current simulation model is
          illustrative and unvalidated; its outputs must not be used as
          operational or regulatory decision support.
        </p>
        <p>
          Each article will identify its authors, sources and publication
          status. A project note or preprint will not be described as a
          peer-reviewed paper.
        </p>
      </section>
    </main>
  );
}
