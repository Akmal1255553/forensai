const $ = (sel) => document.querySelector(sel);
const tr = (k, v) => (window.I18n?.t(k, v) ?? k);

let batchFiles = [];
let dropzone;
let fileInput;
let fileNameEl;
let textInput;
let analyzeBtn;
let emptyState;
let report;
let loading;
let statusPills;

let selectedFile = null;
let selectedFileA = null;
let selectedFileB = null;
let activeTab = "file";
let lastAnalyzedText = "";
let lastPreviewUrl = null;
let lastCompareData = null;

function switchTab(tabName) {
  if (!tabName) return;
  activeTab = tabName;
  document.querySelectorAll(".upload-tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === activeTab);
  });
  document.querySelectorAll(".upload-panel__body > .tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `panel-${activeTab}`);
  });
}

function initTabs() {
  const tablist = document.querySelector(".upload-panel__tabs");
  if (!tablist) return;
  tablist.addEventListener("click", (e) => {
    const btn = e.target.closest(".upload-tab");
    if (!btn?.dataset?.tab) return;
    e.preventDefault();
    switchTab(btn.dataset.tab);
  });
  switchTab(activeTab);
}

function bindFileInput(input, onPick) {
  if (!input) return;
  input.addEventListener("change", () => {
    if (input.files?.length) onPick(input.files[0]);
  });
}

function bindFileDropzone(zone, onPick) {
  if (!zone) return;
  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("dragover");
  });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("dragover");
    if (e.dataTransfer.files?.length) onPick(e.dataTransfer.files[0]);
  });
}

function bindFileUpload() {
  dropzone = $("#dropzone");
  fileInput = $("#fileInput");
  fileNameEl = $("#fileName");

  bindFileInput(fileInput, setFile);
  bindFileDropzone(dropzone, setFile);

  bindFileInput($("#fileInputA"), (f) => {
    selectedFileA = f;
    const el = $("#fileNameA");
    if (el) el.textContent = f.name;
  });
  bindFileInput($("#fileInputB"), (f) => {
    selectedFileB = f;
    const el = $("#fileNameB");
    if (el) el.textContent = f.name;
  });

  const fileInputBatch = $("#fileInputBatch");
  if (fileInputBatch) {
    fileInputBatch.addEventListener("change", () => {
      batchFiles = [...fileInputBatch.files];
      const el = $("#batchFileCount");
      if (el) {
        el.textContent = batchFiles.length
          ? tr("upload.filesSelected", { n: batchFiles.length })
          : tr("upload.pickFile");
      }
    });
  }
  bindFileDropzone($("#dropzoneBatch"), (f) => {
    if (fileInputBatch) {
      const dt = new DataTransfer();
      dt.items.add(f);
      fileInputBatch.files = dt.files;
      batchFiles = [f];
      const el = $("#batchFileCount");
      if (el) el.textContent = tr("upload.filesSelected", { n: 1 });
    }
  });
}

function initAppShell() {
  textInput = $("#textInput");
  analyzeBtn = $("#analyzeBtn");
  emptyState = $("#emptyState");
  report = $("#report");
  loading = $("#loading");
  statusPills = $("#statusPills");
  initTabs();
  bindFileUpload();
}

window.addEventListener("forensai:openReport", (e) => {
  if (e.detail) renderReport(e.detail);
});

window.addEventListener("forensai:lang", () => {
  if (selectedFile && fileNameEl) fileNameEl.textContent = selectedFile.name;
  else if (fileNameEl && !fileNameEl.dataset.filename) fileNameEl.textContent = tr("upload.pickFile");
  const nameA = $("#fileNameA");
  const nameB = $("#fileNameB");
  if (nameA && !selectedFileA) nameA.textContent = tr("upload.fileA");
  if (nameB && !selectedFileB) nameB.textContent = tr("upload.fileB");
  const batchEl = $("#batchFileCount");
  if (batchEl && !batchFiles.length) batchEl.textContent = tr("upload.pickFile");
  if (lastReportData) renderReport(lastReportData, { preserveCompare: !!lastCompareData });
  else if (lastCompareData) renderCompareReport(lastCompareData);
});

function setFile(file) {
  selectedFile = file;
  if (fileNameEl) {
    fileNameEl.textContent = file.name;
    fileNameEl.dataset.filename = "1";
  }
  if (lastPreviewUrl) URL.revokeObjectURL(lastPreviewUrl);
  lastPreviewUrl = null;
}

function showError(msg) {
  const toast = document.createElement("div");
  toast.className = "error-toast";
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}

function esc(str) {
  const d = document.createElement("div");
  d.textContent = str ?? "";
  return d.innerHTML;
}

function safeText(val) {
  if (val == null) return "";
  if (typeof val === "object") return "";
  return String(val);
}

function categoryLabel(key) {
  return I18n?.categoryLabel?.(key) ?? key;
}

