# Overenie pravidiel platieb

Stav overenia: 2026-09-22. Použité sú výhradne zdroje Finančnej správy SR.
Tento dokument je auditná pomôcka; pri zmene oficiálnych dokumentov sa pravidlá
nesmú spätne prepísať, ale musí vzniknúť nová verzia.

## Všeobecné pravidlá

| Pravidlo | Potvrdenie | Verzia / platnosť |
| --- | --- | --- |
| Účet má tvar `predčíslie + OÚD / 8180` a pre platbu sa používa IBAN | [Platenie cla, daní a poplatkov](https://www.financnasprava.sk/sk/infoservis/platenie-dani), [informácia DPPO 2025](https://www.financnasprava.sk/_img/pfsedit/Dokumenty_PFS/Zverejnovanie_dok/Aktualne/DP/DPPO/2026/2026.01.15_001_PO_2026_IM_plat_dane.pdf) | `account-format-2026-01`, platné od 2014-02-01; overené 2026-09-22 |
| VS je 10 číselných znakov; v referencii platby sa odporúča prefix `VS` | [Platenie cla, daní a poplatkov](https://www.financnasprava.sk/sk/infoservis/platenie-dani) | `vs-format-2026-01`, overené 2026-09-22 |
| OÚD sa používa ako základné číslo účtu a používateľ ho zadáva/overí samostatne | [Vytvorenie platobných inštrukcií](https://www.financnasprava.sk/sk/elektronicke-sluzby/verejne-sluzby/vytvorenie-platobnych-instrukc/vytvorenie-platobnych-instrukc) | `oud-manual-2026-01`, overené 2026-09-22 |

## Potvrdené pravidlá v MVP číselníku

| ID | Druh / typ | Obdobie | Predčíslie | VS | Splatnosť | Stav |
| --- | --- | --- | --- | --- | --- | --- |
| `vat-2026-monthly` | DPH, mesačný platiteľ | konkrétny mesiac `MM` roku `YYYY` | `500240` | `1100MMYYYY` | 25. deň nasledujúceho mesiaca, ak oficiálny zoznam potvrdzuje obdobie | podporované iba pre potvrdené obdobia |
| `vat-2026-quarterly` | DPH, štvrťročný platiteľ | štvrťrok `Q` roku `YYYY` | `500240` | `1100(40+Q)YYYY` | 25. deň po skončení štvrťroka, ak oficiálny zoznam potvrdzuje obdobie | podporované iba pre potvrdené obdobia |
| `vat-2026-month-03` | DPH, marec 2026 | 03/2026 | `500240` | `1100032026` | 27.04.2026 | potvrdené |
| `vat-2026-quarter-01` | DPH, I. štvrťrok 2026 | Q1/2026 | `500240` | `1100412026` | 27.04.2026 | potvrdené |
| `income-return-2025` | Daň z príjmov FO/PO z priznania | rok `2025` | podľa subjektu; DPPO tuzemsko `500224`, zahraničie `500232` | `1700992025` | 31.03.2026 pre priznanie za 2025 | potvrdené |
| `income-fo-resident-2025` | Daň z príjmov FO rezident | rok `2025` | `500208` | `1700992025` | 31.03.2026 | potvrdené |
| `income-fo-nonresident-2025` | Daň z príjmov FO nerezident | rok `2025` | `500216` | `1700992025` | 31.03.2026 | potvrdené |
| `motor-vehicle-return-2025` | Daň z motorových vozidiel z priznania | rok `2025` | `501163` | `1700992025` | najneskôr 02.02.2026 | potvrdené |
| `income-po-advance-2026-month-01` | Preddavok DPPO, január | 01/2026 | `500224` | `1100012026` | 02.02.2026 | potvrdené |
| `income-po-advance-2026-quarter-01` | Preddavok DPPO, I. štvrťrok | Q1/2026 | `500224` | `1100412026` | 31.03.2026 | potvrdené |
| `withholding-dividend-2026-05` | Zrážková daň z dividend | dividendy vyplatené 05/2026 | `500267` | `1700052026` | 15.06.2026 | potvrdené iba pre tento konkrétny rez |
| `withholding-2026-month` | Zrážková daň podľa §43 ods. 11 | mesiac `MM` roku `YYYY` | účet a splatnosť sa berú z konkrétneho zoznamu VS | `1700MMYYYY` | 15. deň nasledujúceho mesiaca, posun podľa oficiálneho zoznamu | podporované iba pre potvrdené obdobia |
| `income-advance-2026-month` | Preddavok na daň z príjmov, mesačný | mesiac `MM` roku `YYYY` | podľa konkrétneho druhu platby | `1100MMYYYY` alebo `110000YYYY` | podľa oficiálneho zoznamu VS | podporované iba pre potvrdené obdobia |

Zdroje pre konkrétne potvrdenia: [VS I. štvrťrok 2026](https://www.financnasprava.sk/_img/pfsedit/Dokumenty_PFS/Infoservis/Platenie_dani/2026/2025.12.16_VS_1Q_2026.pdf), [DPH – finančné vyrovnanie](https://www.financnasprava.sk/sk/podnikatelia/dane/dan-z-pridanej-hodnoty/financne-vyrovnanie-dph), [informácia k DPPO 2025](https://www.financnasprava.sk/_img/pfsedit/Dokumenty_PFS/Zverejnovanie_dok/Aktualne/DP/DPPO/2026/2026.01.15_001_PO_2026_IM_plat_dane.pdf), [informácia k DMV 2025](https://www.financnasprava.sk/_img/pfsedit/Dokumenty_PFS/Zverejnovanie_dok/Aktualne/Dan_z_MV/2026/2026.01.12_001_DMV_2026_IM.pdf), [informácia k zrážkovej dani z dividend 2026](https://www.financnasprava.sk/_img/pfsedit/Dokumenty_PFS/Zverejnovanie_dok/Aktualne/DP/DPPO/2026/2026.01.15_006_PO_2026_IM_podiel_zisk.pdf).

## Splatnosť (nastaviteľné pravidlá)

Splatnosť v náhľade sa počíta podľa `app/due_settings.py` a nastavení v UI (manual.md, kapitola 14):

| Skupina | Pravidlo | Zdroj / overenie |
| --- | --- | --- |
| DPH mesačne a štvrťročne | 25. deň mesiaca po skončení obdobia, posun na najbližší pracovný deň | § 78 ods. 1 zákona č. 222/2004 Z.z. ([Slov-Lex](https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/2004/222/)), overené 2026-09-24; posun podľa požiadavky používateľa, znenie daňového poriadku neoverené |
| Preddavky DPPO | posledný deň obdobia, posun na pracovný deň | zhoda s oficiálnym zoznamom VS (02.02.2026 za január 2026) |
| Ostatné potvrdené pravidlá | dátum z číselníka | konkrétna informácia FS SR v riadku pravidla |
| Dni pracovného pokoja | tabuľka `public_holidays` | zákon č. 241/1993 Z.z. v znení 261/2025 Z.z. ([Slov-Lex](https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/1993/241/)), [Úrad vlády SR](https://www.vlada.gov.sk/slovensko/statne-sviatky/), overené 2026-09-24 |

## Nepodporované alebo vyžadujúce doplnenie

- Obdobia, pre ktoré oficiálny zoznam neuvádza presný VS a splatnosť.
- Automatické získavanie OÚD cez službu chránenú CAPTCHA.
- Zrážková daň bez určenia konkrétneho paragrafu a obdobia.
- Preddavky, pri ktorých nie je vybraná jednoznačná oficiálna varianta VS.
- Akékoľvek pravidlo odvodené iba z IČO, DIČ alebo IČ DPH.

## Testovacie vektory bez citlivých údajov

OÚD `1234567890` je syntaktický testovací údaj, nie reálny subjekt.

| Prípad | Vstup | Očakávanie |
| --- | --- | --- |
| DPPO tuzemsko za 2025 | predčíslie `500224`, OÚD `1234567890`, banka `8180` | VS `1700992025`, IBAN MOD-97 platný |
| DMV za 2025 | predčíslie `501163`, OÚD `1234567890`, banka `8180` | VS `1700992025`, IBAN MOD-97 platný |
| DPH január 2026 | predčíslie `500240`, OÚD `1234567890`, banka `8180` | VS `1100012026` |
| Neplatný VS | `110012026` | odmietnuť, nie je 10 číslic |
