from __future__ import annotations

import json
from typing import Any

from .configuration import normalize_config, theme_tokens


def _payload(config: dict[str, Any], view: str) -> dict[str, Any]:
    normalized = normalize_config(config)
    return {
        "view": view,
        "palette": normalized["palette"],
        "colorMode": normalized["color_mode"],
        "density": normalized["density"],
        "motion": normalized["motion"],
        "texture": normalized["texture"],
        "reviewBackdrop": normalized["review_backdrop"],
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


def build_dynamic_bootstrap(
    config: dict[str, Any],
    view: str,
    stylesheet_url: str,
) -> str:
    data = _payload_json(config, view)
    href = json.dumps(stylesheet_url)
    apply_theme = _apply_theme_script(data)
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
}})();
""".strip()