async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    statusPills.innerHTML = "";
    [
      { ok: data.gemini_configured, label: data.gemini_configured ? "Gemini" : "Gemini —" },
      { ok: data.openai_configured, label: data.openai_configured ? "OpenAI" : "OpenAI —" },
      { ok: true, label: "Forensics" },
    ].forEach(({ ok, label }) => {
      const el = document.createElement("span");
      el.className = `pill ${ok ? "pill--ok" : "pill--warn"}`;
      el.textContent = label;
      statusPills.appendChild(el);
    });
  } catch {
    statusPills.innerHTML = `<span class="pill pill--warn">${tr("status.serverDown")}</span>`;
  }
}

function renderMetrics(metrics) {
  const strip = $("#metricsStrip");
  if (!metrics || !Object.keys(metrics).length) {
    strip.classList.add("hidden");
    return;
  }
  strip.classList.remove("hidden");
  strip.innerHTML = "";

  const chips = [
    [tr("metric.crit"), metrics.critical_findings],
    [tr("metric.mod"), metrics.moderate_findings],
    [tr("metric.total"), metrics.total_findings],
    [tr("metric.zones"), metrics.zones_flagged],
    [tr("metric.quality"), metrics.processing_quality != null ? `${metrics.processing_quality}%` : null],
    ["MP", metrics.megapixels],
    ["FPS", metrics.fps],
    [tr("metric.frames"), metrics.frames_analyzed],
    ["ELA", metrics.ela_variance],
  ];

  chips.forEach(([label, val]) => {
    if (val == null || val === "" || val === 0) return;
    const el = document.createElement("span");
    el.className = "metric-chip";
    el.innerHTML = `${label}: <strong>${esc(String(val))}</strong>`;
    strip.appendChild(el);
  });
}

function renderCategories(scores) {
  const section = $("#categoriesSection");
  const container = $("#categoryBars");
  if (!scores || !Object.keys(scores).length) {
    section.classList.add("hidden");
    return;
  }
  section.classList.remove("hidden");
  container.innerHTML = "";

  Object.entries(scores).sort((a, b) => b[1] - a[1]).forEach(([key, val]) => {
    const row = document.createElement("div");
    row.className = "category-row";
    row.innerHTML = `
      <span class="category-row__label">${esc(categoryLabel(key))}</span>
      <div class="category-row__bar"><div class="category-row__fill" style="width:${val}%"></div></div>
      <span class="category-row__val">${val}</span>
    `;
    container.appendChild(row);
  });
}

const riskLabel = (risk) => ({
  clean: tr("risk.clean"), low: tr("risk.low"), medium: tr("risk.medium"), high: tr("risk.high"),
}[risk] || (risk === "high" ? tr("risk.high") : tr("risk.low")));

function zoneHeatClass(score, risk) {
  if (risk === "high" || score >= 62) return "heat-high";
  if (risk === "medium" || score >= 45) return "heat-medium";
  if (risk === "low" || score >= 28) return "heat-low";
  return "heat-clean";
}

function renderZoneHeatmap(zones) {
  const wrap = $("#zoneHeatmapWrap");
  const grid = $("#zoneHeatmap");
  const gridZones = (zones || []).filter((z) => z.zone_type === "grid").sort((a, b) => a.index - b.index);

  if (gridZones.length !== 9) {
    wrap.classList.add("hidden");
    return;
  }
  wrap.classList.remove("hidden");
  grid.innerHTML = "";

  gridZones.forEach((z) => {
    const cell = document.createElement("div");
    cell.className = `zone-heatmap__cell ${zoneHeatClass(z.ai_score, z.risk)}`;
    cell.title = (z.issues || []).join("; ");
    const reg = I18n.regionLabel(z.region);
    cell.innerHTML = `${Math.round(z.ai_score)}%<span>${esc(reg.split("-").join("·"))}</span>`;
    grid.appendChild(cell);
  });
}

function renderZones(zones) {
  const section = $("#zonesSection");
  const container = $("#zonesGrid");
  if (!zones?.length) {
    section.classList.add("hidden");
    return;
  }
  section.classList.remove("hidden");
  container.innerHTML = "";

  renderZoneHeatmap(zones);

  const sorted = [...zones].sort((a, b) => (b.ai_score ?? 0) - (a.ai_score ?? 0));
  const gridFirst = sorted.filter((z) => z.zone_type === "grid" && (z.ai_score ?? 0) >= 28);
  const llmZones = sorted.filter((z) => z.zone_type !== "grid");
  const toShow = [...gridFirst, ...llmZones].slice(0, 12);

  if (!toShow.length) {
    container.innerHTML = `<p class="zone-empty">${tr("zones.allOk")}</p>`;
    return;
  }

  toShow.forEach((z) => {
    const sev = z.severity || (z.ai_score >= 65 ? "critical" : z.ai_score >= 45 ? "moderate" : z.ai_score >= 28 ? "minor" : "clean");
    const card = document.createElement("div");
    card.className = `zone-card zone-card--${sev}`;
    const ts = z.timestamp_sec != null ? ` · ${tr("zone.sec", { n: z.timestamp_sec })}` : "";
    const risk = riskLabel(z.risk) || (z.ai_score >= 45 ? tr("risk.medium") : tr("risk.low"));
    const issues = Array.isArray(z.issues) ? z.issues.map((i) => I18n.translateLine(i)).join("; ") : "—";
    const md = z.metrics_detail;
    let metricsHtml = "";
    if (md) {
      metricsHtml = `<div class="zone-card__metrics">
        ${md.ela != null ? `<span class="zone-metric">ELA ${md.ela}</span>` : ""}
        ${md.noise != null ? `<span class="zone-metric">${tr("zone.noise")} ${md.noise}%</span>` : ""}
        ${md.sharpness != null ? `<span class="zone-metric">${tr("zone.sharp")} ${md.sharpness}</span>` : ""}
        ${md.entropy != null ? `<span class="zone-metric">Ent ${md.entropy}</span>` : ""}
      </div>`;
    }
    card.innerHTML = `
      <div class="zone-card__head">
        <span>${esc(I18n.regionLabel(z.region))}${ts}</span>
        <span class="zone-card__score">${Math.round(z.ai_score ?? 0)}%</span>
      </div>
      <div class="zone-card__issues">${esc(issues)}</div>
      ${metricsHtml}
      <div class="zone-card__issues">${tr("zone.riskLabel", { risk })}</div>
    `;
    container.appendChild(card);
  });
}

