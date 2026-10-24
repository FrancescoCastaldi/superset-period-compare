# Branching and Releases

## Model

Trunk based development. `main` is always releasable and is protected: changes arrive through pull requests with passing checks, and force pushes are not allowed.

| Branch | Purpose | Lifetime |
|:---|:---|:---|
| `main` | the next release | permanent |
| `feat/<topic>` | a new capability | short, deleted after merge |
| `fix/<topic>` | a bug fix | short, deleted after merge |
| `docs/<topic>`, `refactor/<topic>`, `chore/<topic>`, `test/<topic>`, `ci/<topic>` | work of that kind | short, deleted after merge |
| `support/superset-<major>.<minor>` | maintenance of the payload for an older Superset line, for example `support/superset-6.1` | permanent, created only when needed |

Merge with a squash for short branches. Use a merge commit only when a long integration branch must keep its history. Rebase locally before opening a pull request, and never rewrite history that is already pushed.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/): `type(scope): summary`, in the imperative, one logical change per commit, with a body that says why.

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`. Use `!` or a `BREAKING CHANGE:` footer for incompatible changes.

Scopes in use: `installer`, `payload`, `filter`, `backend`, `charts`, `e2e`, `tests`, `docs`, `ci`.

## Versioning

[Semantic Versioning](https://semver.org/). The version describes this project, not Superset:

- patch: a fix that does not change behavior for users of the filter or the installer;
- minor: a new capability, or support for a new Superset minor line;
- major: an incompatible change to the installer interface, the payload layout or the data contract.

The Superset version the payload was generated for is recorded in `compat/compat.json` and in the changelog.

## Releasing

1. Make sure `main` is green and that every verification layer of the [development guide](development.md) was run for this change.
2. Move the `[Unreleased]` entries of [CHANGELOG.md](../CHANGELOG.md) under a new version heading with the date.
3. Commit as `chore(release): vX.Y.Z`.
4. Create an annotated tag on that commit: `git tag -a vX.Y.Z -m "Superset Period Compare vX.Y.Z"`.
5. Push the commit and then the tag. The `release` workflow checks that the changelog has a section for the version, builds a zip of the repository and creates the GitHub release with the changelog section as notes.

Never reuse a version or move a published tag. A defect in a release is fixed in the next patch version.

## Hotfixes

Branch from the tag in use, make the smallest fix with a test, release a patch version, then bring the fix back to `main` with a cherry pick that cites the original hash (`git cherry-pick -x`).
