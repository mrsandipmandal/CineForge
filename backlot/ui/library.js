import { el, fmtAgo, getJSON, subscribe, thumbURL } from "/ui/lib.js";

const grid = document.getElementById("grid");
const extraView = document.getElementById("extraView");
const THEME_KEY = "backlot.theme";
let currentTheme = localStorage.getItem(THEME_KEY) === "light" ? "light" : "dark";

function applyTheme(theme) {
  currentTheme = theme === "light" ? "light" : "dark";
  document.documentElement.dataset.theme = currentTheme;
  localStorage.setItem(THEME_KEY, currentTheme);
}

function renderThemeToggle() {
  const next = currentTheme === "light" ? "dark" : "light";
  return el("button", {
    class: "theme-toggle",
    type: "button",
    title: `Switch to ${next} theme`,
    "aria-label": `Switch to ${next} theme`,
    "aria-pressed": currentTheme === "light" ? "true" : "false",
    onclick: () => {
      applyTheme(next);
      const replacement = renderThemeToggle();
      document.querySelector(".theme-toggle").replaceWith(replacement);
    },
  }, el("span", { class: "theme-toggle-icon", "aria-hidden": "true" }, currentTheme === "light" ? "☾" : "☀"));
}

applyTheme(currentTheme);
document.getElementById("liveBadge").before(renderThemeToggle());

// Matrix navigation in library
const navTabs = document.querySelectorAll(".matrix-nav .matrix-tab");
navTabs.forEach((tab) => {
  tab.addEventListener("click", (e) => {
    e.preventDefault();
    navTabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");

    const target = tab.getAttribute("href");
    if (target === "/") {
      grid.style.display = "grid";
      if (extraView) extraView.style.display = "none";
    } else if (target === "#identities") {
      grid.style.display = "none";
      if (extraView) {
        extraView.style.display = "block";
        loadIdentityCatalog(extraView);
      }
    } else if (target === "#providers") {
      grid.style.display = "none";
      if (extraView) {
        extraView.style.display = "block";
        loadProvidersCatalog(extraView);
      }
    }
  });
});

async function loadIdentityCatalog(container) {
  container.innerHTML = `<div class="identity-card" style="color:var(--matrix-muted)">Loading identities from sample-files/...</div>`;
  try {
    const [voices, faces] = await Promise.all([
      getJSON("/api/identity/voices"),
      getJSON("/api/identity/faces"),
    ]);
    container.innerHTML = "";
    const wrapper = el("div", { class: "lab-container" });
    wrapper.append(el("div", { class: "lab-head" },
      el("h2", {}, "MATRIX IDENTITY REGISTRY"),
      el("span", { class: "chip" }, `${(voices || []).length} Voices · ${(faces || []).length} Characters`),
    ));

    const vGrid = el("div", { class: "lab-grid" });
    for (const v of (voices || [])) {
      vGrid.append(el("div", { class: "identity-card" },
        el("div", { class: "identity-card-head" },
          el("h3", {}, v.name || v.profile_id),
          el("span", { class: "lang-badge" }, v.primary_language || "en-US"),
        ),
        el("p", { class: "identity-card-desc" }, v.description || "Voice profile"),
      ));
    }
    wrapper.append(vGrid);
    container.append(wrapper);
  } catch (err) {
    container.innerHTML = `<div class="identity-card" style="color:var(--matrix-error)">Error loading identities: ${err}</div>`;
  }
}