let progressTimer = null;

function setProgress(pct, label) {
  const fill = $("#progressFill");
  const pctEl = $("#progressPercent");
  const steps = $("#loadingSteps");
  const val = Math.max(0, Math.min(100, Math.round(pct)));
  if (fill) fill.style.width = `${val}%`;
  if (pctEl) pctEl.textContent = `${val}%`;
  if (steps && label) steps.textContent = label;
}

function startAnalysisProgress(contentType) {
  clearInterval(progressTimer);
  setProgress(0, tr("loading.prep"));
  const stages =
    contentType === "video"
      ? [
          { at: 800, p: 15, l: "Извлечение кадров…" },
          { at: 2500, p: 35, l: "ELA и шум…" },
          { at: 5000, p: 55, l: "Анализ зон…" },
          { at: 9000, p: 72, l: "Gemini LLM…" },
          { at: 15000, p: 85, l: "Формирование отчёта…" },
        ]
      : contentType === "image"
        ? [
            { at: 500, p: 20, l: "Сканирование EXIF…" },
            { at: 1500, p: 40, l: "ELA 3×3 зоны…" },
            { at: 4000, p: 60, l: "Локальная экспертиза…" },
            { at: 8000, p: 78, l: "Gemini LLM…" },
            { at: 14000, p: 88, l: "Сборка отчёта…" },
          ]
        : [
            { at: 400, p: 25, l: "Эвристики текста…" },
            { at: 1200, p: 45, l: "Сегменты и плагиат…" },
            { at: 3500, p: 65, l: "LLM-анализ…" },
            { at: 8000, p: 82, l: "Обоснование…" },
          ];

  const t0 = Date.now();
  progressTimer = setInterval(() => {
    const elapsed = Date.now() - t0;
    let cur = stages[0];
    for (const s of stages) {
      if (elapsed >= s.at) cur = s;
    }
    setProgress(cur.p, cur.l);
    if (cur.p >= 88) clearInterval(progressTimer);
  }, 200);
}

function stopProgress(done) {
  clearInterval(progressTimer);
  progressTimer = null;
  if (done) {
    setProgress(100, tr("loading.prep"));
  }
}

function analyzeWithProgress(form, contentType) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/analyze");
    const headers = window.Account?.apiHeaders?.() || {};
    Object.entries(headers).forEach(([k, v]) => xhr.setRequestHeader(k, v));

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable && e.total > 0) {
        const uploadPct = Math.min(35, (e.loaded / e.total) * 35);
        setProgress(uploadPct, `Загрузка файла… ${Math.round((e.loaded / e.total) * 100)}%`);
      }
    });

    xhr.addEventListener("load", () => {
      try {
        const data = JSON.parse(xhr.responseText);
        if (xhr.status >= 200 && xhr.status < 300) {
          Account?.onAnalyzeResponse?.(data);
          resolve(data);
        } else if (xhr.status === 401) {
          window.Auth?.openModal?.("signin");
          reject(new Error(tr("error.auth")));
        } else if (xhr.status === 402) reject(new Error(tr("error.limit")));
        else reject(new Error(data.detail || tr("error.analyze")));
      } catch {
        reject(new Error(tr("error.server")));
      }
    });

    xhr.addEventListener("error", () => reject(new Error(tr("error.network"))));
    xhr.send(form);
  });
}

let lastReportData = null;

function animateCounter(el, target, duration = 800) {
  if (!el) return;
  const start = 0;
  const t0 = performance.now();
  const tick = (now) => {
    const p = Math.min(1, (now - t0) / duration);
    const ease = 1 - (1 - p) ** 3;
    el.textContent = Math.round(start + (target - start) * ease);
    if (p < 1) requestAnimationFrame(tick);
    else el.textContent = target;
  };
  requestAnimationFrame(tick);
}

