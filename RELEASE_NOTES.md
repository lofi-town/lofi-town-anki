## What changed

- Made card-count goals the default reviewer experience, with quick choices,
  custom values, a live countdown, and a non-modal progress bar.
- Made timers, focus blocks, and timed breaks opt-in while keeping them
  available for users who want a timed study flow.
- Hid time-based controls and recap facts whenever the timer is disabled.
- Preserved non-default timer settings while migrating the original 1.3.0
  timer defaults to the new goal-first experience.
- Continues to avoid collection reads, collection writes, scheduling changes,
  and transmission of card, deck, rating, answer-count, or remaining-card data.

## Install or update

Download `lofi-town.ankiaddon`, open it with Anki Desktop, and restart Anki.
Non-default settings and the isolated Lofi Town session are preserved during
an update.

This release supports Anki Desktop 25.09.5 through 26.08.1 on macOS, Windows,
and Linux. AnkiMobile and AnkiDroid do not load desktop add-ons.

See the [installation guide](https://github.com/lofi-town/lofi-town-anki#install),
[privacy details](https://github.com/lofi-town/lofi-town-anki/blob/main/PRIVACY.md),
or [report a problem](https://github.com/lofi-town/lofi-town-anki/issues/new/choose).
