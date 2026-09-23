import { FormEvent, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import QRCode from "qrcode";
import { CurrencyCode, encode as encodePay, PaymentOptions } from "bysquare/pay";
import "./styles.css";

type Subject = {
  id: number;
  name: string;
  oud: string;
  ico?: string | null;
  dic?: string | null;
  ic_dph?: string | null;
};
type LookupResult = {
  name: string;
  oud: string | null;
  ico: string | null;
  dic: string | null;
  ic_dph: string | null;
  address: string;
};
type LookupResponse = {
  results: LookupResult[];
  source_url: string;
  registry_date: string;
  accounts_date: string;
};
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
  const savingSubjectRef = useRef(false);
  const [savingSubject, setSavingSubject] = useState(false);
  const [subjectNotice, setSubjectNotice] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [lookup, setLookup] = useState<LookupResponse | null>(null);
  const [lookingUp, setLookingUp] = useState(false);
  const [lookupError, setLookupError] = useState("");
  const [ico, setIco] = useState("");
  const [dic, setDic] = useState("");
  const [icDph, setIcDph] = useState<string | null>(null);
  async function searchSubject(e: FormEvent) {
    e.preventDefault();
    setLookingUp(true);
    setLookup(null);
    setLookupError("");
    try {
      const response = await fetch(`${API}/subject-lookup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier: identifier.trim() }),
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(typeof data.detail === "string" ? data.detail : "Vyhľadanie zlyhalo.");
      setLookup(data);
    } catch (error) {
      setLookupError(error instanceof Error ? error.message : "Vyhľadanie zlyhalo.");
    } finally {
      setLookingUp(false);
    }
  }
  function chooseSubject(result: LookupResult) {
    setName(result.name);
    setOud(result.oud ?? "");
    setIco(result.ico ?? "");
    setDic(result.dic ?? "");
    setIcDph(result.ic_dph ?? null);
    setSubjectId("");
    setPreview(null);
    setError("");
  }
  const [subjects, setSubjects] = useState<Subject[]>([]),
    [rules, setRules] = useState<Rule[]>([]);
  const [subjectId, setSubjectId] = useState(""),
    [ruleId, setRuleId] = useState(""),
    [name, setName] = useState(""),
    [oud, setOud] = useState(""),
    [amount, setAmount] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null),
    [showPrintPreview, setShowPrintPreview] = useState(false),
    [qrDataUrl, setQrDataUrl] = useState(""),
    [copyNotice, setCopyNotice] = useState(false),
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
    if (savingSubjectRef.current) return;
    savingSubjectRef.current = true;
    setSavingSubject(true);
    setError("");
    setSubjectNotice("");
    try {
      const r = await fetch(`${API}/subjects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, oud, ico: ico || null, dic: dic || null, ic_dph: icDph }),
      });
      const data = await r.json();
      if (!r.ok) {
        setError(
          typeof data.detail === "string"
            ? data.detail
            : "Skontrolujte n?zov a identifik?tory subjektu.",
        );
        return;
      }
      setSubjects((items) => [...items.filter((item) => item.id !== data.id), data]);
      setSubjectId(String(data.id));
      setSubjectNotice(
        r.status === 200
          ? "Subjekt už je uložený. Vybrali sme existujúci záznam."
          : "Subjekt bol uložený.",
      );
      setPreview(null);
      setName("");
      setOud("");
      setIco("");
      setDic("");
      setIcDph(null);
    } catch {
      setError("Subjekt sa nepodarilo ulo?i?. Sk?ste znova.");
    } finally {
      savingSubjectRef.current = false;
      setSavingSubject(false);
    }
  }
  async function updateSubject() {
    const r = await fetch(`${API}/subjects/${subjectId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, oud, ico: ico || null, dic: dic || null, ic_dph: icDph }),
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
    setCopyNotice(false);
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
  useEffect(() => {
    let cancelled = false;
    if (!preview) {
      setQrDataUrl("");
      return;
    }
    try {
      const payload = encodePay({
        payments: [
          {
            type: PaymentOptions.PaymentOrder,
            amount: Number(preview.amount),
            variableSymbol: preview.variable_symbol,
            currencyCode: CurrencyCode.EUR,
            beneficiary: { name: "" },
            bankAccounts: [{ iban: preview.iban }],
            paymentNote: preview.rule_name,
          },
        ],
      });
      QRCode.toDataURL(payload, { errorCorrectionLevel: "M", margin: 2 }).then((url) => {
        if (!cancelled) setQrDataUrl(url);
      });
    } catch {
      setQrDataUrl("");
    }
    return () => {
      cancelled = true;
    };
  }, [preview]);
  function exportSubjects() {
    const rows = [
      "name,oud,ico,dic,ic_dph",
      ...subjects.map((s) =>
        [s.name, s.oud, s.ico ?? "", s.dic ?? "", s.ic_dph ?? ""]
          .map((v) => `"${v.replace(/"/g, '""')}"`)
          .join(","),
      ),
    ];
    const link = document.createElement("a");
    link.href = URL.createObjectURL(
      new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8" }),
    );
    link.download = "subjekty.csv";
    link.click();
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
      `Splatnosť: ${formatDueDate(preview.due_date)}`,
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
  function emailText() {
    if (!preview) return "";
    return [
      "Dobrý deň,",
      "",
      `V prílohe Vám posielame podklad k úhrade: ${preview.rule_name}`,
      `Účet:  ${preview.domestic_account}`,
      `IBAN: ${preview.iban}`,
      `Variabilný symbol: ${preview.variable_symbol}`,
      `Suma: ${preview.amount} ${preview.currency}`,
      `Splatnosť:  ${formatDueDate(preview.due_date)}`,
      `Text: ${preview.rule_name}`,
    ].join("\n");
  }
  function formatDueDate(value: string | null) {
    if (!value) return "neurčená";
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
    return match ? `${Number(match[3])}.${Number(match[2])}.${match[1]}` : value;
  }
  async function copyEmailSection() {
    const text = emailText();
    if (!qrDataUrl || !navigator.clipboard?.write || typeof ClipboardItem === "undefined") {
      await copy(text);
      setCopyNotice(true);
      return;
    }
    const qrBlob = await fetch(qrDataUrl).then((response) => response.blob());
    const html = `<div style="font-family: Arial, sans-serif; white-space: pre-wrap; line-height: 1.35">${text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(
        />/g,
        "&gt;",
      )}</div><p><strong>PAY by square QR kód</strong></p><img src="${qrDataUrl}" alt="PAY by square QR kód" width="240">`;
    await navigator.clipboard.write([
      new ClipboardItem({
        "text/plain": new Blob([`${text}\n\nPAY by square QR kód`], { type: "text/plain" }),
        "text/html": new Blob([html], { type: "text/html" }),
        "image/png": qrBlob,
      }),
    ]);
    setCopyNotice(true);
  }
  return (
    <main>
      <h1>Platobné údaje pre dane</h1>
      <p>Pripravte si kontrolovateľné údaje k úhrade dane.</p>
      <section>
        <h2>1. Daňový subjekt</h2>
        <form onSubmit={searchSubject}>
          <label>
            Vyhľadať podľa názvu, IČO alebo DIČ
            <input
              aria-label="Vyhľadať podľa názvu, IČO alebo DIČ"
              value={identifier}
              onChange={(e) => {
                setIdentifier(e.target.value);
                setLookup(null);
              }}
              inputMode="numeric"
              disabled={lookingUp}
              placeholder="Názov spoločnosti, IČO alebo DIČ"
            />
          </label>
          <button disabled={lookingUp || identifier.trim().length < 3}>
            {lookingUp ? "Načítavam údaje FS…" : "Vyhľadať subjekt"}
          </button>
        </form>
        <p>
          OÚD dopĺňame z účtu zverejneného Finančnou správou pre platiteľov DPH. Pri ostatných
          subjektoch zadajte OÚD ručne. Prvé vyhľadanie môže trvať niekoľko minút.
        </p>
        {lookupError && <p role="alert">{lookupError}</p>}
        {lookup && (
          <div aria-live="polite">
            <p>
              <a href={lookup.source_url} target="_blank" rel="noreferrer">
                Zdroj: Finančné riaditeľstvo SR
              </a>
              {` · Register: ${lookup.registry_date} · Účty: ${lookup.accounts_date}`}
            </p>
            {lookup.results.length === 0 && (
              <p>Subjekt sa v zverejnených zoznamoch nenašiel. Údaje môžete zadať ručne.</p>
            )}
            {lookup.results.map((result, index) => (
              <div key={`${result.ico}-${result.dic}-${index}`}>
                <p>
                  <strong>{result.name}</strong> — {result.address}
                  <br />
                  IČO: {result.ico ?? "neuvedené"} · DIČ: {result.dic ?? "neuvedené"} · OÚD:{" "}
                  {result.oud ?? "nedostupný – doplňte ručne"}
                </p>
                <button type="button" onClick={() => chooseSubject(result)}>
                  Vybrať {result.name}
                </button>
              </div>
            ))}
          </div>
        )}
        <p>
          <a
            href="https://www.financnasprava.sk/sk/elektronicke-sluzby/verejne-sluzby/overenie-prideleneho-oud"
            target="_blank"
            rel="noreferrer"
          >
            Overiť OÚD na portáli Finančnej správy
          </a>
        </p>
        <form onSubmit={addSubject} className="inline-form">
          <label>
            Daňový subjekt
            <input
              aria-label="Názov subjektu"
              placeholder="Názov spoločnosti"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <label>
            IČO
            <input
              aria-label="IČO"
              placeholder="8 číslic (nepovinné)"
              value={ico}
              onChange={(e) => setIco(e.target.value)}
              inputMode="numeric"
            />
          </label>
          <label>
            DIČ
            <input
              aria-label="DIČ"
              placeholder="10 číslic (nepovinné)"
              value={dic}
              onChange={(e) => setDic(e.target.value)}
              inputMode="numeric"
            />
          </label>
          <label>
            OÚD
            <input
              aria-label="OÚD"
              placeholder="10 číslic"
              value={oud}
              onChange={(e) => setOud(e.target.value)}
            />
          </label>
          <button disabled={savingSubject || !name.trim() || !oud}>
            {savingSubject ? "Ukladám subjekt…" : "Uložiť subjekt"}
          </button>
        </form>
        <p>
          Pred uložením potvrďte kontrolou, že názov, identifikátory a OÚD patria vybranému
          subjektu. Kontrola formátu identifikátora nepotvrdzuje jeho existenciu.
        </p>
        {subjectNotice && <p role="status">{subjectNotice}</p>}
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
              setIco(selected?.ico ?? "");
              setDic(selected?.dic ?? "");
              setIcDph(selected?.ic_dph ?? null);
              setPreview(null);
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
            <dd>{preview.iban}</dd>
            <dt>Variabilný symbol</dt>
            <dd>{preview.variable_symbol}</dd>
            <dt>Suma</dt>
            <dd>{preview.amount} EUR</dd>
            <dt>Splatnosť</dt>
            <dd>{formatDueDate(preview.due_date)}</dd>
            <dt>Pravidlo</dt>
            <dd>{preview.rule_name}</dd>
          </dl>
          {qrDataUrl && (
            <div>
              <h3>PAY by square QR</h3>
              <img src={qrDataUrl} alt="PAY by square QR kód" width="240" />
            </div>
          )}
          <p>
            <a href={preview.source_url} target="_blank" rel="noreferrer">
              Oficiálny zdroj pravidla
            </a>
          </p>
          <div role="alert" className="warning">
            {preview.warning}
          </div>
          <button type="button" onClick={() => setShowPrintPreview((visible) => !visible)}>
            Vytvoriť text e-mailu
          </button>
          {showPrintPreview && (
            <div className="print-preview">
              <h3>Text pre e-mail</h3>
              <pre>{emailText()}</pre>
              {qrDataUrl && (
                <div>
                  <h4>PAY by square QR kód</h4>
                  <img src={qrDataUrl} alt="PAY by square QR kód pre e-mail" width="240" />
                </div>
              )}
              <button type="button" onClick={copyEmailSection}>
                Kopírovať do e-mailu
              </button>
              {copyNotice && (
                <span className="copy-status" role="status">
                  Skopírované
                </span>
              )}
            </div>
          )}
          <div className="result-actions">
            <button type="button" onClick={exportPreview}>
              Exportovať TXT
            </button>
            <button type="button" onClick={exportSubjects} disabled={!subjects.length}>
              Exportovať subjekty CSV
            </button>
            <button type="button" onClick={savePreview} disabled={saved}>
              {saved ? "Uložené v histórii" : "Uložiť do histórie"}
            </button>
          </div>
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
