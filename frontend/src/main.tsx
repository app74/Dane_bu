import { FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Subject = { id: number; name: string; oud: string };
type Rule = { id: string; name: string };
type Preview = {
  subject_name: string;
  oud: string;
  domestic_account: string;
  iban: string;
  variable_symbol: string;
  amount: string;
  currency: string;
  due_date: string | null;
  rule_name: string;
  source_url: string;
  last_verified: string;
  warning: string;
};
const API = "http://127.0.0.1:8000";

export function App() {
  const [subjects, setSubjects] = useState<Subject[]>([]),
    [rules, setRules] = useState<Rule[]>([]);
  const [subjectId, setSubjectId] = useState(""),
    [ruleId, setRuleId] = useState(""),
    [name, setName] = useState(""),
    [oud, setOud] = useState(""),
    [amount, setAmount] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null),
    [error, setError] = useState(""),
    [history, setHistory] = useState<Preview[]>([]),
    [saved, setSaved] = useState(false);
  useEffect(() => {
    Promise.all([
      fetch(`${API}/subjects`).then((r) => r.json()),
      fetch(`${API}/tax-rules`).then((r) => r.json()),
      fetch(`${API}/payment-instructions`).then((r) => r.json()),
    ])
      .then(([s, r, h]) => {
        setSubjects(s);
        setRules(r);
        setHistory(h);
        if (s[0]) setSubjectId(String(s[0].id));
        if (r[0]) setRuleId(r[0].id);
      })
      .catch(() => setError("Backend nie je dostupný. Spustite FastAPI na porte 8000."));
  }, []);
  async function addSubject(e: FormEvent) {
    e.preventDefault();
    const r = await fetch(`${API}/subjects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, oud }),
    });
    if (!r.ok) {
      setError("Skontrolujte názov a 10-miestny OÚD.");
      return;
    }
    const s = await r.json();
    setSubjects((x) => [...x, s]);
    setSubjectId(String(s.id));
    setName("");
    setOud("");
  }
  async function updateSubject() {
    const r = await fetch(`${API}/subjects/${subjectId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, oud }),
    });
    if (!r.ok) {
      setError("Subjekt sa nepodarilo upraviť.");
      return;
    }
    const updated = await r.json();
    setSubjects((items) => items.map((item) => (item.id === updated.id ? updated : item)));
  }
  async function removeSubject() {
    const r = await fetch(`${API}/subjects/${subjectId}`, { method: "DELETE" });
    if (!r.ok) {
      setError("Subjekt sa nepodarilo odstrániť.");
      return;
    }
    setSubjects((items) => items.filter((item) => String(item.id) !== subjectId));
    setSubjectId("");
    setName("");
    setOud("");
  }
  async function createPreview(e: FormEvent) {
    e.preventDefault();
    setError("");
    const r = await fetch(`${API}/payment-instructions/preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subject_id: Number(subjectId), rule_id: ruleId, amount }),
    });
    if (!r.ok) {
      setError((await r.json()).detail ?? "Náhľad sa nepodarilo vytvoriť.");
      return;
    }
    setPreview(await r.json());
    setSaved(false);
  }
  async function savePreview() {
    const r = await fetch(`${API}/payment-instructions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subject_id: Number(subjectId), rule_id: ruleId, amount }),
    });
    if (!r.ok) {
      setError("Inštrukciu sa nepodarilo uložiť.");
      return;
    }
    const savedInstruction = await r.json();
    setHistory((items) => [savedInstruction, ...items]);
    setSaved(true);
  }
  async function copy(value: string) {
    await navigator.clipboard.writeText(value);
  }
  function exportPreview() {
    if (!preview) return;
    const text = [
      "Platobné údaje pre slovenské dane",
      `Subjekt: ${preview.subject_name}`,
      `OÚD: ${preview.oud}`,
      `Pravidlo: ${preview.rule_name}`,
      `Účet: ${preview.domestic_account}`,
      `IBAN: ${preview.iban}`,
      `Variabilný symbol: ${preview.variable_symbol}`,
      `Suma: ${preview.amount} ${preview.currency}`,
      `Splatnosť: ${preview.due_date ?? "neurčená"}`,
      `Zdroj: ${preview.source_url}`,
      `Overené: ${preview.last_verified}`,
      `Upozornenie: ${preview.warning}`,
    ].join("\n");
    const url = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "platobne-udaje.txt";
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }
  return (
    <main>
      <h1>Platobné údaje pre dane</h1>
      <p>Pripravte si kontrolovateľné údaje k úhrade dane.</p>
      <section>
        <h2>1. Daňový subjekt</h2>
        <form onSubmit={addSubject} className="inline-form">
          <input
            aria-label="Názov subjektu"
            placeholder="Názov subjektu"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            aria-label="OÚD"
            placeholder="OÚD (10 číslic)"
            value={oud}
            onChange={(e) => setOud(e.target.value)}
          />
          <button>Uložiť subjekt</button>
        </form>
        <label>
          Vybraný subjekt
          <select
            value={subjectId}
            onChange={(e) => {
              const id = e.target.value;
              const selected = subjects.find((item) => String(item.id) === id);
              setSubjectId(id);
              setName(selected?.name ?? "");
              setOud(selected?.oud ?? "");
            }}
          >
            <option value="">Vyberte subjekt</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.oud})
              </option>
            ))}
          </select>
        </label>
        <div className="actions">
          <button type="button" onClick={updateSubject} disabled={!subjectId || !name || !oud}>
            Upraviť subjekt
          </button>
          <button type="button" onClick={removeSubject} disabled={!subjectId}>
            Odstrániť subjekt
          </button>
        </div>
      </section>
      <section>
        <h2>2. Platba</h2>
        <form onSubmit={createPreview}>
          <label>
            Potvrdené pravidlo
            <select value={ruleId} onChange={(e) => setRuleId(e.target.value)}>
              {rules.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Suma v EUR
            <input
              aria-label="Suma v EUR"
              inputMode="decimal"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="100,00"
            />
          </label>
          <button disabled={!subjectId || !ruleId || !amount}>Vytvoriť náhľad</button>
        </form>
      </section>
      {error && (
        <div role="alert" className="error">
          {error}
        </div>
      )}
      {preview && (
        <section className="result">
          <h2>Kontrolný náhľad</h2>
          <dl>
            <dt>Účet</dt>
            <dd>{preview.domestic_account}</dd>
            <dt>IBAN</dt>
            <dd>
              {preview.iban}{" "}
              <button type="button" className="small-button" onClick={() => copy(preview.iban)}>
                Kopírovať
              </button>
            </dd>
            <dt>Variabilný symbol</dt>
            <dd>
              {preview.variable_symbol}{" "}
              <button
                type="button"
                className="small-button"
                onClick={() => copy(preview.variable_symbol)}
              >
                Kopírovať
              </button>
            </dd>
            <dt>Suma</dt>
            <dd>{preview.amount} EUR</dd>
            <dt>Splatnosť</dt>
            <dd>{preview.due_date ?? "neurčená"}</dd>
            <dt>Pravidlo</dt>
            <dd>{preview.rule_name}</dd>
          </dl>
          <p>
            <a href={preview.source_url} target="_blank" rel="noreferrer">
              Oficiálny zdroj pravidla
            </a>
          </p>
          <div role="alert" className="warning">
            {preview.warning}
          </div>
          <button type="button" onClick={() => window.print()}>
            Tlačiť náhľad
          </button>
          <button type="button" onClick={exportPreview}>
            Exportovať TXT
          </button>
          <button type="button" onClick={savePreview} disabled={saved}>
            {saved ? "Uložené v histórii" : "Uložiť do histórie"}
          </button>
        </section>
      )}
      {history.length > 0 && (
        <section>
          <h2>História</h2>
          <ul>
            {history.slice(0, 10).map((item, index) => (
              <li key={`${item.variable_symbol}-${index}`}>
                {item.rule_name} – {item.amount} EUR – VS {item.variable_symbol}
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
const root = document.getElementById("root");
if (root) createRoot(root).render(<App />);
