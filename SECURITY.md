# Security and publication boundary

Report a suspected private-data leak without opening a public issue containing the leaked data.

The generated website and DOGG must never contain:

- private customer identity or brief contents
- prompts, private strategy, or department reports
- source delivery artifacts
- prices, budgets, credentials, API tokens, or session identifiers
- local filesystem paths
- Rapterbox LLC private data

Public DOGG frames are generated from a fixed allowlist and verified as a hash chain before commit.

GitHub issue forms are intentionally public intake surfaces. Anything submitted through them is
already public and must not contain secrets or confidential information. The generated DOGG still
does not copy issue titles, bodies, authors, or customer text.