function zoneColor(score) {
  if (score >= 62) return "rgba(248, 113, 113, 0.45)";
  if (score >= 48) return "rgba(251, 191, 36, 0.4)";
  if (score >= 32) return "rgba(6, 182, 212, 0.3)";
  return "rgba(52, 211, 153, 0.15)";
}

function renderMediaPreview(file, zones, imgW, imgH) {
  const section = $("#mediaPreviewSection");
  const container = $("#mediaPreview");
  const canvas = $("#zoneCanvas");
  if (!file || !(file.type.startsWith("image/") || file.type.startsWith("video/"))) {
    section.classList.add("hidden");
    return;
  }
  section.classList.remove("hidden");
  if (lastPreviewUrl) URL.revokeObjectURL(lastPreviewUrl);
  lastPreviewUrl = URL.createObjectURL(file);

  if (file.type.startsWith("image/")) {
    container.innerHTML = `<img id="previewImg" src="${lastPreviewUrl}" alt="Превью"><canvas id="zoneCanvas" class="zone-canvas"></canvas>`;
    const img = $("#previewImg");
    const cv = $("#zoneCanvas");
    img.onload = () => {
      if (!cv || !zones?.length) return;
      const grid = zones.filter((z) => z.zone_type === "grid" && z.box);
      if (!grid.length) return;
      cv.classList.remove("hidden");
      const rect = img.getBoundingClientRect();
      const wrap = container.getBoundingClientRect();
      const dw = img.clientWidth;
      const dh = img.clientHeight;
      cv.width = dw;
      cv.height = dh;
      cv.style.width = `${dw}px`;
      cv.style.height = `${dh}px`;
      const sx = dw / (imgW || img.naturalWidth || dw);
      const sy = dh / (imgH || img.naturalHeight || dh);
      const ctx = cv.getContext("2d");
      ctx.clearRect(0, 0, dw, dh);
      grid.forEach((z) => {
        const b = z.box;
        ctx.fillStyle = zoneColor(z.ai_score ?? 0);
        ctx.fillRect(b.x * sx, b.y * sy, b.w * sx, b.h * sy);
        ctx.strokeStyle = "rgba(255,255,255,0.35)";
        ctx.strokeRect(b.x * sx, b.y * sy, b.w * sx, b.h * sy);
        if (z.ai_score >= 32) {
          ctx.fillStyle = "#fff";
          ctx.font = "bold 10px IBM Plex Mono, monospace";
          ctx.fillText(`${Math.round(z.ai_score)}%`, b.x * sx + 4, b.y * sy + 14);
        }
      });
    };
  } else {
    canvas?.classList?.add("hidden");
    container.innerHTML = `<video src="${lastPreviewUrl}" controls muted></video>`;
  }
}

function renderVideoTimeline(frames, contentType) {
  const section = $("#videoTimelineSection");
  const el = $("#videoTimeline");
  if (contentType !== "video" || !frames?.length) {
    section.classList.add("hidden");
    return;
  }
  section.classList.remove("hidden");
  el.innerHTML = "";
  const maxScore = Math.max(...frames.map((f) => f.ai_score || 0), 1);
  frames.forEach((f) => {
    const bar = document.createElement("div");
    bar.className = "timeline-item";
    const h = Math.max(12, (f.ai_score / maxScore) * 100);
    bar.innerHTML = `
      <div class="timeline-item__bar" style="height:${h}%" title="AI ${f.ai_score}%"></div>
      <span class="timeline-item__label">${f.timestamp_sec ?? f.index}с</span>
    `;
    el.appendChild(bar);
  });
}

function renderReasoning(report) {
  const grid = $("#reasoningGrid");
  grid.innerHTML = "";
  const reasoning = I18n.localizedReasoning(report);
  const metrics = report.metrics;

  if (!reasoning || typeof reasoning !== "object") {
    grid.innerHTML = `<div class="reasoning-card"><p>${esc(safeText(reasoning) || tr("reasoning.unavailable"))}</p></div>`;
    return;
  }

  const blocks = [
    { key: "summary", title: tr("reasoning.summary"), cls: "reasoning-card--summary", extra: true },
    { key: "ai_analysis", title: tr("reasoning.ai"), cls: "reasoning-card__title--ai" },
    { key: "plagiarism_analysis", title: tr("reasoning.plagiarism"), cls: "reasoning-card__title--pl" },
    { key: "conclusion", title: tr("reasoning.conclusion"), cls: "reasoning-card__title--con" },
  ];

  blocks.forEach(({ key, title, cls, extra }) => {
    const text = safeText(reasoning[key]);
    if (!text) return;
    const card = document.createElement("div");
    card.className = `reasoning-card ${extra ? cls : ""}`;

    let metricsHtml = "";
    if (extra && metrics) {
      const nums = [
        [tr("score.short.ai"), metrics.ai_index], [tr("score.short.pl"), metrics.plagiarism_index],
        [tr("score.short.auth"), metrics.authenticity], [tr("score.short.conf"), `${metrics.confidence}%`],
      ].filter(([, v]) => v != null);
      metricsHtml = `<div class="reasoning-metrics">${nums.map(([l, v]) => `<span>${l} ${v}</span>`).join("")}</div>`;
    }

    card.innerHTML = `
      <div class="reasoning-card__title ${cls}">${title}</div>
      <p>${esc(text)}</p>
      ${metricsHtml}
    `;
    grid.appendChild(card);
  });

  if (!grid.children.length) {
    grid.innerHTML = `<div class="reasoning-card"><p>${tr("reasoning.pending")}</p></div>`;
  }
}

