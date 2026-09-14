# CI/CD and ClickUp

The repository workflow at `.github/workflows/ci.yml` runs on every branch push,
every pull request, and manual dispatch. It performs:

- Python 3.11 and 3.12 test-matrix validation.
- Syntax compilation, Ruff linting, Bandit checks, and dependency auditing.
- Controlled knowledge-register validation.
- Pytest coverage and a downloadable coverage artifact.
- GitHub activity remains available through the existing ClickUp integration.

## ClickUp configuration

No GitHub Actions secrets are required. Commits, branches, pull requests, and
other linked activity are synchronized by the existing ClickUp-GitHub
integration for task `123rgxu5c8m`.

## Enforcing the pipeline

The workflow runs on all branches, but GitHub branch protection is what makes a
check mandatory. In repository **Settings > Rules > Rulesets**, create a ruleset
for the default branch and require the check named:

`Quality and tests (Python 3.12)`

Require pull requests and dismiss stale approvals as appropriate for the team.
For direct pushes to every branch, use a repository ruleset targeting all
branches and require the same status check where that policy is appropriate.