# Repository instructions

## Verification

Use the Makefile targets. Before handing off add-on changes, run:

```sh
make lint typecheck test check-package
make qt-smoke
```

`make check-package` rebuilds `dist/lofi-town.ankiaddon` before validating it.

For plugin-only session changes, also verify in a disposable Anki profile:

- Custom focus lengths at 1, 37, and 180 minutes.
- Break countdown start, skip, completion, and another-block behavior.
- Answer-target completion and repeated targets without interrupting review.
- Each reviewer-strip fact hidden independently, compact mode, and both strip
  positions.
- Recaps after a completed deck and an ordinary reviewer exit.
- Hidden Anki remaining counts stay hidden and no collection data is queried.
