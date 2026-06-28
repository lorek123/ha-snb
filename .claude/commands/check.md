---
description: Run the full local CI gate (ruff, pyright, pytest with coverage)
---

Run the complete quality gate exactly as CI does, and report a concise pass/fail summary.

1. Lint: `uv run ruff check custom_components tests`
2. Types: `uv run pyright custom_components/storzandbickel`
3. Tests + coverage: `PYTHONPATH=. uv run pytest --cov=custom_components/storzandbickel --cov-report=term-missing`

Requirements:
- Coverage must be **≥ 95%** or the build fails — call out any file dragging it down.
- If anything fails, fix it and re-run until all three are green. Do not stop at the first failure
  without attempting a fix.
- Do not run `pip install -e .`. If deps are missing, run
  `uv sync --extra test --extra dev --no-install-project` first.
