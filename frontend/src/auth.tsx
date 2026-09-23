import { FormEvent, ReactNode, useEffect, useState } from "react";
import { apiFetch, AUTH_REQUIRED_EVENT } from "./api";

type State = "checking" | "open" | "signed-in" | "login" | "unavailable";

export function AuthGate({ children }: { children: ReactNode }) {
  const [state, setState] = useState<State>("checking");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    apiFetch("/auth/status")
      .then(async (r) => {
        const data = await r.json().catch(() => ({}));
        if (r.status === 503) {
          setMessage(typeof data.detail === "string" ? data.detail : "");
          setState("unavailable");
        } else if (r.ok && data.enabled === true) {
          setState(data.authenticated ? "signed-in" : "login");
        } else setState("open");
      })
      // Older or unreachable backend: the app itself reports the connection error.
      .catch(() => setState("open"));
    const expired = () => {
      setMessage("Relácia vypršala. Prihláste sa znova.");
      setState("login");
    };
    window.addEventListener(AUTH_REQUIRED_EVENT, expired);
    return () => window.removeEventListener(AUTH_REQUIRED_EVENT, expired);
  }, []);

  async function login(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const r = await apiFetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      if (!r.ok) {
        const data = await r.json().catch(() => ({}));
        setMessage(typeof data.detail === "string" ? data.detail : "Prihlásenie zlyhalo.");
        return;
      }
      setPassword("");
      setState("signed-in");
    } catch {
      setMessage("Server nie je dostupný.");
    } finally {
      setBusy(false);
    }
  }

  async function logout() {
    await apiFetch("/auth/logout", { method: "POST" }).catch(() => undefined);
    setMessage("");
    setState("login");
  }

  if (state === "checking") return <p role="status">Načítavam…</p>;
  if (state === "unavailable")
    return (
      <main>
        <h1>Platobné údaje pre dane</h1>
        <p role="alert">{message || "Aplikácia nie je nakonfigurovaná."}</p>
      </main>
    );
  if (state === "login")
    return (
      <main>
        <h1>Platobné údaje pre dane</h1>
        <form onSubmit={login}>
          <label>
            Heslo
            <input
              aria-label="Heslo"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <button disabled={busy || !password}>{busy ? "Prihlasujem…" : "Prihlásiť sa"}</button>
        </form>
        {message && <p role="alert">{message}</p>}
      </main>
    );
  return (
    <>
      {state === "signed-in" && (
        <div className="actions">
          <button type="button" onClick={logout}>
            Odhlásiť sa
          </button>
        </div>
      )}
      {children}
    </>
  );
}
