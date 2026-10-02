import { Link, useParams } from "react-router-dom";
import { publishedArticles } from "../../research/articles";
export default function ResearchArticlePage() {
  const { slug } = useParams();
  const article = publishedArticles.find((a) => a.slug === slug);
  if (!article)
    return (
      <main id="public-main" className="public-reading">
        <h1>Article not found</h1>
        <p>This article is unavailable or has not been published.</p>
        <Link to="/research">Browse approved research</Link>
      </main>
    );
  return (
    <main id="public-main" className="public-reading">
      <article>
        <h1>{article.title}</h1>
        <p className="reading-intro">{article.authors.join(", ")}</p>
        <p>
          {article.type} · Published {article.publishedAt}
        </p>
        {article.paragraphs.map((p, i) => (
          <p key={i}>{p}</p>
        ))}
        <h2>Limitations</h2>
        <ul>
          {article.limitations.map((limit, i) => (
            <li key={i}>{limit}</li>
          ))}
        </ul>
        <h2>Correction history</h2>
        {article.corrections.length ? (
          <ol>
            {article.corrections.map((c, i) => (
              <li key={i}>
                <time dateTime={c.date}>{c.date}</time>: {c.description}
              </li>
            ))}
          </ol>
        ) : (
          <p>No corrections have been published.</p>
        )}
        <h2>Sources</h2>
        <ul>
          {article.sources.map((s) => (
            <li key={s.url}>
              <a href={s.url} rel="noopener noreferrer">
                {s.title}
              </a>
            </li>
          ))}
        </ul>
      </article>
      <Link to="/research">Back to research</Link>
    </main>
  );
}
