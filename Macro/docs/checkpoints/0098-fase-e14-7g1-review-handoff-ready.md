# Checkpoint 0098 - E14.7g1 handoff review esterna pronto

Data: 2026-07-16

## Obiettivo

Consegnare proposta, queue e dossier E14.7f in un bundle immutabile e rendere
eseguibile l'ingestion fail-closed, senza attribuire al generatore del bundle il
ruolo di reviewer indipendente.

## Bundle

Il bundle contiene:

- proposta taxonomy e queue copiate byte-identiche;
- 2 dossier con SHA-256 verificato;
- 2 worksheet con tutti i locator e la counterevidence;
- 2 template receipt schema v2 con placeholder e `null` intenzionali;
- istruzioni che impongono receipt completate fuori dal bundle.

Audit handoff SHA-256:
`0bf1cbcc51ca8cbf9c7eee7e3bae228a1b0cf1dfad0464b8c6aebf856beb8243`.

## Ingestion fail-closed

Il validatore richiede:

- schema v2 esatto;
- dossier SHA-256 uguale alla queue;
- reviewer diverso dal dossier author;
- una receipt per dossier;
- counterevidence considerata e nessun model output usato;
- per `accept`, locator aperti, meccanismo supportato e confini supportati.

Il dry-run reale con directory receipt assente ha prodotto:

- receipt: 0/2;
- stato: `POST_2005_INDEPENDENT_REVIEW_INCOMPLETE`;
- reviewed queue readiness SHA-256:
  `13e13f0d71d58c003c472820524ba33414b4a30713909d3fbdf80d89325078a0`;
- ingestion readiness audit SHA-256:
  `71a48069d7dc3731f341910bd31f2227c73cf7f16b7913705c79c5234835c120`;
- scope attivo: no;
- acquisizione dati autorizzata: no.

## Decisione

E14.7g1 e' completato tecnicamente. E14.7g2 resta aperto in attesa di due
receipt autentiche prodotte da un reviewer realmente indipendente che apra le
fonti citate. Non sono state fabbricate receipt reali per chiudere il gate.

Anche l'eventuale accettazione di entrambi i dossier autorizzera' soltanto un
gate E14.7h separato; non attivera' direttamente scope o acquisizione.

## Verifiche

- test mirati handoff/ingestion: 5/5;
- bundle deterministico e write-once: superato;
- dossier tamper rejection: superato;
- receipt hash mismatch rejection: superato;
- missing receipt fail-closed: superato;
- regressione Python: 171/171;
- `compileall`: superato;
- test .NET sui sei assembly: 240/240.
