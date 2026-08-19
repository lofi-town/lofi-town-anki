# Lofi Town settings

Open **Tools > Lofi Town Settings...** to customize Anki. The add-on also
updates the panel values as you move, resize, show, or hide Lofi Town.

- `visible`: Show the panel when the Anki profile opens.
- `area`: Dock on the `left` or `right` side.
- `width`: Remembered dock width in pixels, from 320 to 1200.
- `floating`: Reopen as a floating panel.
- `geometry`: Saved floating-window geometry.
- `zoom_factor`: Web content scale, from 0.5 to 2.0.

The `theme` section stores the selected Lofi Town accent, color mode, spacing,
text scale, corner radius, motion, texture, and optional review backdrop.
Theme hooks only target Anki's built-in deck, overview, toolbar, and review
control views. Card templates and AnkiHub-owned views are not modified.

The optional study companion shows reviewer answer events and Anki's rendered
New, Learn, and Review counts. It never queries or writes the collection. Focus
blocks are non-modal and never reveal, answer, or reschedule cards. Lofi Town
break prompts reveal the existing authenticated dock and can be disabled.

`sync_focus_with_lofi_town` is an opt-in setting. When enabled, the first answer
starts a private Lofi Town stopwatch. Pause, resume, break, and reviewer-end
events synchronize with that owned session. Existing Lofi Town sessions remain
read-only inside Anki.
