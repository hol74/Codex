# Checkpoint 0066 - E14.4b3a external review handoff

Data: 2026-07-14

## Obiettivo

Rendere materialmente eseguibile la revisione indipendente dei 12 dossier,
senza confondere la preparazione del materiale con la revisione stessa.

## Piano eseguito

1. congelare gli hash della review queue, dell'audit e degli schemi;
2. ricontrollare hash, dimensione e stato di ogni dossier;
3. copiare i dossier nel bundle senza riserializzarli;
4. generare un worksheet con claim, confini, fonti e controevidenze;
5. generare un template hash-bound per la ricevuta del reviewer;
6. rendere i template non ingeribili fino alla compilazione completa;
7. manifestare ogni file generato e mantenere chiusi label e candidati.

## Realizzato

- contratto `e14-review-handoff-contract-v1`;
- comando CLI `e14-build-review-handoff`;
- 12 copie dossier byte-identiche agli originali;
- 12 worksheet Markdown;
- 12 template JSON per le ricevute;
- 36 occorrenze di locator a evidenze o controevidenze;
- README operativo per il reviewer;
- audit deterministico e write-once di tutti gli artefatti;
- test di determinismo, immutabilita' e rifiuto degli hash alterati.

## Regola operativa

Il reviewer deve lavorare su una copia del template fuori dal bundle, aprire
ogni locator e compilare identita', affiliazione, data, decisione, rationale e
checklist. I template contengono placeholder e `null`, quindi falliscono
intenzionalmente la validazione finche' non vengono completati.

## Esito

Stato: `AWAITING_EXTERNAL_REVIEW`.

- dossier consegnabili: 12;
- worksheet: 12;
- template: 12;
- ricevute indipendenti: 0;
- review eseguite dal generatore: 0;
- label scritte: 0;
- candidati generati: 0.

## Identita' degli artefatti

- handoff contract SHA-256:
  `cde66c507ce86a58b1480325c5f5771e26522428307eb3c7784425d0479137a5`;
- handoff audit SHA-256:
  `31dab5f771b9bf15e46aef3f9025c6394550d118dcddf262fe1be7d61d3ccd6b`;
- gli hash dei 37 file interni al bundle sono inclusi nell'audit.

## Prossimo passo

E14.4b3b e' esterno: consegnare il bundle a un reviewer distinto, ricevere i
12 JSON completati nella directory `e14-independent-reviews-v1` e rieseguire
`e14-adjudication-queue` su nuovi output write-once. Le decisioni negative o
`needs-revision` dovranno produrre un nuovo ciclo di dossier, non modifiche
in-place.

## Verifica

- test mirati E14.4b3a: 2/2 superati;
- `python -m unittest discover -s tests -v`: 66/66 superati;
- `dotnet test MacroRegime.slnx --no-restore`: 240/240 superati;
- `python -m compileall -q regime_eval tests`: superato;
- bundle generato due volte in test con contenuto byte-identico;
- riuso degli output rifiutato;
- alterazione di un hash dossier rifiutata prima della scrittura del bundle.
