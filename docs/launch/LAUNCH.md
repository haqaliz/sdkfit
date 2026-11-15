# Launch kit

> **Name:** **SDK Fit** (`sdkfit`), chosen after the original working name collided with an active
> company. The live availability check and the history are in [`NAME_CHECK.md`](NAME_CHECK.md);
> `sdkfit.com` is registered but has no site, so the launch uses **sdkfit.dev**.

## Positioning

**SDK Fit keeps consumer code fitted to the APIs it depends on.** It reads two versions of an API
contract, finds the call sites that break, rewrites only the ones it can prove, runs your own checks,
and proposes a reviewed PR. It does not guess with an LLM and it does not merge.

**Who it is for**

- **SDK/API vendors** who need to migrate customer code when they ship a breaking change.
- **Platform teams** maintaining many consumer repos through a deprecation.
- **Developers** who want the mechanical part of a migration done and proven, not a chatbot's diff.

**When it is not a fit:** a team that wants a hosted autopilot SaaS, or an API change with no
machine-readable contract (SDK Fit works from OpenAPI 3.x and MCP tool schemas).

## Tagline options

1. **Breaking API changes, fixed and proven.**
2. **Your API changed. Your customers' code didn't.**
3. **Migration PRs your tests can trust.**

## Descriptions

- **One line (≤60 chars):** `Fixes breaking API changes in consumer code — proven.`
- **Short (Product Hunt pitch):** SDK Fit finds the consumer call sites a breaking API change breaks,
  rewrites the ones it can prove, runs your own checks, and opens a reviewed PR. Five languages,
  offline analysis, self-hosted.
- **Long:**

  > When an API ships a breaking change, the vendor knows first and the customers find out in
  > production. SDK Fit closes that gap. It reads the old and new OpenAPI spec (or MCP tool schema),
  > locates the affected call sites across Python, TypeScript/JavaScript, Rust, Go and C#, and
  > proposes the mechanical fix for the certain ones. It applies the diff to a copy, runs your proof
  > stages before and after, and labels the result `TESTS_PASSED`, `CHARACTERIZED`, `REPLAYED` or
  > `TYPES_BUILD_ONLY` — or leaves the site unverified instead of guessing. Only then does it offer a
  > reviewed PR. Vendors can run the same pipeline from a portable migration bundle across many
  > customer repos, with an optional self-hosted queue and service.
  >
  > SDK Fit is pre-1.0, Apache-2.0, and runs on your machine or your cluster. No LLM in the analysis
  > path, no force-push, no auto-merge.

## Differentiators

- **Evidence, not vibes.** Every site is certain, ambiguous or unproven; every patch carries the
  strongest proof level that actually passed.
- **Deterministic and offline.** The analysis and proof never call a model or a remote; only the
  final push/PR uses your git/`gh` or GitHub App.
- **A provider path, not just a CLI.** A portable bundle, an installed fan-out, webhook-triggered
  runs, and a self-hosted service with SQLite or Postgres and Kubernetes manifests.
- **Five languages.** Python, TypeScript/JavaScript, Rust, Go, C#.
- **BYOK and BYO auth.** Your repo, your token, your GitHub App; no SDK Fit account.

## What not to claim

- Not a SaaS or a hosted service; there is no hosted demo or dashboard.
- No LLM/AI magic, no "fixes any API", no auto-merge, no force-push.
- Not all API changes: OpenAPI 3.x and MCP tool schemas; a change with no machine-readable source is
  not covered.
- No customer logos, invented benchmarks or funding claims; the only numbers are the repo's own tests
  and corpus.
- Pre-1.0: flags, config keys and provider contracts may still change.

## Install and verify

```sh
pip install sdkfit
sdkfit --version
sdkfit check --help
```

From source (for the demo):

```sh
git clone https://github.com/haqaliz/sdkfit.git
cd sdkfit
uv sync
bash scripts/launch_demo.sh
```

## Launch-day checklist

- [ ] **Name confirmed** in `NAME_CHECK.md`; re-check PyPI/npm/GitHub/domain/Product Hunt just before the launch.
- [ ] PyPI `sdkfit==<version>` installs in a fresh venv and prints `sdkfit <version>`; the
      trusted publisher and `PYPI_PUBLISH` gate are set.
- [ ] GHCR image public; `docker pull ghcr.io/haqaliz/sdkfit:<version>` succeeds; the manifest pins
      that tag.
- [ ] `bash scripts/launch_demo.sh` is green and `docs/launch/DEMO.md` still matches.
- [ ] README install section switched to the published command; CI/version/changelog links current.
- [ ] Gallery captured from [`GALLERY.md`](GALLERY.md).
- [ ] Product Hunt draft has the final name, tagline, description, topics, gallery and first comment
      from [`FIRST_COMMENT.md`](FIRST_COMMENT.md).
- [ ] Fresh-machine check: install, run the demo, open the README and the release page.
- [ ] Optional but recommended: `CONTRIBUTING.md`, issue templates, a support/security contact.

## Assets and docs

- [`DEMO.md`](DEMO.md) — the recorded offline demo.
- [`FAQ.md`](FAQ.md) — the questions a first installer asks.
- [`GALLERY.md`](GALLERY.md) — the Product Hunt images and exact screens to capture.
- [`NAME_CHECK.md`](NAME_CHECK.md) — the blocker and the live name/handle findings.
- [`FIRST_COMMENT.md`](FIRST_COMMENT.md) — the maker's first comment.
