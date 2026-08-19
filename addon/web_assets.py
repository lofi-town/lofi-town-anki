from __future__ import annotations

import json
from typing import Any

from .configuration import normalize_config, theme_tokens


def _payload(config: dict[str, Any], view: str) -> dict[str, Any]:
    normalized = normalize_config(config)
    session_enabled = normalized["session_hud"]
    return {
        "view": view,
        "palette": normalized["palette"],
        "colorMode": normalized["color_mode"],
        "density": normalized["density"],
        "motion": normalized["motion"],
        "texture": normalized["texture"],
        "reviewBackdrop": normalized["review_backdrop"],
        "reviewFocusMode": session_enabled and normalized["review_focus_mode"],
        "showRatingShortcuts": session_enabled
        and normalized["show_rating_shortcuts"],
        "lowResource": normalized["low_resource"],
        "fontScale": normalized["font_scale"],
        "radius": normalized["corner_radius"],
        "light": theme_tokens(normalized, "light"),
        "dark": theme_tokens(normalized, "dark"),
    }


def _payload_json(config: dict[str, Any], view: str) -> str:
    return json.dumps(
        _payload(config, view),
        separators=(",", ":"),
        sort_keys=True,
    )


def _apply_theme_script(data: str) -> str:
    return f"""
(() => {{
  const config = {data};
  const root = document.documentElement;
  root.classList.add("lofi-town-theme");
  root.dataset.lofiView = config.view;
  root.dataset.lofiPalette = config.palette;
  root.dataset.lofiColorMode = config.colorMode;
  root.dataset.lofiDensity = config.density;
  root.dataset.lofiMotion = config.motion;
  root.dataset.lofiTexture = config.texture ? "on" : "off";
  root.dataset.lofiReviewBackdrop = config.reviewBackdrop ? "on" : "off";
  root.dataset.lofiFocusMode = config.reviewFocusMode ? "on" : "off";
  root.dataset.lofiRatingShortcuts = config.showRatingShortcuts ? "on" : "off";
  root.dataset.lofiLowResource = config.lowResource ? "on" : "off";
  root.style.setProperty("--lofi-font-scale", String(config.fontScale));
  root.style.setProperty("--lofi-radius", `${{config.radius}}px`);
  for (const [mode, tokens] of [["light", config.light], ["dark", config.dark]]) {{
    for (const [name, value] of Object.entries(tokens)) {{
      root.style.setProperty(`--lofi-${{mode}}-${{name.replaceAll("_", "-")}}`, value);
    }}
  }}
}})();
""".strip()


def build_bootstrap(config: dict[str, Any], view: str) -> str:
    script = _apply_theme_script(_payload_json(config, view))
    return f"""
<script id="lofi-town-theme-bootstrap">
{script}
</script>
""".strip()


