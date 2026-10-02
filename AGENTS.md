# Repository guidance

<!-- CODEGRAPH_START -->
## CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- **MCP tool** (when available): `codegraph_explore` answers most code questions in one call — the relevant symbols' verbatim source plus the call paths between them. Name a file or symbol in the query to read its current line-numbered source.
- **Shell**: `codegraph explore "<symbol names or question>"` prints the same output.

If there is no `.codegraph/` directory, skip CodeGraph entirely — indexing is the user's decision.
<!-- CODEGRAPH_END -->

For implementation or verification, read `CONTRIBUTING.md`. For client integration changes, read `docs/migration/ROADMAP.md` to distinguish current legacy routes from target contracts. For model or data changes, read `docs/science/VALIDATION.md` before changing scientific semantics.