function renderSegments(segments, contentType) {
  const section = $("#segmentsSection");
  const tbody = $("#segmentsBody");
  tbody.innerHTML = "";

  if (contentType !== "text" || !segments?.length) {
    section.classList.add("hidden");
    return;
  }
  section.classList.remove("hidden");

  segments.forEach((seg) => {
    const row = document.createElement("tr");
    row.className = seg.combined_risk === "high" ? "seg-row--high" : seg.combined_risk === "medium" ? "seg-row--medium" : "";
    const flags = [...(seg.ai_flags || []), ...(seg.plagiarism_flags || [])];
    row.innerHTML = `
      <td class="seg-num">${seg.index}</td>
      <td class="seg-text">${esc(seg.text)}</td>
      <td class="seg-score seg-score--ai">${seg.ai_score}%</td>
      <td class="seg-score seg-score--pl">${seg.plagiarism_score}%</td>
      <td class="seg-flags">${flags.length ? esc(flags.join("; ")) : "—"}</td>
    `;
    tbody.appendChild(row);
  });
}

function renderTextMap(text, segments, contentType) {
  const section = $("#highlightSection");
  const map = $("#textMap");
  if (contentType !== "text" || !text || !segments?.length) {
    section.classList.add("hidden");
    return;
  }
  section.classList.remove("hidden");
  let html = esc(text);
  [...segments].sort((a, b) => b.start - a.start).forEach((seg) => {
    const fragment = esc(seg.text);
    const ai = seg.ai_score >= 40;
    const pl = seg.plagiarism_score >= 40;
    let cls = ai && pl ? "hl-both" : ai ? "hl-ai" : pl ? "hl-pl" : "";
    if (!cls) return;
    const idx = html.indexOf(fragment);
    if (idx !== -1) html = html.slice(0, idx) + `<mark class="${cls}">${fragment}</mark>` + html.slice(idx + fragment.length);
  });
  map.innerHTML = html;
}

function syncVerdictFromScores(r) {
  const ai = Number(r.scores?.ai ?? 0);
  if (ai >= 65) {
    r.verdict = "ai_generated";
    r.verdict_label = I18n.verdictLabel("ai_generated", r.verdict_label);
    r.confidence = Math.max(r.confidence ?? 0, Math.min(95, ai));
  } else if (ai >= 42) {
    r.verdict = "hybrid";
    r.verdict_label = I18n.verdictLabel("hybrid", r.verdict_label);
    r.confidence = Math.min(82, Math.max(50, ai));
  }
  if (r.scores) r.scores.authenticity = Math.max(0, 100 - ai);
  if (r.metrics) {
    r.metrics.ai_index = ai;
    r.metrics.authenticity = Math.max(0, 100 - ai);
    r.metrics.confidence = r.confidence;
  }
}

function renderOsint(osint, contentType) {
  const section = $("#osintSection");
  const panel = $("#osintPanel");
  if (!osint || !panel) {
    section?.classList.add("hidden");
    return;
  }
  const c = osint.compact || {};
  const hasData = c.hash_full || c.resolution || osint.reverse_search?.length;
  if (!hasData) {
    section.classList.add("hidden");
    return;
  }
  section.classList.remove("hidden");

  const chips = [];
  if (c.resolution) {
    chips.push(`<span class="osint-chip">${esc(c.resolution)}${c.megapixels != null ? ` · ${c.megapixels} MP` : ""}</span>`);
  }
  if (c.format) chips.push(`<span class="osint-chip">${esc(c.format)}</span>`);
  if (c.exif_status) {
    const exifKey = c.exif_status === "camera" ? "osint.exifCamera"
      : c.exif_status === "missing" ? "osint.exifMissingShort"
        : c.exif_status === "error" ? "osint.exifErrorShort" : "osint.exifPresentShort";
    const exifLabel = c.camera ? tr("osint.exifCamera", { model: c.camera }) : tr(exifKey);
    chips.push(`<span class="osint-chip osint-chip--${esc(c.exif_status)}">${esc(exifLabel)}</span>`);
  }
  if (c.duration_sec != null) chips.push(`<span class="osint-chip">${tr("osint.durationShort", { n: c.duration_sec })}</span>`);
  if (c.fps) chips.push(`<span class="osint-chip">${c.fps} fps</span>`);

  const hashRow = c.hash_full
    ? `<div class="osint-hash-row" title="${esc(c.hash_full)}">
        <code class="osint-hash-code">${esc(c.hash_short || c.hash_full.slice(0, 16))}…</code>
        <button type="button" class="osint-copy-btn" data-hash="${esc(c.hash_full)}">${tr("osint.copy")}</button>
      </div>`
    : "";

  const links = osint.reverse_search?.length
    ? `<div class="osint-links">${osint.reverse_search.map((l) =>
        `<a class="osint-link" href="${esc(l.url)}" target="_blank" rel="noopener" title="${esc(l.hint || "")}">${esc(l.name)}</a>`
      ).join("")}</div>`
    : "";

  const exifDetails = osint.metadata_lines?.length
    ? `<details class="osint-details"><summary>${tr("osint.exifDetails")}</summary>
        <ul class="osint-meta-list">${osint.metadata_lines.map((line) => `<li>${esc(line)}</li>`).join("")}</ul>
      </details>`
    : "";

  panel.innerHTML = `<div class="osint-compact">
    ${chips.length ? `<div class="osint-chips">${chips.join("")}</div>` : ""}
    ${hashRow}
    ${links}
    ${exifDetails}
  </div>`;

  panel.querySelector(".osint-copy-btn")?.addEventListener("click", (e) => {
    const hash = e.currentTarget.dataset.hash;
    if (hash) navigator.clipboard?.writeText(hash).then(() => showError(tr("ref.copied")));
  });
}

