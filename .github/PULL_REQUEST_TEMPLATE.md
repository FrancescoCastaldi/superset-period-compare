## Summary

<!-- What changes and why. Link the issue if there is one. -->

## Type of change

- [ ] fix
- [ ] feature
- [ ] docs
- [ ] refactor, test or chore
- [ ] breaking change (installer interface, payload layout or data contract)

## Verification

Tick only what you actually ran. See [ADR 0004](../docs/adr/0004-verify-against-the-real-build.md).

- [ ] `Invoke-Pester -Path tests/installer`
- [ ] Node tests in `tests/frontend`
- [ ] backend pytest inside a Superset 6.1.0 tree
- [ ] the patched Superset tree compiles (`npm run build-dev`) with no TypeScript errors
- [ ] `scripts/e2e/verify-backend-compare.py` passes against a running Superset
- [ ] the test dashboard works in a browser with a comparison active

## Checklist

- [ ] `payload/` and `compat/compat.json` were regenerated with `scripts/make-payload.ps1`, not edited by hand
- [ ] `CHANGELOG.md` is updated under `[Unreleased]`
- [ ] documentation is updated
- [ ] no credentials, machine specific paths or real data were added
