# Checkpoint 0105 - E14.7n redesign in attesa di review

Data: 2026-07-16

## Esito

La proposta di redesign post-2005 e' stata materializzata senza acquisire
osservazioni. Preserva i due meccanismi gia' vintage-fit e contiene due item:

- sostituzione di H.10 con il candidato provider-primary G.5 mensile, che copre
  88/88 mesi prima del taper tantrum e conserva Broad/OITP nelle release datate;
- disponibilita' FDIC basata esclusivamente su data reale di pubblicazione
  corroborata, mai su quarter-end o esistenza odierna del link.

Il break G.5 del 2019-02-04 separa il regime Broad/OITP dal regime
Broad/AFE/EME. Splice, backcast event-time e soglie condivise non sono
autorizzati. Q3 2025 FDIC e' eleggibile dal 2025-11-24; Q4 resta post-cutoff.

Hash principali:

- proposta: `d88716b411e22332545422086521d2987232e293dc92c78b9a426bbeb10a019a`;
- queue: `6f60c9e7c224a4840ff9d1545028ef5a044362614fc676f73dec2f7bafea9ab0`;
- audit: `a477ffe7ed6731bf92ab260740baada0e1976fffb525dbb0416669d900fb4fe0`.

## Decisione

La queue contiene due dossier e zero receipt. E' autorizzato soltanto un bundle
di handoff alla review indipendente. Attivazione policy, request catalog,
acquisizione, trasformazione, candidati, evaluation e outer OOS restano chiusi.
