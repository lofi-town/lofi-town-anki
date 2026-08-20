from __future__ import annotations

import json
from typing import Any

from .configuration import normalize_config, theme_tokens
from .session import SessionSummaryPayload


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
    config: dict[str, Any], session: dict[str, object]
) -> str:
    normalized = normalize_config(config)
    payload = {
        **session,
        "focusMinutes": normalized["focus_minutes"],
        "breakMinutes": normalized["break_minutes"],
        "targetAnswers": normalized["session_target_answers"],
        "showAnswers": normalized["hud_show_answers"],
        "showRemaining": normalized["hud_show_remaining"],
        "showTimer": normalized["hud_show_timer"],
        "showProgress": normalized["hud_show_progress"],
        "showSyncStatus": normalized["hud_show_sync_status"],
        "compact": normalized["hud_compact"],
        "position": normalized["hud_position"],
        "showLofiTownBreak": normalized["lofi_town_breaks"],
    }
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return f"""
<script id="lofi-town-session-bootstrap">
window.__lofiTownSessionBootstrap = {data};
</script>
""".strip()


def build_recap_bootstrap(
    config: dict[str, Any],
    summary: SessionSummaryPayload,
) -> str:
    normalized = normalize_config(config)
    payload = {
        "summary": summary,
        "showOpenButton": normalized["lofi_town_breaks"],
        "showDismissButton": True,
    }
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return f"""
<script id="lofi-town-recap-bootstrap">
window.__lofiTownRecapBootstrap = {data};
</script>
""".strip()


def build_dynamic_bootstrap(
    config: dict[str, Any],
    view: str,
    stylesheet_urls: tuple[str, ...],
    recap_script_url: str,
    summary: SessionSummaryPayload | None = None,
) -> str:
    normalized = normalize_config(config)
    apply_theme = _apply_theme_script(_payload_json(normalized, view))
    stylesheets = json.dumps(stylesheet_urls)
    script_url = json.dumps(recap_script_url)
    recap = json.dumps(
        {
            "summary": summary,
            "showOpenButton": normalized["lofi_town_breaks"],
            "showDismissButton": False,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    show_recap = json.dumps(
        normalized["lofi_town_breaks"] or summary is not None
    )
    return f"""
(() => {{
  const pagePath = location.pathname.endsWith("/")
    ? location.pathname.slice(0, -1)
    : location.pathname;
  if (pagePath !== "/congrats") return;
  for (const href of {stylesheets}) {{
    if (document.querySelector(`link[href="${{href}}"]`)) continue;
    const stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.href = href;
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
  if (!{show_recap}) return;
  window.__lofiTownRecapBootstrap = {recap};
  if (window.__lofiTownInstallRecap) {{
    window.__lofiTownInstallRecap();
    return;
  }}
  if (document.getElementById("lofi-town-recap-runtime")) return;
  const script = document.createElement("script");
  script.id = "lofi-town-recap-runtime";
  script.src = {script_url};
  document.head.appendChild(script);
}})();
""".strip()
