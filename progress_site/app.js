const $ = (selector) => document.querySelector(selector);

const state = {
  installPrompt: null,
  progress: null,
  status: null,
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function renderHighlights(items = []) {
  $("#highlightGrid").innerHTML = items.map((item) => `
    <article class="highlight-card">
      <div class="highlight-label">${escapeHtml(item.label)}</div>
      <h3>${escapeHtml(item.title)}</h3>
      <p>${escapeHtml(item.body)}</p>
    </article>
  `).join("");
}

function renderTimeline(items = []) {
  $("#timeline").innerHTML = items.map((item) => `
    <article class="timeline-item">
      <div class="timeline-code">${escapeHtml(item.code)}</div>
      <div class="timeline-body">
        <div class="timeline-meta">
          <span class="timeline-status">${escapeHtml(item.status)}</span>
          <time>${escapeHtml(item.date)}</time>
        </div>
        <h3>${escapeHtml(item.title)}</h3>
        <p>${escapeHtml(item.description)}</p>
      </div>
    </article>
  `).join("");
}

function renderSystems(items = []) {
  $("#systemList").innerHTML = items.map((item) => `
    <article class="system-row">
      <h3>${escapeHtml(item.name)}</h3>
      <span class="system-status">${escapeHtml(item.status)}</span>
      <p>${escapeHtml(item.note)}</p>
    </article>
  `).join("");
}

function renderNext(items = []) {
  $("#nextList").innerHTML = items.map((item, index) => `
    <article class="next-item">
      <div class="next-number">${String(index + 1).padStart(2, "0")}</div>
      <div><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.body)}</p></div>
    </article>
  `).join("");
}

function renderProgress(progress) {
  state.progress = progress;
  const release = progress.current_release ?? {};
  document.title = progress.site_title ?? "足球共和国 · 开发进度站";
  $("#siteTitle").textContent = progress.site_title ?? "足球共和国 · 开发进度站";
  $("#tagline").textContent = progress.tagline ?? "";
  $("#releaseLabel").textContent = `最新发布 · ${release.date ?? "—"}`;
  $("#version").textContent = release.version ?? "—";
  $("#ribbonVersion").textContent = release.version ?? "—";
  $("#releaseTitle").textContent = release.title ?? "—";
  $("#releaseSummary").textContent = release.summary ?? "";
  $("#commit").textContent = (release.merge_commit ?? "—").slice(0, 7);
  $("#testSummary").textContent = release.validation ?? "—";
  $("#mergeReference").textContent = release.pr ? `PR #${release.pr}` : "—";
  $("#playCommand").textContent = progress.play?.command ?? "";
  $("#playDescription").textContent = progress.play?.description ?? "";

  const links = progress.links ?? {};
  $("#repoLink").href = links.repository ?? "#";
  $("#repositoryLink").href = links.repository ?? "#";
  $("#pullsLink").href = links.pulls ?? "#";
  $("#issuesLink").href = links.issues ?? "#";

  renderHighlights(progress.latest_highlights);
  renderTimeline(progress.milestones);
  renderSystems(progress.system_map);
  renderNext(progress.next_steps);
}

function renderStatus(status) {
  state.status = status;
  const outcome = status?.tests?.outcome ?? "unknown";
  const success = outcome === "success";
  $("#buildStatus").textContent = success ? "全绿" : outcome === "failure" ? "需要修复" : "等待结果";
  $("#buildIcon").classList.toggle("failed", outcome === "failure");
  $("#testSummary").textContent = status?.tests?.summary || state.progress?.current_release?.validation || "—";
  $("#version").textContent = status?.version || state.progress?.current_release?.version || "—";
  $("#ribbonVersion").textContent = status?.version || state.progress?.current_release?.version || "—";
  $("#commit").textContent = status?.commit?.short || (state.progress?.current_release?.merge_commit ?? "—").slice(0, 7);
  $("#updatedAt").textContent = formatDate(status?.generated_at);
  if (status?.commit?.message) {
    $("#commit").title = status.commit.message;
  }
}

async function fetchJson(path) {
  const response = await fetch(`${path}?v=${Date.now()}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response.json();
}

async function loadData() {
  const refresh = $("#refreshButton");
  refresh.classList.add("rotating");
  try {
    const [progress, status] = await Promise.all([
      fetchJson("progress.json"),
      fetchJson("status.json").catch(() => null),
    ]);
    renderProgress(progress);
    if (status) renderStatus(status);
  } catch (error) {
    $("#buildStatus").textContent = "读取失败";
    $("#buildIcon").classList.add("failed");
    console.error(error);
  } finally {
    refresh.classList.remove("rotating");
  }
}

$("#refreshButton").addEventListener("click", loadData);

$("#copyCommand").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  try {
    await navigator.clipboard.writeText($("#playCommand").textContent);
    button.textContent = "已复制";
    button.classList.add("copied");
  } catch {
    button.textContent = "请长按命令复制";
  }
  setTimeout(() => {
    button.textContent = "复制启动命令";
    button.classList.remove("copied");
  }, 1800);
});

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  state.installPrompt = event;
  $("#installButton").hidden = false;
});

$("#installButton").addEventListener("click", async () => {
  if (!state.installPrompt) return;
  state.installPrompt.prompt();
  await state.installPrompt.userChoice;
  state.installPrompt = null;
  $("#installButton").hidden = true;
});

const dialog = $("#installDialog");
$("#homeScreenHelp").addEventListener("click", () => dialog.showModal());
$("#closeDialog").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("service-worker.js"));
}

loadData();
setInterval(loadData, 60_000);
