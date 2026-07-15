# Checkpoint 0073 - E14.4g expansion review ingestion ready

Data: 2026-07-15

## Obiettivo

Rendere ingeribili e verificabili le future ricevute indipendenti sui quattro
hard negative E14.4e, senza fabbricare decisioni, senza creare una queue
parziale e senza riaprire i 12 dossier gia' accettati.

## Piano eseguito

1. congelare gli hash di queue v6, curation audit, handoff audit, handoff
   contract e review schema v2;
2. limitare il dominio delle ricevute ai quattro dossier dell'handoff;
3. validare identita', indipendenza, hash, data, decisione, rationale e
   checklist completa;
4. applicare requisiti piu' stretti agli `accept`;
5. preservare byte-identici i 12 manifest precedentemente accettati;
6. scrivere la queue v7 soltanto dopo quattro ricevute valide;
7. produrre un audit retry-safe in caso di directory assente o incompleta;
8. mantenere chiusi coverage accettata, tassonomia, candidati e outer OOS.

## Astrazione introdotta

Il processo distingue ora tre oggetti:

- handoff immutabile: cosa deve essere revisionato;
- receipt directory esterna: decisioni prodotte fuori dal generatore;
- ingestion audit: validazione delle decisioni, senza modificarne il
  contenuto.

Una queue revisionata e' un oggetto atomico: non viene scritta con 0--3
ricevute. Questo evita che uno stato parziale venga scambiato per una nuova
base autorevole e rende il retry indipendente dall'audit diagnostico iniziale.

## Regole delle ricevute

- schema v2 e chiavi esatte;
- una sola ricevuta per dossier e `reviewId` univoco;
- hash identico al dossier copiato nell'handoff;
- reviewer diverso dall'autore del dossier pack;
- dichiarazione di indipendenza esatta;
- rationale di almeno 80 caratteri;
- controevidenza considerata e output di modello esclusi per ogni decisione;
- per `accept`: fonti aperte, claim supportato e confini supportati.

## Esito reale

- ricevute attese: 4;
- ricevute trovate: 0;
- ricevute mancanti: 4;
- reviewer indipendenti: 0;
- queue v7 scritta: no;
- coverage gate autorizzato: no;
- tassonomia aggiornata: no;
- candidati generati: no.

Stato: `EXPANSION_REVIEW_INCOMPLETE`.

Questo e' un gate metodologico atteso, non un errore applicativo. L'ingestione
non puo' sostituirsi al reviewer e non deve trasformare i template in ricevute.

## Identita' degli artefatti

- ingestion contract SHA-256:
  `ceb9448e549f3c7ea38906a84849d8036278758174c815d9f58c5275001b23c8`;
- readiness audit SHA-256:
  `14a67bc8e2ffd6876446c0916d29ecaf689e86cf1bdfbcc1a18b52010cdf6f39`;
- handoff audit SHA-256 preservato:
  `1521078052aa480173328e3377625909b6b2435a6978210af06a5b6cf2f79083`;
- queue v6 SHA-256 preservata:
  `c4eb4b7763db757e1f5290238efcb4f0c97ba3221063e763d8730f4dc1f59c02`.

## Verifiche

- test mirati E14.4g: 3/3 superati;
- suite Python completa: 87/87 test superati;
- compilazione bytecode Python: superata;
- suite .NET completa Debug/net10.0: 240/240 test superati;
- run incompleto deterministico e senza queue parziale: superato;
- quattro accept validi preservano i 12 manifest e aprono solo il coverage
  gate: superato tramite fixture di test;
- `accept` con fonti non aperte rifiutato prima di scrivere output: superato;
- comando CLI reale senza ricevute: eseguito con esito non-success atteso.

## Prossimo passo

Un reviewer indipendente deve copiare i quattro template fuori dal bundle,
aprire tutte le fonti e produrre le ricevute nella directory indicata. Dopo la
consegna si riesegue E14.4g verso output immutabili nuovi. Solo quattro
`accept` consentiranno E14.4h, il coverage gate accettato; non autorizzeranno
direttamente tassonomia o candidati.
