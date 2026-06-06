/* Аккаунт, подписка, рефералы, история */
(function () {
  const USER_KEY = "forensai_user_id";
  const HIST_KEY = "forensai_history";
  const MAX_HIST = 30;

  let account = null;

  function t(k, v) {
    return window.I18n?.t(k, v) ?? k;
  }

  function getUserId() {
    let id = localStorage.getItem(USER_KEY);
    if (!id) {
      id = crypto.randomUUID?.() || `u-${Date.now()}-${Math.random().toString(16).slice(2)}`;
      localStorage.setItem(USER_KEY, id);
    }
    return id;
  }

  function apiHeaders() {
    return { "X-User-Id": getUserId(), Accept: "application/json" };
  }

  async function init() {
    const ref = localStorage.getItem("forensai_pending_ref");
    const body = ref ? JSON.stringify({ referral_code: ref }) : "{}";
    if (ref) localStorage.removeItem("forensai_pending_ref");
    try {
      const res = await fetch("/api/account/init", {
        method: "POST",
        headers: { ...apiHeaders(), "Content-Type": "application/json" },
        body,
      });
      const data = await res.json();
      if (data.account) account = data.account;
    } catch {
      /* offline */
    }
    updateQuotaBadge();
  }

  async function refresh() {
    try {
      const res = await fetch("/api/account", { headers: apiHeaders() });
      const data = await res.json();
      if (data.account) account = data.account;
      updateQuotaBadge();
      return account;
    } catch {
      return account;
    }
  }

  function updateQuotaBadge() {
    const el = document.getElementById("quotaBadge");
    if (!el || !account) return;
    const plan = account.plan === "pro" ? "Pro" : t("sub.free");
    const left = account.plan === "pro" ? "∞" : account.analyses_remaining;
    el.textContent = t("quota.badge", { plan, left });
    el.classList.toggle("quota-badge--pro", account.plan === "pro");
  }

  function canAnalyze() {
    if (!account) return true;
    return account.plan === "pro" || account.analyses_remaining > 0;
  }

  function onAnalyzeResponse(data) {
    if (data?.account) {
      account = data.account;
      updateQuotaBadge();
    }
  }

  function saveHistory(entry) {
    try {
      const list = JSON.parse(localStorage.getItem(HIST_KEY) || "[]");
      list.unshift({
        id: Date.now(),
        at: new Date().toISOString(),
        filename: entry.filename,
        verdict: entry.report?.verdict,
        verdict_label: entry.report?.verdict_label,
        ai: entry.report?.scores?.ai,
        data: entry,
      });
      localStorage.setItem(HIST_KEY, JSON.stringify(list.slice(0, MAX_HIST)));
    } catch {
      /* ignore */
    }
  }

  function loadHistory() {
    try {
      return JSON.parse(localStorage.getItem(HIST_KEY) || "[]");
    } catch {
      return [];
    }
  }

  function clearHistory() {
    localStorage.removeItem(HIST_KEY);
  }

  function openModal(id) {
    document.getElementById(id)?.classList.remove("hidden");
  }

  function closeModal(id) {
    document.getElementById(id)?.classList.add("hidden");
  }

  function renderSubscriptionModal() {
    const acc = account || {};
    const planEl = document.getElementById("subPlanName");
    const priceEl = document.getElementById("subPrice");
    const remainEl = document.getElementById("subRemaining");
    const discEl = document.getElementById("subDiscount");
    const btn = document.getElementById("upgradeBtn");

    if (planEl) planEl.textContent = acc.plan === "pro" ? t("sub.pro") : t("sub.free");
    if (priceEl) {
      priceEl.textContent = acc.plan === "pro"
        ? t("sub.active")
        : `$${acc.pro_price_discounted_usd ?? 9.99}${t("sub.perMonth")}`;
    }
    if (remainEl) {
      remainEl.textContent = acc.plan === "pro"
        ? t("sub.unlimited")
        : t("sub.remaining", { n: acc.analyses_remaining ?? 0 });
    }
    if (discEl) discEl.textContent = t("sub.discount", { n: acc.discount_percent ?? 0 });
    if (btn) {
      btn.disabled = acc.plan === "pro";
      btn.textContent = acc.plan === "pro" ? t("sub.active") : t("sub.upgrade");
    }
  }

  function renderReferralModal() {
    const acc = account || {};
    const pct = 15;
    const desc = document.getElementById("refDesc");
    if (desc) desc.textContent = t("ref.desc", { n: pct });
    const code = document.getElementById("refCode");
    const link = document.getElementById("refLink");
    const verified = document.getElementById("refVerified");
    const base = location.origin + location.pathname;
    const c = acc.referral_code || "--------";
    if (code) code.textContent = c;
    if (link) link.value = `${base}?ref=${c}`;
    if (verified) verified.textContent = t("ref.verified", { n: acc.referrals_verified ?? 0 });
  }

  function renderHistoryModal() {
    const list = document.getElementById("historyList");
    if (!list) return;
    const items = loadHistory();
    if (!items.length) {
      list.innerHTML = `<p class="modal-muted">${t("hist.empty")}</p>`;
      return;
    }
    list.innerHTML = items.map((h) => `
      <div class="hist-item">
        <div>
          <strong>${h.filename || "—"}</strong>
          <span class="modal-muted">${new Date(h.at).toLocaleString()}</span>
        </div>
        <div>${h.verdict_label || "—"} · AI ${h.ai ?? 0}</div>
        <button type="button" class="btn-outline btn--sm hist-open" data-id="${h.id}">${t("hist.open")}</button>
      </div>
    `).join("");
    list.querySelectorAll(".hist-open").forEach((btn) => {
      btn.addEventListener("click", () => {
        const item = items.find((x) => x.id === Number(btn.dataset.id));
        if (item?.data) {
          closeModal("modalHistory");
          window.dispatchEvent(new CustomEvent("forensai:openReport", { detail: item.data }));
        }
      });
    });
  }

  function bindUi() {
    document.getElementById("navPro")?.addEventListener("click", () => {
      renderSubscriptionModal();
      openModal("modalSub");
    });
    document.getElementById("navReferral")?.addEventListener("click", () => {
      renderReferralModal();
      openModal("modalReferral");
    });
    document.getElementById("navHistory")?.addEventListener("click", () => {
      renderHistoryModal();
      openModal("modalHistory");
    });
    document.querySelectorAll(".modal-close, .modal-backdrop").forEach((el) => {
      el.addEventListener("click", (e) => {
        const modal = e.target.closest(".modal");
        if (modal) modal.classList.add("hidden");
      });
    });
    document.getElementById("themeToggle")?.addEventListener("click", () => I18n.toggleTheme());
    document.querySelectorAll(".lang-btn").forEach((btn) => {
      btn.addEventListener("click", () => I18n.setLang(btn.dataset.lang));
    });
    window.addEventListener("forensai:lang", () => {
      updateQuotaBadge();
      renderSubscriptionModal();
      renderReferralModal();
    });

    document.getElementById("upgradeBtn")?.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/subscription/upgrade", {
          method: "POST",
          headers: { ...apiHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({ plan: "pro" }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "error");
        account = data.account;
        updateQuotaBadge();
        renderSubscriptionModal();
      } catch (e) {
        alert(e.message);
      }
    });

    document.getElementById("copyRefLink")?.addEventListener("click", () => {
      const inp = document.getElementById("refLink");
      inp?.select();
      navigator.clipboard?.writeText(inp?.value || "").then(() => alert(t("ref.copied")));
    });

    document.getElementById("applyRefBtn")?.addEventListener("click", async () => {
      const code = document.getElementById("refInput")?.value?.trim();
      if (!code) return;
      const res = await fetch("/api/account/referral", {
        method: "POST",
        headers: { ...apiHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ referral_code: code }),
      });
      const data = await res.json();
      if (res.ok) {
        account = data.account;
        updateQuotaBadge();
        renderReferralModal();
      }
    });

    document.getElementById("clearHistoryBtn")?.addEventListener("click", () => {
      clearHistory();
      renderHistoryModal();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    I18n.applyDom();
    bindUi();
    init();
  });

  window.Account = {
    getUserId,
    apiHeaders,
    refresh,
    canAnalyze,
    onAnalyzeResponse,
    saveHistory,
    get account() {
      return account;
    },
  };
})();
