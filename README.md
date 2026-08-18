# Lofi Town for Anki

The official Lofi Town companion add-on keeps the live town beside your flashcards in a resizable Anki panel.

## What it does

- Loads the full Lofi Town app from `https://app.lofi.town`.
- Keeps sign-in, music, game state, and local storage in an isolated persistent browser profile.
- Supports docked and floating layouts with remembered size and placement.
- Gives Anki a customizable cozy appearance based on Lofi Town's cream, cocoa,
  and tangerine UI palette.
- Supports light and dark modes, spacing, text size, roundness, motion, and texture.
- Keeps card templates and AnkiHub-owned views outside the theme boundary.
- Opens Google and Discord sign-in in the system browser, then returns securely to Anki.
- Never reads or sends decks, cards, answers, review counts, or collection data.

The add-on supports Anki 25.09.5 through 26.08.1 on macOS, Windows, and Linux.

## Install a packaged build

1. Build or download `lofi-town.ankiaddon`.
2. In Anki, choose **Tools > Add-ons > Install from file**.
3. Select the package and restart Anki.
4. Use **Tools > Lofi Town** to show or hide the panel.
5. Use **Tools > Lofi Town Appearance...** to customize Anki.

## OAuth deployment prerequisite

Google and Discord sign-in require the Lofi Town client runtime bridge to be deployed. Before distributing this add-on:

1. Merge and deploy the companion client PR.
2. Add `http://127.0.0.1:*/**` to the Supabase authentication redirect allowlist.
3. Verify both providers from a packaged add-on.

Email sign-in continues to use the normal Lofi Town web flow.

## Development

Python 3.10 or newer and GNU Make are required.

```sh
make bootstrap
make help
make lint typecheck test check-package
make install-dev
```

`make install-dev` uses the standard Anki add-on directory for the current operating system. Set `ANKI_ADDONS_DIR` to override it.

To run the Qt construction smoke test, install a supported `aqt` wheel in `.venv`, then run `make qt-smoke`.

## Security model

- The WebEngine view allows top-level navigation only within `https://app.lofi.town`.
- Public HTTPS links open in the system browser. Local, credential-bearing, file, and custom-scheme links are rejected.
- OAuth authorization URLs must use the Supabase authorization endpoint.
- The callback listener binds only to `127.0.0.1`, uses a random one-use path, and expires after five minutes.
- Camera, microphone, location, notifications, downloads, screen capture, and clipboard access are disabled.
- Authorization codes are never logged or persisted by the add-on.

## Packaging

`make package` creates `dist/lofi-town.ankiaddon`. The archive is reproducible, has no wrapper directory, excludes caches, and includes only the `user_files/README.txt` placeholder from persistent storage.
