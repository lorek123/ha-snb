---
description: Bump the integration version consistently and prepare a release
argument-hint: <new-version, e.g. 0.1.24>
---

Prepare a release for version **$1**. Keep every version reference in sync.

Steps:
1. Set `version` to `$1` in BOTH:
   - `custom_components/storzandbickel/manifest.json`
   - `pyproject.toml`
2. Verify the library pin matches in both places (`manifest.json` `requirements` is the source of
   truth for what HA installs; `pyproject.toml` `dependencies` must not specify a lower bound).
   Fix any drift now.
3. Run `/check` and confirm everything is green.
4. Show me a `git diff` of the version/pin changes and a one-line summary of what's in this release.
5. Only after I confirm: stage, commit (`chore: release v$1`), and create tag `v$1`.
   Do NOT push or create the tag without my explicit go-ahead.

CI builds the HACS zip automatically on tag push, so the tag must point at a green commit.