function renderCompare(comparison, reportA, reportB, nameA, nameB) {
  const section = $("#compareSection");
  if (!comparison) {
    section?.classList.add("hidden");
    return;
  }
  section.classList.remove("hidden");
  $("#compareSummary").textContent = I18n.localizedCompareSummary(comparison, reportA, reportB, nameA, nameB);
  const cards = $("#compareCards");
  const items = [
    { name: nameA || "A", r: reportA, meta: comparison.file_a },
    { name: nameB || "B", r: reportB, meta: comparison.file_b },
  ];
  cards.innerHTML = items.map(({ name, r }) => {
    const s = r?.scores || {};
    const v = I18n.verdictLabel(r?.verdict, r?.verdict_label);
    const scores = `${tr("score.short.ai")} ${s.ai ?? 0} · ${tr("score.short.pl")} ${s.plagiarism ?? 0} · ${tr("score.short.auth")} ${s.authenticity ?? 0}`;
    return `<div class="compare-card">
      <div class="compare-card__name">${esc(name)}</div>
      <div class="compare-card__verdict">${esc(v || "—")}</div>
      <div class="compare-card__scores">${scores}</div>
    </div>`;
  }).join("");
}

function buildPrintHtml(data) {
  const r = data.report || data;
  const reason = r.reasoning || {};
  const zones = (r.zones || []).slice(0, 9).map((z) =>
    `${z.region}: ${z.ai_score}% — ${(z.issues || []).join("; ")}`
  ).join("<br>");
  const evidence = (r.evidence || []).slice(0, 15).map((e) =>
    `<li><b>${esc(e.category)}</b> (${esc(e.severity)}): ${esc(e.description)}</li>`
  ).join("");
  return `<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><title>ForensAI</title>
<style>body{font-family:Arial,sans-serif;padding:24px;max-width:800px;margin:0 auto}
h1{font-size:22px}h2{font-size:14px;margin-top:20px;color:#444}.meta{color:#666;font-size:12px}
.scores{display:flex;gap:16px;margin:12px 0}ul{padding-left:18px;font-size:13px}</style></head><body>
<h1>${esc(r.verdict_label)}</h1>
<p class="meta">${esc(data.filename || "")} · ${esc(r.analysis_mode || "")} · уверенность ${r.confidence}%</p>
<div class="scores"><span>AI ${r.scores?.ai ?? 0}</span><span>PL ${r.scores?.plagiarism ?? 0}</span><span>AUTH ${r.scores?.authenticity ?? 0}</span></div>
<h2>Резюме</h2><p>${esc(reason.summary || "")}</p>
<h2>Анализ ИИ</h2><p>${esc(reason.ai_analysis || "")}</p>
<h2>Заключение</h2><p>${esc(reason.conclusion || "")}</p>
${zones ? `<h2>Зоны</h2><p>${zones}</p>` : ""}
${evidence ? `<h2>Улики</h2><ul>${evidence}</ul>` : ""}
<p class="meta">ForensAI · ${new Date().toLocaleString("ru-RU")}</p></body></html>`;
}

function exportPdf() {
  if (!lastReportData && !lastCompareData) {
    showError(tr("error.runFirst"));
    return;
  }
  const data = lastCompareData || lastReportData;
  const w = window.open("", "_blank");
  if (!w) {
    showError(tr("error.popup"));
    return;
  }
  if (lastCompareData) {
    const c = lastCompareData.comparison;
    const html = buildPrintHtml({ report: lastCompareData.report_a, filename: lastCompareData.filename_a });
    const html2 = buildPrintHtml({ report: lastCompareData.report_b, filename: lastCompareData.filename_b });
    w.document.write(html + `<hr><h2>Сравнение</h2><p>${esc(c?.summary || "")}</p>` + html2);
  } else {
    w.document.write(buildPrintHtml(lastReportData));
  }
  w.document.close();
  w.onload = () => setTimeout(() => w.print(), 300);
}

