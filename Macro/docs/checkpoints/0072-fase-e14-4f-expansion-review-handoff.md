# Checkpoint 0072 - E14.4f expansion review handoff

Data: 2026-07-15

## Obiettivo

Consegnare i quattro hard negative E14.4e a un reviewer indipendente mediante
un bundle immutabile, senza riaprire i 12 dossier gia' accettati e senza
confondere la preparazione della review con la sua esecuzione.

## Piano eseguito

1. congelare un contratto con gli hash di queue v6, audit E14.4e, contratto di
   espansione e schemi dossier/review;
2. selezionare esclusivamente i quattro manifest
   `awaiting-expansion-independent-review`;
3. verificare hash, dimensione e contenuto di ogni dossier prima di scrivere;
4. copiare i dossier byte-identici in un bundle write-once;
5. creare un worksheet e un template schema v2 per ciascun dossier;
6. dichiarare i template non ingeribili e separare la directory delle future
   ricevute;
7. lasciare review, coverage accettata, tassonomia e candidati chiusi.

## Astrazione introdotta

La review dell'espansione e' separata in due transizioni:

- E14.4f: `reviewed -> handed-off`, senza decisioni;
- E14.4g: `handed-off -> accept|reject|needs-revision`, tramite ricevute
  indipendenti hash-bound.

Questa separazione impedisce al generatore del bundle di auto-attribuirsi
l'indipendenza e permette di ripetere l'ingestione senza ricostruire o mutare
il pacchetto consegnato.

## Contenuto del bundle reale

- dossier inclusi: 4;
- dossier accettati precedenti inclusi o riaperti: 0;
- copie dossier byte-identiche: 4;
- worksheet: 4;
- template di ricevuta schema v2: 4;
- occorrenze di locator evidenza/cont-evidenza: 12;
- ricevute indipendenti: 0.

Ogni worksheet richiede di valutare soltanto il meccanismo e il mese nominati.
Lo stress simultaneo in un altro meccanismo e' controevidenza da considerare,
ma non costituisce automaticamente un conflitto di label.

## Esito reale

Stato: `EXPANSION_AWAITING_EXTERNAL_REVIEW`.

- handoff pronto: si;
- review indipendente completa: no;
- copertura potenziale accettata: no;
- tassonomia aggiornata: no;
- candidati generati: no;
- outer OOS letto: no.

## Identita' degli artefatti

- handoff contract SHA-256:
  `862ae88dbac8c3305f8b0401f8c73570eb9b9e37e2bf9a8964a6fb7080802cec`;
- handoff audit SHA-256:
  `1521078052aa480173328e3377625909b6b2435a6978210af06a5b6cf2f79083`;
- queue v6 preservata SHA-256:
  `c4eb4b7763db757e1f5290238efcb4f0c97ba3221063e763d8730f4dc1f59c02`;
- curation audit preservato SHA-256:
  `cda82f4dfe613db2f93de5bae8c7a96ace9da3ef5cc4df9ccca61d2681a67e47`.

Hash dei dossier consegnati:

- regional bank stress 2023 / broad-market:
  `8f39d55e5521bd7e388ba98aa365dd5485273e9d481576942585eca227bbc291`;
- repo stress 2019 / cross-border:
  `c67c58a0312d68996ab72a79a50e5c8f2d524d70076fcadccff2a2097f64beb0`;
- risk repricing 2018Q4 / funding:
  `22c82fb6dc67a8acf37a82ed350c9bc6161a4a4f9aa1b87dc5face3691a92263`;
- stock market break 1987 / banking:
  `ccd1cc5601f28b712f66bafb63bdfafea9ab898264cc7981a388b4bd473ba114`.

## Garanzie di governance

- i 12 accept precedenti non sono nel bundle;
- un manifest manomesso blocca la scrittura prima di creare il bundle;
- un contratto che autorizza la review al generatore viene rifiutato;
- i template contengono placeholder e valori null, quindi non sono ricevute;
- tutti gli output sono write-once;
- modello, outer OOS e copertura potenziale non devono influenzare il reviewer.

## Verifiche

- test mirati E14.4f: 3/3 superati;
- suite Python completa: 84/84 test superati;
- compilazione bytecode Python: superata;
- suite .NET completa Debug/net10.0: 240/240 test superati;
- bundle deterministico e limitato a quattro dossier: superato;
- rifiuto della manomissione di un hash: superato;
- rifiuto dell'auto-review autorizzata dal contratto: superato;
- comando CLI reale: completato.

## Prossimo passo

E14.4g deve acquisire quattro ricevute da un reviewer indipendente, validarle
contro schema v2 e hash dell'handoff e produrre una nuova queue. Soltanto una
ingestione completa puo' ricontare la copertura accettata; `needs-revision` o
`reject` mantengono chiusi tassonomia e candidati.
