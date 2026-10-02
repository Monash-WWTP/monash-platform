export interface PublishedArticle {
  slug: string;
  title: string;
  authors: string[];
  publishedAt: string;
  type: "peer-reviewed" | "preprint" | "project-note";
  approval: string;
  sources: { title: string; url: string }[];
  paragraphs: string[];
  limitations: string[];
  corrections: { date: string; description: string }[];
}
const text = (v: unknown): v is string =>
  typeof v === "string" && v.trim().length > 0;
const texts = (v: unknown): v is string[] =>
  Array.isArray(v) && v.length > 0 && v.every(text);
export function validatePublishedArticles(input: unknown): PublishedArticle[] {
  if (!Array.isArray(input))
    throw new Error("Published research must be an array.");
  const seen = new Set<string>();
  return input.map((value) => {
    if (!value || typeof value !== "object")
      throw new Error("Invalid research item.");
    const a = value as Record<string, unknown>;
    if (
      !text(a.slug) ||
      !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(a.slug) ||
      seen.has(a.slug) ||
      !text(a.title) ||
      !texts(a.authors) ||
      !text(a.approval) ||
      !texts(a.paragraphs) ||
      !texts(a.limitations) ||
      !Array.isArray(a.corrections) ||
      !text(a.publishedAt) ||
      !/^\d{4}-\d{2}-\d{2}$/.test(a.publishedAt) ||
      !Number.isFinite(Date.parse(a.publishedAt)) ||
      new Date(a.publishedAt).toISOString().slice(0, 10) !== a.publishedAt ||
      !["peer-reviewed", "preprint", "project-note"].includes(String(a.type)) ||
      !Array.isArray(a.sources) ||
      a.sources.length === 0
    )
      throw new Error(
        "Research requires unique slug, approval, attribution, date, type, sources and content.",
      );
    for (const source of a.sources) {
      if (!source || !text(source.title) || !text(source.url))
        throw new Error("Invalid source.");
      const u = new URL(source.url);
      if (u.protocol !== "https:" || u.username || u.password)
        throw new Error("Sources require public HTTPS links.");
    }
    for (const correction of a.corrections as unknown[]) {
      if (!correction || typeof correction !== "object")
        throw new Error("Invalid correction.");
      const c = correction as Record<string, unknown>;
      if (
        !text(c.description) ||
        !text(c.date) ||
        !/^\d{4}-\d{2}-\d{2}$/.test(c.date) ||
        !Number.isFinite(Date.parse(c.date)) ||
        new Date(c.date).toISOString().slice(0, 10) !== c.date ||
        c.date < a.publishedAt
      )
        throw new Error(
          "Correction requires a description and valid date on or after publication.",
        );
    }
    seen.add(a.slug);
    return {
      slug: a.slug,
      title: a.title,
      authors: a.authors,
      publishedAt: a.publishedAt,
      type: a.type as PublishedArticle["type"],
      approval: a.approval,
      sources: a.sources,
      paragraphs: a.paragraphs,
      limitations: a.limitations,
      corrections: a.corrections as PublishedArticle["corrections"],
    };
  });
}
// Drafts are outside the public import graph; no fabricated examples.
export const publishedArticles = validatePublishedArticles([]);
