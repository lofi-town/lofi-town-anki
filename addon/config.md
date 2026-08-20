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
New, Learn, and Review counts. It never queries or writes the collection. The
review goal is a local answer-event count, not a claim about unique cards or
mastery. It can be changed from the reviewer without changing the saved default.
Focus and break blocks are non-modal and never reveal, answer, or reschedule
cards. Lofi Town break prompts reveal the existing authenticated dock and can be
disabled.

`focus_minutes` accepts values from 0 through 180. Zero shows elapsed time only.
`break_minutes` accepts values from 0 through 60. `session_target_answers`
accepts values from 0 through 5000, with zero meaning that no default goal is
shown. The reviewer also offers quick goals of 25, 50, 100, and 200 answers,
plus a custom value from 1 through 5000.

The reviewer strip can independently show or hide answers, Anki's remaining
count, time, and progress. It can use a compact layout and sit above or below
Anki's answer controls. The session recap is kept in memory only long enough to
render the next deck, overview, or completed-deck screen.
