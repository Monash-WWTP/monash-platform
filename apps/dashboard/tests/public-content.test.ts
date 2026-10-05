import { test } from "node:test";
import assert from "node:assert/strict";
import { parseRelease } from "../src/releases/release.ts";
const good = {
  versionName: "1.0.0",
  versionCode: 1,
  notes: ["Initial reviewed release."],
  minAndroid: "8.0",
  publishedAt: "2026-10-02",
  byteSize: 12000000,
  sha256: "a".repeat(64),
  artifactUrl: "https://downloads.example.org/citizenflood/1.0.0/app.apk",
};
test("accepts a complete HTTPS release manifest", () =>
  assert.deepEqual(parseRelease(good), good));
test("absent release does not create a download", () =>
  assert.equal(parseRelease(null), null));
test("rejects unsafe or inaccessible artifact URLs", () => {
  for (const artifactUrl of [
    "http://downloads.example.org/app.apk",
    "https://github.com/Monash-WWTP/monash-platform/releases/download/v1/app.apk",
    "javascript:alert(1)",
    "https://user:password@downloads.example.org/app.apk",
  ])
    assert.equal(parseRelease({ ...good, artifactUrl }), null);
});
test("rejects malformed checksum and invalid version or size", () => {
  for (const patch of [
    { sha256: "bad" },
    { versionCode: 0 },
    { byteSize: -1 },
    { publishedAt: "not-a-date" },
    { versionName: "" },
  ])
    assert.equal(parseRelease({ ...good, ...patch }), null);
});
import { validatePublishedArticles as validate } from "../src/research/articles.ts";
const paper = {
  slug: "reviewed-note",
  title: "A reviewed project note",
  authors: ["Example author"],
  publishedAt: "2026-10-02",
  type: "project-note",
  approval: "review-123",
  sources: [{ title: "Source", url: "https://example.org/source" }],
  paragraphs: ["Reviewed text."],
  limitations: ["Illustrative study; no operational validation."],
  corrections: [],
};
test("accepts approved attributed research", () =>
  assert.deepEqual(validate([paper]), [paper]));
test("rejects unapproved research and incomplete metadata", () => {
  for (const patch of [
    { approval: "" },
    { authors: [] },
    { sources: [] },
    { paragraphs: [] },
  ])
    assert.throws(() => validate([{ ...paper, ...patch }]));
});
test("rejects duplicate article slugs and unsafe source links", () => {
  assert.throws(() => validate([paper, paper]));
  assert.throws(() =>
    validate([
      { ...paper, sources: [{ title: "Bad", url: "javascript:alert(1)" }] },
    ]),
  );
});

test("rejects impossible calendar dates", () => {
  assert.equal(parseRelease({ ...good, publishedAt: "2026-02-30" }), null);
  assert.throws(() => validate([{ ...paper, publishedAt: "2026-02-30" }]));
});

test("requires release notes and research limitations with valid correction history", () => {
  assert.equal(parseRelease({ ...good, notes: [] }), null);
  assert.throws(() => validate([{ ...paper, limitations: [] }]));
  assert.throws(() =>
    validate([
      {
        ...paper,
        corrections: [{ date: "2026-02-30", description: "Correction" }],
      },
    ]),
  );
  assert.throws(() =>
    validate([
      {
        ...paper,
        corrections: [{ date: "2026-01-01", description: "Correction" }],
      },
    ]),
  );
});
