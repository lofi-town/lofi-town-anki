## What changed

- Added opt-in focus sync with private Lofi Town stopwatch sessions.
- Starts local and synced focus timing after the first answered card.
- Synchronizes pause, resume, break, and reviewer-end actions only for sessions
  created by the add-on.
- Keeps existing Lofi Town focus sessions read-only and never sends card, deck,
  rating, answer-count, or remaining-card data.

## Install or update

Download `lofi-town.ankiaddon`, open it with Anki Desktop, and restart Anki.
Existing settings and the isolated Lofi Town session are preserved during an
update.

This release supports Anki Desktop 25.09.5 through 26.08.1 on macOS, Windows,
and Linux. AnkiMobile and AnkiDroid do not load desktop add-ons.

See the [installation guide](https://github.com/lofi-town/lofi-town-anki#install),
[privacy details](https://github.com/lofi-town/lofi-town-anki/blob/main/PRIVACY.md),
or [report a problem](https://github.com/lofi-town/lofi-town-anki/issues/new/choose).
