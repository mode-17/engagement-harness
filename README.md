# engagement-harness

A small request layer for authorized security testing where the program has rules attached.

Three problems come up on almost every engagement. This harness solves all three the same
way: the rule goes in the tool, not in a checklist.

| Problem | Fix |
|---|---|
| A program-mandated identifier header that gets forgotten on the request that matters | Defined once in config, attached to every request. No code path sends without it. |
| An in-scope page loads its API from an out-of-scope host | Every URL argument is checked against an allowlist. Anything else is refused, loudly. |
| Identity bookkeeping across A / B / anonymous sessions | Named identities with their own cookie jars, tokens and browser profiles. Cookies and tokens are gitignored. |

## Components

| File | Purpose |
|---|---|
| `bin/hit` | Scope-guarded, per-identity `curl` wrapper. Reproducible, loggable requests. |
| `bin/pw-session.js` | Headed Playwright session through your proxy. Captures cookies, bearer tokens, storage and in-scope API traffic for a session you signed in to by hand. |
| `bin/header-check.py` | Proves the proxy is really injecting the identifier header, using a loopback listener and zero target traffic. |

## Quickstart

```bash
git clone https://github.com/mode-17/engagement-harness
cd engagement-harness

mkdir -p ~/.config/engagement-harness
cp harness.conf.example ~/.config/engagement-harness/harness.conf
$EDITOR ~/.config/engagement-harness/harness.conf   # identifier + SCOPE_HOSTS

npm i playwright                                     # only for pw-session.js
chmod +x bin/hit bin/pw-session.js bin/header-check.py
```

Capture a session (human signs in, tool captures):

```bash
START_URL=https://app.example.com/ WHO=A bin/pw-session.js
```

Replay with that identity:

```bash
bin/hit A -o /dev/null -w '%{http_code}\n' https://app.example.com/api/me
bin/hit anon https://app.example.com/
```

Try an out-of-scope host:

```bash
$ bin/hit A https://api.other-host.example/x
REFUSED (out of scope): api.other-host.example
```

## Why the scope guard is deliberately annoying

It fired during a real engagement on exactly the URLs I wanted to test: an in-scope page
loaded its data-bearing API from a host the program did not list. Reading the page's own
bundle told me where the API was, but "the page uses it" is not "the program scoped it".

A non-zero exit and a loud refusal are the point. If a wrapper silently allows an
out-of-scope request, the guard is decorative.

## Design notes

- **Read-only helpers.** `pw-session.js` records metadata; request bodies are for requests
  you initiated. Mutation is a deliberate act, never a crawl side effect.
- **Human login, captured session.** Login is completed by a person in a real headed window,
  because automating it is fragile and can look like the automated scanning many programs
  forbid.
- **Bot-defence aware.** Realistic user-agent, headed browser, tiny volume. The goal is to
  read your own session's traffic, not to sweep the target.
- **No secrets in the repo.** Session state lives under `STATE_DIR` (default
  `~/.local/state/engagement-harness`).

## Limitations

- The scope guard parses URL arguments. A script that hard-codes a host is not caught by it.
  It is one layer of defence, not a complete one.
- `SCOPE_HOSTS` empty disables the guard and prints a warning. Do not leave it empty.
- The harness encodes program rules. It does not read them for you.

## Authorized use only

This tooling is intended for testing you are permitted to perform: in-scope bug bounty
programs, or systems you own or have written authorization to assess. You are responsible for
reading the program's rules, keeping your traffic identifiable, and staying in scope.

## License

MIT — see [LICENSE](LICENSE).
