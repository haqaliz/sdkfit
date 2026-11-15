# FAQ

**Is SDK Fit a SaaS?**
No. It is a CLI and a self-hosted service. There is no SDK Fit account, hosted dashboard or data
store in the cloud.

**Does it push to my repository?**
Only when you ask it to (`--open-pr` or the provider/installed path). It clones a clean checkout,
commits the exact diff to a new branch and opens a pull request through your `git`/`gh` or your
GitHub App. It never force-pushes, never deletes branches and never merges.

**Does it auto-merge?**
No. It opens a pull request; a human reviews and merges it.

**Which languages and changes are supported?**
Python, TypeScript/JavaScript, Rust, Go and C# call sites, from OpenAPI 3.x diffs and MCP tool-schema
diffs. A change with no machine-readable contract is not covered.

**Does it use an LLM?**
No. Detection, location, patching and proof are deterministic and offline.

**What does it cost?**
SDK Fit is Apache-2.0 and free. You pay for your own compute, GitHub usage and any database you run.

**How do I self-host it?**
Docker Compose with SQLite (`DEPLOYMENT.md`), or Kubernetes with Postgres and the manifests in
`deploy/k8s` (`docs/technical/CLOUD.md`). The same image does both.

**What happens when it cannot prove a fix?**
The site stays in a separate ambiguity/unverified list and no patch is claimed for it. You can raise
the required proof level or fix it by hand; SDK Fit does not guess.

**Does it open PRs for every affected repo?**
The installed fan-out can, over the repositories an installation grants. It is sequential, reports
per-repo failures, and has no rollback; earlier PRs stay if a later repo fails.

**Is it production-ready?**
It is pre-1.0: flags, config keys and provider contracts may still change. The pipeline, service and
deployment have tests and are used end to end in the repo; start with a dry run and a small repo.

**Where does my code go?**
Nowhere except your own machine and the repository you explicitly push to. The analysis has no
network calls.
