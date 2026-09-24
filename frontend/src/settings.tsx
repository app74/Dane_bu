import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "./api";

type DueSetting = {
  key: string;
  label: string;
  kind: string;
  day: number | null;
  shift_to_workday: boolean;
  description: string;
  basis: string;
  is_default: boolean;
};
type Holiday = { day: string; name: string };

const KIND_LABELS: Record<string, string> = {
  catalog: "Podľa oficiálneho číselníka",
  next_month_day: "Deň nasledujúceho mesiaca",
  period_end: "Posledný deň obdobia",
};

function formatDay(value: string) {
  const [year, month, day] = value.split("-");
  return `${Number(day)}.${Number(month)}.${year}`;
}

async function detail(response: Response, fallback: string) {
  const data = await response.json().catch(() => ({}));
  return typeof data.detail === "string" ? data.detail : fallback;
}

export function Settings() {
  const [rows, setRows] = useState<DueSetting[]>([]);
  const [holidays, setHolidays] = useState<Holiday[]>([]);
  const [year, setYear] = useState(new Date().getFullYear());
  const [newDay, setNewDay] = useState("");
  const [newName, setNewName] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch("/settings/due-dates")
      .then((r) => (r.ok ? r.json() : []))
      .then(setRows)
      .catch(() => setRows([]));
  }, []);
  useEffect(() => {
    apiFetch(`/settings/holidays?year=${year}`)
      .then((r) => (r.ok ? r.json() : { holidays: [] }))
      .then((data) => setHolidays(data.holidays ?? []))
      .catch(() => setHolidays([]));
  }, [year]);

  function change(key: string, patch: Partial<DueSetting>) {
    setRows((items) => items.map((item) => (item.key === key ? { ...item, ...patch } : item)));
  }

  async function save(row: DueSetting) {
    setMessage("");
    setError("");
    const r = await apiFetch(`/settings/due-dates/${row.key}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kind: row.kind,
        day: row.kind === "next_month_day" ? row.day : null,
        shift_to_workday: row.shift_to_workday,
      }),
    });
    if (!r.ok) {
      setError("Pravidlo splatnosti sa nepodarilo uložiť. Skontrolujte deň (1 až 31).");
      return;
    }
    const saved: DueSetting = await r.json();
    change(row.key, saved);
    setMessage(`Uložené: ${saved.label}. Prejaví sa pri ďalšom vytvorení náhľadu.`);
  }

  async function reset(row: DueSetting) {
    setMessage("");
    setError("");
    const r = await apiFetch(`/settings/due-dates/${row.key}`, { method: "DELETE" });
    if (!r.ok) {
      setError("Predvolené pravidlo sa nepodarilo obnoviť.");
      return;
    }
    const saved: DueSetting = await r.json();
    change(row.key, saved);
    setMessage(`Obnovené predvolené pravidlo: ${saved.label}.`);
  }

  async function addHoliday(e: FormEvent) {
    e.preventDefault();
    setMessage("");
    setError("");
    const r = await apiFetch("/settings/holidays", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ day: newDay, name: newName }),
    });
    if (!r.ok) {
      setError(await detail(r, "Sviatok sa nepodarilo pridať."));
      return;
    }
    const added: Holiday = await r.json();
    if (Number(added.day.slice(0, 4)) === year)
      setHolidays((items) => [...items, added].sort((a, b) => a.day.localeCompare(b.day)));
    setNewDay("");
    setNewName("");
    setMessage(`Pridaný deň pracovného pokoja ${formatDay(added.day)}.`);
  }

  async function removeHoliday(holiday: Holiday) {
    setMessage("");
    setError("");
    const r = await apiFetch(`/settings/holidays/${holiday.day}`, { method: "DELETE" });
    if (!r.ok) {
      setError("Sviatok sa nepodarilo odstrániť.");
      return;
    }
    setHolidays((items) => items.filter((item) => item.day !== holiday.day));
  }

  return (
    <section>
      <details>
        <summary>
          <h2>Nastavenia splatnosti</h2>
        </summary>
        <p>
          Splatnosť sa počíta podľa pravidla skupiny. Pri posune sa sobota, nedeľa a deň zo zoznamu
          sviatkov posúvajú na najbližší pracovný deň. Zmeny sa prejavia v novom kontrolnom náhľade
          aj v texte e-mailu; uložená história sa nemení.
        </p>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Skupina pravidiel</th>
                <th>Spôsob výpočtu</th>
                <th>Deň</th>
                <th>Posun na pracovný deň</th>
                <th>Akcie</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.key}>
                  <td>
                    <strong>{row.label}</strong>
                    <br />
                    <small>{row.basis}</small>
                  </td>
                  <td>
                    <select
                      aria-label={`Spôsob výpočtu – ${row.label}`}
                      value={row.kind}
                      onChange={(e) =>
                        change(row.key, {
                          kind: e.target.value,
                          day: e.target.value === "next_month_day" ? (row.day ?? 25) : null,
                        })
                      }
                    >
                      {Object.entries(KIND_LABELS).map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <input
                      aria-label={`Deň splatnosti – ${row.label}`}
                      type="number"
                      min={1}
                      max={31}
                      disabled={row.kind !== "next_month_day"}
                      value={row.day ?? ""}
                      onChange={(e) =>
                        change(row.key, { day: e.target.value ? Number(e.target.value) : null })
                      }
                    />
                  </td>
                  <td>
                    <input
                      aria-label={`Posun na pracovný deň – ${row.label}`}
                      type="checkbox"
                      disabled={row.kind === "catalog"}
                      checked={row.shift_to_workday}
                      onChange={(e) => change(row.key, { shift_to_workday: e.target.checked })}
                    />
                  </td>
                  <td>
                    <button type="button" onClick={() => save(row)}>
                      Uložiť
                    </button>{" "}
                    <button type="button" onClick={() => reset(row)} disabled={row.is_default}>
                      Predvolené
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3>Sviatky a dni pracovného pokoja</h3>
        <p>
          Predvolený zoznam obsahuje iba dni potvrdené zákonom č. 241/1993 Z.z. Pred použitím overte
          aktuálne znenie zákona a chýbajúce dni doplňte.
        </p>
        <label>
          Rok
          <input
            aria-label="Rok sviatkov"
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
          />
        </label>
        <ul>
          {holidays.map((holiday) => (
            <li key={holiday.day}>
              {formatDay(holiday.day)} – {holiday.name}{" "}
              <button
                type="button"
                className="small-button"
                onClick={() => removeHoliday(holiday)}
                aria-label={`Odstrániť ${formatDay(holiday.day)}`}
              >
                Odstrániť
              </button>
            </li>
          ))}
          {holidays.length === 0 && <li>Pre tento rok nie sú zadané žiadne sviatky.</li>}
        </ul>
        <form onSubmit={addHoliday} className="inline-form">
          <label>
            Dátum
            <input
              aria-label="Dátum sviatku"
              type="date"
              value={newDay}
              onChange={(e) => setNewDay(e.target.value)}
            />
          </label>
          <label>
            Názov
            <input
              aria-label="Názov sviatku"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
          </label>
          <button disabled={!newDay || !newName.trim()}>Pridať sviatok</button>
        </form>
        {message && <p role="status">{message}</p>}
        {error && <p role="alert">{error}</p>}
      </details>
    </section>
  );
}