def build_session_bootstrap(
    config: dict[str, Any], session: dict[str, int]
) -> str:
    normalized = normalize_config(config)
    payload = {
        **session,
        "focusMinutes": normalized["focus_minutes"],
        "showLofiTownBreak": normalized["lofi_town_breaks"],
    }
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return f"""
<script id="lofi-town-session-bootstrap">
(() => {{
  let state = {data};
  let breakAnnounced = false;
  let timer = 0;
  let observer = null;

  const formatDuration = (milliseconds) => {{
    const totalSeconds = Math.max(0, Math.ceil(milliseconds / 1000));
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${{minutes}}:${{String(seconds).padStart(2, "0")}}`;
  }};

  const send = (command) => {{
    if (typeof pycmd === "function") pycmd(command);
  }};

  const readRemaining = () => {{
    const selectors = [".new-count", ".learn-count", ".review-count"];
    const nodes = selectors.map((selector) => document.querySelector(selector));
    const values = nodes.flatMap((node) => {{
      if (!node) return [];
      const match = node.textContent.replaceAll(",", "").match(/\\d+/);
      return match ? [Number(match[0])] : [];
    }});
    return {{
      nodes: nodes.filter(Boolean),
      total: values.reduce((sum, value) => sum + value, 0),
    }};
  }};

  const renderWorkload = () => {{
    const workload = document.getElementById("lofi-session-workload");
    if (!workload) return;
    const remaining = readRemaining();
    workload.textContent = remaining.nodes.length
      ? `${{remaining.total.toLocaleString()}} remaining`
      : "remaining hidden";
  }};

  const render = () => {{
    const hud = document.getElementById("lofi-session-hud");
    if (!hud) return;
    const answerCount = document.getElementById("lofi-session-answers");
    const time = document.getElementById("lofi-session-time");
    const status = document.getElementById("lofi-session-status");
    const pause = document.getElementById("lofi-session-pause");
    const restart = document.getElementById("lofi-session-restart");
    const openTown = document.getElementById("lofi-session-open-town");
    answerCount.textContent = `${{state.answers.toLocaleString()}} ${{
      state.answers === 1 ? "answer" : "answers"
    }}`;
    renderWorkload();

    if (!state.focusMinutes) {{
      time.textContent = `${{formatDuration(Date.now() - state.startedAt)}} elapsed`;
      pause.hidden = true;
      restart.hidden = true;
      openTown.hidden = true;
      return;
    }}

    const effectiveNow = state.focusPausedAt || Date.now();
    const elapsed = Math.max(
      0,
      effectiveNow - state.focusStartedAt - state.focusPausedTotal
    );
    const remaining = state.focusMinutes * 60 * 1000 - elapsed;
    const complete = remaining <= 0;
    hud.classList.toggle("is-break-ready", complete);
    pause.hidden = complete;
    pause.textContent = state.focusPausedAt ? "Resume" : "Pause";
    pause.setAttribute("aria-pressed", state.focusPausedAt ? "true" : "false");
    restart.hidden = !complete;
    openTown.hidden = !complete || !state.showLofiTownBreak;

    if (complete) {{
      time.textContent = "Break ready";
      if (!breakAnnounced) {{
        status.textContent = "Focus block complete.";
        breakAnnounced = true;
      }}
    }} else {{
      const suffix = state.focusPausedAt ? " · paused" : "";
      time.textContent = `${{formatDuration(remaining)}} left${{suffix}}`;
      status.textContent = "";
      breakAnnounced = false;
    }}
  }};

  const install = () => {{
    const outer = document.getElementById("outer");
    if (!outer || document.getElementById("lofi-session-hud")) return;
    const hud = document.createElement("section");
    hud.id = "lofi-session-hud";
    hud.setAttribute("aria-label", "Review session");
    hud.innerHTML = `
      <div class="lofi-session-brand" aria-label="Lofi Town focus">
        <span class="lofi-session-light" aria-hidden="true"></span>
        <strong>lofi.town</strong><span>focus</span>
      </div>
      <div class="lofi-session-facts">
        <span id="lofi-session-answers">0 answers</span>
        <span aria-hidden="true">·</span>
        <span id="lofi-session-workload">remaining hidden</span>
      </div>
      <span id="lofi-session-time" class="lofi-session-time"></span>
      <div class="lofi-session-actions">
        <button id="lofi-session-pause" type="button"
          aria-pressed="false">Pause</button>
        <button id="lofi-session-restart" type="button" hidden>
          Another block</button>
        <button id="lofi-session-open-town" type="button" hidden>
          Take a break in Lofi Town</button>
      </div>
      <span id="lofi-session-status" class="lofi-visually-hidden"
        role="status" aria-live="polite"></span>`;
    outer.parentNode.insertBefore(hud, outer);
    document.getElementById("lofi-session-pause").addEventListener(
      "click",
      () => send(
        state.focusPausedAt
          ? "lofi-town:resume-focus"
          : "lofi-town:pause-focus"
      )
    );
    document.getElementById("lofi-session-restart").addEventListener(
      "click",
      () => send("lofi-town:restart-focus")
    );
    document.getElementById("lofi-session-open-town").addEventListener(
      "click",
      () => send("lofi-town:open")
    );
    const remaining = readRemaining();
    observer = new MutationObserver(renderWorkload);
    remaining.nodes.forEach((node) => observer.observe(node, {{
      childList: true,
      characterData: true,
      subtree: true,
    }}));
    window.__lofiTownSession = {{
      update(next) {{
        state = {{ ...state, ...next }};
        render();
      }},
    }};
    render();
    timer = window.setInterval(render, 1000);
    window.addEventListener("pagehide", () => {{
      window.clearInterval(timer);
      observer?.disconnect();
    }}, {{ once: true }});
  }};

  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", install, {{ once: true }});
  }} else {{
    install();
  }}
}})();
</script>
""".strip()


def build_dynamic_bootstrap(
    config: dict[str, Any],
    view: str,
    stylesheet_url: str,
) -> str:
    data = _payload_json(config, view)
    href = json.dumps(stylesheet_url)
    apply_theme = _apply_theme_script(data)
    show_break_prompt = json.dumps(normalize_config(config)["lofi_town_breaks"])
    return f"""
(() => {{
  const pagePath = location.pathname.endsWith("/")
    ? location.pathname.slice(0, -1)
    : location.pathname;
  if (pagePath !== "/congrats") return;
  if (!document.getElementById("lofi-town-theme-stylesheet")) {{
    const stylesheet = document.createElement("link");
    stylesheet.id = "lofi-town-theme-stylesheet";
    stylesheet.rel = "stylesheet";
    stylesheet.href = {href};
    document.head.appendChild(stylesheet);
  }}
  {apply_theme}
  const root = document.documentElement;
  const preserveThemeClass = new MutationObserver(() => {{
    if (!root.classList.contains("lofi-town-theme")) {{
      root.classList.add("lofi-town-theme");
    }}
  }});
  preserveThemeClass.observe(root, {{
    attributes: true,
    attributeFilter: ["class"],
  }});
  window.addEventListener(
    "pagehide",
    () => preserveThemeClass.disconnect(),
    {{ once: true }},
  );
  if (!{show_break_prompt}) return;
  const installCompletion = () => {{
    if (document.getElementById("lofi-town-completion")) return;
    const target = document.querySelector(".congrats");
    if (!target) return;
    const card = document.createElement("section");
    card.id = "lofi-town-completion";
    card.setAttribute("aria-labelledby", "lofi-town-completion-title");
    card.innerHTML = `
      <span class="lofi-completion-eyebrow">LOFI.TOWN STUDY ROOM</span>
      <h2 id="lofi-town-completion-title">Take a short reset.</h2>
      <p>Step away for a few minutes, or continue when you are ready.</p>
      <button id="lofi-town-completion-open" type="button">
        Open Lofi Town</button>`;
    target.appendChild(card);
    document.getElementById("lofi-town-completion-open").addEventListener(
      "click",
      () => {{
        if (typeof pycmd === "function") pycmd("lofi-town:open");
      }}
    );
  }};
  installCompletion();
  const preserveCompletion = new MutationObserver(installCompletion);
  preserveCompletion.observe(document.documentElement, {{
    childList: true,
    subtree: true,
  }});
  window.addEventListener(
    "pagehide",
    () => preserveCompletion.disconnect(),
    {{ once: true }},
  );
}})();
""".strip()