function renderReport(data, opts = {}) {
  lastReportData = data;
  if (!opts.preserveCompare) lastCompareData = null;
  const r = data.report;
  if (!opts.preserveCompare) $("#compareSection")?.classList.add("hidden");
  if (r.content_type === "image" || r.content_type === "video") syncVerdictFromScores(r);

  emptyState.classList.add("hidden");
  report.classList.remove("hidden");

  const card = $("#verdictCard");
  const vMap = {
    ai_generated: "verdict-hero--ai",
    human_created: "verdict-hero--human",
    hybrid: "verdict-hero--hybrid",
  };
  card.classList.remove("verdict-hero--ai", "verdict-hero--human", "verdict-hero--hybrid", "kpi--verdict--ai", "kpi--verdict--human", "kpi--verdict--hybrid");
  card.classList.add(vMap[r.verdict] || "verdict-hero--hybrid");

  const reportId = $("#reportId");
  if (reportId) {
    const d = new Date();
    reportId.textContent = `EXP-${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}-${String(d.getHours()).padStart(2, "0")}${String(d.getMinutes()).padStart(2, "0")}`;
  }

  $("#verdictLabel").textContent = I18n.verdictLabel(r.verdict, r.verdict_label);
  const confEl = $("#confidenceValue");
  const confTarget = r.confidence;
  const cStart = performance.now();
  const cTick = (now) => {
    const p = Math.min(1, (now - cStart) / 700);
    confEl.textContent = `${Math.round(confTarget * (1 - (1 - p) ** 3))}%`;
    if (p < 1) requestAnimationFrame(cTick);
  };
  requestAnimationFrame(cTick);
  $("#confidenceFill").style.width = `${r.confidence}%`;

  const scores = r.scores || {};
  animateCounter($("#aiScore"), scores.ai ?? 0);
  animateCounter($("#plagiarismScore"), scores.plagiarism ?? 0);
  animateCounter($("#authScore"), scores.authenticity ?? r.metrics?.authenticity ?? 0);
  setTimeout(() => {
    $("#aiScoreBar").style.width = `${scores.ai ?? 0}%`;
    $("#plagiarismScoreBar").style.width = `${scores.plagiarism ?? 0}%`;
    $("#authScoreBar").style.width = `${scores.authenticity ?? 0}%`;
  }, 100);

  const modeLabels = {
    gemini: tr("mode.gemini"),
    openai: tr("mode.openai"),
    heuristics_only: tr("mode.heuristics"),
    forensics_local: tr("mode.local"),
    forensics_fallback: tr("mode.fallback"),
  };
  $("#analysisMode").textContent = modeLabels[r.analysis_mode] || r.analysis_mode;

  renderMetrics(r.metrics);
  renderCategories(r.category_scores);
  renderZones(r.zones);
  renderReasoning(r);
  renderSegments(r.segments, r.content_type);
  renderTextMap(lastAnalyzedText, r.segments, r.content_type);
  const fw = r.forensics?.metrics?.width || r.metrics?.width;
  const fh = r.forensics?.metrics?.height || r.metrics?.height;
  renderMediaPreview(selectedFile, r.zones, fw, fh);
  renderVideoTimeline(r.frames, r.content_type);
  renderOsint(r.osint, r.content_type);

  const list = $("#evidenceList");
  list.innerHTML = "";
  if (r.evidence?.length) {
    r.evidence.forEach((item) => {
      const li = document.createElement("li");
      li.className = `evidence-item evidence-item--${item.severity || "minor"}`;
      li.innerHTML = `
        <div class="evidence-item__cat">${esc(I18n.translateEvidenceCategory(item.category))} · ${esc(I18n.severityLabel(item.severity || "minor"))}</div>
        <div class="evidence-item__desc">${esc(I18n.translateLine(item.description))}</div>
        ${item.location ? `<div class="evidence-item__loc">${esc(I18n.translateLine(item.location))}</div>` : ""}
      `;
      list.appendChild(li);
    });
  } else {
    list.innerHTML = `<li class="evidence-item">${tr("evidence.none")}</li>`;
  }
  Account?.saveHistory?.(data);
}

function renderCompareReport(data) {
  lastCompareData = data;
  emptyState.classList.add("hidden");
  report.classList.remove("hidden");
  renderCompare(data.comparison, data.report_a, data.report_b, data.filename_a, data.filename_b);
  renderReport(
    { ok: true, filename: `${data.filename_a} + ${data.filename_b}`, report: data.report_a },
    { preserveCompare: true },
  );
  const hero = $("#verdictLabel");
  if (hero) hero.textContent = tr("verdict.compareTitle");
  $("#confidenceValue").textContent = data.comparison?.verdict_match
    ? tr("verdict.match")
    : tr("verdict.deltaAi", { n: data.comparison?.ai_delta ?? 0 });
  $("#confidenceFill").style.width = "100%";
  const card = $("#verdictCard");
  card?.classList.remove("verdict-hero--ai", "verdict-hero--human", "verdict-hero--hybrid");
  card?.classList.add("verdict-hero--hybrid");
  $("#analysisMode").textContent = tr("mode.compare");
}

