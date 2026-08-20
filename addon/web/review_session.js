(() => {
  let state = window.__lofiTownSessionBootstrap;
  let timer;
  let observer;

  const formatDuration = (milliseconds) => {
    const totalSeconds = Math.max(0, Math.ceil(milliseconds / 1000));
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${String(seconds).padStart(2, "0")}`;
  };

  const send = (command) => {
    if (typeof pycmd === "function") pycmd(command);
  };

  const readRemaining = () => {
    const selectors = [".new-count", ".learn-count", ".review-count"];
    const nodes = selectors.map((selector) => document.querySelector(selector));
    const values = nodes.flatMap((node) => {
      if (!node) return [];
      const match = node.textContent.replaceAll(",", "").match(/\d+/);
      return match ? [Number(match[0])] : [];
    });
    return {
      nodes: nodes.filter(Boolean),
      total: values.reduce((sum, value) => sum + value, 0),
    };
  };

  const currentBlockFocused = (now) => {
    if (!state.focusStartedAt) return 0;
    const effectiveNow = state.focusPausedAt || now;
    return Math.max(
      0,
      effectiveNow - state.focusStartedAt - state.focusPausedTotal,
    );
  };

  const deriveProgress = (now, targetProgress, phase) => {
    if (state.targetAnswers) {
      return {
        ratio: targetProgress / state.targetAnswers,
        label: `${Math.min(targetProgress, state.targetAnswers)} of ${state.targetAnswers} target answers`,
      };
    }
    if (!state.focusMinutes || !state.startedAt) return null;
    if (phase === "break") {
      return {
        ratio:
          (now - state.breakStartedAt) / (state.breakMinutes * 60 * 1000),
        label: "Break progress",
      };
    }
    return {
      ratio: currentBlockFocused(now) / (state.focusMinutes * 60 * 1000),
      label: "Focus block progress",
    };
  };

  const deriveView = (now) => {
    let phase = "elapsed";
    if (state.phase === "ready") phase = "ready";
    else if (state.phase === "break" && state.breakMinutes) phase = "break";
    else if (state.focusMinutes) phase = "focus";
    const targetProgress = Math.max(0, state.answers - state.targetStartedAnswers);
    const targetComplete = Boolean(
      state.targetAnswers && targetProgress >= state.targetAnswers,
    );
    const paused = Boolean(state.focusPausedAt);
    const view = {
      phase,
      paused,
      targetProgress,
      targetComplete,
      progress: deriveProgress(now, targetProgress, phase),
      timerText: "Ready",
      statusText: "",
      pauseVisible: false,
      restartVisible: false,
      restartText: "Another block",
      breakVisible: false,
      townVisible: false,
      breakReady: false,
    };

    if (phase === "ready") return view;
    if (phase === "break") {
      const remaining = state.breakMinutes * 60 * 1000 - (now - state.breakStartedAt);
      view.breakReady = remaining <= 0;
      view.timerText = view.breakReady
        ? "Break over"
        : `${formatDuration(remaining)} break`;
      view.restartVisible = true;
      view.restartText = view.breakReady ? "Another block" : "Skip break";
      view.statusText = view.breakReady ? "Break complete." : "Break in progress.";
      return view;
    }
    if (phase === "elapsed") {
      const elapsed = state.completedFocusMs + currentBlockFocused(now);
      view.timerText = `${formatDuration(elapsed)} elapsed${paused ? " · paused" : ""}`;
      view.pauseVisible = true;
      return view;
    }

    const remaining = state.focusMinutes * 60 * 1000 - currentBlockFocused(now);
    view.breakReady = remaining <= 0;
    view.timerText = view.breakReady
      ? "Break ready"
      : `${formatDuration(remaining)} left${paused ? " · paused" : ""}`;
    view.statusText = view.breakReady ? "Focus block complete." : view.statusText;
    view.pauseVisible = !view.breakReady;
    view.restartVisible = view.breakReady;
    view.breakVisible = view.breakReady && Boolean(state.breakMinutes);
    view.townVisible = view.breakReady && state.showLofiTownBreak;
    return view;
  };

  const renderWorkload = () => {
    const workload = document.getElementById("lofi-session-workload");
    if (!workload) return;
    workload.hidden = !state.showRemaining;
    if (!state.showRemaining) return;
    const remaining = readRemaining();
    workload.textContent = remaining.nodes.length
      ? `${remaining.total.toLocaleString()} remaining`
      : "remaining hidden";
  };

  const renderProgress = (progress) => {
    const element = document.getElementById("lofi-session-progress");
    const fill = document.getElementById("lofi-session-progress-fill");
    if (!element || !fill) return;
    element.hidden = !state.showProgress || progress === null;
    if (element.hidden) return;
    const percent = Math.max(0, Math.min(100, Math.round(progress.ratio * 100)));
    fill.style.width = `${percent}%`;
    element.setAttribute("aria-label", progress.label);
    element.setAttribute("aria-valuenow", String(percent));
  };

  const render = () => {
    const hud = document.getElementById("lofi-session-hud");
    if (!hud) return;
    const view = deriveView(Date.now());
    const answerCount = document.getElementById("lofi-session-answers");
    const facts = document.querySelector(".lofi-session-facts");
    const time = document.getElementById("lofi-session-time");
    const status = document.getElementById("lofi-session-status");
    const pause = document.getElementById("lofi-session-pause");
    const restart = document.getElementById("lofi-session-restart");
    const startBreak = document.getElementById("lofi-session-start-break");
    const openTown = document.getElementById("lofi-session-open-town");
    const restartTarget = document.getElementById("lofi-session-restart-target");
    const separator = document.getElementById("lofi-session-facts-separator");

    answerCount.hidden = !state.showAnswers;
    facts.hidden = !state.showAnswers && !state.showRemaining;
    time.hidden = !state.showTimer;
    answerCount.textContent = state.targetAnswers
      ? `${view.targetProgress.toLocaleString()}/${state.targetAnswers.toLocaleString()} answers`
      : `${state.answers.toLocaleString()} ${state.answers === 1 ? "answer" : "answers"}`;
    separator.hidden = !state.showAnswers || !state.showRemaining;
    renderWorkload();
    renderProgress(view.progress);

    hud.classList.toggle("is-compact", state.compact);
    hud.classList.toggle("is-target-ready", view.targetComplete);
    hud.classList.toggle("is-break-ready", view.breakReady);
    restartTarget.hidden = view.phase === "ready" || !view.targetComplete;
    time.textContent = view.timerText;
    status.textContent = view.statusText;

    pause.hidden = !view.pauseVisible;
    pause.textContent = view.paused ? "Resume" : "Pause";
    pause.setAttribute("aria-pressed", view.paused ? "true" : "false");
    restart.hidden = !view.restartVisible;
    restart.textContent = view.restartText;
    startBreak.hidden = !view.breakVisible;
    startBreak.textContent = `Start ${state.breakMinutes} min break`;
    openTown.hidden = !view.townVisible;
  };

  const install = () => {
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
        <span id="lofi-session-facts-separator" aria-hidden="true">·</span>
        <span id="lofi-session-workload">remaining hidden</span>
      </div>
      <div id="lofi-session-progress" class="lofi-session-progress"
        role="progressbar" aria-valuemin="0" aria-valuemax="100" hidden>
        <span id="lofi-session-progress-fill"></span>
      </div>
      <span id="lofi-session-time" class="lofi-session-time"></span>
      <div class="lofi-session-actions">
        <button id="lofi-session-pause" type="button" aria-pressed="false">Pause</button>
        <button id="lofi-session-restart" type="button" hidden>Another block</button>
        <button id="lofi-session-start-break" type="button" hidden>Start break</button>
        <button id="lofi-session-restart-target" type="button" hidden>Another target</button>
        <button id="lofi-session-open-town" type="button" hidden>Break in Lofi Town</button>
      </div>
      <span id="lofi-session-status" class="lofi-visually-hidden"
        role="status" aria-live="polite"></span>`;
    if (state.position === "bottom") outer.insertAdjacentElement("afterend", hud);
    else outer.parentNode.insertBefore(hud, outer);

    document.getElementById("lofi-session-pause").addEventListener("click", () => {
      send(state.focusPausedAt ? "lofi-town:resume-focus" : "lofi-town:pause-focus");
    });
    document.getElementById("lofi-session-restart").addEventListener(
      "click",
      () => send("lofi-town:restart-focus"),
    );
    document.getElementById("lofi-session-start-break").addEventListener(
      "click",
      () => send("lofi-town:start-break"),
    );
    document.getElementById("lofi-session-restart-target").addEventListener(
      "click",
      () => send("lofi-town:restart-target"),
    );
    document.getElementById("lofi-session-open-town").addEventListener(
      "click",
      () => send("lofi-town:take-break"),
    );

    const remaining = readRemaining();
    observer = new MutationObserver(renderWorkload);
    remaining.nodes.forEach((node) =>
      observer.observe(node, { childList: true, characterData: true, subtree: true }),
    );
    window.__lofiTownSession = {
      update(next) {
        state = { ...state, ...next };
        render();
      },
    };
    render();
    timer = window.setInterval(render, 1000);
    window.addEventListener(
      "pagehide",
      () => {
        window.clearInterval(timer);
        observer.disconnect();
      },
      { once: true },
    );
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install, { once: true });
  } else {
    install();
  }
})();
