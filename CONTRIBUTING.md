# How changes get made

Even as a solo project, every change goes through the same flow a team would use.

## Branch → PR → merge
```bash
git switch main && git pull
git switch -c feat/us-14-calendar-heatmap     # one branch per story or fix
# ...code + tests...
pytest && (cd e2e && npx playwright test)
git add -p                                     # review each change before staging
git commit -m "feat(logs): add calendar heatmap (US-14)"
git push -u origin feat/us-14-calendar-heatmap
# open a PR on GitHub, wait for CI to pass, review your own diff, squash merge
```

## Commit messages: Conventional Commits
`<type>(<scope>): <what changed>`, written in the imperative ("add", not "added").

| Type | Use for | Example |
|---|---|---|
| `feat` | New feature | `feat(booking): let patients cancel appointments` |
| `fix` | Bug fix | `fix(logs): reject pain levels above 10` |
| `test` | Tests only | `test(booking): race 10 bookings for one slot` |
| `docs` | Docs only | `docs: add US-14 acceptance criteria` |
| `refactor` | No behavior change | `refactor(e2e): move chips into a component` |
| `ci` | Pipeline | `ci: upload Playwright report on failure` |
| `chore` | Tooling, deps | `chore: bump playwright to 1.63` |

## Before every commit
- [ ] Tests pass locally
- [ ] `pre-commit` ran (gitleaks blocks secrets)
- [ ] No `.env`, `.db`, `node_modules` or `.venv` in `git status`
- [ ] New AC → new row in `docs/TEST_STRATEGY.md` traceability table
- [ ] `STATUS.md` updated
