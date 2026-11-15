# First comment (maker)

> Update the product name and links here if the decision in [`NAME_CHECK.md`](NAME_CHECK.md) changes
> them.

Hi Product Hunt — I built SDK Fit because breaking API changes are still discovered by customers in
production. The vendor knows first; the consumer finds out last.

SDK Fit reads the old and new OpenAPI spec (or MCP tool schema), finds the consumer call sites that
break, rewrites only the ones it can prove, runs the consumer's own checks before and after, and only
then offers a reviewed PR. It labels every result with the proof that actually passed
(`TESTS_PASSED`, `CHARACTERIZED`, `REPLAYED`, `TYPES_BUILD_ONLY`) and leaves the uncertain sites
alone. No LLM in the analysis, no force-push, no auto-merge.

It works as a CLI for one repo, or as a provider bundle and self-hosted service for a vendor
migrating many customer repos. Python, TypeScript/JavaScript, Rust, Go and C#; Apache-2.0, pre-1.0,
runs on your machine or your cluster.

Two questions I would love your take on:

1. Which SDK or vendor should be the first real migration case?
2. What proof would you trust before merging a generated PR — your test suite, a characterization
   test, or a replay of recorded calls?

The demo is offline and runs from the repo (about 30 seconds):

```sh
git clone https://github.com/haqaliz/sdkfit.git
cd sdkfit
uv sync
bash scripts/launch_demo.sh
```

Source, docs and the demo: https://github.com/haqaliz/sdkfit — thanks for looking.
