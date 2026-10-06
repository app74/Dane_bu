import { useState } from "react";

export const FS_OUD_URL =
  "https://www.financnasprava.sk/sk/elektronicke-sluzby/verejne-sluzby/overenie-prideleneho-oud";

// Format check only: 6 digits, optional slash, 3 or 4 digits. It does not confirm the number exists.
const BIRTH_NUMBER = /^\d{6}\/?\d{3,4}$/;

/**
 * Helps a natural person find their OÚD on the official, CAPTCHA-protected FS form.
 * The birth number lives only in this component's state: it is never stored or sent to the backend.
 */
export function OudHelper() {
  const [birthNumber, setBirthNumber] = useState("");
  const [notice, setNotice] = useState("");
  const value = birthNumber.replace(/\s/g, "");
  const valid = BIRTH_NUMBER.test(value);

  async function copyAndOpen() {
    try {
      await navigator.clipboard.writeText(value);
      setNotice(
        "Rodné číslo je v schránke. Vložte ho do formulára Finančnej správy, opíšte znaky z obrázka a nájdený OÚD zadajte nižšie do poľa OÚD.",
      );
    } catch {
      setNotice(
        "Rodné číslo sa nepodarilo skopírovať. Zadajte ho do formulára Finančnej správy ručne.",
      );
    }
    setBirthNumber("");
    window.open(FS_OUD_URL, "_blank", "noopener,noreferrer");
  }

  return (
    <div className="oud-helper">
      <p>
        <strong>Fyzická osoba bez IČO a DIČ:</strong> OÚD podľa rodného čísla zistíte iba na portáli
        Finančnej správy (formulár je chránený bezpečnostným prvkom). Aplikácia rodné číslo neukladá
        ani neodosiela.
      </p>
      <label>
        Rodné číslo (neukladá sa)
        <input
          aria-label="Rodné číslo"
          placeholder="napr. 000000/0000"
          value={birthNumber}
          onChange={(e) => {
            setBirthNumber(e.target.value);
            setNotice("");
          }}
          autoComplete="off"
          inputMode="numeric"
        />
      </label>
      {birthNumber && !valid && (
        <p role="alert">Rodné číslo má tvar 6 číslic, voliteľne lomka, a 3 alebo 4 číslice.</p>
      )}
      <button type="button" onClick={copyAndOpen} disabled={!valid}>
        Skopírovať rodné číslo a otvoriť overenie OÚD
      </button>
      {notice && <p role="status">{notice}</p>}
      <p>
        <a href={FS_OUD_URL} target="_blank" rel="noreferrer">
          Overiť OÚD na portáli Finančnej správy
        </a>{" "}
        (podľa DIČ alebo rodného čísla)
      </p>
    </div>
  );
}