function compareWithProgress(form) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/compare");
    const headers = window.Account?.apiHeaders?.() || {};
    Object.entries(headers).forEach(([k, v]) => xhr.setRequestHeader(k, v));
    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable && e.total > 0) {
        const uploadPct = Math.min(40, (e.loaded / e.total) * 40);
        setProgress(uploadPct, `Загрузка… ${Math.round((e.loaded / e.total) * 100)}%`);
      }
    });
    xhr.addEventListener("load", () => {
      try {
        const data = JSON.parse(xhr.responseText);
        if (xhr.status >= 200 && xhr.status < 300) {
          Account?.onAnalyzeResponse?.(data);
          resolve(data);
        } else if (xhr.status === 401) {
          window.Auth?.openModal?.("signin");
          reject(new Error(tr("error.auth")));
        } else if (xhr.status === 402) reject(new Error(tr("error.limit")));
        else reject(new Error(data.detail || tr("error.analyze")));
      } catch {
        reject(new Error(tr("error.server")));
      }
    });
    xhr.addEventListener("error", () => reject(new Error(tr("error.network"))));
    xhr.send(form);
  });
}

document.addEventListener("click", (e) => {
  if (e.target?.id === "exportPdfBtn" || e.target?.closest?.("#exportPdfBtn")) {
    exportPdf();
    return;
  }
  if (e.target?.id === "exportBtn" || e.target?.closest?.("#exportBtn")) {
    const payload = lastCompareData || lastReportData;
    if (!payload) { showError(tr("error.runFirst")); return; }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `forensai-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }
});

function initAnalyzeButton() {
  analyzeBtn = $("#analyzeBtn");
  if (!analyzeBtn) return;
  analyzeBtn.addEventListener("click", onAnalyzeClick);
}

async function onAnalyzeClick() {
  if (window.Auth?.isEnabled?.() && !window.Auth?.requireAuth?.()) return;

  lastAnalyzedText = "";
  analyzeBtn.disabled = true;
  loading.classList.remove("hidden");

  try {
    if (activeTab === "batch") {
      if (!batchFiles.length) {
        showError(tr("error.pickFile"));
        return;
      }
      startAnalysisProgress("image");
      for (let i = 0; i < batchFiles.length; i++) {
        if (!Account?.canAnalyze?.()) {
          showError(tr("error.limit"));
          break;
        }
        const f = batchFiles[i];
        selectedFile = f;
        setProgress(((i + 0.5) / batchFiles.length) * 90, tr("batch.done", { done: i + 1, total: batchFiles.length }));
        const form = new FormData();
        form.append("file", f);
        const ct = f.type?.startsWith("video/") ? "video" : f.type?.startsWith("image/") ? "image" : "text";
        const data = await analyzeWithProgress(form, ct);
        renderReport(data);
      }
      stopProgress(true);
      await new Promise((r) => setTimeout(r, 350));
      return;
    }

    if (activeTab === "compare") {
      if (!selectedFileA || !selectedFileB) {
        showError(tr("error.pickBoth"));
        return;
      }
      const acc = Account?.account;
      if (acc?.plan !== "pro" && (acc?.analyses_remaining ?? 0) < 2) {
        showError(tr("error.limit"));
        return;
      }
      const form = new FormData();
      form.append("file_a", selectedFileA);
      form.append("file_b", selectedFileB);
      startAnalysisProgress("image");
      setProgress(5, tr("upload.fileA"));
      const data = await compareWithProgress(form);
      stopProgress(true);
      await new Promise((r) => setTimeout(r, 350));
      renderCompareReport(data);
      return;
    }

    const form = new FormData();
    if (activeTab === "file") {
      if (!selectedFile) { showError(tr("error.pickFile")); return; }
      if (!Account?.canAnalyze?.()) { showError(tr("error.limit")); return; }
      form.append("file", selectedFile);
      if (selectedFile.type.startsWith("text/") || /\.(txt|md|csv)$/i.test(selectedFile.name)) {
        lastAnalyzedText = await selectedFile.text();
      }
    } else {
      const text = textInput?.value?.trim() || "";
      if (!text) { showError(tr("error.enterText")); return; }
      if (!Account?.canAnalyze?.()) { showError(tr("error.limit")); return; }
      form.append("text", text);
      lastAnalyzedText = text;
    }

    const contentType =
      activeTab === "text" ? "text"
        : selectedFile?.type?.startsWith("video/") ? "video"
          : selectedFile?.type?.startsWith("image/") ? "image"
            : "text";

    startAnalysisProgress(contentType);
    const data = await analyzeWithProgress(form, contentType);
    stopProgress(true);
    await new Promise((r) => setTimeout(r, 350));
    renderReport(data);
  } catch (err) {
    stopProgress(false);
    showError(err.message);
  } finally {
    analyzeBtn.disabled = false;
    loading.classList.add("hidden");
    setProgress(0, "");
  }
}

function boot() {
  initAppShell();
  initAnalyzeButton();
  loadStatus();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
