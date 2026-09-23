import { FormEvent, ReactNode, useEffect, useState } from "react";
import { apiFetch, AUTH_REQUIRED_EVENT } from "./api";

type State = "checking" | "open" | "signed-in" | "login" | "unavailable";
type Provider = "password" | "entra";

// Azure App Service authentication (Easy Auth) endpoints for Microsoft Entra ID.
export const ENTRA_LOGIN_URL = "/.auth/login/aad?post_login_redirect_uri=/";
export const ENTRA_LOGOUT_URL = "/.auth/logout?post_logout_redirect_uri=/";

export function AuthGate({ children }: { children: ReactNode }) {
  const [state, setState] = useState<State>("checking");
  const [provider, setProvider] = useState<Provider>("password");
  const [user, setUser] = useState("");
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
          setProvider(data.provider === "entra" ? "entra" : "password");
          setUser(typeof data.user === "string" ? data.user : "");
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
  if (state === "login" && provider === "entra")
    return (
      <main>
        <h1>Platobné údaje pre dane</h1>
        <p>Aplikácia je dostupná iba pre firemné účty Microsoft.</p>
        <p>
          <a className="button" href={ENTRA_LOGIN_URL}>
            Prihlásiť sa účtom Microsoft
          </a>
        </p>
        {message && <p role="alert">{message}</p>}
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
          {user && <span>Prihlásený: {user}</span>}
          {provider === "entra" ? (
            <a className="button" href={ENTRA_LOGOUT_URL}>
              Odhlásiť sa
            </a>
          ) : (
            <button type="button" onClick={logout}>
              Odhlásiť sa
            </button>
          )}
        </div>
      )}
      {children}
    </>
  );
}
