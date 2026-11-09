# Commit messages

Commits use [Conventional Commits](https://www.conventionalcommits.org/). Work lands straight on `main`; there is no release process.

```
<type>(<optional scope>): <summary>

<optional body: why, one paragraph per line>
```

Types:

- `feat`: something new the throttle or a developer can use
- `fix`: a bug fix
- `perf`: faster or cheaper, same behaviour
- `refactor`: restructuring, same behaviour
- `test`: tests only
- `docs`: documentation only
- `chore`: tooling, dependencies, config
- `ci`: deploy scripts and automation
- `style`: formatting only
- `revert`: undoing an earlier commit

Scopes (optional): `protocol` (BLE command bytes), `service` (train state, BLE link, HTTP API, logging), `ui` (`web/`), `deploy` (Pi install, systemd, kiosk).

Rules:

- The summary is lower case after the colon, has no trailing period, and says what changed and why in plain words: `fix(service): retry the engine after 1s so dropouts end sooner`, not `fix: update links.py`.
- A breaking change to the HTTP API or a CLI flag gets `!` after the type and a `BREAKING CHANGE:` line in the body saying what must change.
- Reference an issue as `(#123)`.
- Agent branches are squashed before they reach `main`: one conventional commit per change, with no `wip:` commits.
- Keep the attribution trailers the session asks for at the end of the body.
- Never force-push, amend a pushed commit, or skip hooks.
