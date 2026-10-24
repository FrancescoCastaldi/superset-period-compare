# 0003. Generate the payload from a Superset worktree

Status: Accepted (2026-10-24)

## Context

Editing files in `payload/` directly cannot be type checked, linted or tested, because they have no surrounding Superset project. Hand maintained copies would also drift from the real tree.

## Decision

Develop the change in a worktree of the Superset `6.1.0` tag, where the tests and the TypeScript project work, and commit it there. `scripts/make-payload.ps1` derives `payload/` and `compat/compat.json` from `git diff --name-status 6.1.0 HEAD`, excluding tests.

The hashes of the untouched files are computed from the upstream blob, byte for byte, with CRLF reduced to LF.

## Consequences

- `payload/` is a build artifact: a change made only there is lost at the next generation. Code comments and fixes must be applied in the worktree first.
- The generation is reproducible: running it twice on the same commit gives the same hashes.
- Developing needs a Superset checkout next to this repository.
