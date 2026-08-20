## What changed

- Added optional answer targets with a live, non-modal progress bar.
- Added custom focus lengths from 1 through 180 minutes and optional break
  countdowns from 1 through 60 minutes.
- Added in-memory session recaps with answers, focused time, completed focus
  blocks, and completed answer targets.
- Added controls to independently hide answer, remaining, timer, progress, and
  focus-sync facts, use a compact layout, or move the reviewer strip.
- Keeps custom focus blocks compatible with the existing Lofi Town client by
  using an open-ended synced stopwatch while the add-on enforces the local
  target.
- Continues to avoid collection reads, collection writes, scheduling changes,
  and transmission of card, deck, rating, answer-count, or remaining-card data.

## Install or update

Download `lofi-town.ankiaddon`, open it with Anki Desktop, and restart Anki.
Existing settings and the isolated Lofi Town session are preserved during an
update.

This release supports Anki Desktop 25.09.5 through 26.08.1 on macOS, Windows,
and Linux. AnkiMobile and AnkiDroid do not load desktop add-ons.

See the [installation guide](https://github.com/lofi-town/lofi-town-anki#install),
[privacy details](https://github.com/lofi-town/lofi-town-anki/blob/main/PRIVACY.md),
or [report a problem](https://github.com/lofi-town/lofi-town-anki/issues/new/choose).
