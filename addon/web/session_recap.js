(() => {
  const formatFocused = (milliseconds) => {
    const minutes = Math.floor(milliseconds / 60000);
    if (minutes < 1) return "under 1 min";
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const remaining = minutes % 60;
    return `${hours} hr${remaining ? ` ${remaining} min` : ""}`;
  };

  const recapContent = (summary) => {
    if (!summary) {
      return {
        eyebrow: "LOFI.TOWN STUDY ROOM",
        title: "Take a short reset.",
        detail: "Step away for a few minutes, or continue when you are ready.",
        stats: [],
      };
    }
    const stats = [
      `<span><strong>${summary.answers}</strong> answers</span>`,
      `<span><strong>${formatFocused(summary.focusedMs)}</strong> focused</span>`,
    ];
    if (summary.blocksCompleted) {
      const label = summary.blocksCompleted === 1 ? "block" : "blocks";
      stats.push(
        `<span><strong>${summary.blocksCompleted}</strong> focus ${label}</span>`,
      );
    }
    if (summary.targetsCompleted) {
      const label = summary.targetsCompleted === 1 ? "target" : "targets";
      stats.push(
        `<span><strong>${summary.targetsCompleted}</strong> answer ${label}</span>`,
      );
    }
    let detail = "Your review session is complete.";
    if (summary.targetAnswers) {
      if (summary.targetsCompleted === 1) {
        detail = `You reached your ${summary.targetAnswers}-answer target.`;
      } else if (summary.targetsCompleted > 1) {
        detail = `You reached ${summary.targetsCompleted} answer targets.`;
      } else {
        const completed = Math.min(summary.targetProgress, summary.targetAnswers);
        detail = `You completed ${completed} of your ${summary.targetAnswers}-answer target.`;
      }
    }
    return {
      eyebrow: "SESSION COMPLETE",
      title: "Good stopping point.",
      detail,
      stats,
    };
  };

  const install = () => {
    const config = window.__lofiTownRecapBootstrap;
    if (
      document.getElementById("lofi-town-completion") ||
      document.getElementById("lofi-town-recap")
    ) {
      return;
    }
    const pagePath = location.pathname.endsWith("/")
      ? location.pathname.slice(0, -1)
      : location.pathname;
    const isCongrats = pagePath === "/congrats";
    const target = isCongrats
      ? document.querySelector(".congrats")
      : document.querySelector("main") || document.body;
    if (!target) return;

    const content = recapContent(config.summary);
    const card = document.createElement("section");
    card.id = isCongrats && !config.showDismissButton
      ? "lofi-town-completion"
      : "lofi-town-recap";
    card.setAttribute("aria-labelledby", "lofi-town-completion-title");
    card.innerHTML = `
      <span class="lofi-completion-eyebrow">${content.eyebrow}</span>
      <h2 id="lofi-town-completion-title">${content.title}</h2>
      <p class="lofi-recap-detail">${content.detail}</p>
      ${content.stats.length ? `<div class="lofi-recap-stats">${content.stats.join("")}</div>` : ""}
      ${config.showDismissButton || config.showOpenButton ? '<div class="lofi-recap-actions"></div>' : ""}`;

    const actions = card.querySelector(".lofi-recap-actions");
    if (config.showDismissButton) {
      const dismiss = document.createElement("button");
      dismiss.id = "lofi-town-recap-dismiss";
      dismiss.type = "button";
      dismiss.textContent = "Dismiss";
      dismiss.addEventListener("click", () => card.remove());
      actions.appendChild(dismiss);
    }
    if (config.showOpenButton && isCongrats) {
      const open = document.createElement("button");
      open.id = "lofi-town-completion-open";
      open.type = "button";
      open.textContent = "Open Lofi Town";
      open.addEventListener("click", () => send("lofi-town:open"));
      actions.appendChild(open);
    }
    if (isCongrats) target.appendChild(card);
    else target.prepend(card);
  };

  const send = (command) => {
    if (typeof pycmd === "function") pycmd(command);
  };

  window.__lofiTownInstallRecap = install;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install, { once: true });
  } else {
    install();
  }
  if (location.pathname.replace(/\/$/, "") === "/congrats") {
    const preserve = new MutationObserver(install);
    preserve.observe(document.documentElement, { childList: true, subtree: true });
    window.addEventListener("pagehide", () => preserve.disconnect(), { once: true });
  }
})();