async function loadProvidersCatalog(container) {
  container.innerHTML = `<div class="identity-card" style="color:var(--matrix-muted)">Loading live studio readiness and provider capabilities...</div>`;
  try {
    let doc = null;
    try {
      doc = await getJSON("/api/doctor");
    } catch (_) {
      doc = null;
    }
    const sum = (doc && doc.provider_summary) || await getJSON("/api/providers/summary");
    container.innerHTML = "";
    const wrapper = el("div", { class: "lab-container" });
    wrapper.append(el("div", { class: "lab-head" },
      el("h2", {}, "STUDIO READINESS & PROVIDER ENVELOPE"),
      doc ? el("span", { class: "chip" }, `${doc.total_tools_discovered} tools · ${doc.paths?.workspace_root || ""}`) : null,
    ));

    if (doc) {
      const rt = sum.composition_runtimes || {};
      const bins = doc.binaries || {};
      const rtGrid = el("div", { class: "lab-grid", style: "margin-bottom:18px" },
        el("div", { class: "provider-stat-card" },
          el("h4", {}, el("span", {}, "RUNTIMES & ENGINES"), el("span", { style: "color:var(--matrix-green)" }, "LOCAL")),
          el("div", { class: "provider-tags" },
            el("span", { class: `provider-pill ${rt.ffmpeg || bins.ffmpeg?.installed ? "ok" : "miss"}` }, `FFMPEG: ${rt.ffmpeg || bins.ffmpeg?.installed ? "READY" : "MISSING"}`),
            el("span", { class: `provider-pill ${bins.node?.installed ? "ok" : "miss"}` }, `NODE: ${bins.node?.installed ? (bins.node.version || "READY") : "OPTIONAL"}`),
            el("span", { class: `provider-pill ${rt.remotion ? "ok" : "miss"}` }, `REMOTION: ${rt.remotion ? "READY" : "NOT INSTALLED"}`),
            el("span", { class: `provider-pill ${rt.hyperframes ? "ok" : "miss"}` }, `HYPERFRAMES: ${rt.hyperframes ? "READY" : "NOT READY"}`),
          ),
        ),
        el("div", { class: "provider-stat-card" },
          el("h4", {}, el("span", {}, "QUICK CLI / MCP CONNECT"), el("span", { style: "color:var(--matrix-green)" }, "EASY SETUP")),
          el("p", { class: "identity-card-desc", style: "margin-bottom:6px" }, "Run in terminal to unlock keys, MCP assistants, or skills:"),
          el("div", { class: "provider-tags" },
            el("span", { class: "provider-pill ok" }, "cineforge setup"),
            el("span", { class: "provider-pill ok" }, "cineforge mcp install --client claude"),
            el("span", { class: "provider-pill ok" }, "cineforge skills install --target all"),
          ),
        ),
      );
      wrapper.append(rtGrid);
    }

    const pGrid = el("div", { class: "lab-grid" });
    for (const cap of (sum.capabilities || [])) {
      const avail = (cap.available_providers || []).map((p) => el("span", { class: "provider-pill ok" }, p));
      const unavail = (cap.unavailable_providers || []).map((p) => el("span", { class: "provider-pill miss" }, p));
      pGrid.append(el("div", { class: "provider-stat-card" },
        el("h4", {},
          el("span", {}, cap.capability.toUpperCase()),
          el("span", { style: "color:var(--matrix-green)" }, `${cap.configured} / ${cap.total}`)
        ),
        (avail.length || unavail.length) ? el("div", { class: "provider-tags" }, ...avail, ...unavail) : null,
      ));
    }
    wrapper.append(pGrid);
    container.append(wrapper);
  } catch (err) {
    container.innerHTML = `<div class="identity-card" style="color:var(--matrix-error)">Error loading providers: ${err}</div>`;
  }
}

function miniRail(states) {
  const rail = el("div", { class: "mini-rail" });
  for (const s of states) {
    const cls = s.status === "completed" ? "d"
      : s.status === "in_progress" ? "a"
      : s.status === "awaiting_human" ? "w" : "";
    rail.append(el("i", { class: cls, title: `${s.name}: ${s.status}` }));
  }
  return rail;
}

function card(p) {
  const poster = el("div", { class: "lib-poster" });
  if (p.poster) {
    poster.append(el("img", { src: thumbURL(p.project_id, p.poster, 640), loading: "lazy", alt: "" }));
  } else {
    poster.append(el("span", { class: "lp-txt" }, "NO MEDIA YET"));
  }
  if (p.live && p.active_stage) {
    poster.append(el("span", { class: "lp-live" },
      el("span", { class: "dot" }),
      p.awaiting_human ? "◈ AWAITING YOU" : `LIVE · ${p.active_stage.toUpperCase()}`));
  } else if (p.awaiting_human) {
    poster.append(el("span", { class: "lp-live" }, "◈ AWAITING YOU"));
  }

  const meta = el("div", { class: "lb-meta" },
    el("span", { class: "chip" }, p.pipeline_type || "unknown"),
    p.scene_count ? el("span", { class: "chip" }, `${p.scene_count} scenes`) : null,
    p.render_count ? el("span", { class: "chip" }, `${p.render_count} renders`) : null,
    el("span", { class: "when" }, fmtAgo(p.last_activity)),
  );

  const staticSuffix = new URLSearchParams(location.search).has("static") ? "?static=1" : "";
  return el("a", { class: `lib-card${p.live ? " live-card" : ""}`, href: `/p/${p.project_id}${staticSuffix}`, style: "text-decoration:none;color:inherit" },
    poster,
    el("div", { class: "lib-body" },
      el("h3", {}, (p.title || p.project_id).toUpperCase()),
      meta,
      p.stage_states.length ? miniRail(p.stage_states) : null,
    ),
  );
}

async function render() {
  const projects = await getJSON("/api/projects");
  document.getElementById("count").textContent = `${projects.length} projects`;
  const liveCount = projects.filter((p) => p.live).length;
  const badge = document.getElementById("liveBadge");
  badge.classList.toggle("idle", liveCount === 0);
  document.getElementById("liveText").textContent = liveCount ? `${liveCount} LIVE` : "IDLE";
  grid.innerHTML = "";
  document.getElementById("empty").style.display = projects.length ? "none" : "block";
  for (const p of projects) grid.append(card(p));
}

render().catch(console.error);
if (!new URLSearchParams(location.search).has("static")) {
  subscribe("/api/library/events", () => render().catch(console.error));
}
