# Contributing

Use feature branches and preserve the independent app/API package boundaries. Install from lockfiles. Follow the [local development checks](docs/operations/local-development.md), app README checks and optional research reproduction. Every workflow runs on every pull request so required checks cannot remain pending due to path filters.

An API change includes handler/schema tests and regenerated OpenAPI; generated client compatibility becomes required during cutover. A model/data change includes units, input provenance, assumptions and scientific review. Software tests cannot approve scientific decision use. Verify authorization at the server and privacy in projections.

Keep credentials, local env files, databases, build outputs and restricted datasets out of Git. Run `uv run --locked python scripts/check_repository.py` and the manifest checker. These are narrow repository checks, not a complete security audit. Full source verification can additionally pass all three pinned legacy checkouts to `scripts/check_import_inventory.py --source NAME=PATH --verify-targets`.

Mobile, dashboard and API release independently. A coordinated contract change may require all three checks but does not force simultaneous deployment. Maintainers must assign actual users/teams in CODEOWNERS before enforcing review ownership. Software licensing and deployment permissions are owner decisions.
