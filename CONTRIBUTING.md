# Contributing

Bug reports and focused pull requests are welcome. For significant behavior or
UI changes, open an issue first so the scope can be agreed before implementation.
Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Development checks

Set up the environment and run the repository checks:

```sh
make bootstrap
make lint typecheck test check-package
```

Install a supported `aqt[qt]` version before running `make qt-smoke`.

Keep changes focused, preserve Anki collection safety, and add tests for changed
behavior. Never commit credentials, profile data, card content, generated
packages, or files from `addon/user_files/`.

By submitting a contribution, you agree to license it under AGPL-3.0-or-later
and confirm that you have the right to do so. Lofi Town trademarks and brand
assets are governed separately by `TRADEMARKS.md`.
