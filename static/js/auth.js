/* Supabase authentication */
(function () {
  let enabled = false;
  let client = null;
  let session = null;

  function t(k, v) {
    return window.I18n?.t(k, v) ?? k;
  }

  async function init() {
    try {
      const res = await fetch("/api/config");
      const cfg = await res.json();
      if (!cfg.auth_enabled || !cfg.supabase_url || !cfg.supabase_anon_key) {
        enabled = false;
        return false;
      }
      if (!window.supabase?.createClient) {
        console.warn("Supabase JS SDK not loaded");
        return false;
      }
      client = window.supabase.createClient(cfg.supabase_url, cfg.supabase_anon_key);
      enabled = true;
      const { data } = await client.auth.getSession();
      session = data.session;
      client.auth.onAuthStateChange((_event, s) => {
        session = s;
        updateAuthUi();
        window.dispatchEvent(new CustomEvent("forensai:auth", { detail: s }));
      });
      updateAuthUi();
      return true;
    } catch {
      enabled = false;
      return false;
    }
  }

  function isEnabled() {
    return enabled;
  }

  function isLoggedIn() {
    return Boolean(session?.access_token);
  }

  function getToken() {
    return session?.access_token || null;
  }

  function getUser() {
    return session?.user || null;
  }

  function updateAuthUi() {
    const btn = document.getElementById("navAuth");
    const label = document.getElementById("authUserLabel");
    if (!btn) return;
    if (!enabled) {
      btn.classList.add("hidden");
      return;
    }
    btn.classList.remove("hidden");
    if (isLoggedIn()) {
      const email = session.user.email || t("auth.user");
      btn.textContent = t("auth.logout");
      btn.dataset.mode = "logout";
      if (label) {
        label.textContent = email;
        label.classList.remove("hidden");
      }
    } else {
      btn.textContent = t("auth.login");
      btn.dataset.mode = "login";
      if (label) label.classList.add("hidden");
    }
  }

  function openModal(tab = "signin") {
    document.getElementById("modalAuth")?.classList.remove("hidden");
    switchTab(tab);
    const err = document.getElementById("authError");
    if (err) err.textContent = "";
  }

  function closeModal() {
    document.getElementById("modalAuth")?.classList.add("hidden");
  }

  function switchTab(tab) {
    document.querySelectorAll(".auth-tab").forEach((el) => {
      el.classList.toggle("active", el.dataset.tab === tab);
    });
    document.getElementById("authSignIn")?.classList.toggle("hidden", tab !== "signin");
    document.getElementById("authSignUp")?.classList.toggle("hidden", tab !== "signup");
  }

  function showError(msg) {
    const el = document.getElementById("authError");
    if (el) el.textContent = msg || "";
  }

  async function signIn(email, password) {
    if (!client) return { error: { message: "auth_unavailable" } };
    return client.auth.signInWithPassword({ email, password });
  }

  async function signUp(email, password) {
    if (!client) return { error: { message: "auth_unavailable" } };
    return client.auth.signUp({ email, password });
  }

  async function signInGoogle() {
    if (!client) return { error: { message: "auth_unavailable" } };
    return client.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: window.location.origin + window.location.pathname },
    });
  }

  async function signOut() {
    if (!client) return;
    await client.auth.signOut();
    session = null;
    updateAuthUi();
    window.dispatchEvent(new CustomEvent("forensai:auth", { detail: null }));
  }

  function requireAuth() {
    if (!enabled || isLoggedIn()) return true;
    openModal("signin");
    return false;
  }

  function bindUi() {
    document.getElementById("navAuth")?.addEventListener("click", async () => {
      if (!enabled) return;
      if (isLoggedIn()) {
        await signOut();
        await window.Account?.refresh?.();
      } else {
        openModal("signin");
      }
    });

    document.querySelectorAll(".auth-tab").forEach((btn) => {
      btn.addEventListener("click", () => switchTab(btn.dataset.tab));
    });

    document.getElementById("authSignInBtn")?.addEventListener("click", async () => {
      const email = document.getElementById("authEmailIn")?.value?.trim();
      const password = document.getElementById("authPasswordIn")?.value || "";
      if (!email || !password) {
        showError(t("auth.fillFields"));
        return;
      }
      const { error } = await signIn(email, password);
      if (error) {
        showError(error.message);
        return;
      }
      closeModal();
      await window.Account?.init?.();
    });

    document.getElementById("authSignUpBtn")?.addEventListener("click", async () => {
      const email = document.getElementById("authEmailUp")?.value?.trim();
      const password = document.getElementById("authPasswordUp")?.value || "";
      if (!email || !password) {
        showError(t("auth.fillFields"));
        return;
      }
      const { data, error } = await signUp(email, password);
      if (error) {
        showError(error.message);
        return;
      }
      if (data.session) {
        closeModal();
        await window.Account?.init?.();
      } else {
        showError(t("auth.checkEmail"));
      }
    });

    document.getElementById("authGoogleBtn")?.addEventListener("click", async () => {
      const { error } = await signInGoogle();
      if (error) showError(error.message);
    });

    document.querySelector("#modalAuth .modal-close")?.addEventListener("click", closeModal);
    document.querySelector("#modalAuth .modal-backdrop")?.addEventListener("click", closeModal);
  }

  document.addEventListener("DOMContentLoaded", async () => {
    bindUi();
    await init();
    window.dispatchEvent(new CustomEvent("forensai:auth-ready"));
  });

  window.Auth = {
    init,
    isEnabled,
    isLoggedIn,
    getToken,
    getUser,
    requireAuth,
    openModal,
    signOut,
  };
})();
