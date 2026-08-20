# What medical students want from an Anki add-on

Research date: 2026-08-18

## Conclusion

The strongest recurring problem is the cost of completing hundreds of reviews
every day. Medical students describe multi-hour sessions, review backlogs,
fatigue, avoidance, and uncertainty about whether they are making sustainable
progress. The useful role for this add-on is a calm session companion: honest
workload cues, optional pacing, accessible controls, and a restrained Lofi Town
break experience.

One desktop add-on cannot safely solve scheduling, medical explanations, card
generation, deck synchronization, and mobile reminders. Those are separate
product domains with higher correctness and data-loss risk.

## Method

- Searched r/medicalschoolanki, r/medicalschool, r/Anki, Anki Forums, and
  AnkiHub Community.
- Combined Anki with burnout, reviews, progress, Pomodoro, focus, streak,
  accessibility, contrast, AnkiHub, overwritten, compatibility, lag, and add-on.
- Prioritized direct user discussions over vendor pages and listicles.
- Used official Anki documentation for supported hooks and safety boundaries.
- Rated patterns strong when repeated across independent threads or years,
  moderate when supported by at least two discussions, and emerging when based
  mainly on a single report.

This is qualitative forum research, not a representative survey.

## Evidence and product response

| Need | Evidence | Strength | Response |
|---|---|---|---|
| Reduce burnout from large daily workloads | [Burnout after 1.5 hours](https://www.reddit.com/r/medicalschoolanki/comments/1hsorh7/burnout_after_15_hours_of_anki_how_to_avoid/), [review hell](https://www.reddit.com/r/medicalschoolanki/comments/1tiq85p/learn_more_with_less_anki_how_to_avoid_review_hell/) | Strong | Add optional focus blocks and non-modal breaks. Avoid pressure, forced stopping, and shame copy. |
| Show trustworthy progress | [Supported progress bar request](https://www.reddit.com/r/medicalschoolanki/comments/13dla1d/request_genuine_progress_bar_addon/), [minimal progress bar feedback](https://www.reddit.com/r/medicalschoolanki/comments/1sy6qaf/minimal_progress_bar_addon_number_1882716549/) | Strong | Show answer events and Anki's rendered remaining count. Do not claim mastery or guess an ETA. |
| Let users hide stressful counts | [Reviewing feels like a chore](https://www.reddit.com/r/medicalschoolanki/comments/k6qh68/how_do_you_make_reviewing_not_feel_like_a_chore/), [Anki review preferences](https://docs.ankiweb.net/preferences.html#review) | Strong | Follow Anki when remaining counts are hidden and allow the study companion to be disabled. |
| Support focus without speed anxiety | [Pomodoro request](https://www.reddit.com/r/medicalschoolanki/comments/fozjoo/anki_pomodoro_addon_no_longer_working_on_2120/), [mixed speed-focus responses](https://www.reddit.com/r/medicalschoolanki/comments/18hj5n2/end_of_term_anki_burn_out_need_tips_on_how_to/) | Strong | Provide custom, pauseable focus and break reminders. Never auto-reveal or auto-answer. |
| Make Anki less sterile without distracting from cards | [Redesign add-on discussion](https://www.reddit.com/r/medicalschoolanki/comments/fbyd0c/redesign_addon/), [distracting review background](https://www.reddit.com/r/medicalschoolanki/comments/g5rf00/how_to_turn_off_review_background/) | Strong | Keep the town, color, and completion experience outside `#qa`. Make the review backdrop optional. |
| Improve accessibility | [Dark-mode contrast](https://forums.ankiweb.net/t/accessibility-suggestion-correct-answer-text-contrast-in-dark-mode/10105), [color-blind feedback](https://forums.ankiweb.net/t/suggestion-make-feedback-ticks-easier-to-distinguish-for-colorblind-users/12878), [reduced-motion request](https://forums.ankiweb.net/t/feature-request-more-accessibility-classes-for-css-control/58324) | Strong | Use calculated accent text contrast, visible labels and focus states, rating-key hints, reduced motion, and low-resource mode. |
| Preserve AnkiHub content and local edits | [Protected fields](https://www.reddit.com/r/medicalschoolanki/comments/11fj9az/will_my_annotations_to_anking_cards_be_removed/), [template synchronization risk](https://community.ankihub.net/t/synchronizing-changes-in-the-html-and-css-template-in-my-notes/376180) | Strong constraint | Never edit notes, fields, templates, scheduling, or AnkiHub metadata. Exclude AnkiHub-owned webviews. |
| Avoid lag and add-on conflicts | [Add-on loading time](https://forums.ankiweb.net/t/add-ons-loading-time/12692), [Anki add-on warning](https://docs.ankiweb.net/addons.html) | Strong constraint | Use public hooks, visible DOM counts, one timer, no per-card database scan, and safe fallback when markup is absent. |
| Prevent background music from masking clinical audio | [Focus Music and Pomodoro discussion](https://forums.ankiweb.net/t/new-add-on-focus-music-pomodoro-player-with-smart-auto-pause/67716) | Emerging | Do not add a second audio system. Reliable ducking of the embedded town requires an explicit client audio-control API before shipping. |

## Shipped scope

- A configurable reviewer strip with answer targets, Anki's visible remaining
  count, elapsed or focus time, and honest progress.
- Pause, resume, break, skip, and restart controls for custom focus blocks.
- An in-memory aggregate recap shown after the review session ends.
- A quiet reviewer option and non-color rating-key cues.
- A low-resource mode that removes texture, shadows, and transitions.
- A calm completion prompt that reveals the existing authenticated Lofi Town
  dock instead of opening a second app session.
- Narrow-window reflow down to 320 pixels.

## Explicit non-goals

- Scheduler or FSRS changes
- Backlog postponement or automatic rescheduling
- Medical explanations, card generation, or learning diagnosis
- Card, field, note-type, or template editing
- Retention scores, productivity scores, leaderboards, or punitive streaks
- Mobile notifications or desktop add-on claims about mobile support

## Metric contract

`Answers` means reviewer answer events since the current reviewer session began.
It does not mean unique cards learned or mastered. `Remaining` is the sum of the
New, Learn, and Review values already rendered by Anki. If Anki does not expose
those values, the strip says `remaining hidden`. No collection query or future
scheduler estimate is used.
