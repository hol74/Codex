# Checkpoint 0068 - E14.4b4 targeted revision accepted

Data: 2026-07-14

## Obiettivo

Correggere esclusivamente i quattro dossier `needs-revision`, preservare gli
otto hash gia' accettati e riesaminare soltanto gli artefatti realmente mutati.

## Piano eseguito

1. tradurre ogni rilievo del reviewer in una modifica di confine o fonte;
2. congelare un contratto che lega ogni revisione al suo esatto hash base;
3. generare quattro dossier nuovi, una queue 8+4 e un bundle mirato;
4. affidare il bundle allo stesso ruolo reviewer separato dall'autore delle
   revisioni, senza usare le decisioni precedenti come evidenza;
5. ingerire soltanto le quattro nuove ricevute schema v2;
6. conservare chiusi ground truth, label, dataset e generazione candidati.

## Revisioni effettuate

- Continental Illinois banking-credit: `1984-05`--`1984-08`; i deflussi
  proseguono fino al 29 agosto e l'implementazione del piano in settembre
  fornisce la prima stabilizzazione successiva esplicita.
- Messico broad-market repricing: `1994-12`--`1995-03`; il picco dei tassi a
  meta' marzo e la ripresa di peso ed equity in aprile provano il confine.
- Messico cross-border growth: `1994-12`--`1995-06`; l'aggiustamento commerciale
  resta visibile nel secondo trimestre e viene delimitato dalla tenuta delle
  esportazioni complessive entro giugno.
- Messico banking-credit hard-negative: `1994-12`--`1995-03`; il locator FDIC
  non renderizzabile e' sostituito dal QBP 1995 Q1, che documenta utili bancari
  e crescita record dei prestiti commerciali, insieme all'evidenza FOMC.

## Proprietà di governance

- gli 8 dossier accettati non sono stati copiati nel nuovo bundle e i loro
  hash sono rimasti byte-identici;
- solo i 4 `needs-revision` potevano cambiare;
- ogni revisione dichiara e valida il proprio hash base;
- ogni nuovo dossier deve avere un hash diverso dal precedente;
- il reviewer e' distinto dall'autore delle revisioni;
- un `accept` richiede locator aperti, claim e confini supportati;
- nessun output di modello o metrica outer-OOS e' stato usato.

## Esito

- review mirate: 4/4 `accept`;
- `needs-revision`: 0;
- `reject`: 0;
- dossier complessivamente accettati: 12/12;
- stato: `READY_FOR_LABEL_FOUNDATION_GATE`;
- label scritte: 0;
- candidati generati: 0.

## Identita' degli artefatti

- targeted queue v4 SHA-256:
  `54adb9c12fe01035410468832029b1909b4fa9c7a9af4a975358bc78fe373947`;
- revision audit SHA-256:
  `00a343b5ddb383d0976614bfa14b525b752c14d7bc4201c279a9a35bde502eac`;
- reviewed queue v5 SHA-256:
  `248e11a03925443f0fa9b797e5f6601b68968f0fdb9260de08c3aade5cb3227c`;
- targeted ingestion audit SHA-256:
  `1bccb53e4f63aab5f560c5001dfe44376ad1f3b9da958bcef947594156baee67`.

## Limite dell'indipendenza

Il reviewer e' un'istanza agente distinta dall'autore delle revisioni. La
separazione e' reale a livello di workflow e ricevute, ma non equivale a una
peer review umana o istituzionale esterna.

## Verifiche

- test mirati revisione e ingestion: 5/5 superati;
- suite Python completa: 74/74 test superati;
- compilazione bytecode Python: superata;
- suite .NET completa: 240/240 test superati;
- determinismo e write-once: verificati;
- tentativo di modificare un dossier accettato: rifiutato dai test;
- hash base errato o `accept` con confine non supportato: rifiutati dai test.

## Prossimo passo

E14.4c deve costruire un label-foundation gate separato. Prima di scrivere
ground truth dovra' validare sovrapposizioni, conflitti tra meccanismi,
granularita' mensile, hard negative e regole di composizione. La generazione di
candidati resta chiusa.
