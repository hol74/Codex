# Checkpoint 0063 - E14.4a mechanism detector contract

Data: 2026-07-14

## Obiettivo

Formalizzare detector e dossier per singolo meccanismo prima di curare nuove
label, mantenendo chiusi dataset, outer OOS, composizione e candidati.

## Realizzato

- creato uno schema JSON chiuso e hash-bound per i dossier;
- richiesti almeno due item di evidenza, provider indipendenti, counterevidence
  e due reviewer per un dossier accettato;
- resa obbligatoria la prova affermativa di funzionamento ordinato per ogni
  hard negative;
- congelati quattro detector indipendenti e sei feature proposte;
- confinati NFCI, STLFSI4 e OFR FSI al ruolo diagnostico;
- vietati zero imputation, splicing tra regimi metodologici e soglie scelte
  fuori dall'inner LOEO;
- separati gli stati `calm`, `onset`, `active` e `recovery` con isteresi;
- implementato un contract audit deterministico e write-once.

## Esito

Tutti i controlli del contratto passano. Lo stato e'
`READY_FOR_DOSSIER_CURATION`: sono autorizzati soltanto costruzione e giudizio
dei dossier E14.4b.

Restano vietati:

- modifica diretta della ground truth da un dossier;
- popolazione del corpus;
- fitting e selezione delle soglie;
- composizione dei detector;
- generazione, ranking o promozione di candidati.

## Identita' degli artefatti

- dossier schema SHA-256:
  `6163ab4cf6249aa314708361d1572ade403844b2cca9b4deb9c6bfaca3c7702f`;
- detector contract SHA-256:
  `b974b5b5e865a46438449e6d1dc0beb8d821e3656f0074b207d0eca96fd6d685`;
- contract audit report SHA-256:
  `c1811ece8246569cf151f3f69511a6c4ce5761cbe32b1a9bd5ea8fc40c2b3bd0`.

## Decisione

Procedere con E14.4b: curare e adjudicare dossier mechanism-specific sulle
cinque ipotesi positive, cercando separatamente hard negative con evidenza
affermativa. Un successivo gate, non i dossier stessi, decidera' se aggiornare
la label foundation.

## Verifica

- test mirati E14.4a: 2/2 superati;
- `dotnet test MacroRegime.slnx --no-restore`: 240/240 test superati;
- `python -m unittest discover -s tests -v`: 60/60 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- audit deterministico e write-once;
- dataset e dossier non letti, zero righe outer utilizzate;
- rifiuto di un indice composito diagnostico promosso a feature detector.
