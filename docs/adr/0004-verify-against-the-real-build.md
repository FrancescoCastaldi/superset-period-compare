# 0004. Verify the patch against the real Superset build

Status: Accepted (2026-10-24)

## Context

The first release was declared complete after unit tests, Node scripts and an installer suite passed. When the patched tree was built inside Superset 6.1.0 with Docker, the compiler reported 12 errors, then 31 after a first fix, and the dashboard froze in the browser as soon as a comparison was active. None of the existing tests could see this: the Node scripts use simplified copies of the code, and no suite ran the TypeScript compiler or rendered the filter.

## Decision

A change is verified in layers, and a layer is only reported as passed when it was actually run:

1. installer and logic tests;
2. compilation of the patched tree inside Superset (`npm run build-dev`, zero TypeScript errors);
3. backend end to end check against direct SQL (`scripts/e2e/verify-backend-compare.py`);
4. the test dashboard in a browser with a comparison active.

The verification status in the README lists each layer and what was run.

## Consequences

- Releases need a running Superset and a build, which costs several minutes per iteration.
- The status table stays honest: an unverified layer is shown as such.
- Layers 2 and 4 are candidates for CI automation with a Superset checkout and a headless browser.
